
import React, { useState, useMemo } from 'react';
import { Client, CalendarEvent } from '../types';

interface CalendarViewProps {
  clients: Client[];
  events: CalendarEvent[];
  onAddEvent: (event: CalendarEvent) => void;
  onDeleteEvent: (id: string) => void;
}

const CalendarView: React.FC<CalendarViewProps> = ({ 
  clients, 
  events,
  onAddEvent,
  onDeleteEvent
}) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<string | null>(new Date().toISOString().split('T')[0]);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [eventFormData, setEventFormData] = useState<Omit<CalendarEvent, 'id' | 'clientName'>>({
    clientId: '',
    title: '',
    date: '',
    time: '12:00',
    type: 'workout',
    remindCoach: true,
    remindClient: false,
  });

  const daysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
  const startDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay();

  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const days = daysInMonth(year, month);
    const start = (startDayOfMonth(year, month) + 6) % 7;
    const result = [];
    for (let i = 0; i < start; i++) result.push(null);
    for (let i = 1; i <= days; i++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
      result.push({ day: i, date: dateStr });
    }
    return result;
  }, [currentMonth]);

  const handlePrevMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  const handleNextMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));

  const handleEventSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const client = clients.find(c => c.id === eventFormData.clientId);
    if (!client) return;

    onAddEvent({
      ...eventFormData,
      id: Date.now().toString(),
      clientName: client.name,
    } as CalendarEvent);
    setIsEventModalOpen(false);
  };

  const getDensityClass = (count: number) => {
    if (count === 0) return '';
    if (count === 1) return 'bg-blue-600/[0.03]';
    if (count === 2) return 'bg-blue-600/[0.06]';
    if (count === 3) return 'bg-blue-600/[0.1]';
    return 'bg-blue-600/[0.15] shadow-inner shadow-blue-500/10';
  };

  return (
    <div className="p-6 md:p-12 max-w-7xl mx-auto w-full h-full overflow-y-auto scrollbar-hide view-enter pb-24 md:pb-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight mb-3">Kalendarz</h1>
          <p className="text-slate-500 font-medium text-sm">Harmonogram sesji i konsultacji.</p>
        </div>
        <button 
          onClick={() => setIsEventModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-10 py-5 rounded-2xl font-black uppercase tracking-widest transition-all shadow-2xl flex items-center justify-center gap-3 active:scale-95 text-[10px]"
        >
          <i className="fas fa-plus text-[10px]"></i> Zaplanuj Sesję
        </button>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center justify-between mb-8 bg-white/[0.02] border border-white/5 p-6 rounded-[2rem]">
          <div className="flex items-center gap-6">
            <button onClick={handlePrevMonth} className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all"><i className="fas fa-chevron-left"></i></button>
            <h2 className="text-xl font-black uppercase tracking-[0.2em] min-w-[200px] text-center">
              {currentMonth.toLocaleString('pl-PL', { month: 'long', year: 'numeric' })}
            </h2>
            <button onClick={handleNextMonth} className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all"><i className="fas fa-chevron-right"></i></button>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-px bg-white/5 border border-white/5 rounded-[2.5rem] overflow-hidden shadow-2xl">
          {['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nie'].map(d => (
            <div key={d} className="p-4 text-center text-[10px] font-black uppercase tracking-widest text-slate-600 bg-[#020617]">{d}</div>
          ))}
          {calendarDays.map((day, idx) => {
            if (!day) return <div key={`empty-${idx}`} className="bg-[#020617]/50 p-6 min-h-[120px]"></div>;
            
            const dayEvents = events.filter(e => e.date === day.date);
            const isToday = new Date().toISOString().split('T')[0] === day.date;
            const densityClass = getDensityClass(dayEvents.length);

            return (
              <div 
                key={day.date} 
                onClick={() => setSelectedDay(day.date)}
                className={`bg-[#020617] p-4 min-h-[140px] border border-white/[0.02] transition-all cursor-pointer hover:bg-white/[0.05] group relative ${densityClass} ${selectedDay === day.date ? 'ring-inset ring-1 ring-blue-500/30 bg-blue-500/[0.08]' : ''}`}
              >
                <div className="flex justify-between items-start mb-4">
                  <span className={`text-[10px] font-black ${isToday ? 'bg-blue-600 text-white w-6 h-6 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/40' : 'text-slate-500'}`}>{day.day}</span>
                  {dayEvents.length > 0 && (
                    <div className="flex flex-col items-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)] mb-1"></span>
                      {dayEvents.length >= 4 && <span className="text-[7px] font-black text-blue-400/60 uppercase">Busy</span>}
                    </div>
                  )}
                </div>
                <div className="space-y-1.5">
                  {dayEvents.slice(0, 3).map(e => (
                    <div key={e.id} className={`text-[9px] px-2 py-1 rounded-md border truncate font-bold uppercase tracking-tight ${
                      e.type === 'workout' ? 'bg-blue-600/10 border-blue-500/20 text-blue-400' : 
                      e.type === 'consultation' ? 'bg-purple-600/10 border-purple-500/20 text-purple-400' :
                      'bg-slate-800 border-white/10 text-slate-400'
                    }`}>
                      {e.time} {e.clientName.split(' ')[0]}
                    </div>
                  ))}
                  {dayEvents.length > 3 && (
                    <div className="text-[8px] text-slate-600 font-black text-center">+ {dayEvents.length - 3} more</div>
                  )}
                </div>
                {selectedDay === day.date && <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600 shadow-[0_-4px_10px_rgba(59,130,246,0.4)]"></div>}
              </div>
            );
          })}
        </div>

        {selectedDay && (
          <div className="mt-8 animate-in slide-in-from-bottom-6 duration-400 bg-white/[0.02] border border-white/5 p-8 rounded-[2.5rem] shadow-xl">
            <div className="flex justify-between items-center mb-8 pb-6 border-b border-white/5">
              <h3 className="text-lg font-black uppercase tracking-widest text-slate-300">
                Plan dnia: {selectedDay.split('-').reverse().join('.')}
              </h3>
            </div>
            
            <div className="space-y-4">
              {events.filter(e => e.date === selectedDay).length === 0 ? (
                <div className="text-center py-16">
                  <i className="fas fa-calendar-day text-slate-800 text-4xl mb-6"></i>
                  <p className="text-slate-600 italic text-sm font-medium">Brak zaplanowanych wydarzeń na ten dzień.</p>
                </div>
              ) : (
                events.filter(e => e.date === selectedDay)
                  .sort((a, b) => a.time.localeCompare(b.time))
                  .map(e => (
                    <div key={e.id} className="bg-white/5 p-6 rounded-3xl border border-white/5 flex items-center justify-between group hover:bg-white/[0.08] transition-colors">
                      <div className="flex items-center gap-8">
                        <div className="text-xl font-black text-white min-w-[70px]">{e.time}</div>
                        <div className="w-px h-10 bg-white/5"></div>
                        <div>
                          <p className="text-sm font-black text-blue-400 mb-1">{e.clientName}</p>
                          <div className="flex items-center gap-4">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{e.title || (e.type === 'workout' ? 'Trening Personalny' : 'Konsultacja')}</p>
                            {(e.remindCoach || e.remindClient) && (
                              <div className="flex gap-2">
                                {e.remindCoach && <i className="fas fa-bell text-[10px] text-orange-400" title="Przypomnienie Trener"></i>}
                                {e.remindClient && <i className="fas fa-bell text-[10px] text-blue-400" title="Przypomnienie Podopieczny"></i>}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => onDeleteEvent(e.id)}
                        className="w-10 h-10 rounded-xl bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500 hover:text-white"
                      >
                        <i className="fas fa-trash-alt text-xs"></i>
                      </button>
                    </div>
                  ))
              )}
            </div>
          </div>
        )}
      </div>

      {isEventModalOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-lg rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10">
            <div className="p-8 md:p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="text-lg font-black tracking-tight uppercase">Planowanie Sesji</h2>
              <button onClick={() => setIsEventModalOpen(false)} className="w-10 h-10 rounded-full hover:bg-white/5 text-slate-500 transition-all"><i className="fas fa-times"></i></button>
            </div>
            <form onSubmit={handleEventSubmit} className="p-8 md:p-10 space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Podopieczny</label>
                <select 
                  required 
                  value={eventFormData.clientId} 
                  onChange={e => setEventFormData({...eventFormData, clientId: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 appearance-none font-bold"
                >
                  <option value="" disabled className="bg-slate-900">Wybierz z listy...</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id} className="bg-slate-900">{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Data</label>
                  <input required type="date" value={eventFormData.date} onChange={e => setEventFormData({...eventFormData, date: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 appearance-none font-bold" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Godzina</label>
                  <input required type="time" value={eventFormData.time} onChange={e => setEventFormData({...eventFormData, time: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 appearance-none font-bold" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Typ Sesji</label>
                <select 
                  value={eventFormData.type} 
                  onChange={e => setEventFormData({...eventFormData, type: e.target.value as any})}
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 appearance-none font-bold"
                >
                  <option value="workout" className="bg-slate-900">Trening Personalny</option>
                  <option value="consultation" className="bg-slate-900">Konsultacja</option>
                  <option value="checkup" className="bg-slate-900">Pomiary i Raport</option>
                </select>
              </div>
              <div className="flex flex-col gap-4 py-2">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input type="checkbox" checked={eventFormData.remindCoach} onChange={e => setEventFormData({...eventFormData, remindCoach: e.target.checked})} className="hidden" />
                  <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all ${eventFormData.remindCoach ? 'bg-blue-600 border-blue-600' : 'border-white/10 group-hover:border-white/20'}`}>
                    {eventFormData.remindCoach && <i className="fas fa-check text-[10px] text-white"></i>}
                  </div>
                  <span className="text-xs font-bold text-slate-400">Przypomnij mi (Trener)</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input type="checkbox" checked={eventFormData.remindClient} onChange={e => setEventFormData({...eventFormData, remindClient: e.target.checked})} className="hidden" />
                  <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all ${eventFormData.remindClient ? 'bg-blue-600 border-blue-600' : 'border-white/10 group-hover:border-white/20'}`}>
                    {eventFormData.remindClient && <i className="fas fa-check text-[10px] text-white"></i>}
                  </div>
                  <span className="text-xs font-bold text-slate-400">Wyślij powiadomienie do podopiecznego</span>
                </label>
              </div>
              <div className="flex gap-4 pt-4">
                <button type="button" onClick={() => setIsEventModalOpen(false)} className="flex-1 py-5 font-black uppercase text-[10px] text-slate-500">Anuluj</button>
                <button type="submit" className="flex-1 bg-blue-600 py-5 rounded-2xl font-black uppercase text-[10px] text-white shadow-xl shadow-blue-900/40">Zapisz sesję</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;
