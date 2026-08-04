import 'package:backend/vision/detectors/watermelon_detector.dart';

class VisionService {
  final WatermelonDetector _detector;

  const VisionService({
    WatermelonDetector detector = const WatermelonDetector(),
  }) : _detector = detector;

  Future<DetectionResult> detectWatermelon({
    required int imageWidth,
    required int imageHeight,
  }) {
    return _detector.detect(
      imageWidth: imageWidth,
      imageHeight: imageHeight,
    );
  }
}