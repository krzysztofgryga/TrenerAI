import { useState } from 'react';
import {
    Dumbbell,
    Zap,
    Heart,
    Bike,
    Timer,
    FlameKindling,
    Waves
} from 'lucide-react';
import WorkoutCard from '../components/WorkoutCard';
import './Workouts.css';

function Workouts() {
    const [activeFilter, setActiveFilter] = useState('all');

    const filters = [
        { id: 'all', label: 'Wszystkie' },
        { id: 'strength', label: 'Siła' },
        { id: 'cardio', label: 'Cardio' },
        { id: 'yoga', label: 'Yoga' },
        { id: 'hiit', label: 'HIIT' },
    ];

    const workouts = [
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

    const filteredWorkouts = activeFilter === 'all'
        ? workouts
        : workouts.filter(w => w.category === activeFilter);

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
        </div>
    );
}

export default Workouts;
