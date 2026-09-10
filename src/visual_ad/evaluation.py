"""Shared raw-score calibration and metrics for all model adapters."""

from collections.abc import Sequence

import numpy as np
from scipy.ndimage import label as connected_components
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def _array(values, *, name, dtype=None):
    result = np.asarray(values, dtype=dtype)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} contains NaN or infinity")
    return result


def rank_metrics(labels, scores):
    labels = _array(labels, name="labels", dtype=np.uint8)
    scores = _array(scores, name="scores", dtype=np.float64)
    if labels.ndim != 1 or scores.ndim != 1 or labels.shape != scores.shape:
        raise ValueError("Labels and scores must be aligned one-dimensional arrays")
    if not set(np.unique(labels)).issubset({0, 1}):
        raise ValueError("Labels must be binary")
    if np.unique(labels).size < 2:
        return {"auroc": None, "ap": None}
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        "ap": float(average_precision_score(labels, scores)),
    }


def calibrate(normal_scores, normal_maps, image_quantile=0.99, pixel_quantile=0.995):
    if not 0 < image_quantile < 1 or not 0 < pixel_quantile < 1:
        raise ValueError("Calibration quantiles must be inside (0, 1)")
    scores = _array(normal_scores, name="normal_scores", dtype=np.float64)
    maps = [_array(item, name="normal_map", dtype=np.float32) for item in normal_maps]
    if scores.ndim != 1 or not len(scores) or len(scores) != len(maps):
        raise ValueError("Calibration requires one score/map per held-out normal sample")
    if any(item.ndim != 2 or item.size == 0 for item in maps):
        raise ValueError("Every anomaly map must be a non-empty 2D array")
    pixels = np.concatenate([item.ravel() for item in maps])
    low, high = np.quantile(pixels, (0.01, 0.999))
    return {
        "image_threshold": float(np.quantile(scores, image_quantile)),
        "pixel_threshold": float(np.quantile(pixels, pixel_quantile)),
        "map_low": float(low),
        "map_high": float(max(high, low + np.finfo(np.float32).eps)),
        "image_quantile": image_quantile,
        "pixel_quantile": pixel_quantile,
        "source_role": "calibration_normal",
    }


def aupro(masks: Sequence[np.ndarray], maps: Sequence[np.ndarray], fpr_limit=0.3):
    """Area under mean per-region overlap, normalized over ``[0, fpr_limit]``."""
    if not 0 < fpr_limit <= 1 or not len(masks) or len(masks) != len(maps):
        raise ValueError("AUPRO requires aligned maps/masks and an FPR limit in (0, 1]")
    labels, scores, weights = [], [], []
    region_count = 0
    for mask, score in zip(masks, maps, strict=True):
        mask = _array(mask, name="mask", dtype=bool)
        score = _array(score, name="anomaly_map", dtype=np.float32)
        if mask.ndim != 2 or mask.shape != score.shape:
            raise ValueError("Each mask and anomaly map must have the same 2D shape")
        components, count = connected_components(mask, structure=np.ones((3, 3), dtype=np.uint8))
        sizes = np.bincount(components.ravel())
        weight = np.ones(mask.shape, dtype=np.float64)
        if count:
            weight[mask] = 1.0 / sizes[components[mask]]
        region_count += count
        labels.append(mask.ravel())
        scores.append(score.ravel())
        weights.append(weight.ravel())
    flat_labels = np.concatenate(labels)
    if region_count == 0 or flat_labels.all():
        return None
    fpr, pro, _ = roc_curve(
        flat_labels, np.concatenate(scores), sample_weight=np.concatenate(weights), drop_intermediate=False
    )
    below = fpr < fpr_limit
    x = np.r_[fpr[below], fpr_limit]
    y = np.r_[pro[below], np.interp(fpr_limit, fpr, pro)]
    return float(np.trapezoid(y, x) / fpr_limit)


def evaluate(labels, scores, masks, maps, image_threshold, pixel_threshold, fpr_limit=0.3):
    if not len(labels) or not (len(labels) == len(scores) == len(masks) == len(maps)):
        raise ValueError("Evaluation requires one label, score, mask and map per sample")
    image = rank_metrics(labels, scores)
    pixel_labels = np.concatenate([_array(item, name="mask", dtype=bool).ravel() for item in masks])
    pixel_scores = np.concatenate(
        [_array(item, name="anomaly_map", dtype=np.float32).ravel() for item in maps]
    )
    pixel = rank_metrics(pixel_labels, pixel_scores)
    predicted = _array(scores, name="scores", dtype=np.float64) > image_threshold
    labels_array = _array(labels, name="labels", dtype=np.uint8)
    pixel_predicted = pixel_scores > pixel_threshold
    return {
        "image_auroc": image["auroc"],
        "image_ap": image["ap"],
        "pixel_auroc": pixel["auroc"],
        "pixel_ap": pixel["ap"],
        "aupro_fpr_0_3": aupro(masks, maps, fpr_limit),
        "image_precision": float(precision_score(labels_array, predicted, zero_division=0)),
        "image_recall": float(recall_score(labels_array, predicted, zero_division=0)),
        "image_f1": float(f1_score(labels_array, predicted, zero_division=0)),
        "image_confusion_matrix": confusion_matrix(labels_array, predicted, labels=[0, 1]).tolist(),
        "pixel_f1": float(f1_score(pixel_labels, pixel_predicted, zero_division=0)),
        "image_threshold": float(image_threshold),
        "pixel_threshold": float(pixel_threshold),
        "fpr_limit": float(fpr_limit),
    }
