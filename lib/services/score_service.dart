import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class ScoreService {
  static const String baseUrl = ApiConfig.baseUrl;

  Future<Map<String, dynamic>> calculateScore({
    String groundSpot = '',
    String peduncle = '',
    String shape = '',
    String stripes = '',
    String symmetry = '',
    String color = '',
    String surface = '',
  }) async {
    final Uri uri = Uri.parse('$baseUrl/score');

    final http.Response response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'groundSpot': groundSpot,
        'peduncle': peduncle,
        'shape': shape,
        'stripes': stripes,
        'symmetry': symmetry,
        'color': color,
        'surface': surface,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Errore Score API ${response.statusCode}: ${response.body}',
      );
    }

    final Object? decoded = jsonDecode(response.body);

    if (decoded is! Map<String, dynamic>) {
      throw const FormatException(
        'Risposta AngurIA Score non valida',
      );
    }

    return decoded;
  }
}
