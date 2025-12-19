
import { GoogleGenAI } from "@google/genai";

const SYSTEM_INSTRUCTION = `
Jesteś prywatnym, technicznym asystentem Trenera Personalnego. Twoim zadaniem jest dostarczanie konkretnych, merytorycznych rozwiązań w formie "Raportów Operacyjnych".

ZASADY FORMATOWANIA (KRYTYCZNE):
1. KAŻDA ODPOWIEDŹ musi zaczynać się od głównego nagłówka Markdown (#) opisującego zawartość (np. # PLAN TRENINGOWY - MARCIN).
2. Używaj separatorów sekcji (---) pomiędzy różnymi blokami informacji (np. między treningiem a dietą).
3. Sekcje podrzędne oznaczaj nagłówkami drugiego stopnia (##).
4. Dane liczbowe, serie i powtórzenia MUSZĄ być w tabelach Markdown.
5. Ważne parametry (RPE, Tempo) pogrubiaj.
6. Brak zbędnych wstępów i zakończeń typu "Mam nadzieję, że pomogłem".

STRUKTURA WYMAGANA:
# [TYTUŁ OPERACJI]
[Krótki opis celu/kontekstu]

---
## [SEKCJA 1: np. ROZGRZEWKA]
- Lista punktowana

---
## [SEKCJA 2: np. CZĘŚĆ GŁÓWNA]
| Ćwiczenie | Serie | Powtórzenia | Uwagi |
| :--- | :--- | :--- | :--- |
| ... | ... | ... | ... |

---
## [SEKCJA 3: PODSUMOWANIE / ZALECENIA]
- Konkretne kroki
`;

export const getGeminiResponse = async (prompt: string, history: { role: 'user' | 'model', parts: { text: string }[] }[] = []) => {
  try {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
    
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: [
        ...history.map(h => ({ role: h.role, parts: h.parts })),
        { role: 'user', parts: [{ text: prompt }] }
      ],
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        temperature: 0.3, // Niższa temperatura dla jeszcze większej spójności formatowania
        topP: 0.8,
      },
    });

    return response.text || "Błąd generowania danych.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Błąd połączenia z modułem AI. Sprawdź konfigurację klucza.";
  }
};
