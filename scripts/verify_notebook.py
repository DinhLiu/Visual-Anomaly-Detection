"""Run the actual Jupyter notebook with generated fixture data, never real benchmark scores."""

import os
import runpy
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

from visual_ad.common import CATEGORIES, write_json

root = Path(__file__).resolve().parents[1]
destination = root / "outputs/phase1-verification"
destination.mkdir(parents=True, exist_ok=True)
dataset = destination / "synthetic-mvtec"
if not dataset.exists():
    helper = runpy.run_path(str(root / "tests/conftest.py"))["make_dataset"]
    helper(dataset, CATEGORIES)
os.environ.update(
    {
        "VAD_USE_INSTALLED_PACKAGE": "1",
        "VAD_DATA_ROOT": str(dataset),
        "VAD_OUTPUT_ROOT": str(destination / "notebook-output"),
        "VAD_BUNDLE_ROOT": str(destination / "no-bundle"),
    }
)
# A local kernelspec pins the same interpreter as the tested environment.
kernel_dir = destination / "jupyter/kernels/phase1"
kernel_dir.mkdir(parents=True, exist_ok=True)
write_json(
    kernel_dir / "kernel.json",
    {
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Phase 1 test",
        "language": "python",
    },
)
os.environ["JUPYTER_PATH"] = str(destination / "jupyter")
os.environ["JUPYTER_RUNTIME_DIR"] = str(destination / "runtime")
os.environ["IPYTHONDIR"] = str(destination / "ipython")
notebook = nbformat.read(root / "notebooks/01_prepare_mvtec_kaggle_v2.ipynb", as_version=4)
NotebookClient(
    notebook, timeout=180, kernel_name="phase1", resources={"metadata": {"path": str(root)}}
).execute()
nbformat.write(notebook, destination / "01_prepare.executed.ipynb")
print(f"Executed notebook on 450 synthetic images / 15 categories: {destination}")
