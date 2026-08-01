import 'dart:convert';
import 'dart:io';

import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart';
import 'package:shelf_router/shelf_router.dart';
import 'package:backend/models/analysis_result.dart';
const Map<String, String> _corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept',
};

final Router _router = Router()
  ..get('/', _rootHandler)
  ..post('/analyze', _analyzeHandler);

Response _rootHandler(Request request) {
  return Response.ok(
    jsonEncode({
      'app': 'AngurIA Backend',
      'status': 'online',
    }),
    headers: {
      HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
    },
  );
}

Future<Response> _analyzeHandler(Request request) async {
  final String requestBody = await request.readAsString();

  if (requestBody.isEmpty) {
    return Response(
      HttpStatus.badRequest,
      body: jsonEncode({
        'error': 'Corpo della richiesta vuoto',
      }),
      headers: {
        HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
      },
    );
  }

  final simulatedResult = AnalysisResult(
  score: 91,
  sweetness: 95,
  crunchiness: 88,
  mealiness: 4,
  confidence: 93,
  recommendation: 'Consigliata',
  reasons: [
    'Forma regolare',
    'Buon contrasto delle striature',
    'Aspetto generale compatibile con una buona maturazione',
  ],
);

  return Response.ok(
jsonEncode(simulatedResult.toJson()),
    headers: {
      HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
    },
  );
}

Middleware _corsMiddleware() {
  return (Handler innerHandler) {
    return (Request request) async {
      if (request.method == 'OPTIONS') {
        return Response.ok('', headers: _corsHeaders);
      }

      final Response response = await innerHandler(request);

      return response.change(
        headers: {
          ...response.headers,
          ..._corsHeaders,
        },
      );
    };
  };
}

Future<void> main(List<String> args) async {
  final InternetAddress ip = InternetAddress.anyIPv4;

  final Handler handler = Pipeline()
      .addMiddleware(logRequests())
      .addMiddleware(_corsMiddleware())
      .addHandler(_router.call);

  final int port = int.parse(
    Platform.environment['PORT'] ?? '8080',
  );

  final HttpServer server = await serve(handler, ip, port);

  print('AngurIA backend listening on port ${server.port}');
}