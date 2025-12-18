import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

/// Home screen for configuring training parameters.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();

  // Training parameters
  double _numPeople = 5;
  String _difficulty = 'medium';
  double _restTime = 30;
  bool _isCircuit = true;
  bool _isLoading = false;

  // Exercise counts
  double _warmupCount = 3;
  double _mainCount = 5;
  double _cooldownCount = 3;

  void _generatePlan() async {
    setState(() => _isLoading = true);

    try {
      final plan = await _apiService.generateTraining(
        numPeople: _numPeople.toInt(),
        difficulty: _difficulty,
        restTime: _restTime.toInt(),
        mode: _isCircuit ? 'circuit' : 'common',
        warmupCount: _warmupCount.toInt(),
        mainCount: _mainCount.toInt(),
        cooldownCount: _cooldownCount.toInt(),
      );

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(plan: plan),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Błąd: $e'), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text('AI Trainer',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLabel('Liczba osób: ${_numPeople.toInt()}'),
            Slider(
              value: _numPeople,
              min: 1,
              max: 20,
              divisions: 19,
              label: _numPeople.toInt().toString(),
              onChanged: (val) => setState(() => _numPeople = val),
            ),

            const SizedBox(height: 20),

            _buildLabel('Poziom trudności'),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'easy', label: Text('Łatwy')),
                ButtonSegment(value: 'medium', label: Text('Średni')),
                ButtonSegment(value: 'hard', label: Text('Trudny')),
              ],
              selected: {_difficulty},
              onSelectionChanged: (Set<String> newSelection) {
                setState(() => _difficulty = newSelection.first);
              },
            ),

            const SizedBox(height: 20),

            _buildLabel('Czas przerw: ${_restTime.toInt()} sek'),
            Slider(
              value: _restTime,
              min: 10,
              max: 120,
              divisions: 11,
              onChanged: (val) => setState(() => _restTime = val),
            ),

            const SizedBox(height: 20),

            SwitchListTile(
              title: Text('Trening Obwodowy (Stacje)',
                  style: GoogleFonts.poppins(fontWeight: FontWeight.w600)),
              subtitle: Text(
                  _isCircuit ? 'Każdy robi co innego' : 'Wszyscy robią to samo'),
              value: _isCircuit,
              onChanged: (val) => setState(() => _isCircuit = val),
            ),

            const Divider(height: 40),

            _buildLabel('Liczba ćwiczeń'),
            const SizedBox(height: 10),

            _buildExerciseCountSlider(
              'Rozgrzewka',
              _warmupCount,
              1,
              10,
              Colors.orange,
              (val) => setState(() => _warmupCount = val),
            ),

            _buildExerciseCountSlider(
              'Część główna',
              _mainCount,
              1,
              20,
              Colors.red,
              (val) => setState(() => _mainCount = val),
            ),

            _buildExerciseCountSlider(
              'Wyciszenie',
              _cooldownCount,
              1,
              10,
              Colors.blue,
              (val) => setState(() => _cooldownCount = val),
            ),

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _isLoading ? null : _generatePlan,
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Text('GENERUJ TRENING',
                        style: GoogleFonts.poppins(
                            fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(text,
        style: GoogleFonts.poppins(fontSize: 16, fontWeight: FontWeight.w500));
  }

  Widget _buildExerciseCountSlider(
    String label,
    double value,
    double min,
    double max,
    Color color,
    ValueChanged<double> onChanged,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: GoogleFonts.poppins(fontSize: 14, color: color),
            ),
          ),
          Expanded(
            child: Slider(
              value: value,
              min: min,
              max: max,
              divisions: (max - min).toInt(),
              activeColor: color,
              label: value.toInt().toString(),
              onChanged: onChanged,
            ),
          ),
          SizedBox(
            width: 30,
            child: Text(
              '${value.toInt()}',
              style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}
