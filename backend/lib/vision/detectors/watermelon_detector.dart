class BoundingBox {
  final int x;
  final int y;
  final int width;
  final int height;

  const BoundingBox({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
  });

  Map<String, dynamic> toJson() {
    return {
      'x': x,
      'y': y,
      'width': width,
      'height': height,
    };
  }
}

class DetectionResult {
  final bool found;
  final double confidence;
  final BoundingBox? boundingBox;

  const DetectionResult({
    required this.found,
    required this.confidence,
    required this.boundingBox,
  });

  Map<String, dynamic> toJson() {
    return {
      'found': found,
      'confidence': confidence,
      'boundingBox': boundingBox?.toJson(),
    };
  }
}

class WatermelonDetector {
  const WatermelonDetector();

  Future<DetectionResult> detect({
    required int imageWidth,
    required int imageHeight,
  }) async {
    final int boxWidth = (imageWidth * 0.70).round();
    final int boxHeight = (imageHeight * 0.70).round();

    final int x = ((imageWidth - boxWidth) / 2).round();
    final int y = ((imageHeight - boxHeight) / 2).round();

    return DetectionResult(
      found: true,
      confidence: 0.98,
      boundingBox: BoundingBox(
        x: x,
        y: y,
        width: boxWidth,
        height: boxHeight,
      ),
    );
  }
}