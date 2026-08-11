import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class AnalysisFeedbackService {
  static const String baseUrl =
      ApiConfig.baseUrl;

  Future<Map<String, dynamic>> saveFeedback({
    required String analysisId,
    int? sweetness,
    int? crunchiness,
    int? juiciness,
    int? mealiness,
    double? brix,
    String notes = '',
  }) async {
    final Uri uri = Uri.parse(
      '$baseUrl/analysis/$analysisId/feedback',
    );

    final http.Response response =
        await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'sweetness': sweetness,
        'crunchiness': crunchiness,
        'juiciness': juiciness,
        'mealiness': mealiness,
        'brix': brix,
        'notes': notes,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Errore salvataggio feedback '
        '(${response.statusCode}): '
        '${response.body}',
      );
    }

    final Object? decoded =
        jsonDecode(response.body);

    if (decoded is! Map<String, dynamic>) {
      throw const FormatException(
        'Risposta feedback AngurIA non valida',
      );
    }

    return decoded;
  }
}