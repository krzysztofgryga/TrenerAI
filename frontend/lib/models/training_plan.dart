/// Model representing a single exercise in a training plan.
class Exercise {
  final String id;
  final String name;
  final String description;
  final String muscleGroup;
  final String difficulty;
  final String type;

  Exercise({
    required this.id,
    required this.name,
    required this.description,
    required this.muscleGroup,
    required this.difficulty,
    required this.type,
  });

  factory Exercise.fromJson(Map<String, dynamic> json) {
    return Exercise(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Bez nazwy',
      description: json['description'] ?? '',
      muscleGroup: json['muscle_group'] ?? '',
      difficulty: json['difficulty'] ?? 'medium',
      type: json['type'] ?? 'main',
    );
  }
}

/// Model representing a complete training plan with warmup, main, and cooldown phases.
class TrainingPlan {
  final List<Exercise> warmup;
  final List<Exercise> mainPart;
  final List<Exercise> cooldown;
  final String mode;
  final int totalDuration;

  TrainingPlan({
    required this.warmup,
    required this.mainPart,
    required this.cooldown,
    required this.mode,
    required this.totalDuration,
  });

  factory TrainingPlan.fromJson(Map<String, dynamic> json) {
    return TrainingPlan(
      warmup: (json['warmup'] as List).map((e) => Exercise.fromJson(e)).toList(),
      mainPart: (json['main_part'] as List).map((e) => Exercise.fromJson(e)).toList(),
      cooldown: (json['cooldown'] as List).map((e) => Exercise.fromJson(e)).toList(),
      mode: json['mode'] ?? 'common',
      totalDuration: json['total_duration_minutes'] ?? 0,
    );
  }
}
