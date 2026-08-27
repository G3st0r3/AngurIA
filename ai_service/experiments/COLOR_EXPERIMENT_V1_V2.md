# AngurIA Color Feature Experiments

Date: 2026-08-27

## Dataset

21 labeled watermelon images.

Ground-truth sources:
- manual_ground_truth
- visual_ground_truth_chatgpt

Classes:
- acceptable
- balanced
- poor

## V1

Central ellipse segmentation + HSV-derived metrics.

LOOCV nearest-centroid accuracy:
- 38.1% (8/21)

Majority baseline:
- 47.6%

Conclusion:
V1 performs below baseline and must not be used in production.

## V2

GrabCut segmentation, max feature image side 640 px.

LOOCV nearest-centroid accuracy:
- 47.6% (10/21)

Per-class:
- acceptable: 30.0% (3/10)
- balanced: 87.5% (7/8)
- poor: 0.0% (0/3)

Source evaluation:
- manual_ground_truth: 44.4% (4/9)
- visual_ground_truth_chatgpt: 50.0% (6/12)

Conservative balanced signal:
- precision: 75.0%
- recall: 75.0%

## Decision

Do NOT integrate automatic color classification into /detect yet.

The balanced class shows a promising visual signal, but the dataset is too small
and acceptable/poor discrimination is not reliable enough.

Preferred next step:
collect more labeled examples and revisit color classification later.

Production AngurIA remains unchanged.
