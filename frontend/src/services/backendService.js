/**
 * Backend API Service for TrenerAI
 * Connects frontend to FastAPI backend with JWT authentication
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// =============================================================================
// TOKEN MANAGEMENT
// =============================================================================

const TOKEN_KEY = 'trenerai_token';
const USER_KEY = 'trenerai_user';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const removeToken = () => localStorage.removeItem(TOKEN_KEY);

export const getStoredUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};
export const setStoredUser = (user) => localStorage.setItem(USER_KEY, JSON.stringify(user));
export const removeStoredUser = () => localStorage.removeItem(USER_KEY);

export const isLoggedIn = () => !!getToken();

// =============================================================================
// HTTP HELPERS
// =============================================================================

const authHeaders = () => {
  const token = getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const apiRequest = async (endpoint, options = {}) => {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    // Token expired - logout
    logout();
    throw new Error('Sesja wygasła. Zaloguj się ponownie.');
  }

  return response;
};

// =============================================================================
// AUTHENTICATION
// =============================================================================

/**
 * Register new user
 */
export const register = async (email, password, name, role = 'client') => {
  try {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Błąd rejestracji');
    }

    const data = await response.json();
    setToken(data.access_token);
    setStoredUser({ id: data.user_id, role: data.role, email, name });
    return data;
  } catch (error) {
    console.error('Register error:', error);
    throw error;
  }
};

/**
 * Login user
 */
export const login = async (email, password) => {
  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Nieprawidłowy email lub hasło');
    }

    const data = await response.json();
    setToken(data.access_token);

    // Fetch full user data
    const user = await getCurrentUser();
    return { ...data, user };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Logout user
 */
export const logout = () => {
  removeToken();
  removeStoredUser();
};

/**
 * Get current user info
 */
export const getCurrentUser = async () => {
  try {
    const response = await apiRequest('/api/auth/me');
    if (!response.ok) throw new Error('Not authenticated');
    const user = await response.json();
    setStoredUser(user);
    return user;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
};

/**
 * Get current user's profile (for clients)
 */
export const getMyProfile = async () => {
  try {
    const response = await apiRequest('/api/auth/me/profile');
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Get profile error:', error);
    return null;
  }
};

/**
 * Update current user's profile
 */
export const updateMyProfile = async (profileData) => {
  try {
    const response = await apiRequest('/api/auth/me/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
    return response.ok;
  } catch (error) {
    console.error('Update profile error:', error);
    return false;
  }
};

// =============================================================================
// TRAINER ENDPOINTS
// =============================================================================

/**
 * Get trainer dashboard
 */
export const getTrainerDashboard = async () => {
  try {
    const response = await apiRequest('/api/trainer/dashboard');
    if (!response.ok) throw new Error('Failed to fetch dashboard');
    return await response.json();
  } catch (error) {
    console.error('Dashboard error:', error);
    return null;
  }
};

/**
 * Get trainer's clients
 */
export const getTrainerClients = async () => {
  try {
    const response = await apiRequest('/api/trainer/clients');
    if (!response.ok) throw new Error('Failed to fetch clients');
    return await response.json();
  } catch (error) {
    console.error('Get clients error:', error);
    return [];
  }
};

/**
 * Add client to trainer
 */
export const addTrainerClient = async (clientId, permissions = {}) => {
  try {
    const response = await apiRequest('/api/trainer/clients', {
      method: 'POST',
      body: JSON.stringify({
        client_id: clientId,
        can_generate_training: permissions.canGenerate || false,
        can_view_history: permissions.canViewHistory || true,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Błąd dodawania klienta');
    }
    return await response.json();
  } catch (error) {
    console.error('Add client error:', error);
    throw error;
  }
};

/**
 * Get trainer's groups
 */
export const getTrainerGroups = async () => {
  try {
    const response = await apiRequest('/api/trainer/groups');
    if (!response.ok) throw new Error('Failed to fetch groups');
    return await response.json();
  } catch (error) {
    console.error('Get groups error:', error);
    return [];
  }
};

/**
 * Create new group
 */
export const createGroup = async (name, description = '') => {
  try {
    const response = await apiRequest('/api/trainer/groups', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
    if (!response.ok) throw new Error('Failed to create group');
    return await response.json();
  } catch (error) {
    console.error('Create group error:', error);
    throw error;
  }
};

// =============================================================================
// CHAT
// =============================================================================

/**
 * Send chat message to AI Coach
 */
export const getChatResponse = async (message, history = []) => {
  try {
    const response = await apiRequest('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history: history.map(h => ({
          role: h.role === 'model' ? 'assistant' : h.role,
          content: h.content
        }))
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.response || 'Błąd generowania odpowiedzi.';
  } catch (error) {
    console.error('Chat error:', error);
    throw new Error('Błąd połączenia z backendem.');
  }
};

/**
 * Get chat history for current user
 */
export const getChatHistory = async (limit = 100, offset = 0) => {
  try {
    const response = await apiRequest(`/api/chat/history?limit=${limit}&offset=${offset}`);
    if (!response.ok) {
      if (response.status === 401) return { messages: [], total: 0 };
      throw new Error('Failed to fetch chat history');
    }
    return await response.json();
  } catch (error) {
    console.error('Get chat history error:', error);
    return { messages: [], total: 0 };
  }
};

/**
 * Clear chat history for current user
 */
export const clearChatHistory = async () => {
  try {
    const response = await apiRequest('/api/chat/history', {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Clear chat history error:', error);
    return false;
  }
};

// =============================================================================
// WORKOUTS
// =============================================================================

/**
 * Get all saved workouts
 */
export const getWorkouts = async () => {
  try {
    const response = await apiRequest('/api/workouts');
    if (!response.ok) throw new Error('Failed to fetch workouts');
    return await response.json();
  } catch (error) {
    console.error('Get workouts error:', error);
    return [];
  }
};

/**
 * Save new workout
 */
export const addWorkout = async (workout) => {
  try {
    const response = await apiRequest('/api/workouts', {
      method: 'POST',
      body: JSON.stringify(workout),
    });
    return response.ok;
  } catch (error) {
    console.error('Add workout error:', error);
    return false;
  }
};

/**
 * Delete workout
 */
export const deleteWorkout = async (workoutId) => {
  try {
    const response = await apiRequest(`/api/workouts/${workoutId}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Delete workout error:', error);
    return false;
  }
};

// =============================================================================
// TRAINING GENERATION
// =============================================================================

/**
 * Generate training plan
 */
export const generateTrainingPlan = async (params) => {
  try {
    const response = await apiRequest('/api/trainings/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Failed to generate plan');
    return await response.json();
  } catch (error) {
    console.error('Generate training error:', error);
    throw error;
  }
};

/**
 * Get training history
 */
export const getTrainingHistory = async () => {
  try {
    const response = await apiRequest('/api/trainings/history');
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    console.error('Get history error:', error);
    return [];
  }
};

// =============================================================================
// INVITATIONS
// =============================================================================

/**
 * Generate invitation code (trainers only)
 */
export const generateInvitationCode = async (expiresHours = 24) => {
  try {
    const response = await apiRequest('/api/invitations/generate', {
      method: 'POST',
      body: JSON.stringify({ expires_hours: expiresHours }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Błąd generowania kodu');
    }
    return await response.json();
  } catch (error) {
    console.error('Generate invitation error:', error);
    throw error;
  }
};

/**
 * Join trainer using invitation code (clients only)
 */
export const joinTrainer = async (code) => {
  try {
    const response = await apiRequest('/api/invitations/join', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Nieprawidłowy kod');
    }
    return await response.json();
  } catch (error) {
    console.error('Join trainer error:', error);
    throw error;
  }
};

/**
 * Get my invitations (trainers only)
 */
export const getMyInvitations = async () => {
  try {
    const response = await apiRequest('/api/invitations/my');
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    console.error('Get invitations error:', error);
    return [];
  }
};

/**
 * Delete invitation code (trainers only)
 */
export const deleteInvitation = async (code) => {
  try {
    const response = await apiRequest(`/api/invitations/${code}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Delete invitation error:', error);
    return false;
  }
};

// =============================================================================
// LEGACY CLIENTS (JSON storage)
// =============================================================================

export const getClients = async () => {
  try {
    const response = await fetch(`${API_URL}/clients`);
    if (!response.ok) throw new Error('Failed to fetch clients');
    return await response.json();
  } catch (error) {
    console.error('Get clients error:', error);
    return [];
  }
};

export const addClient = async (client) => {
  try {
    const response = await fetch(`${API_URL}/clients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client),
    });
    return response.ok;
  } catch (error) {
    console.error('Add client error:', error);
    return false;
  }
};
