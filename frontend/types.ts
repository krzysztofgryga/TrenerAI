
export interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: number;
}

export interface SavedWorkout {
  id: string;
  title: string;
  content: string;
  date: string;
  color?: string;
}

export interface ProgressEntry {
  id: string;
  date: string;
  weight: number;
  bodyFat?: number;
  waist?: number;
  notes?: string;
}

export interface Client {
  id: string;
  name: string;
  age: number;
  weight: number;
  goal: string;
  notes: string;
  createdAt: string;
  progress: ProgressEntry[];
}

export enum AppView {
  CHAT = 'chat',
  SAVED = 'saved',
  CLIENTS = 'clients',
  SETTINGS = 'settings'
}
