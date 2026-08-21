import argparse
import json
from pathlib import Path

from intelligence.score_engine import calculate_anguria_score


BASE_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = BASE_DIR / "datasets" / "watermelon" / "cards"


def score_card(item_id: str) -> None:
    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        raise FileNotFoundError(
            f"Scheda non trovata: {card_path}"
        )

    with card_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        card = json.load(file)

    features = {
        "groundSpot": card.get("groundSpot", ""),
        "peduncle": card.get("peduncle", ""),
        "shape": card.get("shape", ""),
        "stripes": card.get("stripes", ""),
        "symmetry": card.get("symmetry", ""),
        "color": card.get("color", ""),
        "surface": card.get("surface", ""),
    }

    result = calculate_anguria_score(features)

    card["anguriaScore"] = result["score"]
    card["anguriaScoreMax"] = result["maxScore"]
    card["recommendation"] = result["recommendation"]
    card["scoreReasons"] = result["reasons"]
    card["scoreWarnings"] = result["warnings"]
    card["scoreExperimental"] = result["experimental"]
    card["scoreDisclaimer"] = result["disclaimer"]

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

    print()
    print(f"🍉 Scheda: {item_id}")
    print(f"Score: {result['score']}/100")
    print(
        f"Valutazione: "
        f"{result['recommendation']}"
    )
    print(f"Aggiornata: {card_path}")
    print()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "item_id",
        help="ID della scheda, es. ANG0002",
    )

    args = parser.parse_args()

    score_card(args.item_id)


if __name__ == "__main__":
    main()
