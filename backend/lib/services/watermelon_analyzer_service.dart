import 'dart:math' as math;

import 'package:backend/models/analysis_result.dart';
import 'package:backend/services/image_analysis_service.dart';

class WatermelonAnalyzerService {
  const WatermelonAnalyzerService();

  AnalysisResult analyze(ImageAnalysisData imageData) {
    final double brightnessScore = _brightnessScore(
      imageData.averageBrightness,
    );

    final double contrastScore = _contrastScore(
      imageData.brightnessContrast,
    );

    final double greenScore = _greenScore(
      imageData.greenPixelPercentage,
    );

    final double resolutionScore = _resolutionScore(
      width: imageData.width,
      height: imageData.height,
    );

    final int score = (
      brightnessScore * 0.30 +
      contrastScore * 0.30 +
      greenScore * 0.25 +
      resolutionScore * 0.15
    ).round().clamp(0, 100).toInt();

    final int confidence = (
      brightnessScore * 0.35 +
      contrastScore * 0.35 +
      resolutionScore * 0.30
    ).round().clamp(0, 100).toInt();

    return AnalysisResult(
      score: score,
      sweetness: 0,
      crunchiness: 0,
      mealiness: 0,
      confidence: confidence,
      recommendation: _recommendation(
        imageData: imageData,
        score: score,
      ),
      reasons: _reasons(
        imageData: imageData,
        brightnessScore: brightnessScore,
        contrastScore: contrastScore,
        greenScore: greenScore,
      ),
    );
  }

  double _brightnessScore(double brightness) {
    const double idealBrightness = 145;
    final double distance = (brightness - idealBrightness).abs();

    return (100 - distance * 0.9).clamp(0, 100).toDouble();
  }

  double _contrastScore(double contrast) {
    if (contrast <= 15) {
      return 20;
    }

    if (contrast >= 55) {
      return 100;
    }

    return ((contrast - 15) / 40 * 80 + 20)
        .clamp(0, 100)
        .toDouble();
  }

  double _greenScore(double greenPercentage) {
    if (greenPercentage >= 45) {
      return 100;
    }

    return (greenPercentage / 45 * 100)
        .clamp(0, 100)
        .toDouble();
  }

  double _resolutionScore({
    required int width,
    required int height,
  }) {
    final int minimumSide = math.min(width, height);

    if (minimumSide >= 1000) {
      return 100;
    }

    if (minimumSide >= 700) {
      return 90;
    }

    if (minimumSide >= 500) {
      return 80;
    }

    if (minimumSide >= 400) {
      return 65;
    }

    return 35;
  }

  String _recommendation({
    required ImageAnalysisData imageData,
    required int score,
  }) {
    if (imageData.photoQuality != 'buona') {
      return 'Ripetere la fotografia';
    }

    if (imageData.greenPixelPercentage < 10) {
      return 'Anguria poco visibile o sfondo dominante';
    }

    if (score >= 80) {
      return 'Foto ottima per l’analisi';
    }

    if (score >= 60) {
      return 'Foto utilizzabile';
    }

    return 'Scattare una foto migliore';
  }

  List<String> _reasons({
    required ImageAnalysisData imageData,
    required double brightnessScore,
    required double contrastScore,
    required double greenScore,
  }) {
    final List<String> reasons = [];

    reasons.add(
      brightnessScore >= 75
          ? 'Illuminazione adeguata'
          : 'Illuminazione da migliorare',
    );

    reasons.add(
      contrastScore >= 75
          ? 'Buon contrasto visivo'
          : 'Contrasto insufficiente',
    );

    reasons.add(
      greenScore >= 70
          ? 'Presenza significativa di tonalità verdi'
          : 'Poche tonalità verdi o anguria non abbastanza inquadrata',
    );

    reasons.add(
      'Risoluzione ${imageData.width} × ${imageData.height} pixel',
    );

    return reasons;
  }
}