import { useState, useEffect } from 'react';
import {
    Dumbbell,
    Zap,
    Heart,
    Bike,
    Timer,
    FlameKindling,
    Waves,
    Plus,
    Loader2
} from 'lucide-react';
import { getWorkouts, getTrainingHistory } from '../services/backendService';
import WorkoutCard from '../components/WorkoutCard';
import GlassCard from '../components/GlassCard';
import './Workouts.css';

// Map category to icon
const categoryIcons = {
    strength: Dumbbell,
    hiit: Zap,
    yoga: Heart,
    cardio: Bike,
    core: FlameKindling,
    swimming: Waves,
    default: Dumbbell
};

function Workouts() {
    const [activeFilter, setActiveFilter] = useState('all');
    const [workouts, setWorkouts] = useState([]);
    const [loading, setLoading] = useState(true);

    const filters = [
        { id: 'all', label: 'Wszystkie' },
        { id: 'strength', label: 'Siła' },
        { id: 'cardio', label: 'Cardio' },
        { id: 'yoga', label: 'Yoga' },
        { id: 'hiit', label: 'HIIT' },
    ];

    // Default workouts if backend returns empty
    const defaultWorkouts = [
        {
            id: 1,
            title: 'Push Day Power',
            description: 'Klatka piersiowa, barki, triceps',
            duration: 45,
            calories: 320,
            difficulty: 'hard',
            icon: Dumbbell,
            category: 'strength',
            progress: 0
        },
        {
            id: 2,
            title: 'HIIT Cardio Blast',
            description: 'Intensywny trening interwałowy',
            duration: 25,
            calories: 380,
            difficulty: 'extreme',
            icon: Zap,
            category: 'hiit',
            progress: 0
        },
        {
            id: 3,
            title: 'Morning Yoga Flow',
            description: 'Rozciąganie i relaksacja',
            duration: 30,
            calories: 120,
            difficulty: 'easy',
            icon: Heart,
            category: 'yoga',
            progress: 65
        },
        {
            id: 4,
            title: 'Cycling Sprint',
            description: 'Trening rowerowy z interwałami',
            duration: 40,
            calories: 450,
            difficulty: 'hard',
            icon: Bike,
            category: 'cardio',
            progress: 0
        },
        {
            id: 5,
            title: 'Leg Day Destroyer',
            description: 'Nogi i pośladki na full',
            duration: 50,
            calories: 400,
            difficulty: 'extreme',
            icon: FlameKindling,
            category: 'strength',
            progress: 0
        },
        {
            id: 6,
            title: 'Tabata Express',
            description: '4 minuty intensywnej pracy',
            duration: 15,
            calories: 200,
            difficulty: 'medium',
            icon: Timer,
            category: 'hiit',
            progress: 100
        },
        {
            id: 7,
            title: 'Swimming Drills',
            description: 'Technika i wytrzymałość w wodzie',
            duration: 45,
            calories: 350,
            difficulty: 'medium',
            icon: Waves,
            category: 'cardio',
            progress: 0
        }
    ];

    // Fetch workouts from backend
    useEffect(() => {
        const fetchWorkouts = async () => {
            try {
                const [savedWorkouts, history] = await Promise.all([
                    getWorkouts(),
                    getTrainingHistory()
                ]);

                // Combine and format workouts
                const allWorkouts = [];

                // Add saved workouts
                if (savedWorkouts && savedWorkouts.length > 0) {
                    savedWorkouts.forEach(w => {
                        allWorkouts.push({
                            id: w.id,
                            title: w.name || w.title || 'Trening',
                            description: w.description || 'Zapisany trening',
                            duration: w.duration || 30,
                            calories: w.calories || 200,
                            difficulty: w.difficulty || 'medium',
                            icon: categoryIcons[w.category] || categoryIcons.default,
                            category: w.category || 'strength',
                            progress: w.progress || 0
                        });
                    });
                }

                // Add history trainings
                if (history && history.length > 0) {
                    history.forEach(h => {
                        allWorkouts.push({
                            id: h.id,
                            title: h.name || 'Trening AI',
                            description: h.focus_area || 'Wygenerowany plan treningowy',
                            duration: h.duration || 45,
                            calories: h.estimated_calories || 300,
                            difficulty: h.difficulty || 'medium',
                            icon: categoryIcons[h.category] || Dumbbell,
                            category: h.category || 'strength',
                            progress: h.completed ? 100 : 0
                        });
                    });
                }

                // Use fetched workouts or default
                setWorkouts(allWorkouts.length > 0 ? allWorkouts : defaultWorkouts);
            } catch (error) {
                console.error('Failed to fetch workouts:', error);
                setWorkouts(defaultWorkouts);
            } finally {
                setLoading(false);
            }
        };

        fetchWorkouts();
    }, []);

    const filteredWorkouts = activeFilter === 'all'
        ? workouts
        : workouts.filter(w => w.category === activeFilter);

    if (loading) {
        return (
            <div className="page workouts">
                <header className="page-header">
                    <div>
                        <h1 className="page-title">Treningi</h1>
                        <p className="page-subtitle">Ładowanie...</p>
                    </div>
                </header>
                <div className="loading-container">
                    <Loader2 size={40} className="spinning" />
                </div>
            </div>
        );
    }

    return (
        <div className="page workouts">
            <header className="page-header">
                <div>
                    <h1 className="page-title">Treningi</h1>
                    <p className="page-subtitle">Wybierz swój dzisiejszy workout</p>
                </div>
            </header>

            {/* Filters */}
            <div className="filters-container">
                <div className="filters-scroll">
                    {filters.map(filter => (
                        <button
                            key={filter.id}
                            className={`filter-btn ${activeFilter === filter.id ? 'filter-btn--active' : ''}`}
                            onClick={() => setActiveFilter(filter.id)}
                        >
                            {filter.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Workout Count */}
            <div className="workouts-count">
                <span>{filteredWorkouts.length} treningów</span>
            </div>

            {/* Workouts List */}
            {filteredWorkouts.length > 0 ? (
                <div className="workouts-list">
                    {filteredWorkouts.map((workout, index) => (
                        <div
                            key={workout.id}
                            className="workout-item animate-fade-in"
                            style={{ animationDelay: `${index * 0.1}s` }}
                        >
                            <WorkoutCard
                                {...workout}
                                onClick={() => console.log('Start workout', workout.id)}
                            />
                        </div>
                    ))}
                </div>
            ) : (
                <GlassCard className="empty-state">
                    <Dumbbell size={48} className="empty-icon" />
                    <h3>Brak treningów</h3>
                    <p>Nie masz jeszcze zapisanych treningów w tej kategorii.</p>
                    <button className="btn btn-primary">
                        <Plus size={18} />
                        Wygeneruj trening
                    </button>
                </GlassCard>
            )}
        </div>
    );
}

export default Workouts;
