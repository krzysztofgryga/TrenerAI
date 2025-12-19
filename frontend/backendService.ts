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
