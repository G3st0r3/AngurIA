import random
import shutil
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

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

TRAIN_RATIO = 0.80
RANDOM_SEED = 42


def clear_directory(directory):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for item in directory.iterdir():
        if item.is_file():
            item.unlink()


def collect_images():
    images = []

    for source_dir in (
        RAW_OWN_DIR,
        RAW_EXTERNAL_DIR,
    ):
        if not source_dir.exists():
            continue

        for file in source_dir.iterdir():
            if not file.is_file():
                continue

            if (
                file.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            label_path = (
                ANNOTATIONS_DIR /
                f"{file.stem}.txt"
            )

            # Entrano nello split solo immagini
            # che possiedono una vera annotazione YOLO.
            if not label_path.exists():
                continue

            if not label_path.read_text(
                encoding="utf-8"
            ).strip():
                continue

            images.append(file)

    return sorted(
        images,
        key=lambda file: file.stem,
    )


def copy_images_and_labels(
    images,
    image_destination,
    label_destination,
):
    for image_path in images:
        shutil.copy2(
            image_path,
            image_destination /
            image_path.name,
        )

        label_path = (
            ANNOTATIONS_DIR /
            f"{image_path.stem}.txt"
        )

        shutil.copy2(
            label_path,
            label_destination /
            label_path.name,
        )


def main():
    images = collect_images()

    if len(images) < 2:
        print(
            "Servono almeno 2 immagini "
            "annotate per creare train "
            "e validation."
        )
        return

    random.seed(RANDOM_SEED)

    shuffled_images = images.copy()
    random.shuffle(shuffled_images)

    split_index = int(
        len(shuffled_images) *
        TRAIN_RATIO
    )

    split_index = max(
        1,
        min(
            split_index,
            len(shuffled_images) - 1,
        ),
    )

    train_images = shuffled_images[
        :split_index
    ]

    val_images = shuffled_images[
        split_index:
    ]

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

    copy_images_and_labels(
        train_images,
        TRAIN_IMAGES_DIR,
        TRAIN_LABELS_DIR,
    )

    copy_images_and_labels(
        val_images,
        VAL_IMAGES_DIR,
        VAL_LABELS_DIR,
    )

    print()
    print("🍉 TRAINING SPLIT COMPLETATO")
    print("=" * 40)

    print(
        f"Immagini totali annotate: "
        f"{len(images)}"
    )

    print(
        f"Train: {len(train_images)}"
    )

    print(
        f"Validation: {len(val_images)}"
    )

    print()
    print("Train:")

    for image in train_images:
        print(
            f"  - {image.stem} "
            f"[{image.parent.name}]"
        )

    print()
    print("Validation:")

    for image in val_images:
        print(
            f"  - {image.stem} "
            f"[{image.parent.name}]"
        )

    print()
    print("=" * 40)


if __name__ == "__main__":
    main()
