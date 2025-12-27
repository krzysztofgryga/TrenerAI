import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Trophy,
    Flame,
    Footprints,
    Timer,
    Dumbbell,
    Zap,
    TrendingUp,
    ChevronRight,
    Users
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getTrainerDashboard, getWorkouts } from '../services/backendService';
import GlassCard from '../components/GlassCard';
import ProgressRing from '../components/ProgressRing';
import WorkoutCard from '../components/WorkoutCard';
import './Home.css';

function Home() {
    const navigate = useNavigate();
    const { user, profile, isTrainer } = useAuth();
    const [dashboardData, setDashboardData] = useState(null);
    const [recentWorkouts, setRecentWorkouts] = useState([]);
    const [loading, setLoading] = useState(true);

    // Generate initials from name
    const getInitials = (name) => {
        if (!name) return 'U';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    // Fetch data on mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                if (isTrainer) {
                    const data = await getTrainerDashboard();
                    setDashboardData(data);
                }
                const workouts = await getWorkouts();
                setRecentWorkouts(workouts.slice(0, 2));
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [isTrainer]);

    const todayProgress = profile?.goal_progress || 68;

    const quickStats = [
        { icon: Flame, value: profile?.calories_today || '0', label: 'Kalorie', color: 'var(--neon-pink)' },
        { icon: Footprints, value: profile?.steps_today || '0', label: 'Kroki', color: 'var(--neon-cyan)' },
        { icon: Timer, value: profile?.minutes_today || '0', label: 'Minuty', color: 'var(--neon-purple)' },
    ];

    // Default workouts if none from backend
    const upcomingWorkouts = recentWorkouts.length > 0 ? recentWorkouts.map(w => ({
        id: w.id,
        title: w.name || w.title,
        description: w.description || 'Trening wygenerowany przez AI',
        duration: w.duration || 30,
        calories: w.calories || 200,
        difficulty: w.difficulty || 'medium',
        icon: Dumbbell,
        progress: w.progress || 0
    })) : [
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
                    <h1 className="home-title">
                        Cześć, {user?.name?.split(' ')[0] || 'Użytkowniku'}!
                    </h1>
                    <p className="home-subtitle">
                        {isTrainer ? 'Sprawdź swoich klientów' : 'Gotowy na dzisiejszy trening?'}
                    </p>
                </div>
                <div className="avatar" onClick={() => navigate('/profile')}>
                    {getInitials(user?.name)}
                </div>
            </div>

            {/* Trainer Dashboard */}
            {isTrainer && dashboardData && (
                <section className="section">
                    <h2 className="section-title">Panel trenera</h2>
                    <GlassCard className="trainer-dashboard" glow>
                        <div className="trainer-stats">
                            <div className="trainer-stat">
                                <Users size={24} className="trainer-stat-icon" />
                                <div className="trainer-stat-info">
                                    <span className="trainer-stat-value">{dashboardData.total_clients || 0}</span>
                                    <span className="trainer-stat-label">Klientów</span>
                                </div>
                            </div>
                            <div className="trainer-stat">
                                <Dumbbell size={24} className="trainer-stat-icon" />
                                <div className="trainer-stat-info">
                                    <span className="trainer-stat-value">{dashboardData.total_trainings || 0}</span>
                                    <span className="trainer-stat-label">Treningów</span>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                </section>
            )}

            {/* Today's Progress (for clients) */}
            {!isTrainer && (
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
                                <h3>
                                    {todayProgress >= 100 ? 'Cel osiągnięty!' :
                                     todayProgress >= 70 ? 'Świetna robota!' :
                                     todayProgress >= 40 ? 'Tak trzymaj!' :
                                     'Zaczynamy!'}
                                </h3>
                                <p>
                                    {todayProgress >= 100 ?
                                        'Gratulacje! Osiągnąłeś dzisiejszy cel!' :
                                        `Pozostało jeszcze ${100 - todayProgress}% do osiągnięcia dzisiejszego celu.`
                                    }
                                </p>
                                <button className="btn btn-primary" onClick={() => navigate('/workouts')}>
                                    <Zap size={18} />
                                    {todayProgress > 0 ? 'Kontynuuj' : 'Zacznij'}
                                </button>
                            </div>
                        </div>
                    </GlassCard>
                </section>
            )}

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
                    <button className="btn-link" onClick={() => navigate('/workouts')}>
                        Zobacz wszystkie <ChevronRight size={16} />
                    </button>
                </div>
                <div className="workout-list">
                    {upcomingWorkouts.map(workout => (
                        <WorkoutCard
                            key={workout.id}
                            {...workout}
                            onClick={() => navigate('/workouts')}
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
