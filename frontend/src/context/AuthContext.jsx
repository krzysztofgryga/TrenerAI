/**
 * Authentication Context for TrenerAI
 * Provides global auth state and functions
 */
import { createContext, useContext, useState, useEffect } from 'react';
import {
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser,
  getStoredUser,
  isLoggedIn as checkIsLoggedIn,
  getMyProfile
} from '../services/backendService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (checkIsLoggedIn()) {
        try {
          const userData = await getCurrentUser();
          if (userData) {
            setUser(userData);
            // Fetch profile if client
            if (userData.role === 'client') {
              const profileData = await getMyProfile();
              setProfile(profileData);
            }
          }
        } catch (err) {
          console.error('Auth check failed:', err);
          apiLogout();
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiLogin(email, password);
      setUser(data.user);
      if (data.user?.role === 'client') {
        const profileData = await getMyProfile();
        setProfile(profileData);
      }
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, name, role = 'client') => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiRegister(email, password, name, role);
      // After registration, fetch full user data
      const userData = await getCurrentUser();
      setUser(userData);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    apiLogout();
    setUser(null);
    setProfile(null);
  };

  const refreshUser = async () => {
    const userData = await getCurrentUser();
    setUser(userData);
    if (userData?.role === 'client') {
      const profileData = await getMyProfile();
      setProfile(profileData);
    }
  };

  const value = {
    user,
    profile,
    loading,
    error,
    isAuthenticated: !!user,
    isTrainer: user?.role === 'trainer',
    isClient: user?.role === 'client',
    login,
    register,
    logout,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
