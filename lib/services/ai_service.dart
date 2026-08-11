import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../config/api_config.dart';

class AiService {
  static const String baseUrl = ApiConfig.baseUrl;

  Future<Map<String, dynamic>> analyzeImage(
    Uint8List imageBytes,
  ) async {
    final Uri uri = Uri.parse('$baseUrl/detect');

    final request = http.MultipartRequest(
      'POST',
      uri,
    );

    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        imageBytes,
        filename: 'anguria.jpg',
        contentType: MediaType(
          'image',
          'jpeg',
        ),
      ),
    );

    final streamedResponse = await request.send();

    final response =
        await http.Response.fromStream(
      streamedResponse,
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Errore AI: ${response.body}',
      );
    }

    return jsonDecode(response.body)
        as Map<String, dynamic>;
  }
}