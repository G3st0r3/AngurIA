import 'package:flutter/material.dart';
import 'camera_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),

              const Icon(
                Icons.energy_savings_leaf,
                size: 100,
                color: Color(0xFF2E7D32),
              ),

              const SizedBox(height: 20),

              const Text(
                "AngurIA",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 42,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2E7D32),
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                "Scopri la qualità della tua anguria\ncon l'Intelligenza Artificiale",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  height: 1.5,
                ),
              ),

              const Spacer(),

              ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const CameraScreen(),
                    ),
                  );
                },
                icon: const Icon(Icons.camera_alt),
                label: const Text(
                  "Analizza un'anguria",
                  style: TextStyle(fontSize: 18),
                ),
              ),

              const SizedBox(height: 15),

              OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.history),
                label: const Text("Cronologia Analisi"),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}
