/**
 * Backend API Service for TrenerAI
 * Connects frontend to FastAPI backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Send chat message to AI Coach
 * @param {string} message - User message
 * @param {Array<{role: string, content: string}>} history - Chat history
 * @returns {Promise<string>} AI response
 */
export const getChatResponse = async (message, history = []) => {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    console.error('Backend API Error:', error);
    throw new Error('Błąd połączenia z backendem. Sprawdź czy serwer działa.');
  }
};

/**
 * Get all clients
 * @returns {Promise<Array>} List of clients
 */
export const getClients = async () => {
  try {
    const response = await fetch(`${API_URL}/api/clients`);
    if (!response.ok) throw new Error('Failed to fetch clients');
    return await response.json();
  } catch (error) {
    console.error('Error fetching clients:', error);
    return [];
  }
};

/**
 * Add new client
 * @param {Object} client - Client data
 * @returns {Promise<boolean>} Success status
 */
export const addClient = async (client) => {
  try {
    const response = await fetch(`${API_URL}/api/clients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client),
    });
    return response.ok;
  } catch (error) {
    console.error('Error adding client:', error);
    return false;
  }
};

/**
 * Update existing client
 * @param {Object} client - Client data with id
 * @returns {Promise<boolean>} Success status
 */
export const updateClient = async (client) => {
  try {
    const response = await fetch(`${API_URL}/api/clients/${client.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client),
    });
    return response.ok;
  } catch (error) {
    console.error('Error updating client:', error);
    return false;
  }
};

/**
 * Delete client
 * @param {string} clientId - Client ID
 * @returns {Promise<boolean>} Success status
 */
export const deleteClient = async (clientId) => {
  try {
    const response = await fetch(`${API_URL}/api/clients/${clientId}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Error deleting client:', error);
    return false;
  }
};

/**
 * Get all saved workouts
 * @returns {Promise<Array>} List of workouts
 */
export const getWorkouts = async () => {
  try {
    const response = await fetch(`${API_URL}/api/workouts`);
    if (!response.ok) throw new Error('Failed to fetch workouts');
    return await response.json();
  } catch (error) {
    console.error('Error fetching workouts:', error);
    return [];
  }
};

/**
 * Save new workout
 * @param {Object} workout - Workout data
 * @returns {Promise<boolean>} Success status
 */
export const addWorkout = async (workout) => {
  try {
    const response = await fetch(`${API_URL}/api/workouts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workout),
    });
    return response.ok;
  } catch (error) {
    console.error('Error adding workout:', error);
    return false;
  }
};

/**
 * Delete workout
 * @param {string} workoutId - Workout ID
 * @returns {Promise<boolean>} Success status
 */
export const deleteWorkout = async (workoutId) => {
  try {
    const response = await fetch(`${API_URL}/api/workouts/${workoutId}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Error deleting workout:', error);
    return false;
  }
};

/**
 * Generate training plan
 * @param {Object} params - Training parameters
 * @returns {Promise<Object>} Generated training plan
 */
export const generateTrainingPlan = async (params) => {
  try {
    const response = await fetch(`${API_URL}/api/trainings/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Failed to generate plan');
    return await response.json();
  } catch (error) {
    console.error('Error generating training plan:', error);
    throw error;
  }
};

/**
 * Get user profile
 * @param {string} userId - User ID (default: 'default')
 * @returns {Promise<Object>} User profile
 */
export const getUserProfile = async (userId = 'default') => {
  try {
    const response = await fetch(`${API_URL}/api/users/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch profile');
    return await response.json();
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }
};

/**
 * Update user profile
 * @param {string} userId - User ID
 * @param {Object} profile - Profile data
 * @returns {Promise<boolean>} Success status
 */
export const updateUserProfile = async (userId, profile) => {
  try {
    const response = await fetch(`${API_URL}/api/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    return response.ok;
  } catch (error) {
    console.error('Error updating profile:', error);
    return false;
  }
};
