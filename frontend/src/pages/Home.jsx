import {
    Trophy,
    Flame,
    Footprints,
    Timer,
    Dumbbell,
    Zap,
    TrendingUp,
    ChevronRight
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import ProgressRing from '../components/ProgressRing';
import WorkoutCard from '../components/WorkoutCard';
import './Home.css';

function Home() {
    const todayProgress = 68;

    const quickStats = [
        { icon: Flame, value: '420', label: 'Calories', color: 'var(--neon-pink)' },
        { icon: Footprints, value: '8,234', label: 'Steps', color: 'var(--neon-cyan)' },
        { icon: Timer, value: '45', label: 'Minutes', color: 'var(--neon-purple)' },
    ];

    const upcomingWorkouts = [
        {
            id: 1,
            title: 'Morning HIIT',
            description: 'High intensity cardio blast',
            duration: 25,
            calories: 280,
            difficulty: 'hard',
            icon: Zap,
            progress: 0
        },
        {
            id: 2,
            title: 'Core Strength',
            description: 'Build your core muscles',
            duration: 20,
            calories: 150,
            difficulty: 'medium',
            icon: Dumbbell,
            progress: 40
        }
    ];

    const achievements = [
        { icon: Trophy, label: '7 Day Streak', unlocked: true },
        { icon: TrendingUp, label: '10kg Lost', unlocked: true },
        { icon: Flame, label: '100 Workouts', unlocked: false },
    ];

    return (
        <div className="page home">
            {/* Header */}
            <div className="home-header">
                <div className="home-greeting">
                    <h1 className="home-title">Cześć, Krzysiek! 👋</h1>
                    <p className="home-subtitle">Gotowy na dzisiejszy trening?</p>
                </div>
                <div className="avatar">KG</div>
            </div>

            {/* Today's Progress */}
            <section className="section">
                <h2 className="section-title">Dzisiejszy postęp</h2>
                <GlassCard className="home-progress-card" glow>
                    <div className="home-progress-content">
                        <ProgressRing
                            progress={todayProgress}
                            size={140}
                            strokeWidth={10}
                            label="ukończone"
                        />
                        <div className="home-progress-info">
                            <h3>Świetna robota!</h3>
                            <p>Pozostało jeszcze 32% do osiągnięcia dzisiejszego celu.</p>
                            <button className="btn btn-primary">
                                <Zap size={18} />
                                Kontynuuj
                            </button>
                        </div>
                    </div>
                </GlassCard>
            </section>

            {/* Quick Stats */}
            <section className="section">
                <h2 className="section-title">Statystyki dnia</h2>
                <div className="stats-grid">
                    {quickStats.map(({ icon: Icon, value, label, color }) => (
                        <GlassCard key={label} className="stat-card">
                            <Icon
                                size={24}
                                style={{ color }}
                                className="stat-icon"
                            />
                            <span className="stat-value" style={{ color }}>{value}</span>
                            <span className="stat-label">{label}</span>
                        </GlassCard>
                    ))}
                </div>
            </section>

            {/* Upcoming Workouts */}
            <section className="section">
                <div className="section-header">
                    <h2 className="section-title">Nadchodzące treningi</h2>
                    <button className="btn-link">
                        Zobacz wszystkie <ChevronRight size={16} />
                    </button>
                </div>
                <div className="workout-list">
                    {upcomingWorkouts.map(workout => (
                        <WorkoutCard
                            key={workout.id}
                            {...workout}
                            onClick={() => console.log('Open workout', workout.id)}
                        />
                    ))}
                </div>
            </section>

            {/* Achievements */}
            <section className="section">
                <h2 className="section-title">Osiągnięcia</h2>
                <div className="achievements-grid">
                    {achievements.map(({ icon: Icon, label, unlocked }) => (
                        <GlassCard
                            key={label}
                            className={`achievement-card ${!unlocked ? 'achievement-card--locked' : ''}`}
                        >
                            <div className="achievement-icon">
                                <Icon size={24} />
                            </div>
                            <span className="achievement-label">{label}</span>
                        </GlassCard>
                    ))}
                </div>
            </section>
        </div>
    );
}

export default Home;
