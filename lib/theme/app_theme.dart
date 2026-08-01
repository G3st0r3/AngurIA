import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF43A047),
      brightness: Brightness.light,
    ),
    scaffoldBackgroundColor: const Color(0xFFF7FBF5),

    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF43A047),
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 58),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
        ),
      ),
    ),

    textTheme: const TextTheme(
      headlineMedium: TextStyle(
        fontSize: 38,
        fontWeight: FontWeight.bold,
        color: Color(0xFF2E7D32),
      ),
      bodyLarge: TextStyle(
        fontSize: 18,
        color: Colors.black87,
      ),
    ),
  );
}