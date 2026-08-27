#!/usr/bin/env python3

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DATASET = (
    ROOT
    / "ai_service"
    / "datasets"
    / "watermelon"
)

CARDS = DATASET / "cards"

OUTPUT = (
    DATASET
    / "ground_truth"
    / "feature_labeling_queue.csv"
)

IMAGE_DIRS = [
    DATASET / "raw" / "own",
    DATASET / "raw" / "external",
    DATASET / "raw" / "opened_external",
]

FEATURES = [
    "groundSpot",
    "peduncle",
    "stripes",
    "color",
    "surface",
]


def find_image(filename):
    if not filename:
        return None

    for directory in IMAGE_DIRS:
        path = directory / filename

        if path.exists():
            return path

    return None


def main():
    rows = []

    for path in sorted(CARDS.glob("ANG*.json")):
        try:
            card = json.loads(
                path.read_text(encoding="utf-8")
            )
        except Exception:
            continue

        image_name = (
            card.get("photo")
            or f"{path.stem}.jpg"
        )

        image_path = find_image(image_name)

        row = {
            "id": card.get("id") or path.stem,
            "photo": image_name,
            "image_path": (
                str(image_path.relative_to(ROOT))
                if image_path
                else ""
            ),
            "image_available": bool(image_path),
            "source": card.get("source", ""),
            "notes": card.get("notes", ""),
        }

        for feature in FEATURES:
            row[feature] = (
                card.get(feature, "") or ""
            )

        rows.append(row)

    fields = [
        "id",
        "photo",
        "image_path",
        "image_available",
        "source",
        "groundSpot",
        "peduncle",
        "stripes",
        "color",
        "surface",
        "notes",
    ]

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    available = sum(
        row["image_available"]
        for row in rows
    )

    print("===== FEATURE LABELING QUEUE =====")
    print(f"Cards: {len(rows)}")
    print(f"Images available: {available}")
    print(
        f"Images missing: "
        f"{len(rows) - available}"
    )
    print(f"Output: {OUTPUT.relative_to(ROOT)}")

    print()
    print("===== EXISTING LABEL COUNTS =====")

    for feature in FEATURES:
        count = sum(
            bool(
                str(row[feature]).strip()
            )
            for row in rows
        )

        print(
            f"{feature}: "
            f"{count}/{len(rows)}"
        )


if __name__ == "__main__":
    main()
