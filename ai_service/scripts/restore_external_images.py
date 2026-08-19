import json
import urllib.parse
import urllib.request
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "datasets" / "watermelon"
CARDS_DIR = DATASET_DIR / "cards"
EXTERNAL_DIR = DATASET_DIR / "raw" / "external"

IDS = [
    "ANG0005",
    "ANG0006",
    "ANG0007",
    "ANG0008",
    "ANG0009",
    "ANG0010",
]

EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

for item_id in IDS:
    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        print(f"⚠️ {item_id}: card assente")
        continue

    card = json.loads(card_path.read_text(encoding="utf-8"))

    source_url = card.get("sourceUrl", "")
    filename = card.get("photo", f"{item_id}.jpg")

    if "commons.wikimedia.org/wiki/File:" not in source_url:
        print(f"⚠️ {item_id}: sourceUrl non Wikimedia")
        continue

    commons_name = source_url.split("/wiki/File:", 1)[1]
    commons_name = urllib.parse.unquote(commons_name)

    direct_url = (
        "https://commons.wikimedia.org/wiki/"
        "Special:Redirect/file/"
        + urllib.parse.quote(commons_name)
    )

    destination = EXTERNAL_DIR / filename

    if destination.exists():
        print(f"✅ {item_id}: già presente")
        continue

    try:
        print(f"⬇️ {item_id}: {commons_name}")

        request = urllib.request.Request(
            direct_url,
            headers={
                "User-Agent":
                    "AngurIA-dataset-builder/1.0"
            },
        )

        success = False

        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=30,
                ) as response:
                    destination.write_bytes(
                        response.read()
                    )

                success = True
                break

            except Exception as error:
                if "429" in str(error):
                    wait_seconds = attempt * 8

                    print(
                        f"⏳ {item_id}: rate limit, "
                        f"attendo {wait_seconds}s "
                        f"(tentativo {attempt}/3)"
                    )

                    time.sleep(wait_seconds)
                    continue

                raise

        if success:
            print(
                f"✅ {item_id}: "
                f"{destination.name} "
                f"({destination.stat().st_size} bytes)"
            )

            time.sleep(4)

        else:
            print(
                f"❌ {item_id}: download non riuscito "
                f"dopo 3 tentativi"
            )

    except Exception as error:
        print(
            f"❌ {item_id}: {error}"
        )
