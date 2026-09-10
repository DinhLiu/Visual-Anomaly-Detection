import subprocess
import sys
from pathlib import Path

import pytest

from visual_ad.cli import main
from visual_ad.common import read_json
from visual_ad.config import load_config
from visual_ad.reporting import PHASE1_RESULT_FILES, archive_phase1_results


def test_prepare_cli_produces_measured_reports(full_dataset, tmp_path):
    output = tmp_path / "result"
    assert main(["data", "prepare", "--root", str(full_dataset), "--output", str(output)]) == 0
    report = read_json(output / "data-report.json")
    assert report["sample_count"] == 450 and report["category_count"] == 15
    assert report["models_trained"] is False
    assert report["execution_location"] == "local"
    assert (output / "data-preview.png").exists()
    assert (output / "samples.csv").exists()
    assert "fit" in (output / "data-report.md").read_text()
    assert main(["data", "prepare", "--root", str(full_dataset), "--output", str(output)]) == 0


def test_validate_then_split_and_reject_changed_config(dataset, tmp_path):
    output = tmp_path / "result"
    flags = ["--root", str(dataset), "--output", str(output), "--allow-partial"]
    assert main(["data", "validate", *flags]) == 0
    assert main(["data", "split", "--inventory", str(output / "inventory.json"), *flags]) == 0
    original = (output / "split-manifest.json").read_bytes()
    assert main(["data", "prepare", *flags, "--seed", "43"]) == 2
    assert (output / "split-manifest.json").read_bytes() == original


def test_failed_validation_report(dataset, tmp_path):
    (dataset / "bottle/ground_truth/scratch/000_mask.png").unlink()
    output = tmp_path / "invalid"
    assert main(["data", "prepare", "--root", str(dataset), "--output", str(output), "--allow-partial"]) == 2
    assert read_json(output / "last-status.json")["status"] == "failed"
    assert (output / "failure-report.md").exists()
    assert not (output / "split-manifest.json").exists()


def test_output_cannot_write_inside_dataset(dataset):
    target = dataset / "output"
    assert main(["data", "prepare", "--root", str(dataset), "--output", str(target), "--allow-partial"]) == 2
    assert not target.exists()


def test_invalid_config(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("unknown: value\n")
    with pytest.raises(ValueError, match="Extra inputs"):
        load_config(config)
    config.write_text("- not a mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        load_config(config)


def test_console_entrypoint():
    result = subprocess.run(
        [str(Path(sys.executable).with_name("vad")), "environment"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "source_fingerprint" in result.stdout


def test_invalid_yaml_cli(tmp_path):
    config = tmp_path / "syntax.yaml"
    config.write_text("data_root: [unclosed\n")
    assert main(["data", "prepare", "--config", str(config)]) == 2


def test_validate_preserves_old_inventory(dataset, tmp_path):
    from PIL import Image

    output = tmp_path / "preserved"
    flags = ["--root", str(dataset), "--output", str(output), "--allow-partial"]
    assert main(["data", "validate", *flags]) == 0
    previous = (output / "inventory.json").read_bytes()
    path = dataset / "bottle/train/good/000.png"
    with Image.open(path) as image:
        image.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(path)
    assert main(["data", "validate", *flags]) == 2
    assert (output / "inventory.json").read_bytes() == previous


def test_existing_output_inside_dataset_is_untouched(dataset):
    target = dataset / "existing"
    target.mkdir()
    assert main(["data", "prepare", "--root", str(dataset), "--output", str(target), "--allow-partial"]) == 2
    assert not list(target.iterdir())


def test_archive_contains_only_portable_evidence(full_dataset, tmp_path):
    import hashlib
    import json
    import zipfile

    output = tmp_path / "result"
    assert main(["data", "prepare", "--root", str(full_dataset), "--output", str(output)]) == 0
    (output / "failure-report.md").write_text("stale failure")
    result = archive_phase1_results(output)
    archive = Path(result["archive"])
    with zipfile.ZipFile(archive) as stream:
        names = set(stream.namelist())
        assert names == (
            {name for name in PHASE1_RESULT_FILES if (output / name).is_file()} | {"checksums.json"}
        )
        assert "failure-report.md" not in names
        checksums = json.loads(stream.read("checksums.json"))
        for name, expected in checksums["files"].items():
            assert hashlib.sha256(stream.read(name)).hexdigest() == expected


def test_archive_rejects_incomplete_or_internal_target(full_dataset, tmp_path):
    output = tmp_path / "result"
    output.mkdir()
    with pytest.raises(ValueError, match="incomplete"):
        archive_phase1_results(output)
    assert main(["data", "prepare", "--root", str(full_dataset), "--output", str(output)]) == 0
    with pytest.raises(ValueError, match="outside"):
        archive_phase1_results(output, output / "result.zip")
    (output / "samples.csv").unlink()
    with pytest.raises(ValueError, match="Missing required"):
        archive_phase1_results(output)


def test_archive_cli(full_dataset, tmp_path, capsys):
    output = tmp_path / "result"
    archive = tmp_path / "download.zip"
    assert main(["data", "prepare", "--root", str(full_dataset), "--output", str(output)]) == 0
    capsys.readouterr()
    assert main(["data", "archive", "--output", str(output), "--archive", str(archive)]) == 0
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["archive"] == str(archive.resolve())
    assert archive.is_file()
