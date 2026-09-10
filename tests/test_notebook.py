from pathlib import Path

import nbformat

from visual_ad.common import read_json


def test_notebook_schema_and_all_code_cells(full_dataset, tmp_path, monkeypatch):
    """Execute source cells as Python; kernel integration is verified separately."""
    notebook = nbformat.read("notebooks/01_prepare_mvtec_kaggle_v2.ipynb", as_version=4)
    nbformat.validate(notebook)
    output = tmp_path / "notebook-output"
    monkeypatch.setenv("VAD_USE_INSTALLED_PACKAGE", "1")
    monkeypatch.setenv("VAD_DATA_ROOT", str(full_dataset))
    monkeypatch.setenv("VAD_OUTPUT_ROOT", str(output))
    monkeypatch.setenv("VAD_BUNDLE_ROOT", str(tmp_path / "no-bundle"))
    scope = {"__name__": "__main__"}
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            assert not cell.outputs and cell.execution_count is None
            exec(compile(cell.source, f"notebook-cell-{index}", "exec"), scope)
    assert read_json(output / "data-report.json")["sample_count"] == 450
    assert Path(output / "data-preview.png").is_file()
