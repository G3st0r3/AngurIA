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
    / "color_feature_v1_results.csv"
)

FEATURES = [
    "median_h",
    "std_h",
    "median_s",
    "median_v",
    "green_ratio",
    "dark_ratio",
    "bright_ratio",
]


def load_data():
    rows = []

    with INPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        for row in csv.DictReader(handle):
            rows.append(row)

    x = np.array(
        [
            [float(row[f]) for f in FEATURES]
            for row in rows
        ],
        dtype=float,
    )

    y = np.array(
        [row["ground_truth"] for row in rows]
    )

    names = [
        row["image"]
        for row in rows
    ]

    return x, y, names


def predict_nearest_centroid(
    train_x,
    train_y,
    test_x,
):
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
            np.linalg.norm(
                test_z - centroid
            )
        )
        for label, centroid
        in centroids.items()
    }

    return min(
        distances,
        key=distances.get,
    )


def evaluate(x, y, names):
    predictions = []

    for index in range(len(y)):
        mask = np.ones(
            len(y),
            dtype=bool,
        )
        mask[index] = False

        predicted = predict_nearest_centroid(
            x[mask],
            y[mask],
            x[index],
        )

        predictions.append(predicted)

    predictions = np.array(predictions)

    correct = predictions == y

    print("===== LOOCV RESULTS =====")
    print(
        f"Accuracy: "
        f"{correct.mean() * 100:.1f}% "
        f"({correct.sum()}/{len(y)})"
    )

    majority = Counter(y).most_common(1)[0]

    print(
        f"Majority baseline: "
        f"{majority[1] / len(y) * 100:.1f}% "
        f"({majority[0]})"
    )

    print()

    labels = sorted(set(y))

    print("===== PER CLASS =====")

    for label in labels:
        mask = y == label

        class_correct = (
            predictions[mask] == y[mask]
        )

        print(
            f"{label}: "
            f"{class_correct.sum()}/"
            f"{mask.sum()} "
            f"({class_correct.mean() * 100:.1f}%)"
        )

    print()
    print("===== CONFUSION MATRIX =====")
    print("actual -> predicted")

    for actual in labels:
        counts = Counter(
            predictions[y == actual]
        )

        print(
            f"{actual}: "
            + ", ".join(
                f"{pred}={counts.get(pred, 0)}"
                for pred in labels
            )
        )

    print()
    print("===== INDIVIDUAL RESULTS =====")

    for name, actual, predicted in zip(
        names,
        y,
        predictions,
    ):
        marker = (
            "✅"
            if actual == predicted
            else "❌"
        )

        print(
            f"{marker} {name}: "
            f"{actual} -> {predicted}"
        )


def main():
    x, y, names = load_data()

    print("===== COLOR CLASSIFIER BENCHMARK V1 =====")
    print(f"Samples: {len(y)}")
    print(f"Features: {len(FEATURES)}")
    print(
        "Feature names: "
        + ", ".join(FEATURES)
    )
    print()

    evaluate(
        x,
        y,
        names,
    )


if __name__ == "__main__":
    main()
