from intelligence.real_quality import (
    calculate_prediction_error,
    calculate_real_quality_score,
)


print("# 🍉 ANGURIA REAL QUALITY TEST")
print()

real_score = calculate_real_quality_score(
    sweetness=5,
    crunchiness=5,
    juiciness=5,
    mealiness=1,
)

print(
    f"Qualità reale: {real_score}/100"
)

error = calculate_prediction_error(
    predicted_score=50,
    real_score=real_score,
)

print(
    f"Errore previsione: {error} punti"
)