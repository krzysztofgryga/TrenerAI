import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/training_plan.dart';

/// Service for communicating with the TrenerAI backend API.
class ApiService {
  /// Automatically detect the base URL depending on the platform.
  /// - Web: localhost
  /// - Android emulator: 10.0.2.2 (special alias for host machine)
  /// - iOS/Desktop: localhost
  String get _baseUrl {
    if (kIsWeb) return 'http://localhost:8000';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    return 'http://localhost:8000';
  }

  /// Generate a training plan using the AI backend.
  ///
  /// Parameters:
  /// - [numPeople]: Number of participants (1-50)
  /// - [difficulty]: Difficulty level (easy, medium, hard)
  /// - [restTime]: Rest time between exercises in seconds (10-300)
  /// - [mode]: Training mode (circuit or common)
  /// - [warmupCount]: Number of warmup exercises (1-10, default 3)
  /// - [mainCount]: Number of main exercises (1-20, default 5)
  /// - [cooldownCount]: Number of cooldown exercises (1-10, default 3)
  Future<TrainingPlan> generateTraining({
    required int numPeople,
    required String difficulty,
    required int restTime,
    required String mode,
    int warmupCount = 3,
    int mainCount = 5,
    int cooldownCount = 3,
  }) async {
    final url = Uri.parse('$_baseUrl/generate-training');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'num_people': numPeople,
          'difficulty': difficulty,
          'rest_time': restTime,
          'mode': mode,
          'warmup_count': warmupCount,
          'main_count': mainCount,
          'cooldown_count': cooldownCount,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return TrainingPlan.fromJson(data);
      } else {
        throw Exception('Błąd serwera: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Nie udało się połączyć z AI: $e');
    }
  }

  /// Check if the backend API is available.
  Future<bool> healthCheck() async {
    try {
      final url = Uri.parse('$_baseUrl/health');
      final response = await http.get(url);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
