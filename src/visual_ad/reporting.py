"""Produce auditable phase-one reports from measured dataset facts."""

import csv
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .common import digest, environment, file_hash, now, read_json, source_hash, write_json
from .data import ROLES, read_image, read_mask, validate_manifest

PHASE1_RESULT_FILES = (
    "resolved-config.json",
    "inventory.json",
    "split-manifest.json",
    "validation.json",
    "last-status.json",
    "data-report.md",
    "data-report.json",
    "split-counts.csv",
    "samples.csv",
    "data-preview.png",
)


def archive_phase1_results(output, archive=None):
    """Create a portable ZIP after a successful phase-one data run."""
    output = Path(output).resolve()
    if not output.is_dir():
        raise ValueError(f"Phase-one output does not exist: {output}")
    status_path = output / "last-status.json"
    report_path = output / "data-report.json"
    if not status_path.is_file() or read_json(status_path).get("status") != "completed":
        raise ValueError("Cannot archive an incomplete phase-one run")
    if not report_path.is_file() or read_json(report_path).get("status") != "data_validated":
        raise ValueError("Cannot archive without a validated data report")
    files = [output / name for name in PHASE1_RESULT_FILES if (output / name).is_file()]
    required = {
        "resolved-config.json",
        "inventory.json",
        "split-manifest.json",
        "last-status.json",
        "data-report.md",
        "data-report.json",
        "split-counts.csv",
        "samples.csv",
        "data-preview.png",
    }
    missing = sorted(required - {path.name for path in files})
    if missing:
        raise ValueError(f"Missing required phase-one result files: {missing}")
    split = read_json(output / "split-manifest.json")
    default_name = f"visual-ad-phase1-{split['split_fingerprint'][:12]}.zip"
    archive = Path(archive).resolve() if archive else output.parent / default_name
    if archive == output or archive.is_relative_to(output):
        raise ValueError("Archive must be outside the result directory")
    archive.parent.mkdir(parents=True, exist_ok=True)
    checksums = {
        "schema_version": 1,
        "archive_type": "visual-ad-phase1-results",
        "dataset_fingerprint": split["dataset_fingerprint"],
        "split_fingerprint": split["split_fingerprint"],
        "files": {path.name: file_hash(path) for path in files},
    }
    temporary = archive.with_name(f".{archive.name}.pending")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
            for path in files:
                stream.write(path, arcname=path.name)
            stream.writestr("checksums.json", json.dumps(checksums, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "archive": str(archive),
        "size_bytes": archive.stat().st_size,
        "file_count": len(files) + 1,
        "split_fingerprint": split["split_fingerprint"],
    }


def montage(root, manifest, target):
    """Preview only fit/selection. Final-test images never enter the learning gallery."""
    rows = []
    for category in manifest["categories"]:
        for anomaly in (0, 1):
            candidates = [
                r
                for r in manifest["samples"]
                if r["category"] == category
                and r["label"] == anomaly
                and r["split_role"] in ("fit", "selection")
            ]
            if candidates:
                rows.append(candidates[0])
    if not rows:
        return None
    cell = 192
    canvas = Image.new("RGB", (cell * 3, len(rows) * (cell + 28)), "#111827")
    draw = ImageDraw.Draw(canvas)
    for index, row in enumerate(rows):
        image = read_image(root, row).resize((cell, cell), Image.Resampling.BILINEAR)
        mask = Image.fromarray(read_mask(root, row).astype(np.uint8) * 255).resize(
            (cell, cell), Image.Resampling.NEAREST
        )
        overlay = np.array(image)
        positive = np.asarray(mask) > 0
        overlay[positive] = (overlay[positive] * 0.5 + np.array([255, 50, 50]) * 0.5).astype(np.uint8)
        y = index * (cell + 28)
        for col, picture in enumerate((image, mask.convert("RGB"), Image.fromarray(overlay))):
            canvas.paste(picture, (col * cell, y))
        draw.text(
            (5, y + cell + 4), f"{row['category']} / {row['defect_type']} / {row['split_role']}", fill="white"
        )
    canvas.save(target)
    return Path(target).name


def write_data_report(root, manifest, output, config=None):
    validate_manifest(manifest)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = Counter((row["category"], row["split_role"]) for row in manifest["samples"])
    warnings = list(manifest["warnings"])
    for category in manifest["categories"]:
        for role in ROLES[3:]:
            labels = {
                r["label"]
                for r in manifest["samples"]
                if r["category"] == category and r["split_role"] == role
            }
            if labels != {0, 1}:
                warnings.append(f"{category}/{role}: lacks both labels; AUROC would be undefined")
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "data_validated",
        "execution_location": "kaggle" if Path("/kaggle/input").is_dir() else "local",
        "dataset_name": manifest["dataset_name"],
        "dataset_version": manifest["dataset_version"],
        "dataset_fingerprint": manifest["dataset_fingerprint"],
        "split_fingerprint": manifest["split_fingerprint"],
        "config_hash": None if config is None else digest(config),
        "seed": manifest["seed"],
        "source_fingerprint": source_hash(),
        "environment": environment(),
        "sample_count": len(manifest["samples"]),
        "category_count": len(manifest["categories"]),
        "counts": [
            {"category": c, **{role: counts[c, role] for role in ROLES}} for c in manifest["categories"]
        ],
        "warnings": warnings,
        "models_trained": False,
    }
    write_json(output / "data-report.json", report)
    with (output / "split-counts.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["category", *ROLES])
        writer.writeheader()
        writer.writerows(report["counts"])
    with (output / "samples.csv").open("w", newline="") as stream:
        fields = ["sample_id", "category", "split_role", "label", "defect_type", "image_path", "mask_path"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(manifest["samples"])
    preview = montage(root, manifest, output / "data-preview.png")
    paragraphs = [
        "# Báo cáo kiểm tra dữ liệu — giai đoạn 1",
        "",
        f"Sinh lúc: {report['generated_at']}. Môi trường: {report['execution_location']}.",
        "",
        f"Đã kiểm tra {report['sample_count']} ảnh thuộc {report['category_count']} category.",
        "Đây là bằng chứng kiểm tra dữ liệu được truyền vào lệnh; không phải kết quả huấn luyện.",
        "",
        "## Thiết kế và lý do",
        "",
        "Adapter giữ đường dẫn tương đối để chuyển dữ liệu giữa Kaggle/local mà không đổi sample ID.",
        "Train normal được chia fit/validation/calibration; test gốc được chia selection/final_test.",
        "Việc giữ final_test độc lập cho phép kiểm chứng lựa chọn mô hình ở giai đoạn sau.",
        "",
        "## Fingerprint và tái lập",
        "",
        f"- Dataset: `{report['dataset_fingerprint']}`",
        f"- Split: `{report['split_fingerprint']}`",
        f"- Seed: `{report['seed']}`",
        f"- Source: `{report['source_fingerprint']}`",
        "",
        "Xem `resolved-config.json`, `inventory.json`, `split-manifest.json` và `data-report.json` cùng thư mục.",
        "",
        "## Số mẫu sau chia tập",
        "",
    ]
    for row in report["counts"]:
        paragraphs.append(f"- {row['category']}: " + ", ".join(f"{role}={row[role]}" for role in ROLES))
    paragraphs += [
        "",
        "## Kiểm chứng",
        "",
        "Đã decode ảnh, kiểm tra mask nhị phân/cùng kích thước, ảnh trùng, fingerprint và vai trò split.",
        "Đọc số lượng từng category trong `split-counts.csv`; không suy diễn rằng mọi loại lỗi có đủ mẫu.",
        "",
        "## Cảnh báo và giới hạn",
        "",
    ]
    paragraphs += [f"- {w}" for w in warnings] or ["Không phát hiện cảnh báo chia tập."]
    paragraphs += [
        "",
        "Kiểm tra duplicate chỉ phát hiện ảnh trùng pixel; chưa phát hiện near-duplicate hoặc cùng vật thể vật lý.",
        "Chưa huấn luyện, calibration threshold hay đo metric mô hình.",
        "",
        "## Kiểm tra trực quan",
        "",
    ]
    if preview:
        paragraphs += [
            f"![Ảnh gốc, mask, overlay]({preview})",
            "",
            "Mỗi hàng: ảnh gốc — mask — overlay. Chỉ xem fit/selection.",
        ]
    paragraphs += [
        "",
        "## Tự kiểm tra",
        "",
        "1. Vì sao đổi data root không đổi fingerprint? Vì hash dùng đường dẫn tương đối và nội dung.",
        "2. Vì sao không xem final_test trong gallery? Để tránh chỉnh thiết kế dựa trên holdout.",
        "3. Vì sao mask dùng nearest-neighbor? Để giữ nhãn rời rạc khi resize.",
        "",
        "## Bước tiếp theo",
        "",
        "Lưu output thành Kaggle Notebook Version, kiểm tra cảnh báo, rồi dùng manifest này cho evaluator và adapter mô hình.",
        "",
    ]
    (output / "data-report.md").write_text("\n".join(paragraphs))
    return report
