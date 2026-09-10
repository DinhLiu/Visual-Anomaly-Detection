"""Strict phase-one configuration; split ratios belong to a versioned protocol."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    data_root: Path = Path("/kaggle/input/datasets/ipythonx/mvtec-ad")
    output_root: Path = Path("/kaggle/working/visual-ad")
    dataset_name: Literal["mvtec-ad"] = "mvtec-ad"
    dataset_version: str = "kaggle-ipythonx-local-content-hash"
    seed: int = Field(default=42, ge=0, le=2**32 - 1)
    require_all_categories: bool = True
    image_size: int = Field(default=256, ge=16, le=4096)

    @field_validator("dataset_version")
    @classmethod
    def version_is_nonempty(cls, value):
        if not value.strip():
            raise ValueError("dataset_version cannot be empty")
        return value


def load_config(path=None, **overrides):
    try:
        payload = yaml.safe_load(Path(path).read_text()) if path else {}
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML configuration: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Config must be a YAML mapping")
    payload.update({key: value for key, value in overrides.items() if value is not None})
    return DataConfig.model_validate(payload)
