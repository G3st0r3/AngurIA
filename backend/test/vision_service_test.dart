import 'package:backend/services/vision_service.dart';

Future<void> main() async {
  const VisionService visionService = VisionService();

  final result = await visionService.detectWatermelon(
    imageWidth: 1000,
    imageHeight: 800,
  );

  print('Anguria trovata: ${result.found}');
  print(
    'Confidenza: ${(result.confidence * 100).toStringAsFixed(0)}%',
  );

  if (result.boundingBox != null) {
    print(
      'Bounding box: '
      '${result.boundingBox!.x}, '
      '${result.boundingBox!.y}, '
      '${result.boundingBox!.width}, '
      '${result.boundingBox!.height}',
    );
  }
}