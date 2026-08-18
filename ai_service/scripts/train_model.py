import argparse
import shutil
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"

RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
RAW_EXTERNAL_DIR = DATASET_DIR / "raw" / "external"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"

TRAIN_IMAGES_DIR = DATASET_DIR / "images" / "train"
VAL_IMAGES_DIR = DATASET_DIR / "images" / "val"

TRAIN_LABELS_DIR = DATASET_DIR / "labels" / "train"
VAL_LABELS_DIR = DATASET_DIR / "labels" / "val"

DATASET_YAML = DATASET_DIR / "watermelon.yaml"

RUNS_DIR = BASE_DIR / "runs"

MODEL_NAME = "yolo11n.pt"
DEFAULT_TRAIN_NAME = "watermelon_v2"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def clear_directory(directory):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for item in directory.iterdir():
        if item.is_file():
            item.unlink()


def collect_annotated_images():
    images = []

    for directory in (
        RAW_OWN_DIR,
        RAW_EXTERNAL_DIR,
    ):
        if not directory.exists():
            continue

        for image_path in sorted(
            directory.iterdir()
        ):
            if (
                not image_path.is_file()
                or image_path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            annotation_path = (
                ANNOTATIONS_DIR
                / f"{image_path.stem}.txt"
            )

            if annotation_path.exists():
                images.append(
                    (
                        image_path,
                        annotation_path,
                    )
                )

    return sorted(
        images,
        key=lambda item: item[0].name,
    )


def prepare_split(items):
    if len(items) < 2:
        raise RuntimeError(
            "Servono almeno 2 immagini annotate."
        )

    split_index = int(
        len(items) * 0.80
    )

    split_index = max(
        1,
        min(
            split_index,
            len(items) - 1,
        ),
    )

    train_items = items[
        :split_index
    ]

    val_items = items[
        split_index:
    ]

    return train_items, val_items


def copy_item(
    image_path,
    annotation_path,
    image_destination,
    label_destination,
):
    shutil.copy2(
        image_path,
        image_destination
        / image_path.name,
    )

    shutil.copy2(
        annotation_path,
        label_destination
        / annotation_path.name,
    )


def prepare_dataset():
    items = collect_annotated_images()

    print(
        f"Immagini annotate trovate: "
        f"{len(items)}"
    )

    train_items, val_items = (
        prepare_split(items)
    )

    clear_directory(
        TRAIN_IMAGES_DIR
    )

    clear_directory(
        VAL_IMAGES_DIR
    )

    clear_directory(
        TRAIN_LABELS_DIR
    )

    clear_directory(
        VAL_LABELS_DIR
    )

    for (
        image_path,
        annotation_path,
    ) in train_items:
        copy_item(
            image_path,
            annotation_path,
            TRAIN_IMAGES_DIR,
            TRAIN_LABELS_DIR,
        )

    for (
        image_path,
        annotation_path,
    ) in val_items:
        copy_item(
            image_path,
            annotation_path,
            VAL_IMAGES_DIR,
            VAL_LABELS_DIR,
        )

    print(
        f"Train: {len(train_items)}"
    )

    print(
        f"Validation: {len(val_items)}"
    )


def train_model(train_name):
    command = [
        "yolo",
        "detect",
        "train",
        f"model={MODEL_NAME}",
        f"data={DATASET_YAML}",
        "epochs=20",
        "imgsz=640",
        "batch=1",
        f"project={RUNS_DIR}",
        f"name={train_name}",
        "exist_ok=True",
    ]

    print()
    print(
        "Avvio training AngurIA..."
    )

    subprocess.run(
        command,
        check=True,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Training manager AngurIA"
    )

    parser.add_argument(
        "train_name",
        nargs="?",
        default=DEFAULT_TRAIN_NAME,
        help=(
            "Nome del run YOLO "
            f"(default: {DEFAULT_TRAIN_NAME})"
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()
    train_name = args.train_name

    print()
    print(
        "🍉 ANGURIA TRAINING MANAGER"
    )

    print(
        "=" * 34
    )

    if not DATASET_YAML.exists():
        raise RuntimeError(
            "watermelon.yaml non trovato."
        )

    prepare_dataset()

    print(
        f"Run selezionato: {train_name}"
    )

    train_model(train_name)

    best_model = (
        RUNS_DIR
        / train_name
        / "weights"
        / "best.pt"
    )

    print()
    print(
        "=" * 34
    )

    if best_model.exists():
        print(
            "✅ Training completato"
        )

        print(
            f"Nuovo modello: "
            f"{best_model}"
        )
    else:
        print(
            "⚠️ Training terminato, "
            "ma best.pt non trovato."
        )


if __name__ == "__main__":
    main()