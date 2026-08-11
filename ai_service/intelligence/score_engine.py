from typing import Any, Dict, List


MAX_SCORE = 100


def _score_choice(
    value: str,
    mapping: Dict[str, int],
) -> int:
    normalized = (value or "").strip().lower()
    return mapping.get(normalized, 0)


def calculate_anguria_score(
    features: Dict[str, Any],
) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []
    warnings: List[str] = []

    ground_spot = _score_choice(
        features.get("groundSpot", ""),
        {
            "creamy_yellow": 20,
            "yellow": 16,
            "light_yellow": 10,
            "white": 3,
        },
    )
    score += ground_spot

    if ground_spot >= 16:
        reasons.append("Macchia d'appoggio favorevole")
    elif ground_spot <= 3:
        warnings.append("Macchia d'appoggio poco favorevole")

    peduncle = _score_choice(
        features.get("peduncle", ""),
        {
            "dry": 15,
            "partly_dry": 10,
            "green": 3,
        },
    )
    score += peduncle

    if peduncle >= 10:
        reasons.append(
            "Peduncolo compatibile con buona maturazione"
        )
    elif peduncle <= 3:
        warnings.append("Peduncolo ancora molto verde")

    shape = _score_choice(
        features.get("shape", ""),
        {
            "regular": 15,
            "slightly_irregular": 9,
            "irregular": 3,
        },
    )
    score += shape

    if shape >= 15:
        reasons.append("Forma regolare")
    elif shape <= 3:
        warnings.append("Forma molto irregolare")

    stripes = _score_choice(
        features.get("stripes", ""),
        {
            "well_defined": 15,
            "medium": 9,
            "weak": 4,
        },
    )
    score += stripes

    if stripes >= 15:
        reasons.append("Striature ben definite")

    symmetry = _score_choice(
        features.get("symmetry", ""),
        {
            "high": 15,
            "medium": 9,
            "low": 3,
        },
    )
    score += symmetry

    if symmetry >= 15:
        reasons.append("Buona simmetria")

    color = _score_choice(
        features.get("color", ""),
        {
            "balanced": 10,
            "acceptable": 6,
            "poor": 2,
        },
    )
    score += color

    if color >= 10:
        reasons.append("Colorazione esterna equilibrata")

    surface = _score_choice(
        features.get("surface", ""),
        {
            "healthy": 10,
            "minor_defects": 6,
            "damaged": 0,
        },
    )
    score += surface

    if surface >= 10:
        reasons.append("Superficie senza difetti rilevanti")
    elif surface == 0:
        warnings.append("Difetti superficiali importanti")

    score = max(0, min(score, MAX_SCORE))

    if score >= 80:
        recommendation = "promettente"
    elif score >= 60:
        recommendation = "discreta"
    elif score >= 40:
        recommendation = "incerta"
    else:
        recommendation = "poco promettente"

    return {
        "score": score,
        "maxScore": MAX_SCORE,
        "recommendation": recommendation,
        "reasons": reasons,
        "warnings": warnings,
        "experimental": True,
        "disclaimer": (
            "Punteggio euristico sperimentale. "
            "Non ancora validato rispetto a Brix "
            "o qualità interna reale."
        ),
    }
