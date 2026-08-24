import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class AiDetectionService {
  final String baseUrl;

  const AiDetectionService({
    this.baseUrl = 'http://127.0.0.1:8000',
  });

  Future<Map<String, dynamic>> detectWatermelon({
    required Uint8List imageBytes,
    String filename = 'watermelon.jpg',
  }) async {
    final Uri uri = Uri.parse('$baseUrl/detect');

    final http.MultipartRequest request =
        http.MultipartRequest('POST', uri);

    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        imageBytes,
        filename: filename,
        contentType: MediaType('image', 'jpeg'),
      ),
    );

    final http.StreamedResponse streamedResponse =
        await request.send().timeout(
      const Duration(seconds: 30),
    );

    final http.Response response =
        await http.Response.fromStream(streamedResponse);

    if (response.statusCode != 200) {
      throw Exception(
        'Errore AI ${response.statusCode}: ${response.body}',
      );
    }

    final Object? decodedBody = jsonDecode(response.body);

    if (decodedBody is! Map<String, dynamic>) {
      throw const FormatException(
        'Risposta del servizio AI non valida',
      );
    }

    return decodedBody;
  }
}