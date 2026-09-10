"""On-disk manifest types. Tensor conversion is deliberately left to model adapters."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .common import CATEGORIES

Role = Literal["fit", "validation_normal", "calibration_normal", "selection", "final_test"]


class SampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sample_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    image_path: str
    mask_path: str | None
    label: Literal[0, 1]
    category: str
    defect_type: str
    original_split: Literal["train", "test"]
    original_size: list[int] = Field(min_length=2, max_length=2)
    image_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    mask_hash: str | None
    pixel_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    split_role: Role | None = None

    @field_validator("image_path", "mask_path")
    @classmethod
    def relative_path(cls, value):
        if value is not None and (
            not value
            or PurePosixPath(value).is_absolute()
            or ".." in PurePosixPath(value).parts
            or "\\" in value
        ):
            raise ValueError("Sample paths must be relative POSIX paths without traversal")
        return value

    @model_validator(mode="after")
    def consistent(self):
        if self.category not in CATEGORIES or min(self.original_size) < 1:
            raise ValueError("Invalid category or image dimensions")
        if self.label != int(self.defect_type != "good"):
            raise ValueError("Label and defect_type disagree")
        if self.label == 1:
            if self.mask_path is None or self.mask_hash is None or len(self.mask_hash) != 64:
                raise ValueError("Anomalous sample requires mask path and hash")
        elif self.mask_path is not None or self.mask_hash is not None:
            raise ValueError("Normal sample must use an implicit zero mask")
        if self.original_split == "train" and self.label:
            raise ValueError("Original train must be normal only")
        if (
            self.split_role in ("fit", "validation_normal", "calibration_normal")
            and self.original_split != "train"
        ):
            raise ValueError("Training/calibration leakage")
        if self.split_role in ("selection", "final_test") and self.original_split != "test":
            raise ValueError("Holdout must come from original test")
        parts = PurePosixPath(self.image_path).parts
        if len(parts) != 4 or parts[:3] != (self.category, self.original_split, self.defect_type):
            raise ValueError("Image path disagrees with sample metadata")
        if self.mask_path is not None:
            expected = PurePosixPath(
                self.category,
                "ground_truth",
                self.defect_type,
                PurePosixPath(self.image_path).stem + "_mask.png",
            )
            if PurePosixPath(self.mask_path) != expected:
                raise ValueError("Mask path disagrees with image path")
        return self
