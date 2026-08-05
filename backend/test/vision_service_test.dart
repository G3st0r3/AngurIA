import 'package:backend/services/vision_service.dart';
import 'package:test/test.dart';

void main() {
  group('VisionService', () {
    test(
      'rileva un’anguria e restituisce una bounding box valida',
      () async {
        const VisionService visionService = VisionService();

        final result = await visionService.detectWatermelon(
          imageWidth: 1000,
          imageHeight: 800,
        );

        expect(result.found, isTrue);
        expect(result.label, equals('watermelon'));
        expect(
          result.confidence,
          closeTo(0.98, 0.001),
        );

        expect(result.boundingBox, isNotNull);

        final box = result.boundingBox!;

        expect(box.x, equals(150));
        expect(box.y, equals(120));
        expect(box.width, equals(700));
        expect(box.height, equals(560));
      },
    );

    test(
      'la bounding box resta dentro i limiti dell’immagine',
      () async {
        const VisionService visionService = VisionService();

        const int imageWidth = 640;
        const int imageHeight = 480;

        final result = await visionService.detectWatermelon(
          imageWidth: imageWidth,
          imageHeight: imageHeight,
        );

        final box = result.boundingBox!;

        expect(box.x, greaterThanOrEqualTo(0));
        expect(box.y, greaterThanOrEqualTo(0));

        expect(
          box.x + box.width,
          lessThanOrEqualTo(imageWidth),
        );

        expect(
          box.y + box.height,
          lessThanOrEqualTo(imageHeight),
        );
      },
    );
  });
}