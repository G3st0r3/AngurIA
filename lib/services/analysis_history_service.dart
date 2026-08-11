import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class AnalysisHistoryService {
  static const String baseUrl = ApiConfig.baseUrl;

  Future<Map<String, dynamic>> saveAnalysis(
    Map<String, dynamic> data,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analysis/save'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode(data),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Errore salvataggio analisi: ${response.body}',
      );
    }

    return jsonDecode(response.body)
        as Map<String, dynamic>;
  }
}
