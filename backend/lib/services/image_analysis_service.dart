import 'dart:math' as math;

import 'package:image/image.dart' as img;

class ImageAnalysisData {
  final double averageBrightness;
  final double averageRed;
  final double averageGreen;
  final double averageBlue;
  final double brightnessContrast;
  final double greenPixelPercentage;
  final String dominantColor;
  final String photoQuality;
  final int width;
  final int height;
  final int sampledPixels;

  const ImageAnalysisData({
    required this.averageBrightness,
    required this.averageRed,
    required this.averageGreen,
    required this.averageBlue,
    required this.brightnessContrast,
    required this.greenPixelPercentage,
    required this.dominantColor,
    required this.photoQuality,
    required this.width,
    required this.height,
    required this.sampledPixels,
  });

  Map<String, dynamic> toJson() {
    return {
      'averageBrightness':
          double.parse(averageBrightness.toStringAsFixed(2)),
      'averageRed': double.parse(averageRed.toStringAsFixed(2)),
      'averageGreen': double.parse(averageGreen.toStringAsFixed(2)),
      'averageBlue': double.parse(averageBlue.toStringAsFixed(2)),
      'brightnessContrast':
          double.parse(brightnessContrast.toStringAsFixed(2)),
      'greenPixelPercentage':
          double.parse(greenPixelPercentage.toStringAsFixed(2)),
      'dominantColor': dominantColor,
      'photoQuality': photoQuality,
      'width': width,
      'height': height,
      'sampledPixels': sampledPixels,
    };
  }
}

class ImageAnalysisService {
  const ImageAnalysisService();

  ImageAnalysisData analyze(img.Image image) {
    double totalRed = 0;
    double totalGreen = 0;
    double totalBlue = 0;
    double totalBrightness = 0;
    double totalSquaredBrightness = 0;

    int sampledPixels = 0;
    int greenPixels = 0;

    const int samplingStep = 4;

    for (int y = 0; y < image.height; y += samplingStep) {
      for (int x = 0; x < image.width; x += samplingStep) {
        final img.Pixel pixel = image.getPixel(x, y);

        final double red = pixel.r.toDouble();
        final double green = pixel.g.toDouble();
        final double blue = pixel.b.toDouble();

        final double brightness =
            (0.299 * red) + (0.587 * green) + (0.114 * blue);

        totalRed += red;
        totalGreen += green;
        totalBlue += blue;
        totalBrightness += brightness;
        totalSquaredBrightness += brightness * brightness;

        if (_isGreenPixel(
          red: red,
          green: green,
          blue: blue,
        )) {
          greenPixels++;
        }

        sampledPixels++;
      }
    }

    if (sampledPixels == 0) {
      throw StateError('Immagine senza pixel analizzabili');
    }

    final double averageRed = totalRed / sampledPixels;
    final double averageGreen = totalGreen / sampledPixels;
    final double averageBlue = totalBlue / sampledPixels;
    final double averageBrightness =
        totalBrightness / sampledPixels;

    final double brightnessVariance =
        (totalSquaredBrightness / sampledPixels) -
            (averageBrightness * averageBrightness);

    final double brightnessContrast =
        math.sqrt(math.max(0, brightnessVariance));

    final double greenPixelPercentage =
        (greenPixels / sampledPixels) * 100;

    final String dominantColor = _calculateDominantColor(
      red: averageRed,
      green: averageGreen,
      blue: averageBlue,
    );

    final String photoQuality = _calculatePhotoQuality(
      brightness: averageBrightness,
      contrast: brightnessContrast,
      width: image.width,
      height: image.height,
    );

    return ImageAnalysisData(
      averageBrightness: averageBrightness,
      averageRed: averageRed,
      averageGreen: averageGreen,
      averageBlue: averageBlue,
      brightnessContrast: brightnessContrast,
      greenPixelPercentage: greenPixelPercentage,
      dominantColor: dominantColor,
      photoQuality: photoQuality,
      width: image.width,
      height: image.height,
      sampledPixels: sampledPixels,
    );
  }

  bool _isGreenPixel({
    required double red,
    required double green,
    required double blue,
  }) {
    return green > red * 1.08 &&
        green > blue * 1.08 &&
        green > 45;
  }

  String _calculateDominantColor({
    required double red,
    required double green,
    required double blue,
  }) {
    final double maximumValue =
        math.max(red, math.max(green, blue));
    final double minimumValue =
        math.min(red, math.min(green, blue));

    if (maximumValue - minimumValue < 10) {
      if (maximumValue < 70) {
        return 'scuro';
      }

      if (maximumValue > 190) {
        return 'chiaro';
      }

      return 'neutro';
    }

    if (green == maximumValue) {
      return 'verde';
    }

    if (red == maximumValue) {
      return 'rosso';
    }

    return 'blu';
  }

  String _calculatePhotoQuality({
    required double brightness,
    required double contrast,
    required int width,
    required int height,
  }) {
    if (width < 400 || height < 400) {
      return 'risoluzione insufficiente';
    }

    if (brightness < 45) {
      return 'foto troppo scura';
    }

    if (brightness > 225) {
      return 'foto troppo luminosa';
    }

    if (contrast < 18) {
      return 'contrasto insufficiente';
    }

    return 'buona';
  }
}