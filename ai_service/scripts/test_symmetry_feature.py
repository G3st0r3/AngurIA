from pathlib import Path

import cv2
from ultralytics import YOLO

from app import estimate_symmetry_feature


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "watermelon_v3"
    / "weights"
    / "best.pt"
)

TESTS = [
    Path.home() / "Desktop" / "anguria_test.jpg",
    Path.home() / "Desktop" / "anguria_test_2.jpg",
    Path.home() / "Desktop" / "negative_test.jpg",
]

model = YOLO(str(MODEL_PATH))

for image_path in TESTS:
    print()
    print("=" * 60)
    print(image_path.name)

    if not image_path.exists():
        print("❌ immagine non trovata")
        continue

    result = model.predict(
        source=str(image_path),
        imgsz=416,
        conf=0.01,
        max_det=20,
        verbose=False,
    )[0]

    if result.boxes is None or len(result.boxes) == 0:
        print("Nessun candidato")
        continue

    best = max(
        result.boxes,
        key=lambda box: float(box.conf[0]),
    )

    x1, y1, x2, y2 = [
        round(float(value))
        for value in best.xyxy[0].tolist()
    ]

    box = {
        "x": x1,
        "y": y1,
        "width": max(0, x2 - x1),
        "height": max(0, y2 - y1),
    }

    image = cv2.imread(str(image_path))

    symmetry = estimate_symmetry_feature(
        image,
        box,
    )

    print(
        "confidence:",
        round(float(best.conf[0]), 4),
    )
    print("symmetry:", symmetry)
    print("box:", box)
