#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "ai_service" / "datasets" / "watermelon"
LABELS = DATASET / "color_labels_experiment.csv"
OUTPUT = DATASET / "color_feature_v1_results.csv"

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


def central_watermelon_region(image):
    h, w = image.shape[:2]

    # V1 intentionally avoids detector dependency.
    # Use a conservative central ellipse to reduce
    # background contamination.
    mask = np.zeros((h, w), dtype=np.uint8)

    center = (w // 2, h // 2)
    axes = (
        max(1, int(w * 0.34)),
        max(1, int(h * 0.34)),
    )

    cv2.ellipse(
        mask,
        center,
        axes,
        0,
        0,
        360,
        255,
        -1,
    )

    return mask


def extract_metrics(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = central_watermelon_region(image)

    pixels = hsv[mask > 0]

    if len(pixels) == 0:
        raise ValueError("empty analysis region")

    h = pixels[:, 0].astype(np.float32)
    s = pixels[:, 1].astype(np.float32)
    v = pixels[:, 2].astype(np.float32)

    chromatic = s >= 35

    if chromatic.sum() >= 50:
        h_use = h[chromatic]
        s_use = s[chromatic]
        v_use = v[chromatic]
    else:
        h_use = h
        s_use = s
        v_use = v

    median_h = float(np.median(h_use))
    std_h = float(np.std(h_use))
    median_s = float(np.median(s_use))
    median_v = float(np.median(v_use))

    green = (
        (h_use >= 30)
        & (h_use <= 95)
        & (s_use >= 35)
    )

    green_ratio = float(green.mean())

    dark_ratio = float((v_use < 70).mean())
    bright_ratio = float((v_use > 180).mean())

    return {
        "median_h": median_h,
        "std_h": std_h,
        "median_s": median_s,
        "median_v": median_v,
        "green_ratio": green_ratio,
        "dark_ratio": dark_ratio,
        "bright_ratio": bright_ratio,
    }


def main():
    if not LABELS.exists():
        print(f"ERROR: missing {LABELS}")
        return 1

    rows = []

    with LABELS.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        for item in reader:
            filename = item["image"]
            image_path = find_image(filename)

            if image_path is None:
                print(f"MISSING {filename}")
                continue

            image = cv2.imread(str(image_path))

            if image is None:
                print(f"UNREADABLE {filename}")
                continue

            metrics = extract_metrics(image)

            row = {
                "image": filename,
                "ground_truth": item["color_label"],
                "source": item["notes"],
                "path": str(image_path.relative_to(ROOT)),
                **metrics,
            }

            rows.append(row)

    fieldnames = [
        "image",
        "ground_truth",
        "source",
        "path",
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
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    print("===== COLOR FEATURE V1 =====")
    print(f"Samples analysed: {len(rows)}")
    print(f"Output: {OUTPUT.relative_to(ROOT)}")
    print()

    labels = sorted(
        set(row["ground_truth"] for row in rows)
    )

    for label in labels:
        subset = [
            row for row in rows
            if row["ground_truth"] == label
        ]

        print(f"[{label}] n={len(subset)}")

        for metric in [
            "median_h",
            "std_h",
            "median_s",
            "median_v",
            "green_ratio",
            "dark_ratio",
            "bright_ratio",
        ]:
            values = np.array(
                [row[metric] for row in subset],
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
