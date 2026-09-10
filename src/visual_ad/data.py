"""Read-only MVTec inspection and deterministic, leakage-resistant manifests."""

import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from .common import CATEGORIES, digest, file_hash, read_json, safe_path, write_json
from .schema import SampleRecord

ROLES = ("fit", "validation_normal", "calibration_normal", "selection", "final_test")


def resolve_root(path):
    path = Path(path)
    if not path.is_dir():
        raise ValueError(f"Dataset directory unavailable: {path}")
    candidates = set()
    for train in path.glob("**/train"):
        category = train.parent
        if category.name in CATEGORIES and (train / "good").is_dir() and (category / "test").is_dir():
            candidates.add(category.parent.resolve())
    if len(candidates) != 1:
        raise ValueError(f"Expected one MVTec root, found {sorted(map(str, candidates))}")
    return candidates.pop()


def dataset_fingerprint(rows):
    records = [{k: v for k, v in row.items() if k != "split_role"} for row in rows]
    return digest(sorted(records, key=lambda row: row["sample_id"]))


def inspect_dataset(path, require_all=True, dataset_version="kaggle-ipythonx-local-content-hash"):
    root = resolve_root(path)
    categories = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name in CATEGORIES)
    if require_all and categories != list(CATEGORIES):
        raise ValueError(f"Missing categories: {sorted(set(CATEGORIES) - set(categories))}")
    rows, hashes, used_masks = [], {}, set()
    for category in categories:
        for original_split in ("train", "test"):
            folders = sorted((root / category / original_split).iterdir())
            if not folders:
                raise ValueError(f"Empty split: {category}/{original_split}")
            for folder in folders:
                if not folder.is_dir():
                    continue
                if original_split == "train" and folder.name != "good":
                    raise ValueError("Normal-only train contains an anomalous folder")
                paths = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".png")
                unexpected = [
                    str(p)
                    for p in folder.iterdir()
                    if p.is_dir() or p.suffix.lower() in {".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
                ]
                if unexpected:
                    raise ValueError(f"Unexpected image format or nested folder: {unexpected}")
                if not paths:
                    raise ValueError(f"No PNG images in {folder}")
                for path in paths:
                    relative = path.relative_to(root).as_posix()
                    safe_path(root, relative)
                    with Image.open(path) as image:
                        image.load()
                        size = image.size
                        pixels = np.asarray(image.convert("RGB"))
                    # Pixel checksum catches identical images with different PNG encodings.
                    pixel_hash = digest(
                        {"size": size, "pixels": hashlib.sha256(pixels.tobytes()).hexdigest()}
                    )
                    if pixel_hash in hashes:
                        raise ValueError(
                            f"Duplicate images require explicit curation: {relative} and {hashes[pixel_hash]}"
                        )
                    hashes[pixel_hash] = relative
                    label = int(folder.name != "good")
                    mask_path = None
                    mask_hash = None
                    if label:
                        mask = root / category / "ground_truth" / folder.name / f"{path.stem}_mask.png"
                        if not mask.is_file():
                            raise ValueError(f"Missing mask: {mask}")
                        safe_path(root, mask.relative_to(root))
                        with Image.open(mask) as image:
                            values = np.asarray(image.convert("L"))
                            if image.size != size or not np.any(values):
                                raise ValueError(f"Empty or misaligned mask: {mask}")
                            if not set(np.unique(values)).issubset({0, 1, 255}):
                                raise ValueError(f"Nonbinary mask: {mask}")
                        mask_path, mask_hash = str(mask.relative_to(root)), file_hash(mask)
                        used_masks.add(mask.resolve())
                    rows.append(
                        {
                            "sample_id": digest(relative)[:24],
                            "image_path": relative,
                            "mask_path": mask_path,
                            "label": label,
                            "category": category,
                            "defect_type": folder.name,
                            "original_split": original_split,
                            "original_size": [size[1], size[0]],
                            "image_hash": file_hash(path),
                            "mask_hash": mask_hash,
                            "pixel_hash": pixel_hash,
                        }
                    )
    actual_masks = {
        p.resolve() for category in categories for p in (root / category / "ground_truth").rglob("*.png")
    }
    if actual_masks != used_masks:
        raise ValueError(f"Orphan masks: {sorted(map(str, actual_masks - used_masks))}")
    for category in categories:
        if not any(
            row["category"] == category and row["original_split"] == "test" and row["label"] == 0
            for row in rows
        ):
            raise ValueError(f"Missing test/good samples in {category}")
        if not any(row["category"] == category and row["label"] == 1 for row in rows):
            raise ValueError(f"Missing test anomalies in {category}")
    for row in rows:
        SampleRecord.model_validate(row)
    return {
        "schema_version": 1,
        "root_hint": str(root),
        "categories": categories,
        "dataset_name": "mvtec-ad",
        "dataset_version": dataset_version,
        "dataset_fingerprint": dataset_fingerprint(rows),
        "samples": rows,
        "counts": dict(Counter(f"{r['category']}/{r['original_split']}/{r['defect_type']}" for r in rows)),
    }


def make_split(inventory, seed=42):
    if inventory["dataset_fingerprint"] != dataset_fingerprint(inventory["samples"]):
        raise ValueError("Inventory fingerprint mismatch")
    groups = defaultdict(list)
    for row in inventory["samples"]:
        groups[(row["category"], row["original_split"], row["defect_type"])].append(dict(row))
    samples, warnings = [], []
    for key, rows in sorted(groups.items()):
        rows.sort(key=lambda row: row["sample_id"])
        rng = np.random.default_rng(int(digest([seed, key])[:16], 16))
        rows = [rows[i] for i in rng.permutation(len(rows))]
        n = len(rows)
        if key[1] == "train":
            if n < 3:
                raise ValueError(f"Need at least 3 normal training samples: {key}")
            nval = max(1, int(n * 0.15))
            ncal = max(1, int(n * 0.15))
            roles = ["fit"] * (n - nval - ncal) + ["validation_normal"] * nval + ["calibration_normal"] * ncal
        else:
            nselect = max(1, min(n - 1, int(n * 0.4))) if n >= 2 else 0
            if n < 2:
                warnings.append(f"Singleton {key}: assigned to final_test only")
            roles = ["selection"] * nselect + ["final_test"] * (n - nselect)
        samples.extend(dict(row, split_role=role) for row, role in zip(rows, roles, strict=True))
    samples.sort(key=lambda r: r["sample_id"])
    manifest = {
        "schema_version": 1,
        "dataset_fingerprint": inventory["dataset_fingerprint"],
        "dataset_name": inventory["dataset_name"],
        "dataset_version": inventory["dataset_version"],
        "categories": inventory["categories"],
        "seed": seed,
        "samples": samples,
        "warnings": warnings,
        "protocol": "normal70-15-15_test40-60_v1",
    }
    manifest["split_fingerprint"] = digest(manifest)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest):
    if manifest.get("schema_version") != 1 or manifest.get("protocol") != "normal70-15-15_test40-60_v1":
        raise ValueError("Unsupported manifest schema or protocol")
    payload = {k: v for k, v in manifest.items() if k != "split_fingerprint"}
    if digest(payload) != manifest["split_fingerprint"]:
        raise ValueError("Split fingerprint mismatch")
    if not manifest["samples"] or manifest["dataset_fingerprint"] != dataset_fingerprint(manifest["samples"]):
        raise ValueError("Empty manifest or dataset fingerprint mismatch")
    if sorted({row["category"] for row in manifest["samples"]}) != manifest["categories"]:
        raise ValueError("Category list does not match samples")
    ids, pixels = set(), set()
    for row in manifest["samples"]:
        SampleRecord.model_validate(row)
        if digest(row["image_path"])[:24] != row["sample_id"]:
            raise ValueError("sample_id must match the relative image path")
        if row["sample_id"] in ids or row["pixel_hash"] in pixels:
            raise ValueError("Duplicate sample in manifest")
        ids.add(row["sample_id"])
        pixels.add(row["pixel_hash"])
        role = row["split_role"]
        if role not in ROLES or row["label"] not in (0, 1):
            raise ValueError("Invalid sample schema")
        if role in ROLES[:3] and (row["label"] != 0 or row["original_split"] != "train"):
            raise ValueError("Training/calibration leakage")
        if role in ROLES[3:] and row["original_split"] != "test":
            raise ValueError("Holdout must come from original test")
    for category in manifest["categories"]:
        for role in ROLES[:3]:
            if not samples_for(manifest, category, role):
                raise ValueError(f"Missing normal split {category}/{role}")
    return manifest


def load_manifest(path):
    return validate_manifest(read_json(path))


def samples_for(manifest, category, role):
    if role not in ROLES or category not in manifest["categories"]:
        raise ValueError("Unknown category or split role")
    return [r for r in manifest["samples"] if r["category"] == category and r["split_role"] == role]


def verify_files(root, rows):
    for row in rows:
        for path_key, hash_key in (("image_path", "image_hash"), ("mask_path", "mask_hash")):
            if row[path_key] and file_hash(safe_path(root, row[path_key])) != row[hash_key]:
                raise ValueError(f"Dataset changed: {row[path_key]}")


def read_image(root, row):
    with Image.open(safe_path(root, row["image_path"])) as image:
        return image.convert("RGB")


def read_mask(root, row):
    if row["mask_path"] is None:
        return np.zeros(row["original_size"], dtype=bool)
    with Image.open(safe_path(root, row["mask_path"])) as image:
        return np.asarray(image.convert("L")) > 0


def prepare(root, target, require_all=True, seed=42, dataset_version="kaggle-ipythonx-local-content-hash"):
    inventory = inspect_dataset(root, require_all, dataset_version)
    manifest = make_split(inventory, seed)
    target = Path(target)
    if target.exists() and read_json(target) != manifest:
        raise ValueError("Refusing to overwrite a different split manifest")
    write_json(target, manifest)
    write_json(target.with_name("inventory.json"), inventory)
    return manifest


def load_sample(root, row, image_size=256):
    """Canonical CPU sample: RGB float32 CHW in [0,1], binary HW mask.

    ImageNet normalization is model-specific and does not belong to the adapter.
    Geometry is resize-only, so original_size is sufficient to invert it.
    """
    SampleRecord.model_validate(row)
    if not isinstance(image_size, int) or image_size < 1:
        raise ValueError("image_size must be a positive integer")
    image = read_image(root, row)
    mask = read_mask(root, row)
    if list(reversed(image.size)) != row["original_size"] or list(mask.shape) != row["original_size"]:
        raise ValueError("Image/mask geometry changed since validation")
    resized = image.resize((image_size, image_size), Image.Resampling.BILINEAR)
    mask_image = Image.fromarray(mask.astype(np.uint8)).resize(
        (image_size, image_size), Image.Resampling.NEAREST
    )
    return {
        **row,
        "image": np.asarray(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0,
        "mask": np.asarray(mask_image, dtype=bool),
        "transform": {
            "kind": "resize",
            "size": [image_size, image_size],
            "original_size": row["original_size"],
        },
    }
