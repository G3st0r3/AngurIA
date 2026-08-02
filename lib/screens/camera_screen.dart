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
  String? _errorMessage;
  Map<String, dynamic>? _analysis;

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
      _analysis = null;
      _errorMessage = null;
    });
  }

  Future<void> _analyzeImage() async {
    final Uint8List? imageBytes = _imageBytes;

    if (imageBytes == null) {
      setState(() {
        _errorMessage = 'Seleziona prima una fotografia.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _analysis = null;
      _errorMessage = null;
    });

    try {
      final Map<String, dynamic> result =
          await _aiService.analyzeImage(imageBytes);

      if (!mounted) {
        return;
      }

      setState(() {
        _analysis = result;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = 'Errore durante l’analisi:\n$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final Map<String, dynamic>? imageAnalysis =
        _analysis?['imageAnalysis'] as Map<String, dynamic>?;

    final List<dynamic> reasons =
        (_analysis?['reasons'] as List<dynamic>?) ?? <dynamic>[];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analisi AngurIA'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildImagePreview(),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _isLoading
                    ? null
                    : () => _selectImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Scegli dalla galleria'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _isLoading
                    ? null
                    : () => _selectImage(ImageSource.camera),
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Scatta una foto'),
              ),
              if (_imageBytes != null) ...[
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _analyzeImage,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Analizza la foto'),
                ),
              ],
              if (_isLoading) ...[
                const SizedBox(height: 24),
                const Center(
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 12),
                      Text('Analisi in corso...'),
                    ],
                  ),
                ),
              ],
              if (_errorMessage != null) ...[
                const SizedBox(height: 20),
                _InfoCard(
                  title: 'Errore',
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ],
              if (_analysis != null) ...[
                const SizedBox(height: 24),
                _InfoCard(
                  title: 'Idoneità della fotografia',
                  child: Column(
                    children: [
                      _ResultRow(
                        label: 'Punteggio foto',
                        value: '${_analysis!['score']}/100',
                      ),
                      _ResultRow(
                        label: 'Affidabilità tecnica',
                        value: '${_analysis!['confidence']}%',
                      ),
                      _ResultRow(
                        label: 'Esito',
                        value: '${_analysis!['recommendation']}',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Valutazioni interne',
                  child: const Column(
                    children: [
                      _ResultRow(
                        label: 'Dolcezza',
                        value: 'Non disponibile',
                      ),
                      _ResultRow(
                        label: 'Croccantezza',
                        value: 'Non disponibile',
                      ),
                      _ResultRow(
                        label: 'Probabilità farinosa',
                        value: 'Non disponibile',
                      ),
                    ],
                  ),
                ),
              ],
              if (imageAnalysis != null) ...[
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Analisi reale della fotografia',
                  child: Column(
                    children: [
                      _ResultRow(
                        label: 'Dimensioni',
                        value:
                            '${imageAnalysis['width']} × ${imageAnalysis['height']} px',
                      ),
                      _ResultRow(
                        label: 'Luminosità',
                        value: '${imageAnalysis['averageBrightness']}',
                      ),
                      _ResultRow(
                        label: 'Contrasto',
                        value: '${imageAnalysis['brightnessContrast']}',
                      ),
                      _ResultRow(
                        label: 'Pixel verdi',
                        value: '${imageAnalysis['greenPixelPercentage']}%',
                      ),
                      _ResultRow(
                        label: 'Colore dominante',
                        value: '${imageAnalysis['dominantColor']}',
                      ),
                      _ResultRow(
                        label: 'Qualità foto',
                        value: '${imageAnalysis['photoQuality']}',
                      ),
                    ],
                  ),
                ),
              ],
              if (reasons.isNotEmpty) ...[
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Perché questo risultato',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: reasons
                        .map(
                          (dynamic reason) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 5),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(
                                  Icons.check_circle_outline,
                                  size: 20,
                                  color: Color(0xFF2E7D32),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(reason.toString()),
                                ),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildImagePreview() {
    return Container(
      height: 330,
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
                  'Seleziona una foto\ndella tua anguria',
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
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _InfoCard({
    required this.title,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF2E7D32),
                  ),
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _ResultRow extends StatelessWidget {
  final String label;
  final String value;

  const _ResultRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(label),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
}