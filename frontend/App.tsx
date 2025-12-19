
import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SavedWorkouts from './components/SavedWorkouts';
import ClientsManager from './components/ClientsManager';
import { AppView, SavedWorkout, Client } from './types';
import * as api from './backendService';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<AppView>(AppView.CHAT);
  const [savedItems, setSavedItems] = useState<SavedWorkout[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({ message: '', visible: false });
  const [sharedWorkout, setSharedWorkout] = useState<SavedWorkout | null>(null);

  // Load data from backend on mount
  useEffect(() => {
    const loadData = async () => {
      const [workouts, clientsData] = await Promise.all([
        api.getWorkouts(),
        api.getClients()
      ]);
      setSavedItems(workouts);
      setClients(clientsData);
    };
    loadData();

    const params = new URLSearchParams(window.location.search);
    const shareId = params.get('share');
    if (shareId) {
      const sharedCache = JSON.parse(localStorage.getItem('fitcoach_shared_cache') || '{}');
      if (sharedCache[shareId]) {
        setSharedWorkout(sharedCache[shareId]);
      }
    }
  }, []);

  const showToast = (message: string) => {
    setToast({ message, visible: true });
    setTimeout(() => {
      setToast(prev => ({ ...prev, visible: false }));
    }, 3000);
  };

  const handleSaveWorkout = async (title: string, content: string) => {
    const newItem: SavedWorkout = {
      id: Date.now().toString(),
      title,
      content,
      date: new Date().toLocaleDateString('pl-PL'),
      color: '#3b82f6'
    };
    await api.addWorkout(newItem);
    setSavedItems(prev => [newItem, ...prev]);
    showToast("Plan został zapisany!");
  };

  const handleUpdateWorkout = (updatedItem: SavedWorkout) => {
    setSavedItems(prev => prev.map(item => item.id === updatedItem.id ? updatedItem : item));
    showToast("Zmiany zapisane.");
  };

  const handleDeleteSaved = async (id: string) => {
    await api.deleteWorkout(id);
    setSavedItems(prev => prev.filter(item => item.id !== id));
    showToast("Plan usunięty.");
  };

  const handleAddClient = async (client: Client) => {
    await api.addClient(client);
    setClients(prev => [client, ...prev]);
    showToast("Dodano podopiecznego.");
  };

  const handleUpdateClient = async (updatedClient: Client) => {
    await api.updateClient(updatedClient);
    setClients(prev => prev.map(c => c.id === updatedClient.id ? updatedClient : c));
    showToast("Dane zaktualizowane.");
  };

  const handleDeleteClient = async (id: string) => {
    await api.deleteClient(id);
    setClients(prev => prev.filter(c => c.id !== id));
    showToast("Usunięto z bazy.");
  };

  const closeSharedView = () => {
    setSharedWorkout(null);
    const url = new URL(window.location.href);
    url.searchParams.delete('share');
    window.history.replaceState({}, '', url);
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Toast Notification */}
      <div className={`fixed top-6 left-1/2 -translate-x-1/2 md:left-auto md:right-6 md:translate-x-0 z-[100] transition-all duration-500 transform ${toast.visible ? 'translate-y-0 opacity-100' : '-translate-y-24 opacity-0 pointer-events-none'}`}>
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3 rounded-full md:rounded-2xl shadow-2xl flex items-center gap-3 border border-white/10">
          <i className="fas fa-check text-xs text-white"></i>
          <span className="font-bold text-xs md:text-sm whitespace-nowrap">{toast.message}</span>
        </div>
      </div>

      {/* Shared View Modal */}
      {sharedWorkout && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-950/95 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="glass-effect w-full max-w-2xl rounded-[2.5rem] overflow-hidden shadow-2xl border-white/5">
            <div className="p-6 md:p-8 border-b border-slate-800 flex justify-between items-center bg-blue-600/5">
              <h2 className="text-xl font-bold">{sharedWorkout.title}</h2>
              <button onClick={closeSharedView} className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/5"><i className="fas fa-times"></i></button>
            </div>
            <div className="p-8 max-h-[50vh] overflow-y-auto whitespace-pre-wrap text-slate-300 text-sm leading-relaxed scrollbar-hide">
              {sharedWorkout.content}
            </div>
            <div className="p-8 border-t border-slate-800 flex flex-col sm:flex-row gap-3">
              <button 
                onClick={() => { handleSaveWorkout(sharedWorkout.title, sharedWorkout.content); closeSharedView(); }}
                className="flex-1 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-xl shadow-blue-900/30"
              >
                Dodaj do moich planów
              </button>
              <button onClick={closeSharedView} className="py-4 px-8 rounded-2xl bg-white/5 hover:bg-white/10 text-white font-bold transition-all">Zamknij</button>
            </div>
          </div>
        </div>
      )}

      {/* Desktop Sidebar (Hidden on Mobile) */}
      <div className="hidden md:flex">
        <Sidebar 
          activeView={activeView} 
          onViewChange={setActiveView} 
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 relative flex flex-col min-w-0 overflow-hidden pb-20 md:pb-0">
        {activeView === AppView.CHAT && (
          <ChatInterface onSaveWorkout={handleSaveWorkout} />
        )}
        
        {activeView === AppView.SAVED && (
          <SavedWorkouts 
            items={savedItems} 
            onDelete={handleDeleteSaved} 
            onUpdate={handleUpdateWorkout}
          />
        )}

        {activeView === AppView.CLIENTS && (
          <ClientsManager 
            clients={clients} 
            onAdd={handleAddClient} 
            onUpdate={handleUpdateClient} 
            onDelete={handleDeleteClient}
          />
        )}

        {activeView === AppView.SETTINGS && (
          <div className="p-6 md:p-12 max-w-2xl mx-auto w-full overflow-y-auto">
            <h1 className="text-3xl font-black mb-8">Konfiguracja</h1>
            <div className="space-y-6">
              <div className="bg-white/5 border border-white/5 p-6 rounded-[2rem]">
                <p className="text-slate-400 text-sm mb-6">Ustawienia systemowe CoachOS.</p>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-5 bg-black/20 rounded-2xl">
                    <span className="text-sm font-bold text-slate-300">Wersja Silnika</span>
                    <span className="text-xs font-black text-blue-400 uppercase">Ollama + RAG</span>
                  </div>
                  <div className="flex justify-between items-center p-5 bg-black/20 rounded-2xl">
                    <span className="text-sm font-bold text-slate-300">Przechowywanie</span>
                    <span className="text-xs font-black text-green-500 uppercase">Backend API</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Mobile Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#020617]/95 backdrop-blur-xl border-t border-white/5 px-6 py-4 flex justify-between items-center z-[100] shadow-2xl">
        {[
          { id: AppView.CHAT, icon: 'fa-terminal', label: 'AI' },
          { id: AppView.SAVED, icon: 'fa-folder-closed', label: 'Plany' },
          { id: AppView.CLIENTS, icon: 'fa-user-group', label: 'Ludzie' },
          { id: AppView.SETTINGS, icon: 'fa-sliders', label: 'Opcje' },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`flex flex-col items-center gap-1.5 transition-all ${
              activeView === item.id ? 'text-blue-400 scale-110' : 'text-slate-600'
            }`}
          >
            <i className={`fas ${item.icon} text-lg`}></i>
            <span className="text-[10px] font-black uppercase tracking-widest">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};

export default App;
