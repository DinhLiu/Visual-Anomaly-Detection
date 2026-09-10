"""Tiny generated data, not MVTec results or copyrighted dataset files."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from visual_ad.common import CATEGORIES


def make_dataset(root: Path, categories=("bottle",), train_count=20, defect_count=5):
    rng = np.random.default_rng(101)
    for category in categories:
        for split, kind, count in (
            ("train", "good", train_count),
            ("test", "good", 5),
            ("test", "scratch", defect_count),
        ):
            folder = root / category / split / kind
            folder.mkdir(parents=True)
            for index in range(count):
                array = rng.integers(0, 256, (24, 32, 3), dtype=np.uint8)
                Image.fromarray(array).save(folder / f"{index:03}.png")
                if kind != "good":
                    mask = np.zeros((24, 32), dtype=np.uint8)
                    mask[4:12, 8:16] = 255
                    target = root / category / "ground_truth" / kind
                    target.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(mask).save(target / f"{index:03}_mask.png")
    return root


@pytest.fixture
def dataset(tmp_path):
    return make_dataset(tmp_path / "mvtec")


@pytest.fixture
def full_dataset(tmp_path):
    return make_dataset(tmp_path / "mvtec-full", CATEGORIES)
