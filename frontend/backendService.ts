import { Client, SavedWorkout } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export const getChatResponse = async (
  message: string,
  history: ChatMessage[] = []
): Promise<string> => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
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
    return 'Błąd połączenia z backendem. Sprawdź czy serwer działa (uvicorn app.main:app).';
  }
};

// Client API
export const getClients = async (): Promise<Client[]> => {
  try {
    const response = await fetch(`${API_URL}/clients`);
    if (!response.ok) throw new Error('Failed to fetch clients');
    return await response.json();
  } catch (error) {
    console.error('Error fetching clients:', error);
    return [];
  }
};

export const addClient = async (client: Client): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/clients`, {
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

export const updateClient = async (client: Client): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/clients/${client.id}`, {
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

export const deleteClient = async (clientId: string): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/clients/${clientId}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Error deleting client:', error);
    return false;
  }
};

// Workouts API
export const getWorkouts = async (): Promise<SavedWorkout[]> => {
  try {
    const response = await fetch(`${API_URL}/workouts`);
    if (!response.ok) throw new Error('Failed to fetch workouts');
    return await response.json();
  } catch (error) {
    console.error('Error fetching workouts:', error);
    return [];
  }
};

export const addWorkout = async (workout: SavedWorkout): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/workouts`, {
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

export const deleteWorkout = async (workoutId: string): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/workouts/${workoutId}`, {
      method: 'DELETE',
    });
    return response.ok;
  } catch (error) {
    console.error('Error deleting workout:', error);
    return false;
  }
};
