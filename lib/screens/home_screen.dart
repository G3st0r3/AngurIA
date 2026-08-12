import 'package:flutter/material.dart';

import 'camera_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _betaFriendController =
      TextEditingController();

  String _betaFriendId = '';

  @override
  void dispose() {
    _betaFriendController.dispose();
    super.dispose();
  }

  void _updateBetaFriendId(String value) {
    setState(() {
      _betaFriendId = value.trim().toUpperCase();
    });
  }

  bool get _isBetaFriendIdValid {
    return RegExp(r'^BF-\d{3}$').hasMatch(_betaFriendId);
  }

  void _startTest() {
    if (!_isBetaFriendIdValid) {
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          betaFriendId: _betaFriendId,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F8F3),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 620,
              ),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 32),

                  const Icon(
                    Icons.energy_savings_leaf,
                    size: 88,
                    color: Color(0xFF2E7D32),
                  ),

                  const SizedBox(height: 14),

                  const Text(
                    'AngurIA',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF2E7D32),
                    ),
                  ),

                  const SizedBox(height: 8),

                  Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE1F0DF),
                        borderRadius:
                            BorderRadius.circular(30),
                      ),
                      child: const Text(
                        '🍉 BETA FRIENDS',
                        style: TextStyle(
                          color: Color(0xFF2E7D32),
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.7,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 22),

                  const Text(
                    'Possiamo prevedere quanto sarà buona '
                    'un’anguria prima di aprirla?',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      height: 1.3,
                    ),
                  ),

                  const SizedBox(height: 12),

                  const Text(
                    'Stai partecipando alla beta '
                    'sperimentale di AngurIA.\n'
                    'La tua prova ci aiuterà a confrontare '
                    'la previsione dell’AI con la qualità '
                    'reale dell’anguria dopo l’apertura.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.black54,
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 28),

                  const Card(
                    elevation: 0,
                    child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          Text(
                            '📸 Come fare una buona prova',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF2E7D32),
                            ),
                          ),
                          SizedBox(height: 18),
                          _GuideRow(
                            number: '1',
                            text:
                                'Fotografa l’anguria intera '
                                'con buona luce.',
                          ),
                          SizedBox(height: 14),
                          _GuideRow(
                            number: '2',
                            text:
                                'Fai analizzare la foto prima '
                                'di aprire l’anguria.',
                          ),
                          SizedBox(height: 14),
                          _GuideRow(
                            number: '3',
                            text:
                                'Dopo averla aperta e '
                                'assaggiata, usa '
                                '“Com’è davvero?” per '
                                'registrare il risultato reale.',
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius:
                          BorderRadius.circular(14),
                    ),
                    child: const Row(
                      crossAxisAlignment:
                          CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.lightbulb_outline,
                          color: Colors.orange,
                        ),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Più la foto è chiara e completa, '
                            'più il test sarà utile per '
                            'migliorare AngurIA.',
                            style: TextStyle(height: 1.4),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // BETA FRIEND ID
                  TextField(
                    controller: _betaFriendController,
                    textCapitalization:
                        TextCapitalization.characters,
                    onChanged: _updateBetaFriendId,
                    decoration: InputDecoration(
                      labelText: 'Codice Beta Friend',
                      hintText: 'BF-001',
                      prefixIcon:
                          const Icon(Icons.badge_outlined),
                      helperText:
                          'Inserisci il codice ricevuto '
                          'per partecipare alla prova.',
                      errorText:
                          _betaFriendId.isNotEmpty &&
                                  !_isBetaFriendIdValid
                              ? 'Formato richiesto: BF-001'
                              : null,
                      border: OutlineInputBorder(
                        borderRadius:
                            BorderRadius.circular(14),
                      ),
                    ),
                  ),

                  const SizedBox(height: 22),

                  ElevatedButton.icon(
                    onPressed:
                        _isBetaFriendIdValid
                            ? _startTest
                            : null,
                    icon: const Icon(
                      Icons.camera_alt_outlined,
                    ),
                    label: const Padding(
                      padding: EdgeInsets.symmetric(
                        vertical: 4,
                      ),
                      child: Text(
                        'Inizia il test',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  const Text(
                    'Versione Beta Friends • '
                    'I risultati sono sperimentali e '
                    'servono a migliorare il sistema.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.black45,
                    ),
                  ),

                  const SizedBox(height: 30),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _GuideRow extends StatelessWidget {
  final String number;
  final String text;

  const _GuideRow({
    required this.number,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 28,
          height: 28,
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: Color(0xFFE1F0DF),
            shape: BoxShape.circle,
          ),
          child: Text(
            number,
            style: const TextStyle(
              color: Color(0xFF2E7D32),
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              text,
              style: const TextStyle(
                height: 1.4,
              ),
            ),
          ),
        ),
      ],
    );
  }
}