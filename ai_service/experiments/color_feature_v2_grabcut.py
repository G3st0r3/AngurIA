#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "ai_service" / "datasets" / "watermelon"

LABELS = DATASET / "color_labels_experiment.csv"
OUTPUT = DATASET / "color_feature_v2_grabcut_results.csv"

SEARCH_DIRS = [
    DATASET / "raw" / "own",
    DATASET / "raw" / "external",
    DATASET / "raw" / "opened_external",
]


def find_image(filename):
    for directory in SEARCH_DIRS:
        candidate = directory / filename
        if candidate.exists():
            return candidate

    return None


def grabcut_mask(image):
    h, w = image.shape[:2]

    mask = np.zeros(
        (h, w),
        np.uint8,
    )

    bg_model = np.zeros(
        (1, 65),
        np.float64,
    )

    fg_model = np.zeros(
        (1, 65),
        np.float64,
    )

    margin_x = max(
        2,
        int(w * 0.08),
    )

    margin_y = max(
        2,
        int(h * 0.08),
    )

    rect = (
        margin_x,
        margin_y,
        max(1, w - 2 * margin_x),
        max(1, h - 2 * margin_y),
    )

    cv2.grabCut(
        image,
        mask,
        rect,
        bg_model,
        fg_model,
        5,
        cv2.GC_INIT_WITH_RECT,
    )

    binary = np.where(
        (mask == cv2.GC_FGD)
        | (mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype("uint8")

    kernel = np.ones(
        (5, 5),
        np.uint8,
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel,
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
    )

    return binary


def largest_component(mask):
    count, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )
    )

    if count <= 1:
        return mask

    largest = 1 + np.argmax(
        stats[1:, cv2.CC_STAT_AREA]
    )

    return np.where(
        labels == largest,
        255,
        0,
    ).astype("uint8")


def resize_for_features(image, max_side=640):
    h, w = image.shape[:2]
    long_side = max(h, w)

    if long_side <= max_side:
        return image

    scale = max_side / long_side

    return cv2.resize(
        image,
        (
            max(1, round(w * scale)),
            max(1, round(h * scale)),
        ),
        interpolation=cv2.INTER_AREA,
    )


def extract_metrics(image):
    image = resize_for_features(image)
    mask = grabcut_mask(image)
    mask = largest_component(mask)

    area = int(
        np.count_nonzero(mask)
    )

    total = mask.shape[0] * mask.shape[1]

    coverage = (
        area / total
        if total
        else 0.0
    )

    if area < 100:
        raise ValueError(
            "GrabCut foreground too small"
        )

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    pixels = hsv[mask > 0]

    h = pixels[:, 0].astype(
        np.float32
    )

    s = pixels[:, 1].astype(
        np.float32
    )

    v = pixels[:, 2].astype(
        np.float32
    )

    chromatic = s >= 35

    if chromatic.sum() >= 50:
        h_use = h[chromatic]
        s_use = s[chromatic]
        v_use = v[chromatic]
    else:
        h_use = h
        s_use = s
        v_use = v

    median_h = float(
        np.median(h_use)
    )

    std_h = float(
        np.std(h_use)
    )

    median_s = float(
        np.median(s_use)
    )

    median_v = float(
        np.median(v_use)
    )

    green = (
        (h_use >= 30)
        & (h_use <= 95)
        & (s_use >= 35)
    )

    green_ratio = float(
        green.mean()
    )

    dark_ratio = float(
        (v_use < 70).mean()
    )

    bright_ratio = float(
        (v_use > 180).mean()
    )

    return {
        "mask_coverage": coverage,
        "median_h": median_h,
        "std_h": std_h,
        "median_s": median_s,
        "median_v": median_v,
        "green_ratio": green_ratio,
        "dark_ratio": dark_ratio,
        "bright_ratio": bright_ratio,
    }


def main():
    rows = []

    with LABELS.open(
        newline="",
        encoding="utf-8",
    ) as handle:

        reader = csv.DictReader(handle)

        for item in reader:
            filename = item["image"]

            path = find_image(filename)

            if path is None:
                print(
                    f"MISSING {filename}"
                )
                continue

            image = cv2.imread(
                str(path)
            )

            if image is None:
                print(
                    f"UNREADABLE {filename}"
                )
                continue

            try:
                metrics = extract_metrics(
                    image
                )
            except Exception as exc:
                print(
                    f"FAILED {filename}: {exc}"
                )
                continue

            rows.append(
                {
                    "image": filename,
                    "ground_truth":
                        item["color_label"],
                    "source":
                        item["notes"],
                    "path":
                        str(
                            path.relative_to(
                                ROOT
                            )
                        ),
                    **metrics,
                }
            )

    fields = [
        "image",
        "ground_truth",
        "source",
        "path",
        "mask_coverage",
        "median_h",
        "std_h",
        "median_s",
        "median_v",
        "green_ratio",
        "dark_ratio",
        "bright_ratio",
    ]

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        "===== COLOR FEATURE V2 GRABCUT ====="
    )

    print(
        f"Samples analysed: {len(rows)}"
    )

    print(
        f"Output: {OUTPUT.relative_to(ROOT)}"
    )

    print()

    labels = sorted(
        set(
            row["ground_truth"]
            for row in rows
        )
    )

    metrics = [
        "mask_coverage",
        "median_h",
        "std_h",
        "median_s",
        "median_v",
        "green_ratio",
        "dark_ratio",
        "bright_ratio",
    ]

    for label in labels:

        subset = [
            row
            for row in rows
            if row["ground_truth"]
            == label
        ]

        print(
            f"[{label}] n={len(subset)}"
        )

        for metric in metrics:

            values = np.array(
                [
                    row[metric]
                    for row in subset
                ],
                dtype=float,
            )

            print(
                f"  {metric}: "
                f"mean={values.mean():.3f} "
                f"median={np.median(values):.3f} "
                f"min={values.min():.3f} "
                f"max={values.max():.3f}"
            )

        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
