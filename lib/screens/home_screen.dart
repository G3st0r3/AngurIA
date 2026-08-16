import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';

import 'camera_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _betaFriendId;
  bool _isPreparing = true;

  @override
  void initState() {
    super.initState();
    _prepareBetaFriend();
  }

  Future<void> _prepareBetaFriend() async {
  // Fallback immediato:
  // il tester può iniziare anche se lo storage mobile
  // è lento o non disponibile.
  final fallbackId = _generateBetaFriendId();

  if (mounted) {
    setState(() {
      _betaFriendId = fallbackId;
      _isPreparing = false;
    });

    _registerBetaVisit(fallbackId);
  }

  // Prova poi a recuperare o salvare
  // l'identificativo persistente nel browser.
  try {
    final prefs = await SharedPreferences.getInstance()
        .timeout(const Duration(seconds: 2));

    String? storedId =
        prefs.getString('anguria_beta_friend_id');

    if (storedId == null || storedId.isEmpty) {
      storedId = fallbackId;

      await prefs
          .setString(
            'anguria_beta_friend_id',
            storedId,
          )
          .timeout(const Duration(seconds: 2));
    }

    if (!mounted) return;

    setState(() {
      _betaFriendId = storedId;
    });

    if (storedId != fallbackId) {
      _registerBetaVisit(storedId);
    }
  } catch (error) {
    debugPrint(
      'Beta Friend storage non disponibile: $error',
    );

    // Nessun blocco:
    // resta valido l'ID generato inizialmente.
  }
}


  Future<void> _registerBetaVisit(
    String betaFriendId,
  ) async {
    try {
      await http
          .post(
            Uri.parse(
              '${ApiConfig.baseUrl}/beta/visit',
            ),
            headers: {
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'betaFriendId': betaFriendId,
            }),
          )
          .timeout(
            const Duration(seconds: 4),
          );
    } catch (error) {
      debugPrint(
        'Beta visit non registrata: $error',
      );
    }
  }

  String _generateBetaFriendId() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    final random = Random.secure();

    final code = List.generate(
      6,
      (_) => chars[random.nextInt(chars.length)],
    ).join();

    return 'BF-$code';
  }

  void _startTest() {
    final betaFriendId = _betaFriendId;

    if (betaFriendId == null) return;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          betaFriendId: betaFriendId,
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
                            style: TextStyle(
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  ElevatedButton.icon(
                    onPressed:
                        _isPreparing ? null : _startTest,
                    icon: _isPreparing
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                            ),
                          )
                        : const Icon(
                            Icons.camera_alt_outlined,
                          ),
                    label: Padding(
                      padding: const EdgeInsets.symmetric(
                        vertical: 4,
                      ),
                      child: Text(
                        _isPreparing
                            ? 'Preparazione...'
                            : 'Inizia il test',
                        style: const TextStyle(
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