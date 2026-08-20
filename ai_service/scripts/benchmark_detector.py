import argparse
from pathlib import Path

from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent.parent
RUNS_DIR = BASE_DIR / "runs"


def available_models():
    models = {}

    for version in ("watermelon_v1", "watermelon_v2", "watermelon_v3"):
        path = RUNS_DIR / version / "weights" / "best.pt"

        if path.exists():
            models[version] = path

    return models


def benchmark_image(image_path, models, confidence):
    print()
    print("=" * 64)
    print("🍉 IMMAGINE:", image_path)
    print("=" * 64)

    for name, model_path in models.items():
        model = YOLO(str(model_path))

        result = model(
            str(image_path),
            conf=confidence,
            verbose=False,
        )[0]

        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            print(
                f"{name}: "
                "NESSUN CANDIDATO"
            )
            continue

        confidences = sorted(
            (
                float(value)
                for value in boxes.conf
            ),
            reverse=True,
        )

        top5 = [
            round(value, 4)
            for value in confidences[:5]
        ]

        print(
            f"{name}: "
            f"BEST={confidences[0]:.4f} | "
            f"CANDIDATI={len(confidences)} | "
            f"TOP5={top5}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark detector AngurIA V1/V2/V3"
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="Una o più immagini reali di test",
    )

    parser.add_argument(
        "--conf",
        type=float,
        default=0.001,
        help="Confidence diagnostica (default 0.001)",
    )

    args = parser.parse_args()

    models = available_models()

    if not models:
        raise SystemExit(
            "❌ Nessun modello AngurIA trovato"
        )

    print()
    print("🍉 ANGURIA DETECTOR BENCHMARK")
    print("=" * 64)

    print("Modelli:")
    for name, path in models.items():
        print(
            f"  {name} -> {path}"
        )

    valid_images = []

    for image in args.images:
        path = Path(image).expanduser()

        if not path.exists():
            print(
                f"⚠️ Immagine non trovata: {path}"
            )
            continue

        valid_images.append(path)

    if not valid_images:
        raise SystemExit(
            "❌ Nessuna immagine valida"
        )

    for image_path in valid_images:
        benchmark_image(
            image_path,
            models,
            args.conf,
        )


if __name__ == "__main__":
    main()
