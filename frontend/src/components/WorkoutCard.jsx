import { Clock, Flame, ChevronRight } from 'lucide-react';
import GlassCard from './GlassCard';
import './WorkoutCard.css';

function WorkoutCard({
    title,
    description,
    duration,
    calories,
    difficulty,
    icon: Icon,
    progress = 0,
    onClick
}) {
    const difficultyColors = {
        easy: 'var(--neon-green)',
        medium: 'var(--neon-cyan)',
        hard: 'var(--neon-pink)',
        extreme: 'var(--neon-purple)'
    };

    return (
        <GlassCard className="workout-card" onClick={onClick}>
            <div className="workout-card-header">
                <div
                    className="workout-card-icon"
                    style={{ '--icon-glow': difficultyColors[difficulty] || 'var(--neon-purple)' }}
                >
                    {Icon && <Icon size={24} strokeWidth={1.5} />}
                </div>
                <div className="workout-card-info">
                    <h3 className="workout-card-title">{title}</h3>
                    <p className="workout-card-desc">{description}</p>
                </div>
                <ChevronRight className="workout-card-arrow" size={20} />
            </div>

            <div className="workout-card-meta">
                <div className="workout-card-stat">
                    <Clock size={14} />
                    <span>{duration} min</span>
                </div>
                <div className="workout-card-stat">
                    <Flame size={14} />
                    <span>{calories} kcal</span>
                </div>
                <span
                    className="workout-card-difficulty"
                    style={{ color: difficultyColors[difficulty] }}
                >
                    {difficulty}
                </span>
            </div>

            {progress > 0 && (
                <div className="workout-card-progress">
                    <div
                        className="workout-card-progress-bar"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}
        </GlassCard>
    );
}

export default WorkoutCard;
