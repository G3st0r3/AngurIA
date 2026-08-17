from typing import Any, Dict, List


MAX_SCORE = 100


FEATURES = {
    "groundSpot": {
        "max": 20,
        "mapping": {
            "creamy_yellow": 20,
            "yellow": 16,
            "light_yellow": 10,
            "white": 3,
        },
    },

    "peduncle": {
        "max": 15,
        "mapping": {
            "dry": 15,
            "partly_dry": 10,
            "green": 3,
        },
    },

    "shape": {
        "max": 15,
        "mapping": {
            "regular": 15,
            "slightly_irregular": 9,
            "irregular": 3,
        },
    },

    "stripes": {
        "max": 15,
        "mapping": {
            "well_defined": 15,
            "medium": 9,
            "weak": 4,
        },
    },

    "symmetry": {
        "max": 15,
        "mapping": {
            "high": 15,
            "medium": 9,
            "low": 3,
        },
    },

    "color": {
        "max": 10,
        "mapping": {
            "balanced": 10,
            "acceptable": 6,
            "poor": 2,
        },
    },

    "surface": {
        "max": 10,
        "mapping": {
            "healthy": 10,
            "minor_defects": 6,
            "damaged": 0,
        },
    },
}


def _normalize_value(value: Any) -> str:
    return str(value or "").strip().lower()


def _score_feature(
    value: Any,
    mapping: Dict[str, int],
) -> tuple[int, bool]:
    normalized = _normalize_value(value)

    if not normalized:
        return 0, False

    if normalized not in mapping:
        return 0, False

    return mapping[normalized], True


def calculate_anguria_score(
    features: Dict[str, Any],
) -> Dict[str, Any]:

    raw_score = 0
    available_max_score = 0

    reasons: List[str] = []
    warnings: List[str] = []
    missing_features: List[str] = []

    observed_features = 0

    scored = {}

    for feature_name, config in FEATURES.items():
        value = features.get(feature_name, "")

        points, observed = _score_feature(
            value,
            config["mapping"],
        )

        scored[feature_name] = {
            "value": _normalize_value(value),
            "points": points,
            "maxPoints": config["max"],
            "observed": observed,
        }

        if observed:
            raw_score += points
            available_max_score += config["max"]
            observed_features += 1
        else:
            missing_features.append(feature_name)

    # ------------------------------------------------
    # Reasons / warnings
    # ------------------------------------------------

    ground_spot = scored["groundSpot"]

    if ground_spot["observed"]:
        if ground_spot["points"] >= 16:
            reasons.append(
                "Macchia d'appoggio favorevole"
            )
        elif ground_spot["points"] <= 3:
            warnings.append(
                "Macchia d'appoggio poco favorevole"
            )

    peduncle = scored["peduncle"]

    if peduncle["observed"]:
        if peduncle["points"] >= 10:
            reasons.append(
                "Peduncolo compatibile con buona maturazione"
            )
        elif peduncle["points"] <= 3:
            warnings.append(
                "Peduncolo ancora molto verde"
            )

    shape = scored["shape"]

    if shape["observed"]:
        if shape["points"] >= 15:
            reasons.append("Forma regolare")
        elif shape["points"] <= 3:
            warnings.append(
                "Forma molto irregolare"
            )

    stripes = scored["stripes"]

    if stripes["observed"]:
        if stripes["points"] >= 15:
            reasons.append(
                "Striature ben definite"
            )

    symmetry = scored["symmetry"]

    if symmetry["observed"]:
        if symmetry["points"] >= 15:
            reasons.append(
                "Buona simmetria"
            )

    color = scored["color"]

    if color["observed"]:
        if color["points"] >= 10:
            reasons.append(
                "Colorazione esterna equilibrata"
            )

    surface = scored["surface"]

    if surface["observed"]:
        if surface["points"] >= 10:
            reasons.append(
                "Superficie senza difetti rilevanti"
            )
        elif surface["points"] == 0:
            warnings.append(
                "Difetti superficiali importanti"
            )

    # ------------------------------------------------
    # Score V2 confidence-aware
    # ------------------------------------------------
    #
    # Il punteggio normalizzato puro stima come sarebbe
    # il risultato se i segnali osservati fossero
    # rappresentativi anche di quelli mancanti.
    #
    # Per evitare di gonfiare eccessivamente lo score
    # quando mancano feature importanti, recuperiamo
    # solo una parte del gap tra raw_score e
    # normalized_score.
    #
    # Più alta è la completezza, maggiore è la fiducia
    # concessa alla normalizzazione.
    # ------------------------------------------------

    completeness = round(
        available_max_score /
        MAX_SCORE *
        100
    )

    if available_max_score > 0:
        normalized_score = round(
            raw_score /
            available_max_score *
            MAX_SCORE
        )
    else:
        normalized_score = 0

    normalized_score = max(
        0,
        min(normalized_score, MAX_SCORE),
    )

    confidence = completeness / 100.0

    # Recuperiamo al massimo il 50% del gap teorico,
    # modulato ulteriormente dalla completezza.
    recovery_factor = 0.5 * confidence

    recovery_gap = (
        normalized_score - raw_score
    )

    confidence_adjustment = round(
        recovery_gap * recovery_factor
    )

    final_score = raw_score + confidence_adjustment

    final_score = max(
        0,
        min(final_score, MAX_SCORE),
    )

    # ------------------------------------------------
    # Recommendation
    # ------------------------------------------------

    if final_score >= 80:
        recommendation = "promettente"
    elif final_score >= 60:
        recommendation = "discreta"
    elif final_score >= 40:
        recommendation = "incerta"
    else:
        recommendation = "poco promettente"

    return {
        "score": final_score,

        "rawScore": raw_score,
        "normalizedScore": normalized_score,
        "confidenceAdjustment": confidence_adjustment,
        "recoveryFactor": round(recovery_factor, 3),
        "availableMaxScore":
            available_max_score,

        "maxScore": MAX_SCORE,

        "completeness": completeness,
        "observedFeatures":
            observed_features,

        "missingFeatures":
            missing_features,

        "recommendation":
            recommendation,

        "reasons": reasons,
        "warnings": warnings,

        "featureScores": scored,

        "experimental": True,

        "disclaimer": (
            "Punteggio euristico sperimentale. "
            "I segnali non osservati non vengono "
            "considerati negativi. "
            "I segnali mancanti vengono gestiti "
            "con una normalizzazione prudenziale "
            "pesata sulla completezza dell'analisi."
        ),
    }
