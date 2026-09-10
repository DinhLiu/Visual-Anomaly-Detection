import shutil
from collections import Counter
from copy import deepcopy

import numpy as np
import pytest
from conftest import make_dataset
from PIL import Image

from visual_ad.common import digest, read_json
from visual_ad.data import (
    dataset_fingerprint,
    inspect_dataset,
    load_sample,
    make_split,
    prepare,
    resolve_root,
    samples_for,
    validate_manifest,
    verify_files,
)


def test_root_direct_nested_missing_and_ambiguous(dataset, tmp_path):
    assert resolve_root(dataset) == dataset
    assert resolve_root(dataset.parent) == dataset
    with pytest.raises(ValueError, match="unavailable"):
        resolve_root(tmp_path / "missing")
    make_dataset(tmp_path / "second")
    with pytest.raises(ValueError, match="Expected one"):
        resolve_root(tmp_path)


def test_all_categories_required(dataset, full_dataset):
    with pytest.raises(ValueError, match="Missing categories"):
        inspect_dataset(dataset)
    assert len(inspect_dataset(full_dataset)["categories"]) == 15


def test_rounding_determinism_and_disjointness(dataset):
    inventory = inspect_dataset(dataset, False)
    a = make_split(inventory)
    reversed_inventory = deepcopy(inventory)
    reversed_inventory["samples"].reverse()
    assert a == make_split(reversed_inventory)
    assert a != make_split(inventory, 43)
    assert Counter(row["split_role"] for row in a["samples"]) == {
        "fit": 14,
        "validation_normal": 3,
        "calibration_normal": 3,
        "selection": 4,
        "final_test": 6,
    }
    assert len({row["sample_id"] for row in a["samples"]}) == 30
    assert all(
        row["label"] == 0
        for row in a["samples"]
        if row["split_role"].endswith("normal") or row["split_role"] == "fit"
    )


def test_stratification_singleton_and_small_train(tmp_path):
    root = make_dataset(tmp_path / "single", defect_count=1)
    manifest = make_split(inspect_dataset(root, False))
    assert manifest["warnings"]
    assert next(row for row in manifest["samples"] if row["label"])["split_role"] == "final_test"
    short = make_dataset(tmp_path / "short", train_count=2)
    with pytest.raises(ValueError, match="at least 3"):
        make_split(inspect_dataset(short, False))


@pytest.mark.parametrize("problem", ["missing", "empty", "size", "soft", "orphan"])
def test_reject_bad_masks(dataset, problem):
    target = dataset / "bottle/ground_truth/scratch/000_mask.png"
    if problem == "missing":
        target.unlink()
    elif problem == "orphan":
        shutil.copy2(target, target.with_name("orphan_mask.png"))
    else:
        shape = (8, 8) if problem == "size" else (24, 32)
        value = 0 if problem == "empty" else 128 if problem == "soft" else 255
        Image.fromarray(np.full(shape, value, np.uint8)).save(target)
    with pytest.raises(ValueError):
        inspect_dataset(dataset, False)


def test_corrupt_and_duplicate_image(dataset):
    target = dataset / "bottle/test/good/000.png"
    original = target.read_bytes()
    target.write_bytes(b"not an image")
    with pytest.raises(OSError):
        inspect_dataset(dataset, False)
    target.write_bytes(original)
    # Same decoded content, different compression/file hash.
    with Image.open(dataset / "bottle/train/good/000.png") as image:
        image.save(target, compress_level=0)
    with pytest.raises(ValueError, match="Duplicate images"):
        inspect_dataset(dataset, False)


def test_unexpected_train_label(dataset):
    source = dataset / "bottle/train/good"
    source.rename(source.with_name("bad"))
    with pytest.raises(ValueError):
        inspect_dataset(dataset, False)


def test_manifest_tampering_and_leakage(dataset):
    manifest = make_split(inspect_dataset(dataset, False))
    broken = deepcopy(manifest)
    broken["seed"] = 99
    with pytest.raises(ValueError, match="fingerprint"):
        validate_manifest(broken)
    broken = deepcopy(manifest)
    row = next(r for r in broken["samples"] if r["label"])
    row["split_role"] = "fit"
    broken["split_fingerprint"] = digest({k: v for k, v in broken.items() if k != "split_fingerprint"})
    with pytest.raises(ValueError, match="leakage"):
        validate_manifest(broken)


def test_manifest_relative_path_validation(dataset):
    manifest = make_split(inspect_dataset(dataset, False))
    manifest["samples"][0]["image_path"] = "../../private.png"
    manifest["dataset_fingerprint"] = dataset_fingerprint(manifest["samples"])
    manifest["split_fingerprint"] = digest({k: v for k, v in manifest.items() if k != "split_fingerprint"})
    with pytest.raises(ValueError, match="relative POSIX"):
        validate_manifest(manifest)


def test_portability_and_mutation_detection(dataset, tmp_path):
    inventory = inspect_dataset(dataset, False)
    copy = tmp_path / "relocated"
    shutil.copytree(dataset, copy)
    assert make_split(inventory) == make_split(inspect_dataset(copy, False))
    row = inventory["samples"][0]
    verify_files(copy, [row])
    with Image.open(copy / row["image_path"]) as image:
        image.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(copy / row["image_path"])
    with pytest.raises(ValueError, match="Dataset changed"):
        verify_files(copy, [row])


def test_canonical_sample_normal_and_anomaly(dataset):
    manifest = make_split(inspect_dataset(dataset, False))
    normal = samples_for(manifest, "bottle", "fit")[0]
    sample = load_sample(dataset, normal, 64)
    assert sample["image"].shape == (3, 64, 64)
    assert sample["image"].dtype == np.float32
    assert 0 <= sample["image"].min() <= sample["image"].max() <= 1
    assert not sample["mask"].any()
    abnormal = next(r for r in manifest["samples"] if r["label"])
    sample = load_sample(dataset, abnormal, 64)
    assert sample["mask"].dtype == bool
    assert sample["mask"].shape == (64, 64)
    # Source x:[8,16)/32 becomes x:[16,32)/64.
    assert sample["mask"][15, 20]
    assert not sample["mask"][15, 40]
    assert sample["original_size"] == [24, 32]
    with pytest.raises(ValueError):
        samples_for(manifest, "bottle", "bogus")


def test_prepare_is_immutable(dataset, tmp_path):
    target = tmp_path / "result/split-manifest.json"
    first = prepare(dataset, target, False)
    assert first == prepare(dataset, target, False) == read_json(target)
    with pytest.raises(ValueError, match="overwrite"):
        prepare(dataset, target, False, seed=43)
    assert read_json(target) == first
