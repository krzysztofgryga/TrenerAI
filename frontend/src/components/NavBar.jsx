import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Dumbbell, MessageCircle, User, Settings, Bell, Shield, HelpCircle, ChevronRight } from 'lucide-react';
import './NavBar.css';

function NavBar() {
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme') || 'purple';
    });
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [activeSection, setActiveSection] = useState(null);

    const themes = [
        { id: 'purple', name: 'Fioletowy', colors: ['#a855f7', '#ec4899', '#22d3ee'] },
        { id: 'gold', name: 'Złoto-Czarny', colors: ['#fbbf24', '#f59e0b', '#eab308'] },
    ];

    const settingsSections = [
        { id: 'settings', icon: Settings, title: 'Ustawienia', subtitle: 'Preferencje aplikacji' },
        { id: 'notifications', icon: Bell, title: 'Powiadomienia', subtitle: 'Zarządzaj alertami' },
        { id: 'privacy', icon: Shield, title: 'Prywatność', subtitle: 'Twoje dane i bezpieczeństwo' },
        { id: 'help', icon: HelpCircle, title: 'Pomoc', subtitle: 'FAQ i wsparcie' },
    ];

    useEffect(() => {
        if (theme === 'purple') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        localStorage.setItem('theme', theme);
    }, [theme]);

    const handleThemeChange = (themeId) => {
        setTheme(themeId);
    };

    const handleSettingsToggle = () => {
        setIsSettingsOpen(!isSettingsOpen);
        setActiveSection(null);
    };

    const handleSectionClick = (sectionId) => {
        setActiveSection(activeSection === sectionId ? null : sectionId);
    };

    const navItems = [
        { path: '/', icon: Home, label: 'Home' },
        { path: '/workouts', icon: Dumbbell, label: 'Workouts' },
        { path: '/coach', icon: MessageCircle, label: 'AI Coach' },
        { path: '/profile', icon: User, label: 'Profile' },
    ];

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {navItems.map(({ path, icon: Icon, label }) => (
                    <NavLink
                        key={path}
                        to={path}
                        className={({ isActive }) =>
                            `navbar-item ${isActive ? 'navbar-item--active' : ''}`
                        }
                    >
                        <div className="navbar-icon">
                            <Icon size={24} strokeWidth={1.5} />
                        </div>
                        <span className="navbar-label">{label}</span>
                    </NavLink>
                ))}

                {/* Settings Tile */}
                <div className="navbar-settings-wrapper">
                    <button
                        className={`navbar-item navbar-settings-btn ${isSettingsOpen ? 'navbar-item--active' : ''}`}
                        onClick={handleSettingsToggle}
                    >
                        <div className="navbar-icon">
                            <Settings size={24} strokeWidth={1.5} />
                        </div>
                        <span className="navbar-label">Ustawienia</span>
                    </button>

                    {isSettingsOpen && (
                        <div className="settings-menu settings-menu--expanded">
                            <div className="settings-menu-header">Ustawienia</div>

                            {settingsSections.map(({ id, icon: Icon, title, subtitle }) => (
                                <div key={id} className="settings-section">
                                    <button
                                        className={`settings-section-btn ${activeSection === id ? 'settings-section-btn--active' : ''}`}
                                        onClick={() => handleSectionClick(id)}
                                    >
                                        <div className="settings-section-icon">
                                            <Icon size={22} strokeWidth={1.5} />
                                        </div>
                                        <div className="settings-section-text">
                                            <span className="settings-section-title">{title}</span>
                                            <span className="settings-section-subtitle">{subtitle}</span>
                                        </div>
                                        <ChevronRight
                                            size={20}
                                            className={`settings-section-arrow ${activeSection === id ? 'settings-section-arrow--rotated' : ''}`}
                                        />
                                    </button>

                                    {/* Theme Selection (inside Ustawienia section) */}
                                    {id === 'settings' && activeSection === 'settings' && (
                                        <div className="settings-subsection">
                                            <div className="settings-subsection-title">Wybierz motyw</div>
                                            {themes.map((t) => (
                                                <button
                                                    key={t.id}
                                                    className={`settings-option ${theme === t.id ? 'settings-option--active' : ''}`}
                                                    onClick={() => handleThemeChange(t.id)}
                                                >
                                                    <div className="settings-colors">
                                                        {t.colors.map((color, index) => (
                                                            <span
                                                                key={index}
                                                                className="settings-color-dot"
                                                                style={{ backgroundColor: color }}
                                                            />
                                                        ))}
                                                    </div>
                                                    <span className="settings-name">{t.name}</span>
                                                    {theme === t.id && <span className="settings-check">✓</span>}
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {/* Notifications Section */}
                                    {id === 'notifications' && activeSection === 'notifications' && (
                                        <div className="settings-subsection">
                                            <div className="settings-toggle-row">
                                                <span>Powiadomienia push</span>
                                                <label className="settings-toggle">
                                                    <input type="checkbox" defaultChecked />
                                                    <span className="settings-toggle-slider"></span>
                                                </label>
                                            </div>
                                            <div className="settings-toggle-row">
                                                <span>Przypomnienia o treningu</span>
                                                <label className="settings-toggle">
                                                    <input type="checkbox" defaultChecked />
                                                    <span className="settings-toggle-slider"></span>
                                                </label>
                                            </div>
                                            <div className="settings-toggle-row">
                                                <span>Porady AI Coach</span>
                                                <label className="settings-toggle">
                                                    <input type="checkbox" />
                                                    <span className="settings-toggle-slider"></span>
                                                </label>
                                            </div>
                                        </div>
                                    )}

                                    {/* Privacy Section */}
                                    {id === 'privacy' && activeSection === 'privacy' && (
                                        <div className="settings-subsection">
                                            <div className="settings-toggle-row">
                                                <span>Udostępniaj statystyki</span>
                                                <label className="settings-toggle">
                                                    <input type="checkbox" />
                                                    <span className="settings-toggle-slider"></span>
                                                </label>
                                            </div>
                                            <div className="settings-toggle-row">
                                                <span>Analityka użytkowania</span>
                                                <label className="settings-toggle">
                                                    <input type="checkbox" defaultChecked />
                                                    <span className="settings-toggle-slider"></span>
                                                </label>
                                            </div>
                                            <button className="settings-link-btn">
                                                Polityka prywatności
                                                <ChevronRight size={16} />
                                            </button>
                                        </div>
                                    )}

                                    {/* Help Section */}
                                    {id === 'help' && activeSection === 'help' && (
                                        <div className="settings-subsection">
                                            <button className="settings-link-btn">
                                                FAQ
                                                <ChevronRight size={16} />
                                            </button>
                                            <button className="settings-link-btn">
                                                Kontakt z supportem
                                                <ChevronRight size={16} />
                                            </button>
                                            <button className="settings-link-btn">
                                                Zgłoś problem
                                                <ChevronRight size={16} />
                                            </button>
                                            <div className="settings-version">
                                                Wersja aplikacji: 1.0.0
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}

export default NavBar;
