import json
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"

RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
CARDS_DIR = DATASET_DIR / "cards"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def create_card(
    item_id,
    filename,
):
    annotation_path = (
        ANNOTATIONS_DIR
        / f"{item_id}.txt"
    )

    training_status = (
        "annotated"
        if annotation_path.exists()
        else "not_annotated"
    )

    card = {
        "id": item_id,
        "status": "active",
        "photo": filename,
        "source": "own",
        "date": date.today().isoformat(),
        "variety": "",
        "origin": "",
        "weightKg": None,
        "pricePerKg": None,
        "brix": None,
        "sweetness": None,
        "crunchiness": None,
        "juiciness": None,
        "mealiness": None,
        "seedLevel": None,
        "peduncle": "",
        "groundSpot": "",
        "shape": "",
        "stripes": "",
        "externalQuality": None,
        "openedPhoto": "",
        "trainingStatus": training_status,
        "notes": "scheda ricostruita automaticamente",
    }

    card_path = (
        CARDS_DIR
        / f"{item_id}.json"
    )

    with card_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            card,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():
    CARDS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    created = 0
    existing = 0

    for image_path in sorted(
        RAW_OWN_DIR.iterdir()
    ):
        if (
            not image_path.is_file()
            or image_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        item_id = image_path.stem

        card_path = (
            CARDS_DIR
            / f"{item_id}.json"
        )

        if card_path.exists():
            print(
                f"Gia presente: "
                f"{card_path.name}"
            )
            existing += 1
            continue

        create_card(
            item_id=item_id,
            filename=image_path.name,
        )

        print(
            f"Creata scheda: "
            f"{item_id}.json"
        )

        created += 1

    print()
    print(
        f"Schede create: {created}"
    )
    print(
        f"Schede gia presenti: {existing}"
    )


if __name__ == "__main__":
    main()