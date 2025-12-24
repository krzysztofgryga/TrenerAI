import { useState, useEffect } from 'react';
import { Palette } from 'lucide-react';
import './ThemeSwitcher.css';

function ThemeSwitcher() {
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme') || 'purple';
    });
    const [isOpen, setIsOpen] = useState(false);

    const themes = [
        { id: 'purple', name: 'Fioletowy', colors: ['#a855f7', '#ec4899', '#22d3ee'] },
        { id: 'gold', name: 'Złoto-Czarny', colors: ['#fbbf24', '#f59e0b', '#eab308'] },
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
        setIsOpen(false);
    };

    return (
        <div className="theme-switcher">
            <button
                className="theme-switcher-btn"
                onClick={() => setIsOpen(!isOpen)}
                aria-label="Zmień motyw"
            >
                <Palette size={20} />
            </button>

            {isOpen && (
                <div className="theme-menu">
                    <div className="theme-menu-header">Wybierz motyw</div>
                    {themes.map((t) => (
                        <button
                            key={t.id}
                            className={`theme-option ${theme === t.id ? 'theme-option--active' : ''}`}
                            onClick={() => handleThemeChange(t.id)}
                        >
                            <div className="theme-colors">
                                {t.colors.map((color, index) => (
                                    <span
                                        key={index}
                                        className="theme-color-dot"
                                        style={{ backgroundColor: color }}
                                    />
                                ))}
                            </div>
                            <span className="theme-name">{t.name}</span>
                            {theme === t.id && <span className="theme-check">✓</span>}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ThemeSwitcher;
