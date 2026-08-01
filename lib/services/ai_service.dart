import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

class AiService {
  static const String baseUrl = 'http://localhost:8080';

  Future<Map<String, dynamic>> analyzeImage(
    Uint8List imageBytes,
  ) async {
    final String imageBase64 = base64Encode(imageBytes);

    final http.Response response = await http.post(
      Uri.parse('$baseUrl/analyze'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'image': imageBase64,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Errore del backend: ${response.statusCode} ${response.body}',
      );
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}