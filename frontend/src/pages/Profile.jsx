import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Settings,
    Bell,
    Shield,
    HelpCircle,
    LogOut,
    ChevronRight,
    Trophy,
    Flame,
    Calendar,
    Target,
    UserCircle,
    Users,
    UserPlus,
    Check,
    X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { joinTrainer } from '../services/backendService';
import GlassCard from '../components/GlassCard';
import './Profile.css';

function Profile() {
    const navigate = useNavigate();
    const { user, profile, logout, isTrainer } = useAuth();

    // Join trainer state (for clients)
    const [joinCode, setJoinCode] = useState('');
    const [joining, setJoining] = useState(false);
    const [joinResult, setJoinResult] = useState(null);
    const [joinError, setJoinError] = useState(null);

    // Handle join trainer
    const handleJoinTrainer = async (e) => {
        e.preventDefault();
        if (!joinCode.trim()) return;

        setJoining(true);
        setJoinError(null);
        setJoinResult(null);

        try {
            const result = await joinTrainer(joinCode.trim());
            setJoinResult(result);
            setJoinCode('');
        } catch (err) {
            setJoinError(err.message);
        } finally {
            setJoining(false);
        }
    };

    // Generate initials from name
    const getInitials = (name) => {
        if (!name) return 'U';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    // Format member since date
    const getMemberSince = () => {
        if (!user?.created_at) return 'Nowy członek';
        const date = new Date(user.created_at);
        return date.toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' });
    };

    const weeklyStats = [
        { label: 'Treningi', value: profile?.training_count || '0', icon: Calendar },
        { label: 'Kalorie', value: profile?.calories_burned || '0', icon: Flame },
        { label: 'Cel', value: profile?.goal_progress || '0%', icon: Target },
        { label: 'Streak', value: profile?.streak_days || '0', icon: Trophy },
    ];

    const menuItems = [
        { icon: Settings, label: 'Ustawienia', description: 'Preferencje aplikacji' },
        { icon: Bell, label: 'Powiadomienia', description: 'Zarządzaj alertami' },
        { icon: Shield, label: 'Prywatność', description: 'Twoje dane i bezpieczeństwo' },
        { icon: HelpCircle, label: 'Pomoc', description: 'FAQ i wsparcie' },
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="page profile">
            <header className="page-header">
                <h1 className="page-title">Profil</h1>
            </header>

            {/* Profile Card */}
            <GlassCard className="profile-card" glow>
                <div className="profile-header">
                    <div className="profile-avatar">
                        {getInitials(user?.name)}
                    </div>
                    <div className="profile-info">
                        <h2 className="profile-name">{user?.name || 'Użytkownik'}</h2>
                        <p className="profile-email">{user?.email}</p>
                        <span className="profile-badge">
                            {isTrainer ? (
                                <><Users size={14} /> Trener</>
                            ) : (
                                <><UserCircle size={14} /> Klient</>
                            )}
                        </span>
                    </div>
                </div>
                <div className="profile-meta">
                    <span>Członek od: {getMemberSince()}</span>
                </div>
            </GlassCard>

            {/* Join Trainer Section (for clients only) */}
            {!isTrainer && (
                <section className="section">
                    <h2 className="section-title">
                        <UserPlus size={20} />
                        Dołącz do trenera
                    </h2>
                    <GlassCard className="join-trainer-card">
                        <p className="join-trainer-desc">
                            Masz kod zaproszenia od trenera? Wpisz go poniżej, aby dołączyć.
                        </p>

                        {joinResult && (
                            <div className="join-success">
                                <Check size={20} />
                                <span>{joinResult.message}</span>
                                <button
                                    className="join-close"
                                    onClick={() => setJoinResult(null)}
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {joinError && (
                            <div className="join-error">
                                <span>{joinError}</span>
                                <button
                                    className="join-close"
                                    onClick={() => setJoinError(null)}
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        <form className="join-form" onSubmit={handleJoinTrainer}>
                            <input
                                type="text"
                                className="join-input"
                                placeholder="Wpisz kod (np. ABC123)"
                                value={joinCode}
                                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                                maxLength={6}
                                disabled={joining}
                            />
                            <button
                                type="submit"
                                className="btn btn-primary join-btn"
                                disabled={joining || !joinCode.trim()}
                            >
                                {joining ? 'Dołączanie...' : 'Dołącz'}
                            </button>
                        </form>
                    </GlassCard>
                </section>
            )}

            {/* Client Profile Data */}
            {profile && (
                <section className="section">
                    <h2 className="section-title">Twoje dane</h2>
                    <GlassCard className="profile-data-card">
                        <div className="profile-data-grid">
                            {profile.age && (
                                <div className="profile-data-item">
                                    <span className="profile-data-label">Wiek</span>
                                    <span className="profile-data-value">{profile.age} lat</span>
                                </div>
                            )}
                            {profile.weight && (
                                <div className="profile-data-item">
                                    <span className="profile-data-label">Waga</span>
                                    <span className="profile-data-value">{profile.weight} kg</span>
                                </div>
                            )}
                            {profile.height && (
                                <div className="profile-data-item">
                                    <span className="profile-data-label">Wzrost</span>
                                    <span className="profile-data-value">{profile.height} cm</span>
                                </div>
                            )}
                            {profile.goal && (
                                <div className="profile-data-item profile-data-item--full">
                                    <span className="profile-data-label">Cel</span>
                                    <span className="profile-data-value">{profile.goal}</span>
                                </div>
                            )}
                        </div>
                    </GlassCard>
                </section>
            )}

            {/* Weekly Stats */}
            <section className="section">
                <h2 className="section-title">Statystyki tygodnia</h2>
                <div className="weekly-stats">
                    {weeklyStats.map(({ label, value, icon: Icon }) => (
                        <GlassCard key={label} className="weekly-stat-card">
                            <Icon size={20} className="weekly-stat-icon" />
                            <span className="weekly-stat-value">{value}</span>
                            <span className="weekly-stat-label">{label}</span>
                        </GlassCard>
                    ))}
                </div>
            </section>

            {/* Progress Chart Placeholder */}
            <section className="section">
                <h2 className="section-title">Postęp treningowy</h2>
                <GlassCard className="chart-card">
                    <div className="chart-placeholder">
                        <div className="chart-bars">
                            {[40, 65, 35, 80, 55, 90, 70].map((height, index) => (
                                <div
                                    key={index}
                                    className="chart-bar"
                                    style={{
                                        height: `${height}%`,
                                        animationDelay: `${index * 0.1}s`
                                    }}
                                />
                            ))}
                        </div>
                        <div className="chart-labels">
                            {['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'].map(day => (
                                <span key={day}>{day}</span>
                            ))}
                        </div>
                    </div>
                </GlassCard>
            </section>

            {/* Menu Items */}
            <section className="section">
                <h2 className="section-title">Ustawienia</h2>
                <div className="menu-list">
                    {menuItems.map(({ icon: Icon, label, description }) => (
                        <GlassCard key={label} className="menu-item" onClick={() => console.log(label)}>
                            <div className="menu-icon">
                                <Icon size={20} />
                            </div>
                            <div className="menu-content">
                                <span className="menu-label">{label}</span>
                                <span className="menu-desc">{description}</span>
                            </div>
                            <ChevronRight size={18} className="menu-arrow" />
                        </GlassCard>
                    ))}
                </div>
            </section>

            {/* Logout Button */}
            <button className="logout-btn" onClick={handleLogout}>
                <LogOut size={18} />
                Wyloguj się
            </button>
        </div>
    );
}

export default Profile;
