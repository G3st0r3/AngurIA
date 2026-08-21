import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"

RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
RAW_EXTERNAL_DIR = DATASET_DIR / "raw" / "external"
RAW_OPENED_DIR = DATASET_DIR / "raw" / "opened"

CARDS_DIR = DATASET_DIR / "cards"

TRAIN_IMAGES_DIR = DATASET_DIR / "images" / "train"
VAL_IMAGES_DIR = DATASET_DIR / "images" / "val"

TRAIN_LABELS_DIR = DATASET_DIR / "labels" / "train"
VAL_LABELS_DIR = DATASET_DIR / "labels" / "val"

METADATA_FILE = DATASET_DIR / "metadata.csv"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def count_images(directory):
    if not directory.exists():
        return 0

    return sum(
        1
        for file in directory.iterdir()
        if file.is_file()
        and file.suffix.lower()
        in IMAGE_EXTENSIONS
    )


def count_txt_files(directory):
    if not directory.exists():
        return 0

    return sum(
        1
        for file in directory.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".txt"
    )


def load_cards():
    if not CARDS_DIR.exists():
        return []

    cards = []

    for file in sorted(CARDS_DIR.glob("ANG*.json")):
        try:
            with file.open(
                "r",
                encoding="utf-8",
            ) as handle:
                cards.append(
                    json.load(handle)
                )
        except Exception as error:
            print(
                f"⚠️ Errore nella scheda "
                f"{file.name}: {error}"
            )

    return cards


def count_metadata_rows():
    if not METADATA_FILE.exists():
        return 0

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return sum(
            1 for _ in csv.DictReader(file)
        )


def main():
    cards = load_cards()

    total_cards = len(cards)

    annotated_cards = sum(
        1
        for card in cards
        if card.get("trainingStatus")
        == "annotated"
    )

    not_annotated_cards = sum(
        1
        for card in cards
        if card.get("trainingStatus")
        == "not_annotated"
    )

    with_brix = sum(
        1
        for card in cards
        if card.get("brix") is not None
    )

    with_sweetness = sum(
        1
        for card in cards
        if card.get("sweetness") is not None
    )

    with_opened_photo = sum(
        1
        for card in cards
        if card.get("openedPhoto")
    )

    print()
    print("🍉 ANGURIA DATASET REPORT")
    print("=" * 36)

    print()
    print("📸 IMMAGINI")
    print(
        f"Foto proprie: "
        f"{count_images(RAW_OWN_DIR)}"
    )
    print(
        f"Foto esterne: "
        f"{count_images(RAW_EXTERNAL_DIR)}"
    )
    print(
        f"Foto dopo il taglio: "
        f"{count_images(RAW_OPENED_DIR)}"
    )

    print()
    print("🧠 TRAINING")
    print(
        f"Immagini train: "
        f"{count_images(TRAIN_IMAGES_DIR)}"
    )
    print(
        f"Annotazioni train: "
        f"{count_txt_files(TRAIN_LABELS_DIR)}"
    )
    print(
        f"Immagini validation: "
        f"{count_images(VAL_IMAGES_DIR)}"
    )
    print(
        f"Annotazioni validation: "
        f"{count_txt_files(VAL_LABELS_DIR)}"
    )

    print()
    print("🗂 SCHEDE")
    print(
        f"Schede totali: "
        f"{total_cards}"
    )
    print(
        f"Annotate: "
        f"{annotated_cards}"
    )
    print(
        f"Da annotare: "
        f"{not_annotated_cards}"
    )
    print(
        f"Record metadata.csv: "
        f"{count_metadata_rows()}"
    )

    print()
    print("🍬 QUALITÀ REALE")
    print(
        f"Con valore Brix: "
        f"{with_brix}"
    )
    print(
        f"Con valutazione dolcezza: "
        f"{with_sweetness}"
    )
    print(
        f"Con foto dopo il taglio: "
        f"{with_opened_photo}"
    )

    print()
    print("=" * 36)


if __name__ == "__main__":
    main()