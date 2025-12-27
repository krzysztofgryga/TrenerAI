import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    User,
    Target,
    Scale,
    Ruler,
    Calendar,
    TrendingUp,
    TrendingDown,
    Minus,
    Edit3,
    Save,
    X,
    Dumbbell,
    MessageCircle,
    AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getClientDetails, updateClientProfile } from '../services/backendService';
import GlassCard from '../components/GlassCard';
import './ClientDetail.css';

function ClientDetail() {
    const { clientId } = useParams();
    const navigate = useNavigate();
    const { isTrainer } = useAuth();

    const [client, setClient] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [editData, setEditData] = useState({});

    // Mock progress data (TODO: fetch from API)
    const [progressData] = useState([
        { date: '1 tyg', weight: 82 },
        { date: '2 tyg', weight: 81.5 },
        { date: '3 tyg', weight: 80.8 },
        { date: '4 tyg', weight: 80.2 },
        { date: 'Dziś', weight: 79.5 },
    ]);

    useEffect(() => {
        if (!isTrainer) {
            navigate('/');
            return;
        }
        fetchClient();
    }, [clientId, isTrainer, navigate]);

    const fetchClient = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getClientDetails(clientId);
            if (data) {
                setClient(data);
                setEditData({
                    age: data.profile?.age || '',
                    weight: data.profile?.weight || '',
                    height: data.profile?.height || '',
                    goals: data.profile?.goals || '',
                    trainer_notes: data.profile?.trainer_notes || '',
                });
            } else {
                setError('Nie znaleziono klienta');
            }
        } catch (err) {
            setError('Błąd ładowania danych klienta');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updated = await updateClientProfile(clientId, editData);
            setClient(prev => ({
                ...prev,
                profile: updated
            }));
            setEditing(false);
        } catch (err) {
            console.error('Save failed:', err);
        } finally {
            setSaving(false);
        }
    };

    const getInitials = (name) => {
        if (!name) return 'K';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    const calculateBMI = () => {
        if (!client?.profile?.weight || !client?.profile?.height) return null;
        const heightM = client.profile.height / 100;
        return (client.profile.weight / (heightM * heightM)).toFixed(1);
    };

    const getBMICategory = (bmi) => {
        if (!bmi) return null;
        if (bmi < 18.5) return { label: 'Niedowaga', color: '#f59e0b' };
        if (bmi < 25) return { label: 'Norma', color: '#22c55e' };
        if (bmi < 30) return { label: 'Nadwaga', color: '#f59e0b' };
        return { label: 'Otyłość', color: '#ef4444' };
    };

    const getWeightTrend = () => {
        if (progressData.length < 2) return 'stable';
        const first = progressData[0].weight;
        const last = progressData[progressData.length - 1].weight;
        if (last < first) return 'down';
        if (last > first) return 'up';
        return 'stable';
    };

    const getWeightChange = () => {
        if (progressData.length < 2) return 0;
        const first = progressData[0].weight;
        const last = progressData[progressData.length - 1].weight;
        return (last - first).toFixed(1);
    };

    if (!isTrainer) return null;

    if (loading) {
        return (
            <div className="page client-detail">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <span>Ładowanie...</span>
                </div>
            </div>
        );
    }

    if (error || !client) {
        return (
            <div className="page client-detail">
                <header className="page-header">
                    <button className="back-btn" onClick={() => navigate('/clients')}>
                        <ArrowLeft size={20} />
                    </button>
                    <h1 className="page-title">Błąd</h1>
                </header>
                <GlassCard className="error-card">
                    <AlertCircle size={48} />
                    <p>{error || 'Nie znaleziono klienta'}</p>
                    <button className="btn btn-primary" onClick={() => navigate('/clients')}>
                        Wróć do listy
                    </button>
                </GlassCard>
            </div>
        );
    }

    const bmi = calculateBMI();
    const bmiCategory = getBMICategory(bmi);
    const trend = getWeightTrend();
    const weightChange = getWeightChange();

    return (
        <div className="page client-detail">
            <header className="page-header">
                <button className="back-btn" onClick={() => navigate('/clients')}>
                    <ArrowLeft size={20} />
                </button>
                <h1 className="page-title">Profil klienta</h1>
                {!editing ? (
                    <button className="edit-btn" onClick={() => setEditing(true)}>
                        <Edit3 size={18} />
                    </button>
                ) : (
                    <div className="edit-actions">
                        <button className="cancel-btn" onClick={() => setEditing(false)}>
                            <X size={18} />
                        </button>
                        <button className="save-btn" onClick={handleSave} disabled={saving}>
                            <Save size={18} />
                        </button>
                    </div>
                )}
            </header>

            {/* Client Header */}
            <GlassCard className="client-header-card" glow>
                <div className="client-avatar-large">
                    {getInitials(client.name)}
                </div>
                <div className="client-header-info">
                    <h2>{client.name}</h2>
                    <p>{client.email}</p>
                    <span className="client-since">
                        <Calendar size={14} />
                        Od: {new Date(client.created_at).toLocaleDateString('pl-PL')}
                    </span>
                </div>
            </GlassCard>

            {/* Stats Grid */}
            <section className="section">
                <h3 className="section-title">Dane</h3>
                <div className="stats-grid">
                    <GlassCard className="stat-card">
                        <div className="stat-icon">
                            <Calendar size={20} />
                        </div>
                        {editing ? (
                            <input
                                type="number"
                                className="stat-input"
                                value={editData.age}
                                onChange={(e) => setEditData({...editData, age: e.target.value})}
                                placeholder="Wiek"
                            />
                        ) : (
                            <span className="stat-value">{client.profile?.age || '-'}</span>
                        )}
                        <span className="stat-label">Wiek</span>
                    </GlassCard>

                    <GlassCard className="stat-card">
                        <div className="stat-icon">
                            <Scale size={20} />
                        </div>
                        {editing ? (
                            <input
                                type="number"
                                step="0.1"
                                className="stat-input"
                                value={editData.weight}
                                onChange={(e) => setEditData({...editData, weight: e.target.value})}
                                placeholder="Waga"
                            />
                        ) : (
                            <span className="stat-value">
                                {client.profile?.weight ? `${client.profile.weight} kg` : '-'}
                            </span>
                        )}
                        <span className="stat-label">Waga</span>
                    </GlassCard>

                    <GlassCard className="stat-card">
                        <div className="stat-icon">
                            <Ruler size={20} />
                        </div>
                        {editing ? (
                            <input
                                type="number"
                                className="stat-input"
                                value={editData.height}
                                onChange={(e) => setEditData({...editData, height: e.target.value})}
                                placeholder="Wzrost"
                            />
                        ) : (
                            <span className="stat-value">
                                {client.profile?.height ? `${client.profile.height} cm` : '-'}
                            </span>
                        )}
                        <span className="stat-label">Wzrost</span>
                    </GlassCard>

                    <GlassCard className="stat-card">
                        <div className="stat-icon">
                            <User size={20} />
                        </div>
                        <span className="stat-value">{bmi || '-'}</span>
                        <span className="stat-label">
                            BMI
                            {bmiCategory && (
                                <span className="bmi-badge" style={{ color: bmiCategory.color }}>
                                    {bmiCategory.label}
                                </span>
                            )}
                        </span>
                    </GlassCard>
                </div>
            </section>

            {/* Goal */}
            <section className="section">
                <h3 className="section-title">
                    <Target size={18} />
                    Cel treningowy
                </h3>
                <GlassCard className="goal-card">
                    {editing ? (
                        <textarea
                            className="goal-input"
                            value={editData.goals}
                            onChange={(e) => setEditData({...editData, goals: e.target.value})}
                            placeholder="Opisz cel klienta..."
                            rows={3}
                        />
                    ) : (
                        <p className="goal-text">
                            {client.profile?.goals || 'Brak zdefiniowanego celu'}
                        </p>
                    )}
                </GlassCard>
            </section>

            {/* Progress Chart */}
            <section className="section">
                <h3 className="section-title">
                    <TrendingUp size={18} />
                    Postęp wagi
                </h3>
                <GlassCard className="progress-card">
                    <div className="progress-summary">
                        <div className={`trend-indicator trend-${trend}`}>
                            {trend === 'down' && <TrendingDown size={24} />}
                            {trend === 'up' && <TrendingUp size={24} />}
                            {trend === 'stable' && <Minus size={24} />}
                        </div>
                        <div className="trend-info">
                            <span className="trend-value">{weightChange > 0 ? '+' : ''}{weightChange} kg</span>
                            <span className="trend-label">ostatnie 4 tygodnie</span>
                        </div>
                    </div>

                    <div className="progress-chart">
                        <div className="chart-bars">
                            {progressData.map((point, index) => {
                                const maxWeight = Math.max(...progressData.map(p => p.weight));
                                const minWeight = Math.min(...progressData.map(p => p.weight));
                                const range = maxWeight - minWeight || 1;
                                const height = 30 + ((point.weight - minWeight) / range) * 70;
                                return (
                                    <div key={index} className="chart-bar-wrapper">
                                        <div
                                            className="chart-bar"
                                            style={{ height: `${height}%` }}
                                        >
                                            <span className="bar-value">{point.weight}</span>
                                        </div>
                                        <span className="bar-label">{point.date}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </GlassCard>
            </section>

            {/* Trainer Notes */}
            <section className="section">
                <h3 className="section-title">
                    <Edit3 size={18} />
                    Notatki trenera
                </h3>
                <GlassCard className="notes-card">
                    {editing ? (
                        <textarea
                            className="notes-input"
                            value={editData.trainer_notes}
                            onChange={(e) => setEditData({...editData, trainer_notes: e.target.value})}
                            placeholder="Dodaj notatki o kliencie..."
                            rows={4}
                        />
                    ) : (
                        <p className="notes-text">
                            {client.profile?.trainer_notes || 'Brak notatek'}
                        </p>
                    )}
                </GlassCard>
            </section>

            {/* Quick Actions */}
            <section className="section">
                <h3 className="section-title">Szybkie akcje</h3>
                <div className="actions-grid">
                    <GlassCard className="action-card" onClick={() => navigate('/coach')}>
                        <Dumbbell size={24} />
                        <span>Generuj trening</span>
                    </GlassCard>
                    <GlassCard className="action-card" onClick={() => navigate('/coach')}>
                        <MessageCircle size={24} />
                        <span>Wyślij wiadomość</span>
                    </GlassCard>
                </div>
            </section>
        </div>
    );
}

export default ClientDetail;
