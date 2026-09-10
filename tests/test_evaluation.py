import numpy as np
import pytest

from visual_ad.evaluation import aupro, calibrate, evaluate, rank_metrics


def test_rank_metrics_perfect_and_single_class():
    assert rank_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == {"auroc": 1.0, "ap": 1.0}
    assert rank_metrics([0, 0], [0.1, 0.2]) == {"auroc": None, "ap": None}


def test_calibration_uses_normal_scores_and_maps():
    result = calibrate([1, 2, 3, 4], [np.full((2, 2), value) for value in range(4)], 0.75, 0.75)
    assert result["image_threshold"] == 3.25
    # NumPy's default linear quantile interpolates between the repeated 2 and 3 blocks.
    assert result["pixel_threshold"] == 2.25
    assert result["source_role"] == "calibration_normal"


def test_perfect_aupro_and_evaluation():
    masks = [np.zeros((3, 3), bool), np.eye(3, dtype=bool)]
    maps = [np.zeros((3, 3), float), np.eye(3, dtype=float)]
    assert aupro(masks, maps) == pytest.approx(1.0)
    result = evaluate([0, 1], [0.1, 0.9], masks, maps, 0.5, 0.5)
    assert result["image_auroc"] == result["pixel_auroc"] == 1.0
    assert result["image_f1"] == result["pixel_f1"] == 1.0
    assert result["image_confusion_matrix"] == [[1, 0], [0, 1]]


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: rank_metrics([0, 1], [0, np.nan]), "NaN"),
        (lambda: rank_metrics([0, 2], [0, 1]), "binary"),
        (lambda: calibrate([], []), "one score"),
        (lambda: calibrate([1], [np.zeros((2, 2))], 1.0, 0.9), "quantiles"),
        (lambda: aupro([np.zeros((2, 2))], []), "aligned"),
        (lambda: evaluate([0], [0], [], [], 0.5, 0.5), "one label"),
    ],
)
def test_invalid_inputs_fail_explicitly(call, message):
    with pytest.raises(ValueError, match=message):
        call()
