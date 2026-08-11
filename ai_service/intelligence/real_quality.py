from typing import Optional


def calculate_real_quality_score(
    sweetness: Optional[int] = None,
    crunchiness: Optional[int] = None,
    juiciness: Optional[int] = None,
    mealiness: Optional[int] = None,
) -> Optional[int]:
    """
    Calcola la qualità reale dell'anguria su scala 0-100.

    sweetness:
        1 = poco dolce
        5 = molto dolce

    crunchiness:
        1 = morbida
        5 = molto croccante

    juiciness:
        1 = poco succosa
        5 = molto succosa

    mealiness:
        1 = non farinosa
        5 = molto farinosa

    La farinosità viene invertita perché un valore alto
    rappresenta una caratteristica negativa.
    """

    values = []

    if sweetness is not None:
        values.append(sweetness)

    if crunchiness is not None:
        values.append(crunchiness)

    if juiciness is not None:
        values.append(juiciness)

    if mealiness is not None:
        inverted_mealiness = 6 - mealiness
        values.append(inverted_mealiness)

    if not values:
        return None

    average = sum(values) / len(values)

    score = round(
        ((average - 1) / 4) * 100
    )

    return max(
        0,
        min(100, score),
    )


def calculate_prediction_error(
    predicted_score: int,
    real_score: Optional[int],
) -> Optional[int]:
    if real_score is None:
        return None

    return abs(
        predicted_score - real_score
    )