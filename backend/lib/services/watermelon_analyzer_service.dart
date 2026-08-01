import 'package:backend/models/analysis_result.dart';

class WatermelonAnalyzerService {
  const WatermelonAnalyzerService();

  AnalysisResult analyzeSimulated() {
    return const AnalysisResult(
      score: 91,
      sweetness: 95,
      crunchiness: 88,
      mealiness: 4,
      confidence: 93,
      recommendation: 'Consigliata',
      reasons: [
        'Forma regolare',
        'Buon contrasto delle striature',
        'Aspetto generale compatibile con una buona maturazione',
      ],
    );
  }
}