import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:backend/models/analysis_result.dart';
import 'package:backend/services/image_analysis_service.dart';
import 'package:backend/services/watermelon_analyzer_service.dart';
import 'package:image/image.dart' as img;
import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart';
import 'package:shelf_router/shelf_router.dart';

const WatermelonAnalyzerService _analyzerService =
    WatermelonAnalyzerService();

const ImageAnalysisService _imageAnalysisService =
    ImageAnalysisService();

const Map<String, String> _corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept',
};

final Router _router = Router()
  ..get('/', _rootHandler)
  ..post('/analyze', _analyzeHandler);

Response _jsonResponse(
  int statusCode,
  Map<String, dynamic> body,
) {
  return Response(
    statusCode,
    body: jsonEncode(body),
    headers: {
      HttpHeaders.contentTypeHeader: ContentType.json.mimeType,
    },
  );
}

Response _rootHandler(Request request) {
  return _jsonResponse(
    HttpStatus.ok,
    {
      'app': 'AngurIA Backend',
      'status': 'online',
      'version': '0.2.0',
    },
  );
}

Future<Response> _analyzeHandler(Request request) async {
  final String requestBody = await request.readAsString();

  if (requestBody.isEmpty) {
    return _jsonResponse(
      HttpStatus.badRequest,
      {
        'error': 'Corpo della richiesta vuoto',
      },
    );
  }

  try {
    final Object? decodedBody = jsonDecode(requestBody);

    if (decodedBody is! Map<String, dynamic>) {
      return _jsonResponse(
        HttpStatus.badRequest,
        {
          'error': 'Formato della richiesta non valido',
        },
      );
    }

    final Object? imageValue = decodedBody['image'];

    if (imageValue is! String || imageValue.isEmpty) {
      return _jsonResponse(
        HttpStatus.badRequest,
        {
          'error': 'Immagine mancante nella richiesta',
        },
      );
    }

    final String imageBase64 = imageValue;

    final Uint8List imageBytes = base64Decode(imageBase64);

    final img.Image? decodedImage = img.decodeImage(imageBytes);

    if (decodedImage == null) {
      return _jsonResponse(
        HttpStatus.badRequest,
        {
          'error': 'Il file ricevuto non è un’immagine valida',
        },
      );
    }

    final ImageAnalysisData imageAnalysis =
        _imageAnalysisService.analyze(decodedImage);

    print(
      'Immagine valida: '
      '${imageAnalysis.width}x${imageAnalysis.height} pixel',
    );

    print(
      'Luminosità media: '
      '${imageAnalysis.averageBrightness.toStringAsFixed(2)}',
    );

    print(
      'RGB medio: '
      'R ${imageAnalysis.averageRed.toStringAsFixed(2)}, '
      'G ${imageAnalysis.averageGreen.toStringAsFixed(2)}, '
      'B ${imageAnalysis.averageBlue.toStringAsFixed(2)}',
    );

    print(
      'Colore dominante: ${imageAnalysis.dominantColor}',
    );
print(
  'Contrasto luminosità: '
  '${imageAnalysis.brightnessContrast.toStringAsFixed(2)}',
);

print(
  'Pixel verdi: '
  '${imageAnalysis.greenPixelPercentage.toStringAsFixed(2)}%',
);

print(
  'Qualità foto: ${imageAnalysis.photoQuality}',
);
    final AnalysisResult simulatedResult =
    _analyzerService.analyze(imageAnalysis);

    return _jsonResponse(
      HttpStatus.ok,
      {
        ...simulatedResult.toJson(),
        'imageAnalysis': imageAnalysis.toJson(),
      },
    );
  } on FormatException {
    return _jsonResponse(
      HttpStatus.badRequest,
      {
        'error': 'JSON o immagine Base64 non validi',
      },
    );
  } catch (error, stackTrace) {
    print('Errore durante l’analisi: $error');
    print(stackTrace);

    return _jsonResponse(
      HttpStatus.internalServerError,
      {
        'error': 'Errore interno durante l’analisi',
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
    'AngurIA backend v0.2.0 listening on port ${server.port}',
  );
}