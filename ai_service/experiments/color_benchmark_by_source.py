#!/usr/bin/env python3

import csv
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "ai_service"
    / "datasets"
    / "watermelon"
    / "color_feature_v2_grabcut_results.csv"
)

FEATURES = [
    "mask_coverage",
    "median_h",
    "std_h",
    "median_s",
    "median_v",
    "green_ratio",
    "dark_ratio",
    "bright_ratio",
]


def load_rows():
    with INPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return list(csv.DictReader(handle))


def predict_nearest_centroid(train_rows, test_row):
    train_x = np.array(
        [
            [float(row[f]) for f in FEATURES]
            for row in train_rows
        ],
        dtype=float,
    )

    train_y = np.array(
        [row["ground_truth"] for row in train_rows]
    )

    test_x = np.array(
        [float(test_row[f]) for f in FEATURES],
        dtype=float,
    )

    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std[std == 0] = 1.0

    train_z = (train_x - mean) / std
    test_z = (test_x - mean) / std

    centroids = {}

    for label in sorted(set(train_y)):
        centroids[label] = (
            train_z[train_y == label].mean(axis=0)
        )

    distances = {
        label: float(
            np.linalg.norm(test_z - centroid)
        )
        for label, centroid in centroids.items()
    }

    return min(distances, key=distances.get)


def evaluate_subset(rows, source_name):
    subset = [
        row for row in rows
        if row["source"] == source_name
    ]

    predictions = []

    for test in subset:
        train = [
            row for row in rows
            if row["image"] != test["image"]
        ]

        predictions.append(
            predict_nearest_centroid(train, test)
        )

    actual = [
        row["ground_truth"]
        for row in subset
    ]

    correct = sum(
        a == p
        for a, p in zip(actual, predictions)
    )

    print(f"===== {source_name} =====")
    print(f"Samples: {len(subset)}")

    if subset:
        print(
            f"Accuracy: "
            f"{correct / len(subset) * 100:.1f}% "
            f"({correct}/{len(subset)})"
        )

    print()

    for row, predicted in zip(
        subset,
        predictions,
    ):
        marker = (
            "✅"
            if row["ground_truth"] == predicted
            else "❌"
        )

        print(
            f"{marker} {row['image']}: "
            f"{row['ground_truth']} -> {predicted}"
        )

    print()


def balanced_signal(rows):
    actual = np.array(
        [
            row["ground_truth"] == "balanced"
            for row in rows
        ]
    )

    # Conservative signal candidate:
    # central green hue + high green presence.
    predicted = np.array(
        [
            (
                39 <= float(row["median_h"]) <= 51
                and float(row["green_ratio"]) >= 0.80
                and float(row["median_s"]) >= 115
            )
            for row in rows
        ]
    )

    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    tn = int((~predicted & ~actual).sum())

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    print("===== CONSERVATIVE BALANCED SIGNAL =====")
    print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"Precision: {precision * 100:.1f}%")
    print(f"Recall: {recall * 100:.1f}%")
    print()

    for row, is_predicted in zip(
        rows,
        predicted,
    ):
        if is_predicted:
            print(
                f"BALANCED SIGNAL -> "
                f"{row['image']} "
                f"(truth={row['ground_truth']}, "
                f"source={row['source']})"
            )


def main():
    rows = load_rows()

    evaluate_subset(
        rows,
        "manual_ground_truth",
    )

    evaluate_subset(
        rows,
        "visual_ground_truth_chatgpt",
    )

    balanced_signal(rows)


if __name__ == "__main__":
    main()
