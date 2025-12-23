import React, { useState, useEffect, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SavedWorkouts from './components/SavedWorkouts';
import ClientsManager from './components/ClientsManager';
import CalendarView from './components/CalendarView';
import { AppView, SavedWorkout, Client, CalendarEvent } from './types';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<AppView>(AppView.CHAT);
  const [savedItems, setSavedItems] = useState<SavedWorkout[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({ message: '', visible: false });

  // Persist data in localStorage
  useEffect(() => {
    const storedWorkouts = localStorage.getItem('fitcoach_saved');
    if (storedWorkouts) setSavedItems(JSON.parse(storedWorkouts));
    const storedClients = localStorage.getItem('fitcoach_clients');
    if (storedClients) setClients(JSON.parse(storedClients));
    const storedEvents = localStorage.getItem('fitcoach_events');
    if (storedEvents) setEvents(JSON.parse(storedEvents));
  }, []);

  useEffect(() => { localStorage.setItem('fitcoach_saved', JSON.stringify(savedItems)); }, [savedItems]);
  useEffect(() => { localStorage.setItem('fitcoach_clients', JSON.stringify(clients)); }, [clients]);
  useEffect(() => { localStorage.setItem('fitcoach_events', JSON.stringify(events)); }, [events]);

  const showToast = (message: string) => {
    setToast({ message, visible: true });
    setTimeout(() => setToast(prev => ({ ...prev, visible: false })), 3000);
  };

  const handleSaveWorkout = (title: string, content: string) => {
    const newItem: SavedWorkout = { id: Date.now().toString(), title, content, date: new Date().toLocaleDateString('pl-PL'), color: '#3b82f6' };
    setSavedItems(prev => [newItem, ...prev]);
    showToast("Plan został zapisany!");
  };

  const currentViewContent = useMemo(() => {
    switch (activeView) {
      case AppView.CHAT:
        return <ChatInterface key="chat" onSaveWorkout={handleSaveWorkout} />;
      case AppView.SAVED:
        return (
          <SavedWorkouts 
            key="saved"
            items={savedItems} 
            onDelete={id => setSavedItems(prev => prev.filter(i => i.id !== id))} 
            onUpdate={item => setSavedItems(prev => prev.map(i => i.id === item.id ? item : i))} 
          />
        );
      case AppView.CLIENTS:
        return (
          <ClientsManager 
            key="clients"
            clients={clients} 
            events={events}
            onAdd={c => setClients(prev => [c, ...prev])} 
            onUpdate={c => setClients(prev => prev.map(i => i.id === c.id ? c : i))} 
            onDelete={id => setClients(prev => prev.filter(i => i.id !== id))} 
          />
        );
      case AppView.CALENDAR:
        return (
          <CalendarView 
            key="calendar"
            clients={clients} 
            events={events} 
            onAddEvent={e => setEvents(prev => [...prev, e])} 
            onDeleteEvent={id => setEvents(prev => prev.filter(e => e.id !== id))} 
          />
        );
      case AppView.SETTINGS:
        return (
          <div key="settings" className="p-8 md:p-12 max-w-2xl mx-auto w-full view-enter">
            <h1 className="text-4xl font-black mb-10 tracking-tight text-white">Konfiguracja Systemu</h1>
            <div className="bg-white/5 border border-white/5 p-10 rounded-[3rem] shadow-2xl backdrop-blur-sm">
              <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em] mb-8">Status Operacyjny</p>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-6 bg-black/40 rounded-[2rem] border border-white/5 group hover:border-blue-500/30 transition-all">
                  <div className="flex items-center gap-5">
                    <div className="w-10 h-10 rounded-xl bg-blue-600/10 flex items-center justify-center text-blue-400">
                      <i className="fas fa-brain"></i>
                    </div>
                    <div>
                      <span className="text-sm font-bold text-slate-300 block">Silnik AI</span>
                      <span className="text-[10px] text-slate-500 uppercase font-black">Gemini 3 Pro Preview</span>
                    </div>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]"></div>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  }, [activeView, savedItems, clients, events]);

  return (
    <div className="flex flex-col md:flex-row h-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      <div className={`fixed top-8 left-1/2 -translate-x-1/2 md:left-auto md:right-8 md:translate-x-0 z-[200] transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1) transform ${toast.visible ? 'translate-y-0 opacity-100' : '-translate-y-24 opacity-0 pointer-events-none'}`}>
        <div className="bg-white text-black px-8 py-4 rounded-3xl shadow-[0_30px_60px_rgba(0,0,0,0.5)] flex items-center gap-4 border border-white/20">
          <i className="fas fa-check-circle text-blue-600"></i>
          <span className="font-black text-[11px] uppercase tracking-widest">{toast.message}</span>
        </div>
      </div>

      <div className="hidden md:flex">
        <Sidebar 
          activeView={activeView} 
          onViewChange={setActiveView} 
          isCollapsed={isSidebarCollapsed} 
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
        />
      </div>

      <main className="flex-1 relative flex flex-col min-w-0 overflow-hidden pb-24 md:pb-0">
        {currentViewContent}
      </main>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-950/90 backdrop-blur-2xl border-t border-white/5 px-6 py-5 flex justify-between items-center z-[150] shadow-[0_-20px_50px_rgba(0,0,0,0.8)]">
        {[
          { id: AppView.CHAT, icon: 'fa-terminal', label: 'AI' },
          { id: AppView.SAVED, icon: 'fa-layer-group', label: 'Plany' },
          { id: AppView.CLIENTS, icon: 'fa-users-viewfinder', label: 'Ludzie' },
          { id: AppView.CALENDAR, icon: 'fa-calendar-check', label: 'Dzień' },
          { id: AppView.SETTINGS, icon: 'fa-gear', label: 'Opcje' },
        ].map((item) => (
          <button 
            key={item.id} 
            onClick={() => setActiveView(item.id)} 
            className={`flex flex-col items-center gap-2 transition-all duration-500 relative ${activeView === item.id ? 'text-blue-400' : 'text-slate-600 hover:text-slate-400'}`}
          >
            <div className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-500 ${activeView === item.id ? 'bg-blue-600/10 shadow-[0_0_20px_rgba(59,130,246,0.15)] scale-110' : ''}`}>
              <i className={`fas ${item.icon} text-lg`}></i>
            </div>
            <span className="text-[7px] font-black uppercase tracking-tighter opacity-80">{item.label}</span>
            {activeView === item.id && (
              <div className="absolute -top-1 w-1 h-1 bg-blue-500 rounded-full"></div>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default App;