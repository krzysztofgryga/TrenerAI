import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../models/training_plan.dart';

/// Service for generating PDF documents from training plans.
class PdfService {
  /// Generates and opens print/share dialog for the training plan PDF.
  static Future<void> generateAndShare(TrainingPlan plan) async {
    final pdf = await _buildPdf(plan);
    await Printing.layoutPdf(
      onLayout: (PdfPageFormat format) async => pdf.save(),
      name: 'plan_treningowy.pdf',
    );
  }

  /// Generates and directly shares the PDF (mobile).
  static Future<void> sharePdf(TrainingPlan plan) async {
    final pdf = await _buildPdf(plan);
    await Printing.sharePdf(
      bytes: await pdf.save(),
      filename: 'plan_treningowy.pdf',
    );
  }

  /// Builds the PDF document.
  static Future<pw.Document> _buildPdf(TrainingPlan plan) async {
    final pdf = pw.Document(
      title: 'Plan Treningowy',
      author: 'TrenerAI',
    );

    // Load a font that supports Polish characters
    final font = await PdfGoogleFonts.nunitoRegular();
    final fontBold = await PdfGoogleFonts.nunitoBold();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        header: (context) => _buildHeader(fontBold),
        footer: (context) => _buildFooter(context, font),
        build: (context) => [
          _buildSummarySection(plan, font, fontBold),
          pw.SizedBox(height: 20),
          _buildExerciseSection(
            'ROZGRZEWKA',
            plan.warmup,
            PdfColors.orange,
            font,
            fontBold,
          ),
          pw.SizedBox(height: 16),
          _buildExerciseSection(
            'CZESC GLOWNA',
            plan.mainPart,
            PdfColors.red,
            font,
            fontBold,
            isCircuit: plan.mode == 'circuit',
          ),
          pw.SizedBox(height: 16),
          _buildExerciseSection(
            'ROZCIAGANIE',
            plan.cooldown,
            PdfColors.blue,
            font,
            fontBold,
          ),
        ],
      ),
    );

    return pdf;
  }

  /// Builds the PDF header.
  static pw.Widget _buildHeader(pw.Font fontBold) {
    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 20),
      padding: const pw.EdgeInsets.only(bottom: 10),
      decoration: const pw.BoxDecoration(
        border: pw.Border(
          bottom: pw.BorderSide(color: PdfColors.grey400, width: 1),
        ),
      ),
      child: pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Text(
            'TrenerAI',
            style: pw.TextStyle(
              font: fontBold,
              fontSize: 24,
              color: PdfColors.blue800,
            ),
          ),
          pw.Text(
            'Plan Treningowy',
            style: pw.TextStyle(
              font: fontBold,
              fontSize: 18,
              color: PdfColors.grey700,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the PDF footer with page numbers.
  static pw.Widget _buildFooter(pw.Context context, pw.Font font) {
    return pw.Container(
      margin: const pw.EdgeInsets.only(top: 10),
      child: pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Text(
            'Wygenerowano przez TrenerAI',
            style: pw.TextStyle(font: font, fontSize: 10, color: PdfColors.grey),
          ),
          pw.Text(
            'Strona ${context.pageNumber} z ${context.pagesCount}',
            style: pw.TextStyle(font: font, fontSize: 10, color: PdfColors.grey),
          ),
        ],
      ),
    );
  }

  /// Builds the summary section.
  static pw.Widget _buildSummarySection(
    TrainingPlan plan,
    pw.Font font,
    pw.Font fontBold,
  ) {
    final totalExercises =
        plan.warmup.length + plan.mainPart.length + plan.cooldown.length;

    return pw.Container(
      padding: const pw.EdgeInsets.all(16),
      decoration: pw.BoxDecoration(
        color: PdfColors.grey100,
        borderRadius: pw.BorderRadius.circular(8),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(
            'Podsumowanie',
            style: pw.TextStyle(font: fontBold, fontSize: 16),
          ),
          pw.SizedBox(height: 8),
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceAround,
            children: [
              _buildSummaryItem(
                'Tryb',
                plan.mode == 'circuit' ? 'Obwodowy' : 'Wspolny',
                font,
                fontBold,
              ),
              _buildSummaryItem(
                'Czas',
                '${plan.totalDuration} min',
                font,
                fontBold,
              ),
              _buildSummaryItem(
                'Cwiczenia',
                '$totalExercises',
                font,
                fontBold,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds a single summary item.
  static pw.Widget _buildSummaryItem(
    String label,
    String value,
    pw.Font font,
    pw.Font fontBold,
  ) {
    return pw.Column(
      children: [
        pw.Text(label, style: pw.TextStyle(font: font, fontSize: 12, color: PdfColors.grey700)),
        pw.SizedBox(height: 4),
        pw.Text(value, style: pw.TextStyle(font: fontBold, fontSize: 14)),
      ],
    );
  }

  /// Builds an exercise section (warmup, main, cooldown).
  static pw.Widget _buildExerciseSection(
    String title,
    List<Exercise> exercises,
    PdfColor color,
    pw.Font font,
    pw.Font fontBold, {
    bool isCircuit = false,
  }) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Container(
          padding: const pw.EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: pw.BoxDecoration(
            color: color,
            borderRadius: pw.BorderRadius.circular(4),
          ),
          child: pw.Text(
            title,
            style: pw.TextStyle(
              font: fontBold,
              fontSize: 14,
              color: PdfColors.white,
            ),
          ),
        ),
        pw.SizedBox(height: 10),
        if (isCircuit)
          pw.Padding(
            padding: const pw.EdgeInsets.only(bottom: 8),
            child: pw.Text(
              'Tryb obwodowy: Ustaw uczestnikow na stacjach 1-${exercises.length}',
              style: pw.TextStyle(
                font: font,
                fontSize: 10,
                fontStyle: pw.FontStyle.italic,
                color: PdfColors.grey600,
              ),
            ),
          ),
        ...exercises.asMap().entries.map((entry) {
          final index = entry.key;
          final exercise = entry.value;
          return _buildExerciseRow(
            exercise,
            color,
            font,
            fontBold,
            number: isCircuit ? index + 1 : null,
          );
        }),
      ],
    );
  }

  /// Builds a single exercise row.
  static pw.Widget _buildExerciseRow(
    Exercise exercise,
    PdfColor color,
    pw.Font font,
    pw.Font fontBold, {
    int? number,
  }) {
    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 8),
      padding: const pw.EdgeInsets.all(12),
      decoration: pw.BoxDecoration(
        border: pw.Border.all(color: PdfColors.grey300),
        borderRadius: pw.BorderRadius.circular(6),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Container(
            width: 30,
            height: 30,
            decoration: pw.BoxDecoration(
              color: color.shade(0.9),
              shape: pw.BoxShape.circle,
            ),
            alignment: pw.Alignment.center,
            child: pw.Text(
              number != null ? '$number' : exercise.name[0].toUpperCase(),
              style: pw.TextStyle(
                font: fontBold,
                fontSize: 12,
                color: color,
              ),
            ),
          ),
          pw.SizedBox(width: 12),
          pw.Expanded(
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text(
                  exercise.name,
                  style: pw.TextStyle(font: fontBold, fontSize: 12),
                ),
                pw.SizedBox(height: 4),
                pw.Text(
                  exercise.description,
                  style: pw.TextStyle(font: font, fontSize: 10, color: PdfColors.grey700),
                ),
                if (exercise.difficulty.isNotEmpty) ...[
                  pw.SizedBox(height: 4),
                  pw.Container(
                    padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: pw.BoxDecoration(
                      color: PdfColors.grey200,
                      borderRadius: pw.BorderRadius.circular(4),
                    ),
                    child: pw.Text(
                      exercise.difficulty,
                      style: pw.TextStyle(font: font, fontSize: 8),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
