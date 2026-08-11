import 'package:flutter/material.dart';

import '../services/analysis_feedback_service.dart';

class FeedbackScreen extends StatefulWidget {
  final String analysisId;

  const FeedbackScreen({
    super.key,
    required this.analysisId,
  });

  @override
  State<FeedbackScreen> createState() =>
      _FeedbackScreenState();
}

class _FeedbackScreenState
    extends State<FeedbackScreen> {
  final AnalysisFeedbackService _feedbackService =
      AnalysisFeedbackService();

  final TextEditingController _brixController =
      TextEditingController();

  final TextEditingController _notesController =
      TextEditingController();

  int? _sweetness;
  int? _crunchiness;
  int? _juiciness;
  int? _mealiness;

  bool _isSaving = false;
  bool _saved = false;

  String? _errorMessage;

  @override
  void dispose() {
    _brixController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  bool get _hasRating {
    return _sweetness != null ||
        _crunchiness != null ||
        _juiciness != null ||
        _mealiness != null;
  }

  Future<void> _saveFeedback() async {
    if (_isSaving || _saved) {
      return;
    }

    final String brixText =
        _brixController.text.trim();

    double? brix;

    if (brixText.isNotEmpty) {
      brix = double.tryParse(
        brixText.replaceAll(',', '.'),
      );

      if (brix == null) {
        setState(() {
          _errorMessage =
              'Inserisci un valore Brix valido.';
        });

        return;
      }

      if (brix < 0 || brix > 30) {
        setState(() {
          _errorMessage =
              'Controlla il valore Brix inserito.';
        });

        return;
      }
    }

    if (!_hasRating && brix == null) {
      setState(() {
        _errorMessage =
            'Inserisci almeno una valutazione '
            'oppure un valore Brix.';
      });

      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      await _feedbackService.saveFeedback(
        analysisId: widget.analysisId,
        sweetness: _sweetness,
        crunchiness: _crunchiness,
        juiciness: _juiciness,
        mealiness: _mealiness,
        brix: brix,
        notes: _notesController.text.trim(),
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _saved = true;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage =
            'Errore durante il salvataggio:\n$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  Widget _buildRating({
    required String title,
    required String subtitle,
    required int? value,
    required ValueChanged<int?> onChanged,
  }) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.stretch,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 4),

            Text(
              subtitle,
              style: const TextStyle(
                color: Colors.black54,
              ),
            ),

            const SizedBox(height: 14),

            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List.generate(
                5,
                (index) {
                  final int rating = index + 1;

                  return ChoiceChip(
                    label: Text(
                      '$rating',
                    ),
                    selected:
                        value == rating,
                    onSelected:
                        _isSaving || _saved
                            ? null
                            : (selected) {
                                onChanged(
                                  selected
                                      ? rating
                                      : null,
                                );
                              },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSuccessCard() {
    return const Card(
      elevation: 0,
      child: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(
              Icons.check_circle,
              size: 48,
              color: Color(0xFF2E7D32),
            ),

            SizedBox(height: 12),

            Text(
              'Feedback salvato',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Color(0xFF2E7D32),
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),

            SizedBox(height: 8),

            Text(
              'Grazie. Il risultato reale '
              'di questa anguria è stato '
              'associato alla previsione AngurIA.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.black54,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor:
          const Color(0xFFF4F8F3),

      appBar: AppBar(
        title: const Text(
          'Com’è davvero?',
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
            crossAxisAlignment:
                CrossAxisAlignment.stretch,
            children: [
              const Icon(
                Icons.water_drop_outlined,
                size: 58,
                color: Color(0xFF2E7D32),
              ),

              const SizedBox(height: 12),

              const Text(
                'Ora che hai aperto l’anguria, '
                'aiuta AngurIA a confrontare '
                'la previsione con il risultato reale.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 17,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 8),

              Text(
                'Analisi: ${widget.analysisId}',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.black54,
                ),
              ),

              const SizedBox(height: 22),

              _buildRating(
                title: 'Dolcezza',
                subtitle:
                    '1 = poco dolce • 5 = molto dolce',
                value: _sweetness,
                onChanged: (value) {
                  setState(() {
                    _sweetness = value;
                    _errorMessage = null;
                  });
                },
              ),

              _buildRating(
                title: 'Croccantezza',
                subtitle:
                    '1 = morbida • 5 = molto croccante',
                value: _crunchiness,
                onChanged: (value) {
                  setState(() {
                    _crunchiness = value;
                    _errorMessage = null;
                  });
                },
              ),

              _buildRating(
                title: 'Succosità',
                subtitle:
                    '1 = poco succosa • 5 = molto succosa',
                value: _juiciness,
                onChanged: (value) {
                  setState(() {
                    _juiciness = value;
                    _errorMessage = null;
                  });
                },
              ),

              _buildRating(
                title: 'Farinosità',
                subtitle:
                    '1 = assente • 5 = molto farinosa',
                value: _mealiness,
                onChanged: (value) {
                  setState(() {
                    _mealiness = value;
                    _errorMessage = null;
                  });
                },
              ),

              const SizedBox(height: 12),

              TextField(
                controller: _brixController,
                enabled: !_isSaving && !_saved,
                keyboardType:
                    const TextInputType
                        .numberWithOptions(
                  decimal: true,
                ),
                decoration:
                    const InputDecoration(
                  labelText:
                      'Brix (opzionale)',
                  hintText:
                      'Es. 11.8',
                  helperText:
                      'Inseriscilo solo se misurato.',
                  border:
                      OutlineInputBorder(),
                ),
              ),

              const SizedBox(height: 16),

              TextField(
                controller: _notesController,
                enabled: !_isSaving && !_saved,
                maxLines: 3,
                decoration:
                    const InputDecoration(
                  labelText:
                      'Note (opzionali)',
                  hintText:
                      'Come ti è sembrata l’anguria?',
                  border:
                      OutlineInputBorder(),
                ),
              ),

              if (_errorMessage != null) ...[
                const SizedBox(height: 16),

                Card(
                  elevation: 0,
                  child: Padding(
                    padding:
                        const EdgeInsets.all(16),
                    child: Row(
                      crossAxisAlignment:
                          CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.error_outline,
                          color: Colors.red,
                        ),

                        const SizedBox(width: 10),

                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style:
                                const TextStyle(
                              color:
                                  Colors.red,
                              fontWeight:
                                  FontWeight.bold,
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              if (_saved) ...[
                const SizedBox(height: 18),
                _buildSuccessCard(),
              ],

              const SizedBox(height: 20),

              ElevatedButton.icon(
                onPressed:
                    _isSaving || _saved
                        ? null
                        : _saveFeedback,
                icon: Icon(
                  _saved
                      ? Icons.check
                      : Icons.favorite_outline,
                ),
                label: Text(
                  _isSaving
                      ? 'Salvataggio...'
                      : _saved
                          ? 'Feedback salvato'
                          : 'Salva il risultato reale',
                ),
              ),

              if (_saved) ...[
                const SizedBox(height: 12),

                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).pop(
                      true,
                    );
                  },
                  icon: const Icon(
                    Icons.arrow_back,
                  ),
                  label: const Text(
                    'Torna ad AngurIA',
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