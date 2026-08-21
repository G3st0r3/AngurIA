from intelligence.score_engine import calculate_anguria_score


features = {
    "groundSpot": "creamy_yellow",
    "peduncle": "dry",
    "shape": "regular",
    "stripes": "well_defined",
    "symmetry": "high",
    "color": "balanced",
    "surface": "healthy",
}

result = calculate_anguria_score(features)

print()
print("🍉 ANGURIA SCORE TEST")
print("=" * 32)
print(f"Score: {result['score']}/100")
print(f"Valutazione: {result['recommendation']}")
print()

print("Punti favorevoli:")
for reason in result["reasons"]:
    print(f"  ✅ {reason}")

print()

if result["warnings"]:
    print("Attenzioni:")
    for warning in result["warnings"]:
        print(f"  ⚠️ {warning}")

print()
print(result["disclaimer"])
