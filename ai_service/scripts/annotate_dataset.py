from pathlib import Path

import cv2


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"

RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
RAW_EXTERNAL_DIR = DATASET_DIR / "raw" / "external"

ANNOTATIONS_DIR = DATASET_DIR / "annotations"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def save_yolo_annotation(
    image_path,
    rectangle,
):
    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        print(
            f"Impossibile leggere "
            f"{image_path.name}"
        )
        return False

    image_height, image_width = (
        image.shape[:2]
    )

    x, y, width, height = rectangle

    if width <= 0 or height <= 0:
        return False

    center_x = (
        x + width / 2
    ) / image_width

    center_y = (
        y + height / 2
    ) / image_height

    normalized_width = (
        width / image_width
    )

    normalized_height = (
        height / image_height
    )

    label_path = (
        ANNOTATIONS_DIR
        / f"{image_path.stem}.txt"
    )

    with label_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "0 "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{normalized_width:.6f} "
            f"{normalized_height:.6f}\n"
        )

    return True


def main():
    ANNOTATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    images = []

    for directory in (
        RAW_OWN_DIR,
        RAW_EXTERNAL_DIR,
    ):
        if not directory.exists():
            continue

        images.extend(
            file
            for file in directory.iterdir()
            if file.is_file()
            and file.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )

    images = sorted(
        images,
        key=lambda file: file.name,
    )

    if not images:
        print(
            "Nessuna immagine da annotare."
        )
        return

    annotated_count = 0
    skipped_count = 0

    for image_path in images:
        label_path = (
            ANNOTATIONS_DIR
            / f"{image_path.stem}.txt"
        )

        if label_path.exists():
            print(
                f"Gia annotata: "
                f"{image_path.name}"
            )
            skipped_count += 1
            continue

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            print(
                f"Errore lettura: "
                f"{image_path.name}"
            )
            continue

        print()
        print(
            f"Annotazione: "
            f"{image_path.name}"
        )

        print(
            "Disegna un rettangolo "
            "attorno all'anguria."
        )

        print(
            "Premi INVIO o SPAZIO "
            "per confermare."
        )

        print(
            "Premi C per annullare."
        )

        rectangle = cv2.selectROI(
            "AngurIA Dataset Annotator",
            image,
            showCrosshair=True,
            fromCenter=False,
        )

        cv2.destroyAllWindows()

        if rectangle[2] <= 0:
            print(
                "Annotazione saltata."
            )
            continue

        if save_yolo_annotation(
            image_path,
            rectangle,
        ):
            annotated_count += 1

            print(
                f"Salvata: "
                f"{label_path.name}"
            )

    print()
    print(
        "🍉 ANNOTAZIONE COMPLETATA"
    )

    print(
        f"Nuove annotazioni: "
        f"{annotated_count}"
    )

    print(
        f"Gia presenti: "
        f"{skipped_count}"
    )


if __name__ == "__main__":
    main()