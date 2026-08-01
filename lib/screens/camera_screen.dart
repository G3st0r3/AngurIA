import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/ai_service.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  final AiService _aiService = AiService();

  Uint8List? _imageBytes;

  bool _isLoading = false;
  String? _analysisResult;

  Future<void> _selectImage(ImageSource source) async {
    final XFile? selectedImage = await _picker.pickImage(
      source: source,
      imageQuality: 85,
      maxWidth: 1600,
    );

    if (selectedImage == null) {
      return;
    }

    final Uint8List bytes = await selectedImage.readAsBytes();

    if (!mounted) {
      return;
    }

    setState(() {
      _imageBytes = bytes;
      _analysisResult = null;
    });
  }

  Future<void> _analyzeImage() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final Uint8List? imageBytes = _imageBytes;

if (imageBytes == null) {
  setState(() {
    _analysisResult = 'Seleziona prima una foto.';
    _isLoading = false;
  });
  return;
}

final Map<String, dynamic> result =
    await _aiService.analyzeImage(imageBytes);

      if (!mounted) return;

      setState(() {
        _analysisResult =
            "🍉 Indice AngurIA: ${result['score']}/100\n\n"
            "🍯 Dolcezza: ${result['sweetness']}%\n"
            "🥬 Croccantezza: ${result['crunchiness']}%\n"
            "⚪ Probabilità farinosa: ${result['mealiness']}%\n"
            "🎯 Affidabilità: ${result['confidence']}%\n\n"
            "✅ ${result['recommendation']}";
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _analysisResult = "Errore durante l'analisi:\n$e";
      });
    } finally {
      if (!mounted) return;

      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Analisi AngurIA"),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: const Color(0xFFB7D8B9),
                    ),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: _imageBytes == null
                      ? const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.add_a_photo_outlined,
                              size: 80,
                              color: Color(0xFF2E7D32),
                            ),
                            SizedBox(height: 16),
                            Text(
                              "Seleziona una foto\ndella tua anguria",
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 20,
                                height: 1.4,
                              ),
                            ),
                          ],
                        )
                      : Image.memory(
                          _imageBytes!,
                          fit: BoxFit.cover,
                          width: double.infinity,
                          height: double.infinity,
                        ),
                ),
              ),

              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: () => _selectImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text("Scegli dalla galleria"),
              ),

              const SizedBox(height: 12),

              OutlinedButton.icon(
                onPressed: () => _selectImage(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text("Scatta una foto"),
              ),

              if (_imageBytes != null) ...[
                const SizedBox(height: 16),

                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _analyzeImage,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text("Analizza la foto"),
                ),
              ],

              if (_isLoading) ...[
                const SizedBox(height: 20),
                const Center(
                  child: CircularProgressIndicator(),
                ),
              ],

              if (_analysisResult != null) ...[
                const SizedBox(height: 20),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      _analysisResult!,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}