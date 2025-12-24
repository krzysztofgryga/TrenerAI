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
    Target
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import './Profile.css';

function Profile() {
    const user = {
        name: 'Kamil Gryga',
        email: 'kamil@example.com',
        initials: 'KG',
        memberSince: 'Grudzień 2024',
        level: 'Pro Athlete'
    };

    const weeklyStats = [
        { label: 'Treningi', value: '5', icon: Calendar },
        { label: 'Kalorie', value: '2,450', icon: Flame },
        { label: 'Cel', value: '85%', icon: Target },
        { label: 'Streak', value: '12', icon: Trophy },
    ];

    const menuItems = [
        { icon: Settings, label: 'Ustawienia', description: 'Preferencje aplikacji' },
        { icon: Bell, label: 'Powiadomienia', description: 'Zarządzaj alertami' },
        { icon: Shield, label: 'Prywatność', description: 'Twoje dane i bezpieczeństwo' },
        { icon: HelpCircle, label: 'Pomoc', description: 'FAQ i wsparcie' },
    ];

    return (
        <div className="page profile">
            <header className="page-header">
                <h1 className="page-title">Profil</h1>
            </header>

            {/* Profile Card */}
            <GlassCard className="profile-card" glow>
                <div className="profile-header">
                    <div className="profile-avatar">
                        {user.initials}
                    </div>
                    <div className="profile-info">
                        <h2 className="profile-name">{user.name}</h2>
                        <p className="profile-email">{user.email}</p>
                        <span className="profile-badge">{user.level}</span>
                    </div>
                </div>
                <div className="profile-meta">
                    <span>Członek od: {user.memberSince}</span>
                </div>
            </GlassCard>

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
            <button className="logout-btn">
                <LogOut size={18} />
                Wyloguj się
            </button>
        </div>
    );
}

export default Profile;
