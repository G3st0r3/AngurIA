import argparse
import csv
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"
INCOMING_DIR = DATASET_DIR / "incoming"
METADATA_FILE = DATASET_DIR / "metadata.csv"

IMPORT_SCRIPT = BASE_DIR / "scripts" / "import_dataset.py"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def read_dataset_ids():
    if not METADATA_FILE.exists():
        return set()

    ids = set()

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            item_id = row.get("id", "").strip()

            if item_id:
                ids.add(item_id)

    return ids


def prepare_image(source_path):
    source_path = source_path.expanduser().resolve()

    if not source_path.exists():
        print(
            f"⚠️ File non trovato: {source_path}"
        )
        return False

    extension = source_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        print(
            f"⚠️ Formato non supportato: "
            f"{source_path.name}"
        )
        return False

    INCOMING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        INCOMING_DIR / source_path.name
    )

    if destination.exists():
        print(
            f"⚠️ Già presente in incoming: "
            f"{destination.name}"
        )
        return False

    shutil.copy2(
        source_path,
        destination,
    )

    print(
        f"📥 Preparata: "
        f"{source_path.name}"
    )

    return True


def run_import(source):
    subprocess.run(
        [
            sys.executable,
            str(IMPORT_SCRIPT),
            "--source",
            source,
        ],
        cwd=PROJECT_DIR,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Import batch immagini AngurIA "
            "e apertura annotatore web"
        )
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="Percorsi delle immagini da importare",
    )

    parser.add_argument(
        "--source",
        choices=["own", "external"],
        default="own",
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
    )

    args = parser.parse_args()

    before_ids = read_dataset_ids()

    copied = 0

    print()
    print("🍉 ANGURIA BATCH DATASET")
    print("=" * 40)

    for image_name in args.images:
        if prepare_image(
            Path(image_name)
        ):
            copied += 1

    if copied == 0:
        print()
        print("⚠️ Nessuna nuova immagine preparata.")
        return

    print()
    print(
        f"🚚 Importazione di "
        f"{copied} immagini..."
    )

    run_import(args.source)

    after_ids = read_dataset_ids()

    new_ids = sorted(
        after_ids - before_ids
    )

    if not new_ids:
        print()
        print(
            "⚠️ Nessun nuovo ID rilevato."
        )
        return

    print()
    print("✅ NUOVI ELEMENTI:")
    for item_id in new_ids:
        print(f"   {item_id}")

    print()
    print(
        "🌐 Apertura annotatore web..."
    )

    for index, item_id in enumerate(new_ids):
        url = (
            f"{args.base_url}"
            f"/annotate/{item_id}"
        )

        print(
            f"   {item_id} -> {url}"
        )

        webbrowser.open_new_tab(url)

        if index < len(new_ids) - 1:
            time.sleep(0.7)

    print()
    print(
        "✅ Batch pronto: "
        "disegna e salva i bounding box "
        "nelle schede aperte."
    )


if __name__ == "__main__":
    main()
