"""Build an uploadable source wheel + config + constraints with checksum manifest.

Run in the locked dev environment. No publishing or account access is performed.
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from visual_ad.common import file_hash, source_hash, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dist/kaggle-bundle"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("Bundle output already exists; choose a new --output to preserve previous artifacts")
    output.mkdir(parents=True)
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(output), str(root)],
        check=True,
    )
    for relative in ("requirements-kaggle.lock", "uv.lock", "configs/data.yaml"):
        source = root / relative
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    provenance = {
        "schema_version": 1,
        "source_fingerprint": source_hash(),
        "files": {
            p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob("*")) if p.is_file()
        },
    }
    write_json(output / "bundle-manifest.json", provenance)
    archive = output.with_suffix(".zip")
    if archive.exists():
        raise SystemExit("Archive already exists; choose a new --output")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as stream:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                stream.write(path, path.relative_to(output))
    print(f"Bundle: {output}\nUpload archive to a private Kaggle Dataset: {archive}")


if __name__ == "__main__":
    main()
