import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:backend/models/analysis_result.dart';
import 'package:backend/services/watermelon_analyzer_service.dart';
import 'package:image/image.dart' as img;
import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart';
import 'package:shelf_router/shelf_router.dart';

const WatermelonAnalyzerService _analyzerService =
    WatermelonAnalyzerService();

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

  try {
    final Map<String, dynamic> body =
        jsonDecode(requestBody) as Map<String, dynamic>;

    final Object? imageValue = body['image'];

    if (imageValue is! String || imageValue.isEmpty) {
      return Response(
        HttpStatus.badRequest,
        body: jsonEncode({
          'error': 'Immagine mancante nella richiesta',
        }),
        headers: {
          HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
        },
      );
    }

    final String imageBase64 = imageValue;

    print(
      'Dimensione Base64: ${imageBase64.length} caratteri',
    );

    final Uint8List imageBytes = base64Decode(imageBase64);

    print(
      'Dimensione immagine: ${imageBytes.length} byte',
    );

    final img.Image? decodedImage = img.decodeImage(imageBytes);

    if (decodedImage == null) {
      return Response(
        HttpStatus.badRequest,
        body: jsonEncode({
          'error': 'Il file ricevuto non è un’immagine valida',
        }),
        headers: {
          HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
        },
      );
    }

    print(
      'Immagine valida: '
      '${decodedImage.width}x${decodedImage.height} pixel',
    );

    final AnalysisResult simulatedResult =
        _analyzerService.analyzeSimulated();

    return Response.ok(
      jsonEncode(simulatedResult.toJson()),
      headers: {
        HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
      },
    );
  } on FormatException {
    return Response(
      HttpStatus.badRequest,
      body: jsonEncode({
        'error': 'JSON o immagine Base64 non validi',
      }),
      headers: {
        HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
      },
    );
  } catch (error) {
    print('Errore durante l’analisi: $error');

    return Response(
      HttpStatus.internalServerError,
      body: jsonEncode({
        'error': 'Errore interno durante l’analisi',
      }),
      headers: {
        HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
      },
    );
  }
}

Middleware _corsMiddleware() {
  return (Handler innerHandler) {
    return (Request request) async {
      if (request.method == 'OPTIONS') {
        return Response.ok(
          '',
          headers: _corsHeaders,
        );
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

  final HttpServer server = await serve(
    handler,
    ip,
    port,
  );

  print(
    'AngurIA backend listening on port ${server.port}',
  );
}