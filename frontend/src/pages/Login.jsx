import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, Loader2, Dumbbell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GlassCard from '../components/GlassCard';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const { login, register, loading, error } = useAuth();

  const [isLoginMode, setIsLoginMode] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'client'
  });
  const [formError, setFormError] = useState('');

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    setFormError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    try {
      if (isLoginMode) {
        await login(formData.email, formData.password);
      } else {
        if (!formData.name.trim()) {
          setFormError('Podaj swoje imię');
          return;
        }
        await register(formData.email, formData.password, formData.name, formData.role);
      }
      navigate('/');
    } catch (err) {
      setFormError(err.message);
    }
  };

  const toggleMode = () => {
    setIsLoginMode(prev => !prev);
    setFormError('');
  };

  return (
    <div className="page login-page">
      {/* Logo */}
      <div className="login-logo">
        <div className="logo-icon">
          <Dumbbell size={40} />
        </div>
        <h1 className="logo-text">TrenerAI</h1>
        <p className="logo-subtitle">Twój osobisty AI trener</p>
      </div>

      {/* Login Form */}
      <GlassCard className="login-card" glow>
        <h2 className="login-title">
          {isLoginMode ? 'Zaloguj się' : 'Załóż konto'}
        </h2>

        <form onSubmit={handleSubmit} className="login-form">
          {/* Name field (register only) */}
          {!isLoginMode && (
            <div className="form-group">
              <div className="input-icon">
                <User size={20} />
              </div>
              <input
                type="text"
                name="name"
                placeholder="Twoje imię"
                value={formData.name}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          )}

          {/* Email */}
          <div className="form-group">
            <div className="input-icon">
              <Mail size={20} />
            </div>
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>

          {/* Password */}
          <div className="form-group">
            <div className="input-icon">
              <Lock size={20} />
            </div>
            <input
              type="password"
              name="password"
              placeholder="Hasło"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={6}
              className="form-input"
            />
          </div>

          {/* Role selector (register only) */}
          {!isLoginMode && (
            <div className="role-selector">
              <button
                type="button"
                className={`role-btn ${formData.role === 'client' ? 'role-btn--active' : ''}`}
                onClick={() => setFormData(prev => ({ ...prev, role: 'client' }))}
              >
                Klient
              </button>
              <button
                type="button"
                className={`role-btn ${formData.role === 'trainer' ? 'role-btn--active' : ''}`}
                onClick={() => setFormData(prev => ({ ...prev, role: 'trainer' }))}
              >
                Trener
              </button>
            </div>
          )}

          {/* Error message */}
          {(formError || error) && (
            <div className="form-error">
              {formError || error}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            className="btn btn-primary login-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={20} className="spinning" />
                Proszę czekać...
              </>
            ) : (
              isLoginMode ? 'Zaloguj się' : 'Zarejestruj się'
            )}
          </button>
        </form>

        {/* Toggle mode */}
        <div className="login-toggle">
          <span>
            {isLoginMode ? 'Nie masz konta?' : 'Masz już konto?'}
          </span>
          <button onClick={toggleMode} className="toggle-btn">
            {isLoginMode ? 'Zarejestruj się' : 'Zaloguj się'}
          </button>
        </div>
      </GlassCard>

      {/* Demo info */}
      <p className="demo-info">
        Demo: użyj dowolnego email/hasła aby się zarejestrować
      </p>
    </div>
  );
}

export default Login;
