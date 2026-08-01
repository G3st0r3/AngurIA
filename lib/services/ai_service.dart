import 'dart:convert';

import 'package:http/http.dart' as http;

class AiService {
  static const String baseUrl = 'http://localhost:8080';

  Future<Map<String, dynamic>> analyzeImage() async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'image': 'test',
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('Errore del backend');
    }

    return jsonDecode(response.body);
  }
}