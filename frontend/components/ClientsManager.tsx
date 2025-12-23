
import React, { useState, useMemo } from 'react';
import { Client, ProgressEntry, CalendarEvent } from '../types';
import { exportClientReport } from '../utils/pdfExport';

interface ClientsManagerProps {
  clients: Client[];
  events: CalendarEvent[];
  onAdd: (client: Client) => void;
  onUpdate: (client: Client) => void;
  onDelete: (id: string) => void;
}

type MetricType = 'weight' | 'bodyFat' | 'waist';
type TimeRange = '30' | '90' | 'all' | 'custom';

const ClientsManager: React.FC<ClientsManagerProps> = ({ 
  clients, 
  onAdd, 
  onUpdate, 
  onDelete
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [clientToDelete, setClientToDelete] = useState<Client | null>(null);
  const [viewingProgressId, setViewingProgressId] = useState<string | null>(null);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  
  const [expandedClientIds, setExpandedClientIds] = useState<Set<string>>(new Set());
  
  // Advanced Analytics States
  const [activeMetrics, setActiveMetrics] = useState<Set<MetricType>>(new Set(['weight']));
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [showOverlay, setShowOverlay] = useState(false);
  const [customDates, setCustomDates] = useState({ start: '', end: '' });

  const initialFormState = { name: '', age: 0, weight: 0, goal: '', notes: '' };
  const [formData, setFormData] = useState(initialFormState);
  const [progressFormData, setProgressFormData] = useState({ weight: 0, bodyFat: 0, waist: 0, notes: '' });

  const filteredClients = useMemo(() => {
    return clients.filter(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [clients, searchTerm]);

  const activeClientForProgress = useMemo(() => clients.find(c => c.id === viewingProgressId), [clients, viewingProgressId]);

  const toggleExpand = (id: string) => {
    const newSet = new Set(expandedClientIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setExpandedClientIds(newSet);
  };

  const toggleMetric = (metric: MetricType) => {
    const newSet = new Set(activeMetrics);
    if (newSet.has(metric)) {
      if (newSet.size > 1) newSet.delete(metric);
    } else {
      newSet.add(metric);
    }
    setActiveMetrics(newSet);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingClient(null);
    setFormData(initialFormState);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingClient) {
      onUpdate({ ...editingClient, ...formData });
    } else {
      onAdd({ 
        ...formData, 
        id: Date.now().toString(), 
        createdAt: new Date().toLocaleDateString('pl-PL'),
        progress: [] 
      } as Client);
    }
    closeModal();
  };

  const handleAddProgress = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeClientForProgress) return;
    
    const newEntry: ProgressEntry = {
      id: Date.now().toString(),
      date: new Date().toLocaleDateString('pl-PL'),
      weight: progressFormData.weight,
      bodyFat: progressFormData.bodyFat || undefined,
      waist: progressFormData.waist || undefined,
      notes: progressFormData.notes
    };

    const updatedClient = {
      ...activeClientForProgress,
      progress: [newEntry, ...(activeClientForProgress.progress || [])]
    };
    
    onUpdate(updatedClient);
    setIsProgressModalOpen(false);
    setProgressFormData({ weight: 0, bodyFat: 0, waist: 0, notes: '' });
  };

  const renderChart = (client: Client) => {
    if (!client.progress || client.progress.length < 2) {
      return (
        <div className="h-64 flex flex-col items-center justify-center bg-black/20 rounded-[2.5rem] border border-white/5 border-dashed">
          <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center mb-4">
             <i className="fas fa-chart-line text-slate-700 text-2xl"></i>
          </div>
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-12 text-center leading-relaxed">System wymaga przynajmniej 2 pomiarów do wygenerowania analizy wizualnej.</p>
        </div>
      );
    }

    // Process Primary Data
    let data = [...client.progress].map(p => ({
        ...p,
        _dateObj: new Date(p.date.split('.').reverse().join('-'))
    })).sort((a, b) => a._dateObj.getTime() - b._dateObj.getTime());

    if (timeRange === 'custom' && customDates.start && customDates.end) {
        const start = new Date(customDates.start);
        const end = new Date(customDates.end);
        data = data.filter(d => d._dateObj >= start && d._dateObj <= end);
    } else if (timeRange !== 'all' && timeRange !== 'custom') {
        const days = parseInt(timeRange);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);
        data = data.filter(d => d._dateObj >= cutoff);
    }

    // Process Historical Data (Overlay)
    let historicalData: any[] = [];
    if (showOverlay && timeRange !== 'all' && timeRange !== 'custom') {
        const days = parseInt(timeRange);
        const endOfHistory = new Date();
        endOfHistory.setDate(endOfHistory.getDate() - days);
        const startOfHistory = new Date();
        startOfHistory.setDate(startOfHistory.getDate() - (days * 2));
        
        historicalData = [...client.progress].map(p => ({
            ...p,
            _dateObj: new Date(p.date.split('.').reverse().join('-'))
        }))
        .filter(d => d._dateObj >= startOfHistory && d._dateObj < endOfHistory)
        .sort((a, b) => a._dateObj.getTime() - b._dateObj.getTime());
    }

    if (data.length < 2) {
        return (
            <div className="h-64 flex flex-col items-center justify-center bg-black/20 rounded-[2.5rem] border border-white/5 border-dashed">
              <i className="fas fa-calendar-xmark text-slate-800 text-3xl mb-4"></i>
              <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Brak danych w wybranym oknie czasowym</p>
            </div>
        );
    }

    const width = 800;
    const height = 300;
    const padding = 50;

    const colors: Record<MetricType, string> = {
      weight: '#3b82f6',
      bodyFat: '#a855f7',
      waist: '#ec4899'
    };

    const drawLine = (dataset: any[], metric: MetricType, isHistorical: boolean = false) => {
        const vals = dataset.map(d => d[metric] as number).filter(v => v !== undefined && v !== null);
        if (vals.length < 2) return null;

        const min = Math.min(...vals) * 0.98;
        const max = Math.max(...vals) * 1.02;
        const range = max - min || 1;
        
        const points = dataset.map((d, i) => {
          const val = d[metric] as number;
          if (val === undefined || val === null) return null;
          const x = padding + (i / (dataset.length - 1)) * (width - padding * 2);
          const y = (height - padding) - ((val - min) / range) * (height - padding * 2);
          return `${x},${y}`;
        }).filter(p => p !== null).join(' ');

        const gradientId = `grad-${metric}-${isHistorical ? 'hist' : 'main'}-${client.id}`;

        return (
          <g key={`${metric}-${isHistorical ? 'hist' : 'main'}`} className={isHistorical ? 'opacity-20' : ''}>
            <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={colors[metric]} stopOpacity={isHistorical ? "0.1" : "0.3"} />
                    <stop offset="100%" stopColor={colors[metric]} stopOpacity="0" />
                </linearGradient>
            </defs>
            <path
                d={`M ${padding},${height - padding} L ${points} L ${padding + (width - padding * 2)},${height - padding} Z`}
                fill={`url(#${gradientId})`}
                className="transition-all duration-700"
            />
            <polyline
              fill="none"
              stroke={colors[metric]}
              strokeWidth={isHistorical ? "2" : "4"}
              strokeDasharray={isHistorical ? "5,5" : "0"}
              strokeLinecap="round"
              strokeLinejoin="round"
              points={points}
              className="transition-all duration-1000"
            />
            {!isHistorical && dataset.map((d, i) => {
              const val = d[metric] as number;
              if (val === undefined || val === null) return null;
              const x = padding + (i / (dataset.length - 1)) * (width - padding * 2);
              const y = (height - padding) - ((val - min) / range) * (height - padding * 2);
              return (
                <g key={`${metric}-${i}`} className="group/dot">
                    <circle 
                        cx={x} cy={y} r="6" 
                        fill="#020617" 
                        stroke={colors[metric]} 
                        strokeWidth="3"
                        className="transition-all duration-300 group-hover/dot:r-8 group-hover/dot:stroke-white cursor-help"
                    />
                    <rect x={x - 25} y={y - 35} width="50" height="20" rx="6" fill="#1e293b" className="opacity-0 group-hover/dot:opacity-100 transition-opacity" />
                    <text 
                        x={x} y={y - 21} 
                        fill="white" 
                        fontSize="9" 
                        fontWeight="900"
                        textAnchor="middle"
                        className="opacity-0 group-hover/dot:opacity-100 transition-opacity uppercase tracking-tighter"
                    >
                        {val}
                    </text>
                </g>
              );
            })}
          </g>
        );
    };

    return (
      <div className="relative mt-8 bg-black/30 p-8 rounded-[3rem] border border-white/5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-10">
            <div className="flex flex-wrap gap-3">
                {(['weight', 'bodyFat', 'waist'] as MetricType[]).map(m => (
                    <button 
                        key={m}
                        onClick={() => toggleMetric(m)}
                        className={`px-5 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border flex items-center gap-3 ${
                            activeMetrics.has(m) 
                            ? 'bg-white/10 border-white/10 text-white shadow-xl' 
                            : 'bg-transparent border-white/5 text-slate-600 hover:text-slate-400'
                        }`}
                    >
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[m] }}></div>
                        {m === 'weight' ? 'Waga' : m === 'bodyFat' ? 'Body Fat %' : 'Talia'}
                    </button>
                ))}
            </div>
            
            <div className="flex flex-wrap gap-3">
                {(['30', '90', 'all', 'custom'] as TimeRange[]).map(r => (
                    <button 
                        key={r}
                        onClick={() => setTimeRange(r)}
                        className={`px-5 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                            timeRange === r 
                            ? 'bg-blue-600 text-white shadow-xl shadow-blue-900/40' 
                            : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-white'
                        }`}
                    >
                        {r === 'all' ? 'Pełna historia' : r === 'custom' ? 'Zakres' : `${r} dni`}
                    </button>
                ))}
                
                {timeRange !== 'all' && timeRange !== 'custom' && (
                    <button 
                        onClick={() => setShowOverlay(!showOverlay)}
                        className={`px-5 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border ${
                            showOverlay ? 'bg-orange-500/10 border-orange-500/20 text-orange-400' : 'bg-white/5 border-white/5 text-slate-600'
                        }`}
                        title="Porównaj z poprzednim okresem"
                    >
                        <i className="fas fa-layer-group mr-2"></i> Nakładka historyczna
                    </button>
                )}
            </div>
        </div>

        {timeRange === 'custom' && (
            <div className="flex gap-4 mb-8 p-6 bg-slate-900/50 rounded-3xl border border-white/5 animate-in slide-in-from-top-2">
                <div className="flex-1 space-y-2">
                    <label className="text-[9px] font-black text-slate-600 uppercase tracking-widest ml-1">Od</label>
                    <input type="date" value={customDates.start} onChange={e => setCustomDates({...customDates, start: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-white focus:outline-none focus:border-blue-500/50" />
                </div>
                <div className="flex-1 space-y-2">
                    <label className="text-[9px] font-black text-slate-600 uppercase tracking-widest ml-1">Do</label>
                    <input type="date" value={customDates.end} onChange={e => setCustomDates({...customDates, end: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-white focus:outline-none focus:border-blue-500/50" />
                </div>
            </div>
        )}

        <div className="relative group/svg">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
              {/* Horizontal grid lines */}
              {[0, 1, 2, 3, 4].map(i => (
                <line 
                    key={i}
                    x1={padding} 
                    y1={padding + (i * (height - padding * 2) / 4)} 
                    x2={width - padding} 
                    y2={padding + (i * (height - padding * 2) / 4)} 
                    stroke="rgba(255,255,255,0.03)" 
                    strokeWidth="1" 
                />
              ))}
              
              {/* Historical Overlay Drawing */}
              {/* Fix: Explicitly cast metric to MetricType to resolve unknown type error */}
              {showOverlay && historicalData.length > 1 && Array.from(activeMetrics).map((metric: MetricType) => drawLine(historicalData, metric, true))}
              
              {/* Primary Data Drawing */}
              {/* Fix: Explicitly cast metric to MetricType to resolve unknown type error */}
              {Array.from(activeMetrics).map((metric: MetricType) => drawLine(data, metric, false))}
            </svg>
            
            <div className="flex justify-between mt-4 px-12">
                <span className="text-[8px] font-black text-slate-700 uppercase tracking-widest">{data[0].date}</span>
                <span className="text-[8px] font-black text-slate-700 uppercase tracking-widest">{data[data.length-1].date}</span>
            </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 md:p-12 max-w-7xl mx-auto w-full h-full overflow-y-auto scrollbar-hide view-enter pb-32">
      <div className="text-center mb-16">
        <div className="inline-block px-4 py-1.5 rounded-full bg-blue-600/10 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-4 border border-blue-500/10">
          Database Core
        </div>
        <h1 className="text-6xl font-black tracking-tighter mb-4 text-white">Podopieczni</h1>
        <p className="text-slate-500 font-medium text-sm">Inteligentne zarządzanie bazą i analiza biometryczna.</p>
      </div>

      <div className="flex flex-col items-center gap-8 mb-20">
        <button 
          onClick={() => setIsModalOpen(true)}
          className="w-full max-w-sm bg-slate-900 border border-white/10 hover:bg-slate-800 text-white px-10 py-6 rounded-[2.5rem] font-black uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-5 group shadow-2xl"
        >
          <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center group-hover:rotate-90 transition-transform">
            <i className="fas fa-plus text-white text-xs"></i>
          </div>
          Nowy Profil
        </button>

        <div className="w-full relative max-w-2xl group">
          <i className="fas fa-search absolute left-8 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-blue-500 transition-colors"></i>
          <input 
            type="text"
            placeholder="Szukaj po nazwisku..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-black/40 border border-white/5 rounded-[2.5rem] py-6 pl-20 pr-10 focus:outline-none focus:border-blue-500/30 text-sm transition-all backdrop-blur-md text-white font-medium"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-10">
        {filteredClients.length === 0 ? (
          <div className="text-center py-32 bg-white/[0.02] rounded-[4rem] border border-white/5 border-dashed">
            <div className="w-20 h-20 bg-slate-900 rounded-[2rem] flex items-center justify-center mx-auto mb-8 border border-white/5">
                <i className="fas fa-users-slash text-slate-800 text-3xl"></i>
            </div>
            <p className="text-slate-600 font-bold uppercase tracking-widest text-xs">Nie znaleziono aktywnych rekordów.</p>
          </div>
        ) : (
          filteredClients.map((client) => {
            const isExpanded = expandedClientIds.has(client.id);
            const latestProgress = client.progress?.[0];

            return (
              <div key={client.id} className={`bg-slate-900/40 border transition-all duration-500 group overflow-hidden ${isExpanded ? 'rounded-[3.5rem] border-blue-500/20 ring-1 ring-blue-500/10' : 'rounded-[3rem] border-white/5 hover:border-white/10'}`}>
                <div className="p-8 md:p-10 flex items-center justify-between">
                  <div className="flex items-center gap-8">
                    <div className="w-20 h-20 rounded-[2rem] bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white font-black text-3xl shadow-xl shadow-blue-900/40">
                      {client.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold tracking-tight mb-2 text-white">{client.name}</h3>
                      <div className="flex flex-wrap items-center gap-5 text-[10px] font-black uppercase tracking-widest text-slate-500">
                        <span className="flex items-center gap-2"><i className="fas fa-birthday-cake text-blue-500/50"></i> {client.age} lat</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-800"></div>
                        <span className="flex items-center gap-2 text-blue-400"><i className="fas fa-bullseye"></i> {client.goal}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <button 
                      onClick={() => { setViewingProgressId(client.id); setIsProgressModalOpen(true); }}
                      className="w-14 h-14 rounded-2xl bg-white/5 hover:bg-blue-600 hover:text-white transition-all flex items-center justify-center text-slate-400 shadow-xl group-hover:scale-105 active:scale-95"
                      title="Nowy pomiar"
                    >
                      <i className="fas fa-weight-scale text-lg"></i>
                    </button>
                    <button 
                      onClick={() => toggleExpand(client.id)}
                      className={`w-14 h-14 rounded-2xl bg-white/5 transition-all flex items-center justify-center text-slate-400 hover:text-white ${isExpanded ? 'rotate-180 bg-blue-600/20 text-blue-400' : 'group-hover:bg-white/10'}`}
                    >
                      <i className="fas fa-chevron-down text-sm"></i>
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-10 pb-12 animate-in slide-in-from-top-4 duration-500">
                    <div className="mb-12">
                        <div className="flex justify-between items-center mb-4 px-2">
                            <h4 className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-500">Terminal Analityczny</h4>
                            <button onClick={() => exportClientReport(client)} className="text-[10px] font-black text-blue-500 hover:text-blue-400 transition-colors uppercase tracking-widest bg-blue-500/5 px-4 py-2 rounded-xl border border-blue-500/10">Generuj Raport .PDF</button>
                        </div>
                        {renderChart(client)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                      <div className="bg-black/40 p-8 rounded-[2rem] border border-white/5 transition-all hover:border-white/10">
                        <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-2">Masa Startowa</p>
                        <p className="text-3xl font-black text-white">{client.weight} <span className="text-xs text-slate-600">kg</span></p>
                      </div>
                      <div className="bg-black/40 p-8 rounded-[2rem] border border-white/5 transition-all hover:border-white/10">
                        <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-2">Bieżący Odczyt</p>
                        <p className="text-3xl font-black text-blue-400">{latestProgress?.weight || client.weight} <span className="text-xs text-slate-600">kg</span></p>
                      </div>
                      <div className="bg-black/40 p-8 rounded-[2rem] border border-white/5 transition-all hover:border-white/10">
                        <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-2">Delta (Trend)</p>
                        <div className="flex items-baseline gap-2">
                            <p className={`text-3xl font-black ${((latestProgress?.weight || client.weight) - client.weight) <= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {((latestProgress?.weight || client.weight) - client.weight).toFixed(1)} <span className="text-xs text-slate-600">kg</span>
                            </p>
                            <i className={`fas fa-arrow-${((latestProgress?.weight || client.weight) - client.weight) <= 0 ? 'down' : 'up'} text-xs ${((latestProgress?.weight || client.weight) - client.weight) <= 0 ? 'text-green-500' : 'text-red-500'}`}></i>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-4 pt-10 border-t border-white/5">
                      <button 
                        onClick={() => { setEditingClient(client); setFormData({ name: client.name, age: client.age, weight: client.weight, goal: client.goal, notes: client.notes }); setIsModalOpen(true); }}
                        className="flex-1 py-5 rounded-[1.5rem] bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all border border-white/5 text-slate-300"
                      >
                        Modyfikuj Profil
                      </button>
                      <button 
                        onClick={() => setClientToDelete(client)}
                        className="w-16 h-16 rounded-[1.5rem] bg-red-500/10 text-red-500 hover:bg-red-600 hover:text-white transition-all flex items-center justify-center border border-red-500/20"
                      >
                        <i className="fas fa-trash-alt text-lg"></i>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Profile Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-6 bg-black/95 backdrop-blur-2xl animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-lg rounded-[4rem] overflow-hidden shadow-2xl border border-white/10">
            <div className="p-12 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="text-3xl font-black tracking-tighter text-white">{editingClient ? 'Edytuj Profil' : 'Nowy Profil'}</h2>
              <button onClick={closeModal} className="w-14 h-14 rounded-full hover:bg-white/5 text-slate-500 transition-all flex items-center justify-center"><i className="fas fa-times text-xl"></i></button>
            </div>
            <form onSubmit={handleSubmit} className="p-12 space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Personal Data</label>
                <input required type="text" placeholder="Imię i Nazwisko" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold text-base" />
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Wiek</label>
                  <input required type="number" value={formData.age || ''} onChange={e => setFormData({...formData, age: parseInt(e.target.value) || 0})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Waga Start (kg)</label>
                  <input required type="number" step="0.1" value={formData.weight || ''} onChange={e => setFormData({...formData, weight: parseFloat(e.target.value) || 0})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Cel Strategiczny</label>
                <input required type="text" placeholder="np. Redukcja tkanki tłuszczowej" value={formData.goal} onChange={e => setFormData({...formData, goal: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
              </div>
              <button type="submit" className="w-full bg-blue-600 py-6 rounded-3xl font-black uppercase text-xs tracking-widest text-white shadow-2xl shadow-blue-900/50 transition-all hover:bg-blue-500 active:scale-95 border border-blue-400/20">Zapisz Rekord Systemowy</button>
            </form>
          </div>
        </div>
      )}

      {/* Progress Entry Modal */}
      {isProgressModalOpen && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-6 bg-black/95 backdrop-blur-2xl animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-lg rounded-[4rem] overflow-hidden shadow-2xl border border-white/10">
            <div className="p-12 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <div>
                <h2 className="text-3xl font-black tracking-tighter text-white">Nowy Pomiar</h2>
                <p className="text-blue-500 text-[10px] font-black uppercase tracking-[0.2em] mt-2">{activeClientForProgress?.name}</p>
              </div>
              <button onClick={() => setIsProgressModalOpen(false)} className="w-14 h-14 rounded-full hover:bg-white/5 text-slate-500 transition-all flex items-center justify-center"><i className="fas fa-times text-xl"></i></button>
            </div>
            <form onSubmit={handleAddProgress} className="p-12 space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Waga Bieżąca (kg)</label>
                <input required type="number" step="0.1" value={progressFormData.weight || ''} onChange={e => setProgressFormData({...progressFormData, weight: parseFloat(e.target.value) || 0})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-black text-2xl text-center" />
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Body Fat (%)</label>
                  <input type="number" step="0.1" value={progressFormData.bodyFat || ''} onChange={e => setProgressFormData({...progressFormData, bodyFat: parseFloat(e.target.value) || 0})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Talia (cm)</label>
                  <input type="number" step="0.1" value={progressFormData.waist || ''} onChange={e => setProgressFormData({...progressFormData, waist: parseFloat(e.target.value) || 0})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
              </div>
              <button type="submit" className="w-full bg-blue-600 py-6 rounded-3xl font-black uppercase text-xs tracking-widest text-white shadow-2xl shadow-blue-900/50 border border-blue-400/20">Zatwierdź Odczyt</button>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {clientToDelete && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 bg-black/98 backdrop-blur-3xl animate-in zoom-in-95 duration-200">
          <div className="bg-[#0f172a] p-16 rounded-[4rem] max-w-md w-full text-center border border-red-500/20 shadow-2xl shadow-red-950/20">
            <div className="w-24 h-24 bg-red-600/10 text-red-500 rounded-[2rem] flex items-center justify-center mx-auto mb-10 border border-red-500/10">
                <i className="fas fa-user-slash text-4xl"></i>
            </div>
            <h2 className="text-3xl font-black mb-4 tracking-tighter text-white">Usunąć profil?</h2>
            <p className="text-slate-500 mb-12 text-sm font-medium leading-relaxed uppercase tracking-widest px-8">Wszystkie dane historyczne i pomiary <span className="text-white font-black">{clientToDelete.name}</span> zostaną trwale wymazane z systemu.</p>
            <div className="flex gap-4">
              <button onClick={() => setClientToDelete(null)} className="flex-1 py-6 rounded-3xl bg-white/5 font-black uppercase text-[10px] tracking-widest text-slate-500 hover:bg-white/10 transition-all">Anuluj</button>
              <button onClick={() => { onDelete(clientToDelete.id); setClientToDelete(null); }} className="flex-1 py-6 rounded-3xl bg-red-600 text-white font-black uppercase text-[10px] tracking-widest transition-all shadow-xl shadow-red-900/40">Potwierdź</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsManager;
