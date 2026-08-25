import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/ai_service.dart';
import '../services/score_service.dart';
import '../services/analysis_history_service.dart';
import 'feedback_screen.dart';

class CameraScreen extends StatefulWidget {
  final String betaFriendId;

  const CameraScreen({
    super.key,
    required this.betaFriendId,
  });

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  final AiService _aiService = AiService();
  final ScoreService _scoreService = ScoreService();
  final AnalysisHistoryService _historyService = AnalysisHistoryService();

  Uint8List? _imageBytes;
  Uint8List? _annotatedImageBytes;

  bool _isLoading = false;
  bool _isScoreLoading = false;

  String? _errorMessage;
  String? _saveMessage;
  String? _savedAnalysisId;

  bool _saveSuccess = false;
  bool _feedbackCompleted = false;

  Map<String, dynamic>? _analysis;
  Map<String, dynamic>? _scoreResult;

  String _groundSpot = '';
  String _peduncle = '';
  String _shape = '';
  String _stripes = '';
  String _symmetry = '';
  String _color = '';
  String _surface = '';

  Future<void> _selectImage(ImageSource source) async {
    final XFile? selectedImage = await _picker.pickImage(
      source: source,
      imageQuality: 90,
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
      _annotatedImageBytes = null;

      _analysis = null;
      _scoreResult = null;

      _errorMessage = null;
      _saveMessage = null;
      _savedAnalysisId = null;

      _saveSuccess = false;
      _feedbackCompleted = false;

      _groundSpot = '';
      _peduncle = '';
      _shape = '';
      _stripes = '';
      _symmetry = '';
      _color = '';
      _surface = '';
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
      _scoreResult = null;

      _annotatedImageBytes = null;

      _errorMessage = null;
      _saveMessage = null;
      _savedAnalysisId = null;

      _saveSuccess = false;
      _feedbackCompleted = false;
    });

    try {
      final Map<String, dynamic> result = await _aiService.analyzeImage(
        imageBytes,
      );

      Uint8List? annotatedBytes;

      final Object? annotatedImageValue = result['annotatedImageBase64'];

      if (annotatedImageValue is String && annotatedImageValue.isNotEmpty) {
        annotatedBytes = base64Decode(annotatedImageValue);
      }

      if (!mounted) {
        return;
      }

      final Map<String, dynamic>? features =
          result['features'] as Map<String, dynamic>?;

      final String automaticShape = (features?['shape'] as String?) ?? '';

      final String automaticSymmetry = (features?['symmetry'] as String?) ?? '';

      setState(() {
        _analysis = result;
        _annotatedImageBytes = annotatedBytes;

        if (automaticShape.isNotEmpty) {
          _shape = automaticShape;
        }

        if (automaticSymmetry.isNotEmpty) {
          _symmetry = automaticSymmetry;
        }
      });

      // Photo-first flow:
      // every completed AI analysis produces a preliminary score.
      // Automatic features enrich it when available; manual features
      // can refine the result afterwards.
      await _calculateScore();
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = 'Errore durante l’analisi AI:\n$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _resetAnalysis() {
    setState(() {
      _imageBytes = null;
      _annotatedImageBytes = null;

      _analysis = null;
      _scoreResult = null;

      _errorMessage = null;
      _saveMessage = null;
      _savedAnalysisId = null;

      _saveSuccess = false;
      _feedbackCompleted = false;

      _isLoading = false;
      _isScoreLoading = false;

      _groundSpot = '';
      _peduncle = '';
      _shape = '';
      _stripes = '';
      _symmetry = '';
      _color = '';
      _surface = '';
    });
  }

  Future<void> _calculateScore() async {
    setState(() {
      _isScoreLoading = true;

      _scoreResult = null;

      _errorMessage = null;
      _saveMessage = null;
      _savedAnalysisId = null;

      _saveSuccess = false;
      _feedbackCompleted = false;
    });

    try {
      final Map<String, dynamic> result = await _scoreService.calculateScore(
        groundSpot: _groundSpot,
        peduncle: _peduncle,
        shape: _shape,
        stripes: _stripes,
        symmetry: _symmetry,
        color: _color,
        surface: _surface,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _scoreResult = result;
      });

      final Map<String, dynamic>? detection =
          _analysis?['detection'] as Map<String, dynamic>?;

      final Map<String, dynamic>? bestCandidate =
          _analysis?['bestCandidate'] as Map<String, dynamic>?;

      final Map<String, dynamic>? detectorResult = detection ?? bestCandidate;

      try {
        final Map<String, dynamic> saved = await _historyService.saveAnalysis({
          'score': ((result['score'] as num?) ?? 0).toInt(),
          'advice': (result['advice'] as String?) ?? '',
          'betaFriendId': widget.betaFriendId,
          'groundSpot': _groundSpot,
          'peduncle': _peduncle,
          'shape': _shape,
          'stripes': _stripes,
          'symmetry': _symmetry,
          'color': _color,
          'surface': _surface,
          'reasons': (result['reasons'] as List<dynamic>?) ?? <dynamic>[],
          'warnings': (result['warnings'] as List<dynamic>?) ?? <dynamic>[],
          'detectorFound': (_analysis?['found'] as bool?) ?? false,
          'detectorConfidence':
              ((detectorResult?['confidence'] as num?) ?? 0).toDouble(),
          'detectorLabel': (detectorResult?['label'] as String?) ?? '',
          'shadowV2': (result['shadowV2'] as Map<String, dynamic>?) ??
              <String, dynamic>{},
        });

        if (!mounted) {
          return;
        }

        setState(() {
          _saveSuccess = true;

          _savedAnalysisId = saved['analysisId'] as String?;

          _saveMessage = 'Analisi salvata: '
              '${saved['analysisId']}';
        });
      } catch (error) {
        if (!mounted) {
          return;
        }

        setState(() {
          _saveSuccess = false;
          _savedAnalysisId = null;

          _saveMessage = 'Salvataggio non riuscito: '
              '$error';
        });
      }
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = 'Errore durante il calcolo '
            'AngurIA Score:\n$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isScoreLoading = false;
        });
      }
    }
  }

  Widget _buildFeatureDropdown({
    required String label,
    required String value,
    required Map<String, String> options,
    required ValueChanged<String?> onChanged,
  }) {
    return DropdownButtonFormField<String>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      items: [
        const DropdownMenuItem<String>(
          value: '',
          child: Text(
            'Non valutato',
          ),
        ),
        ...options.entries.map(
          (entry) => DropdownMenuItem<String>(
            value: entry.key,
            child: Text(
              entry.value,
            ),
          ),
        ),
      ],
      onChanged: _isScoreLoading ? null : onChanged,
    );
  }

  Widget _buildScoreSection() {
    final int score = ((_scoreResult?['score'] as num?) ?? 0).toInt();

    final String advice = (_scoreResult?['advice'] as String?) ?? '';

    final List<dynamic> reasons =
        (_scoreResult?['reasons'] as List<dynamic>?) ?? <dynamic>[];

    final List<dynamic> warnings =
        (_scoreResult?['warnings'] as List<dynamic>?) ?? <dynamic>[];

    final Map<String, dynamic> shadowV2 =
        (_scoreResult?['shadowV2'] as Map<String, dynamic>?) ??
            <String, dynamic>{};

    final int completeness = ((shadowV2['completeness'] as num?) ?? 0).round();

    final int observedFeatures =
        ((shadowV2['observedFeatures'] as num?) ?? 0).toInt();

    final List<dynamic> missingFeatures =
        (shadowV2['missingFeatures'] as List<dynamic>?) ?? <dynamic>[];

    final String analysisLevel = completeness >= 70
        ? 'Analisi approfondita'
        : completeness >= 40
            ? 'Analisi intermedia'
            : 'Analisi preliminare';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _InfoCard(
          title: 'Valutazione AngurIA',
          icon: Icons.stars_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Valuta le caratteristiche '
                'visibili dell’anguria. '
                'Se un elemento non è '
                'chiaramente osservabile, '
                'lascialo su "Non valutato".',
                style: TextStyle(
                  color: Colors.black54,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 18),
              _buildFeatureDropdown(
                label: 'Macchia d’appoggio',
                value: _groundSpot,
                options: const {
                  'creamy_yellow': 'Giallo crema',
                  'yellow': 'Gialla',
                  'light_yellow': 'Giallo chiaro',
                  'white': 'Bianca',
                },
                onChanged: (value) {
                  setState(() {
                    _groundSpot = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Peduncolo',
                value: _peduncle,
                options: const {
                  'dry': 'Secco',
                  'partly_dry': 'Parzialmente secco',
                  'green': 'Verde',
                },
                onChanged: (value) {
                  setState(() {
                    _peduncle = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Forma',
                value: _shape,
                options: const {
                  'regular': 'Regolare',
                  'slightly_irregular': 'Leggermente irregolare',
                  'irregular': 'Irregolare',
                },
                onChanged: (value) {
                  setState(() {
                    _shape = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Striature',
                value: _stripes,
                options: const {
                  'well_defined': 'Ben definite',
                  'medium': 'Medie',
                  'weak': 'Poco definite',
                },
                onChanged: (value) {
                  setState(() {
                    _stripes = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Simmetria',
                value: _symmetry,
                options: const {
                  'high': 'Alta',
                  'medium': 'Media',
                  'low': 'Bassa',
                },
                onChanged: (value) {
                  setState(() {
                    _symmetry = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Colore',
                value: _color,
                options: const {
                  'balanced': 'Equilibrato',
                  'acceptable': 'Accettabile',
                  'poor': 'Poco favorevole',
                },
                onChanged: (value) {
                  setState(() {
                    _color = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildFeatureDropdown(
                label: 'Superficie',
                value: _surface,
                options: const {
                  'healthy': 'Sana',
                  'minor_defects': 'Piccoli difetti',
                  'damaged': 'Danneggiata',
                },
                onChanged: (value) {
                  setState(() {
                    _surface = value ?? '';
                    _scoreResult = null;
                    _saveMessage = null;
                    _savedAnalysisId = null;
                    _saveSuccess = false;
                    _feedbackCompleted = false;
                  });
                },
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: _isScoreLoading ? null : _calculateScore,
                icon: const Icon(
                  Icons.calculate_outlined,
                ),
                label: Text(
                  _isScoreLoading
                      ? 'Calcolo in corso...'
                      : 'Calcola AngurIA Score',
                ),
              ),
              if (_isScoreLoading) ...[
                const SizedBox(height: 16),
                const Center(
                  child: CircularProgressIndicator(),
                ),
              ],
            ],
          ),
        ),
        if (_saveMessage != null) ...[
          const SizedBox(height: 16),
          Card(
            elevation: 0,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                _saveSuccess ? '✅ $_saveMessage' : '❌ $_saveMessage',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: _saveSuccess ? const Color(0xFF2E7D32) : Colors.red,
                ),
              ),
            ),
          ),
        ],
        if (_saveSuccess && _savedAnalysisId != null) ...[
          const SizedBox(height: 12),
          if (_feedbackCompleted)
            const Card(
              elevation: 0,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.check_circle,
                      color: Color(0xFF2E7D32),
                    ),
                    SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        'Risultato reale registrato',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF2E7D32),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            ElevatedButton.icon(
              onPressed: () async {
                final String analysisId = _savedAnalysisId!;

                final bool? feedbackSaved =
                    await Navigator.of(context).push<bool>(
                  MaterialPageRoute(
                    builder: (context) => FeedbackScreen(
                      analysisId: analysisId,
                    ),
                  ),
                );

                if (feedbackSaved == true && mounted) {
                  setState(() {
                    _feedbackCompleted = true;
                  });
                }
              },
              icon: const Icon(
                Icons.restaurant_outlined,
              ),
              label: const Text(
                'Com’è davvero?',
              ),
            ),
        ],
        if (_scoreResult != null) ...[
          const SizedBox(height: 16),
          Card(
            elevation: 0,
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'ANGURIA SCORE',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      letterSpacing: 1.3,
                      fontWeight: FontWeight.w600,
                      color: Colors.black54,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '$score',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 58,
                      height: 1,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF2E7D32),
                    ),
                  ),
                  const Text(
                    'su 100',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.black45,
                    ),
                  ),
                  const SizedBox(height: 18),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 18,
                      vertical: 11,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE7F2E5),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: Text(
                      advice,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF2E7D32),
                      ),
                    ),
                  ),
                  const SizedBox(height: 22),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          children: [
                            Text(
                              '$completeness%',
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 3),
                            const Text(
                              'completezza',
                              style: TextStyle(
                                color: Colors.black54,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Column(
                          children: [
                            Text(
                              '$observedFeatures/7',
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 3),
                            const Text(
                              'indicatori',
                              style: TextStyle(
                                color: Colors.black54,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  LinearProgressIndicator(
                    value: completeness.clamp(0, 100) / 100,
                    minHeight: 8,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    analysisLevel,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (missingFeatures.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Puoi migliorare il risultato '
                      'aggiungendo ${missingFeatures.length} '
                      '${missingFeatures.length == 1 ? 'indicatore' : 'indicatori'} '
                      'non ancora valutati.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.black54,
                        height: 1.4,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (reasons.isNotEmpty) ...[
            const SizedBox(height: 16),
            _InfoCard(
              title: 'Punti favorevoli',
              icon: Icons.check_circle_outline,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: reasons
                    .map(
                      (reason) => Padding(
                        padding: const EdgeInsets.symmetric(
                          vertical: 5,
                        ),
                        child: Text(
                          '✅ ${reason.toString()}',
                          style: const TextStyle(
                            height: 1.4,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
          ],
          if (warnings.isNotEmpty) ...[
            const SizedBox(height: 16),
            _InfoCard(
              title: 'Aspetti da verificare',
              icon: Icons.warning_amber_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: warnings
                    .map(
                      (warning) => Padding(
                        padding: const EdgeInsets.symmetric(
                          vertical: 5,
                        ),
                        child: Text(
                          '⚠️ ${warning.toString()}',
                          style: const TextStyle(
                            height: 1.4,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
          ],
          const SizedBox(height: 12),
          const Text(
            'Score euristico sperimentale: '
            'non ancora validato rispetto '
            'a Brix o qualità interna reale.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.black54,
              fontSize: 12,
              height: 1.4,
            ),
          ),
        ],
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool found = (_analysis?['found'] as bool?) ?? false;

    final Map<String, dynamic>? detection =
        _analysis?['detection'] as Map<String, dynamic>?;

    final Map<String, dynamic>? bestCandidate =
        _analysis?['bestCandidate'] as Map<String, dynamic>?;

    final Map<String, dynamic>? displayedDetection = detection ?? bestCandidate;

    final Map<String, dynamic>? boundingBox =
        displayedDetection?['boundingBox'] as Map<String, dynamic>?;

    final double confidence =
        ((displayedDetection?['confidence'] as num?) ?? 0).toDouble();

    final int inferenceTimeMs =
        ((_analysis?['inferenceTimeMs'] as num?) ?? 0).toInt();

    final int rawCandidateCount =
        ((_analysis?['rawCandidateCount'] as num?) ?? 0).toInt();

    final double minimumConfidence =
        ((_analysis?['minimumAcceptedConfidence'] as num?) ?? 0).toDouble();

    return Scaffold(
      backgroundColor: const Color(0xFFF4F8F3),
      appBar: AppBar(
        title: const Text(
          'Analisi AngurIA',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildImagePreview(),
              const SizedBox(height: 20),
              if (_imageBytes == null) ...[
                ElevatedButton.icon(
                  onPressed: _isLoading
                      ? null
                      : () => _selectImage(
                            ImageSource.gallery,
                          ),
                  icon: const Icon(
                    Icons.photo_library_outlined,
                  ),
                  label: const Text(
                    'Scegli dalla galleria',
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: _isLoading
                      ? null
                      : () => _selectImage(
                            ImageSource.camera,
                          ),
                  icon: const Icon(
                    Icons.camera_alt_outlined,
                  ),
                  label: const Text(
                    'Scatta una foto',
                  ),
                ),
              ],
              if (_imageBytes != null && _analysis == null && !_isLoading) ...[
                ElevatedButton.icon(
                  onPressed: _analyzeImage,
                  icon: const Icon(
                    Icons.auto_awesome,
                  ),
                  label: const Text(
                    'Analizza con AngurIA',
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: _resetAnalysis,
                  child: const Text(
                    'Scegli un’altra foto',
                  ),
                ),
              ],
              if (_isLoading) ...[
                const SizedBox(height: 24),
                const _LoadingCard(),
              ],
              if (_errorMessage != null) ...[
                const SizedBox(height: 20),
                _InfoCard(
                  title: 'Errore',
                  icon: Icons.error_outline,
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: Colors.red,
                    ),
                  ),
                ),
              ],
              if (_analysis != null) ...[
                const SizedBox(height: 24),
                _DetectionResultCard(
                  found: found,
                  confidence: confidence,
                ),
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Analisi AI',
                  icon: Icons.psychology_outlined,
                  child: Column(
                    children: [
                      _ResultRow(
                        label: 'Oggetto',
                        value: '${displayedDetection?['label'] ?? 'Nessuno'}',
                      ),
                      _ResultRow(
                        label: 'Confidenza',
                        value: '${(confidence * 100).toStringAsFixed(1)}%',
                      ),
                      _ResultRow(
                        label: 'Soglia minima',
                        value:
                            '${(minimumConfidence * 100).toStringAsFixed(0)}%',
                      ),
                      _ResultRow(
                        label: 'Tempo AI',
                        value: '$inferenceTimeMs ms',
                      ),
                      _ResultRow(
                        label: 'Candidati rilevati',
                        value: '$rawCandidateCount',
                      ),
                    ],
                  ),
                ),
                if (boundingBox != null) ...[
                  const SizedBox(height: 16),
                  _InfoCard(
                    title: 'Bounding Box',
                    icon: Icons.crop_free,
                    child: Column(
                      children: [
                        _ResultRow(
                          label: 'X',
                          value: '${boundingBox['x']}',
                        ),
                        _ResultRow(
                          label: 'Y',
                          value: '${boundingBox['y']}',
                        ),
                        _ResultRow(
                          label: 'Larghezza',
                          value: '${boundingBox['width']} px',
                        ),
                        _ResultRow(
                          label: 'Altezza',
                          value: '${boundingBox['height']} px',
                        ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                _buildScoreSection(),
                const SizedBox(height: 16),
                const _InfoCard(
                  title: 'Stato del modello',
                  icon: Icons.science_outlined,
                  child: Text(
                    'Il detector è ancora '
                    'sperimentale. '
                    'La bounding box '
                    'visualizzata è il miglior '
                    'candidato trovato dal '
                    'modello corrente.',
                    style: TextStyle(
                      height: 1.45,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: _resetAnalysis,
                  icon: const Icon(
                    Icons.refresh,
                  ),
                  label: const Text(
                    'Analizza un’altra anguria',
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
    final Uint8List? imageToDisplay = _annotatedImageBytes ?? _imageBytes;

    return Container(
      height: 340,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(
          color: const Color(0xFFB7D8B9),
        ),
        boxShadow: const [
          BoxShadow(
            blurRadius: 18,
            offset: Offset(0, 6),
            color: Color(0x14000000),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: imageToDisplay == null
          ? const Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.camera_alt_outlined,
                  size: 76,
                  color: Color(0xFF2E7D32),
                ),
                SizedBox(height: 18),
                Text(
                  'Fotografa la tua anguria',
                  style: TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 8),
                Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: 36,
                  ),
                  child: Text(
                    'Inquadra il frutto intero, '
                    'con buona luce e poco '
                    'sfondo.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.black54,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            )
          : Stack(
              fit: StackFit.expand,
              children: [
                Image.memory(
                  imageToDisplay,
                  fit: BoxFit.contain,
                ),
                if (_annotatedImageBytes != null)
                  Positioned(
                    top: 12,
                    right: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'AI overlay',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
}

class _DetectionResultCard extends StatelessWidget {
  final bool found;
  final double confidence;

  const _DetectionResultCard({
    required this.found,
    required this.confidence,
  });

  @override
  Widget build(BuildContext context) {
    final String title =
        found ? 'Anguria rilevata' : 'Rilevamento non affidabile';

    final String subtitle = found
        ? 'AngurIA ha individuato il frutto.'
        : 'Il modello vede un possibile '
            'candidato, ma la confidenza '
            'è ancora troppo bassa.';

    final IconData icon =
        found ? Icons.check_circle : Icons.warning_amber_rounded;

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          children: [
            Icon(
              icon,
              size: 60,
              color: found ? const Color(0xFF2E7D32) : Colors.orange,
            ),
            const SizedBox(height: 14),
            Text(
              title,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.black54,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 18),
            Text(
              '${(confidence * 100).toStringAsFixed(1)}%',
              style: const TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
                color: Color(0xFF2E7D32),
              ),
            ),
            const Text(
              'confidenza AI',
              style: TextStyle(
                color: Colors.black54,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadingCard extends StatelessWidget {
  const _LoadingCard();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(28),
        child: Column(
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 18),
            Text(
              'AngurIA sta analizzando '
              'la foto...',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 6),
            Text(
              'Il modello AI sta cercando '
              'l’anguria.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.black54,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;

  const _InfoCard({
    required this.title,
    required this.icon,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(
                  icon,
                  color: const Color(0xFF2E7D32),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ),
              ],
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
      padding: const EdgeInsets.symmetric(
        vertical: 7,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: Colors.black54,
              ),
            ),
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
