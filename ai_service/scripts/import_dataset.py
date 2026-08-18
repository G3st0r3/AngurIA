import argparse
import csv
import json
import shutil
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"
INCOMING_DIR = DATASET_DIR / "incoming"
RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
RAW_EXTERNAL_DIR = DATASET_DIR / "raw" / "external"
CARDS_DIR = DATASET_DIR / "cards"
METADATA_FILE = DATASET_DIR / "metadata.csv"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_next_id():
    if not METADATA_FILE.exists():
        return 1

    highest_id = 0

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            item_id = row.get("id", "")

            if not item_id.startswith("ANG"):
                continue

            try:
                numeric_id = int(item_id[3:])
            except ValueError:
                continue

            highest_id = max(
                highest_id,
                numeric_id,
            )

    return highest_id + 1


def append_metadata(
    item_id,
    filename,
    source,
):
    with METADATA_FILE.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                item_id,
                filename,
                source,
                date.today().isoformat(),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "import automatico",
            ]
        )


def create_card(
    item_id,
    filename,
    source,
):
    card = {
        "id": item_id,
        "status": "new",
        "photo": filename,
        "source": source,
        "sourceUrl": "",
        "author": "",
        "license": "",
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
        "trainingStatus": "not_annotated",
        "notes": "",
    }

    card_path = CARDS_DIR / f"{item_id}.json"

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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import dataset AngurIA"
    )

    parser.add_argument(
        "--source",
        choices=["own", "external"],
        default="own",
        help="Origine delle immagini da importare",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    INCOMING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RAW_OWN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RAW_EXTERNAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CARDS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    incoming_files = sorted(
        file
        for file in INCOMING_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower()
        in SUPPORTED_EXTENSIONS
    )

    if not incoming_files:
        print(
            "Nessuna nuova immagine "
            "nella cartella incoming."
        )
        return

    next_id = get_next_id()
    imported_count = 0

    for source_file in incoming_files:
        item_id = f"ANG{next_id:04d}"

        extension = source_file.suffix.lower()

        if extension == ".jpeg":
            extension = ".jpg"

        filename = f"{item_id}{extension}"

        destination_dir = (
            RAW_OWN_DIR
            if args.source == "own"
            else RAW_EXTERNAL_DIR
        )

        destination = (
            destination_dir / filename
        )

        shutil.move(
            str(source_file),
            str(destination),
        )

        append_metadata(
            item_id=item_id,
            filename=filename,
            source=args.source,
        )

        create_card(
            item_id=item_id,
            filename=filename,
            source=args.source,
        )

        print(
            f"Importata: "
            f"{source_file.name} "
            f"-> {filename}"
        )

        print(
            f"Scheda creata: "
            f"cards/{item_id}.json"
        )

        next_id += 1
        imported_count += 1

    print()
    print(
        f"Import completato: "
        f"{imported_count} immagini."
    )


if __name__ == "__main__":
    main()