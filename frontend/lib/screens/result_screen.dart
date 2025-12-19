import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/training_plan.dart';
import '../services/pdf_service.dart';

/// Screen displaying the generated training plan.
class ResultScreen extends StatelessWidget {
  final TrainingPlan plan;

  const ResultScreen({super.key, required this.plan});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Twój Plan',
            style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            tooltip: 'Zapisz jako PDF',
            onPressed: () => _exportToPdf(context),
          ),
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Udostępnij PDF',
            onPressed: () => _sharePdf(context),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSectionHeader('Rozgrzewka 🔥', Colors.orange),
          ...plan.warmup.map((ex) => _buildExerciseCard(ex, Colors.orange)),

          const SizedBox(height: 20),
          _buildSectionHeader('Część Główna 💪', Colors.red),
          if (plan.mode == 'circuit')
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Text(
                  'ℹ️ Ustaw uczestników na stacjach 1-${plan.mainPart.length}',
                  style: TextStyle(
                      color: Colors.grey[600], fontStyle: FontStyle.italic)),
            ),
          ...plan.mainPart.asMap().entries.map((entry) {
            final index = entry.key + 1;
            final ex = entry.value;
            return _buildExerciseCard(ex, Colors.red,
                number: plan.mode == 'circuit' ? index : null);
          }),

          const SizedBox(height: 20),
          _buildSectionHeader('Relaks & Stretching 🧘', Colors.blue),
          ...plan.cooldown.map((ex) => _buildExerciseCard(ex, Colors.blue)),

          const SizedBox(height: 20),

          // Summary card
          Card(
            color: Colors.grey[200],
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Podsumowanie',
                    style: GoogleFonts.poppins(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                      'Tryb: ${plan.mode == 'circuit' ? 'Obwodowy' : 'Wspólny'}'),
                  Text('Czas trwania: ${plan.totalDuration} min'),
                  Text(
                      'Liczba ćwiczeń: ${plan.warmup.length + plan.mainPart.length + plan.cooldown.length}'),
                ],
              ),
            ),
          ),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Text(
        title,
        style: GoogleFonts.poppins(
            fontSize: 22, fontWeight: FontWeight.bold, color: color),
      ),
    );
  }

  Widget _buildExerciseCard(Exercise ex, Color color, {int? number}) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.2),
          child: Text(
            number != null ? '$number' : ex.name[0],
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ),
        title: Text(ex.name,
            style: GoogleFonts.poppins(fontWeight: FontWeight.w600)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(ex.description, style: GoogleFonts.poppins(fontSize: 13)),
            if (ex.difficulty.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Chip(
                  label: Text(
                    ex.difficulty,
                    style: const TextStyle(fontSize: 10),
                  ),
                  padding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                ),
              ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }

  /// Opens print/preview dialog to save as PDF.
  Future<void> _exportToPdf(BuildContext context) async {
    try {
      await PdfService.generateAndShare(plan);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Błąd generowania PDF: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// Shares the PDF directly (useful on mobile).
  Future<void> _sharePdf(BuildContext context) async {
    try {
      await PdfService.sharePdf(plan);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Błąd udostępniania PDF: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}
