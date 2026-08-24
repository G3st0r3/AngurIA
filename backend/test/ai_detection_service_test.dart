import 'dart:io';
import 'dart:typed_data';

import 'package:backend/services/ai_detection_service.dart';

Future<void> main() async {
  const String imagePath =
      '/Users/giannimelfi/Desktop/anguria_test.jpg';

  final File imageFile = File(imagePath);

  if (!await imageFile.exists()) {
    print('Foto non trovata: $imagePath');
    exitCode = 1;
    return;
  }

  final Uint8List imageBytes =
      await imageFile.readAsBytes();

  const AiDetectionService service =
      AiDetectionService();

  print('Invio della fotografia al servizio AI...');

  final Map<String, dynamic> result =
      await service.detectWatermelon(
    imageBytes: imageBytes,
    filename: 'anguria_test.jpg',
  );

  print('Risposta ricevuta:');
  print(result);
}