class AnalysisResult {
  final int score;
  final int sweetness;
  final int crunchiness;
  final int mealiness;
  final int confidence;
  final String recommendation;
  final List<String> reasons;

  const AnalysisResult({
    required this.score,
    required this.sweetness,
    required this.crunchiness,
    required this.mealiness,
    required this.confidence,
    required this.recommendation,
    required this.reasons,
  });

  Map<String, dynamic> toJson() {
    return {
      'score': score,
      'sweetness': sweetness,
      'crunchiness': crunchiness,
      'mealiness': mealiness,
      'confidence': confidence,
      'recommendation': recommendation,
      'reasons': reasons,
    };
  }
}