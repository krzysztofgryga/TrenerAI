
import React, { useState, useMemo } from 'react';
import { Client, ProgressEntry } from '../types';
import { exportClientReport } from '../utils/pdfExport';

interface ClientsManagerProps {
  clients: Client[];
  onAdd: (client: Client) => void;
  onUpdate: (client: Client) => void;
  onDelete: (id: string) => void;
}

type ProgressTab = 'charts' | 'history' | 'stats';
type TimeRange = '7d' | '30d' | '90d' | 'all';

const ClientsManager: React.FC<ClientsManagerProps> = ({ clients, onAdd, onUpdate, onDelete }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [clientToDelete, setClientToDelete] = useState<Client | null>(null);
  const [viewingProgressId, setViewingProgressId] = useState<string | null>(null);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [activeProgressTab, setActiveProgressTab] = useState<ProgressTab>('charts');
  
  // Advanced Chart State
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [showOverlay, setShowOverlay] = useState(false);
  const [compareMetrics, setCompareMetrics] = useState<string[]>(['weight']);

  // State for collapsible cards
  const [expandedClientIds, setExpandedClientIds] = useState<Set<string>>(new Set());

  const initialFormState: Omit<Client, 'id' | 'createdAt' | 'progress'> = {
    name: '', age: 0, weight: 0, goal: '', notes: ''
  };

  const [formData, setFormData] = useState(initialFormState);
  const [progressFormData, setProgressFormData] = useState({
    weight: 0, bodyFat: 0, waist: 0, notes: ''
  });

  const getGoalIcon = (goal: string) => {
    const g = goal.toLowerCase();
    if (g.includes('schud') || g.includes('waga') || g.includes('redukcja') || g.includes('odchudz') || g.includes('fat')) return 'fa-weight-scale';
    if (g.includes('mięśn') || g.includes('masa') || g.includes('sylwetk') || g.includes('kulturyst') || g.includes('biceps')) return 'fa-dumbbell';
    if (g.includes('sił') || g.includes('trójbój') || g.includes('moc') || g.includes('power')) return 'fa-weight-hanging';
    if (g.includes('kondycj') || g.includes('biega') || g.includes('wytrzyma') || g.includes('cardio')) return 'fa-person-running';
    if (g.includes('zdrowie') || g.includes('kręgosłup') || g.includes('mobilno')) return 'fa-heart-pulse';
    return 'fa-bullseye';
  };

  const filteredClients = useMemo(() => {
    return clients.filter(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [clients, searchTerm]);

  const activeClient = useMemo(() => 
    clients.find(c => c.id === viewingProgressId), 
  [clients, viewingProgressId]);

  const toggleExpand = (id: string) => {
    const newSet = new Set(expandedClientIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setExpandedClientIds(newSet);
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
      });
    }
    closeModal();
  };

  const handleAddProgress = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeClient) return;

    const newEntry: ProgressEntry = {
      id: Date.now().toString(),
      date: new Date().toLocaleDateString('pl-PL'),
      weight: progressFormData.weight,
      bodyFat: progressFormData.bodyFat || undefined,
      waist: progressFormData.waist || undefined,
      notes: progressFormData.notes
    };

    const updatedClient = {
      ...activeClient,
      weight: newEntry.weight,
      progress: [...(activeClient.progress || []), newEntry]
    };

    onUpdate(updatedClient);
    setIsProgressModalOpen(false);
    setProgressFormData({ weight: 0, bodyFat: 0, waist: 0, notes: '' });
  };

  const openAddModal = () => { setEditingClient(null); setFormData(initialFormState); setIsModalOpen(true); };
  const openEditModal = (client: Client) => {
    setEditingClient(client);
    setFormData({ name: client.name, age: client.age, weight: client.weight, goal: client.goal, notes: client.notes });
    setIsModalOpen(true);
  };
  const closeModal = () => { setIsModalOpen(false); setEditingClient(null); };

  /**
   * Advanced multi-line chart component
   */
  const AdvancedMultiChart = ({ 
    entries, 
    overlayEntries = [], 
    metrics 
  }: { 
    entries: ProgressEntry[], 
    overlayEntries?: ProgressEntry[], 
    metrics: string[] 
  }) => {
    if (entries.length < 2) return (
      <div className="h-64 flex flex-col items-center justify-center bg-white/[0.02] rounded-3xl border border-dashed border-white/10">
        <i className="fas fa-chart-line text-slate-700 text-3xl mb-4"></i>
        <p className="text-slate-500 text-xs font-black uppercase tracking-widest">Wymagane minimum 2 wpisy dla wybranego okresu</p>
      </div>
    );

    const width = 800;
    const height = 300;
    const padding = 40;
    const colors: Record<string, string> = {
      weight: '#3b82f6',
      bodyFat: '#10b981',
      waist: '#f59e0b'
    };

    const getScale = (data: number[]) => {
      const min = Math.min(...data) * 0.95;
      const max = Math.max(...data) * 1.05;
      const range = (max - min) || 1;
      return { min, max, range };
    };

    const drawLine = (data: number[], color: string, isOverlay = false) => {
      if (data.length < 2) return null;
      const { min, range } = getScale(data);
      const points = data.map((val, i) => {
        const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((val - min) / range) * (height - 2 * padding);
        return `${x},${y}`;
      }).join(' ');

      return (
        <g key={`${color}-${isOverlay}`}>
          <polyline
            fill="none"
            stroke={color}
            strokeWidth={isOverlay ? "2" : "4"}
            strokeDasharray={isOverlay ? "5,5" : "none"}
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
            className={`transition-all duration-700 ${isOverlay ? 'opacity-30' : 'drop-shadow-[0_8px_15px_rgba(0,0,0,0.5)]'}`}
          />
          {!isOverlay && data.map((val, i) => {
            const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
            const y = height - padding - ((val - min) / range) * (height - 2 * padding);
            return (
              <circle 
                key={i} cx={x} cy={y} r="5" fill={color} 
                className="opacity-0 hover:opacity-100 transition-opacity cursor-help"
              >
                <title>{val}</title>
              </circle>
            );
          })}
        </g>
      );
    };

    return (
      <div className="bg-white/[0.02] border border-white/5 p-8 rounded-[2.5rem] space-y-6">
        <div className="flex flex-wrap gap-6 items-center justify-between">
           <div className="flex gap-4">
              {metrics.map(m => (
                <div key={m} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[m] }}></div>
                  <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">
                    {m === 'weight' ? 'Waga' : m === 'bodyFat' ? 'Fat' : 'Pas'}
                  </span>
                </div>
              ))}
              {showOverlay && (
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 border-t-2 border-dashed border-slate-600"></div>
                  <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Poprzedni Okres</span>
                </div>
              )}
           </div>
        </div>
        
        <div className="relative">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64 md:h-80 overflow-visible">
            {[0, 0.25, 0.5, 0.75, 1].map(p => (
              <line 
                key={p} 
                x1={padding} y1={padding + p * (height - 2 * padding)} 
                x2={width - padding} y2={padding + p * (height - 2 * padding)} 
                stroke="white" strokeOpacity="0.03" strokeWidth="1" 
              />
            ))}
            
            {metrics.map(metric => {
              const data = entries.map(e => (e as any)[metric]).filter(v => v !== undefined && v !== 0);
              const overlayData = overlayEntries.map(e => (e as any)[metric]).filter(v => v !== undefined && v !== 0);
              
              return (
                <React.Fragment key={metric}>
                  {showOverlay && drawLine(overlayData, colors[metric], true)}
                  {drawLine(data, colors[metric])}
                </React.Fragment>
              );
            })}
          </svg>
        </div>
      </div>
    );
  };

  const getFilteredData = () => {
    if (!activeClient) return { current: [], overlay: [] };
    const all = activeClient.progress || [];
    let current: ProgressEntry[] = [];
    let overlay: ProgressEntry[] = [];

    const now = Date.now();
    const dayMs = 24 * 60 * 60 * 1000;

    const parseDate = (dStr: string) => {
      const parts = dStr.split('.');
      return new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0])).getTime();
    };

    const filterByDays = (days: number) => {
      const cutOff = now - days * dayMs;
      const overlayCutOff = now - 2 * days * dayMs;
      return {
        current: all.filter(e => parseDate(e.date) >= cutOff),
        overlay: all.filter(e => {
          const d = parseDate(e.date);
          return d >= overlayCutOff && d < cutOff;
        })
      };
    };

    switch(timeRange) {
      case '7d': return filterByDays(7);
      case '30d': return filterByDays(30);
      case '90d': return filterByDays(90);
      default: return { current: all, overlay: [] };
    }
  };

  const { current: chartData, overlay: overlayData } = getFilteredData();

  if (viewingProgressId && activeClient) {
    const progressData = activeClient.progress || [];

    return (
      <div className="flex-1 flex flex-col h-full bg-[#020617] view-enter overflow-hidden">
        {/* Profile Header */}
        <div className="p-4 md:p-8 border-b border-white/5 bg-[#020617]/50 backdrop-blur-md">
          <button 
            onClick={() => setViewingProgressId(null)}
            className="mb-6 text-slate-500 hover:text-white flex items-center gap-2 font-black text-[10px] uppercase tracking-widest transition-colors"
          >
            <i className="fas fa-chevron-left text-[10px]"></i> Powrót do bazy
          </button>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 bg-blue-600 rounded-[1.5rem] flex items-center justify-center text-2xl font-black shadow-2xl shadow-blue-900/40 border border-blue-400/30">
                {activeClient.name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-4">
                  <h1 className="text-2xl md:text-3xl font-black tracking-tight">{activeClient.name}</h1>
                  <div className="w-10 h-10 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
                    <i className={`fas ${getGoalIcon(activeClient.goal)} text-blue-400`}></i>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] mt-2">Strategia: {activeClient.goal}</p>
              </div>
            </div>
            
            <div className="flex gap-4">
              <button 
                onClick={() => exportClientReport(activeClient)}
                className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-6 py-4 rounded-2xl font-black uppercase tracking-widest transition-all flex items-center gap-3 text-[10px]"
              >
                <i className="fas fa-file-pdf text-blue-400"></i> Raport PDF
              </button>
              <button 
                onClick={() => {
                  setProgressFormData({ weight: activeClient.weight, bodyFat: 0, waist: 0, notes: '' });
                  setIsProgressModalOpen(true);
                }}
                className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-2xl font-black uppercase tracking-widest transition-all shadow-2xl flex items-center justify-center gap-3 active:scale-95 text-[10px]"
              >
                <i className="fas fa-plus"></i> Nowy Log
              </button>
            </div>
          </div>
        </div>

        {/* Local Tab Nav */}
        <div className="px-4 md:px-8 bg-[#020617] border-b border-white/5 flex gap-10">
          {[
            { id: 'charts', label: 'Trendy', icon: 'fa-chart-area' },
            { id: 'history', label: 'Logi', icon: 'fa-clock-rotate-left' },
            { id: 'stats', label: 'Analiza', icon: 'fa-calculator' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveProgressTab(tab.id as ProgressTab)}
              className={`py-6 text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-3 transition-all relative ${
                activeProgressTab === tab.id ? 'text-blue-400' : 'text-slate-600 hover:text-slate-400'
              }`}
            >
              <i className={`fas ${tab.icon}`}></i>
              {tab.label}
              {activeProgressTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-t-full shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 scrollbar-hide pb-24 md:pb-8">
          <div className="max-w-6xl mx-auto space-y-12">
            {activeProgressTab === 'charts' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Advanced Controls Bar */}
                <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between bg-white/[0.02] border border-white/5 p-6 rounded-3xl">
                  <div className="flex flex-wrap gap-2">
                    {[
                      { id: '7d', label: '7 Dni' },
                      { id: '30d', label: '30 Dni' },
                      { id: '90d', label: '90 Dni' },
                      { id: 'all', label: 'Wszystko' }
                    ].map(r => (
                      <button
                        key={r.id}
                        onClick={() => setTimeRange(r.id as TimeRange)}
                        className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                          timeRange === r.id ? 'bg-blue-600 text-white shadow-lg' : 'bg-white/5 text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        {r.label}
                      </button>
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-6 items-center">
                    <div className="flex gap-2">
                      {[
                        { id: 'weight', label: 'Waga' },
                        { id: 'bodyFat', label: 'Fat %' },
                        { id: 'waist', label: 'Pas' }
                      ].map(m => (
                        <button
                          key={m.id}
                          onClick={() => setCompareMetrics(prev => 
                            prev.includes(m.id) ? prev.filter(x => x !== m.id) : [...prev, m.id]
                          )}
                          className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border ${
                            compareMetrics.includes(m.id) 
                              ? 'bg-white/10 border-white/20 text-white' 
                              : 'bg-transparent border-white/5 text-slate-600 hover:text-slate-400'
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>

                    <label className="flex items-center gap-3 cursor-pointer group">
                      <div 
                        onClick={() => setShowOverlay(!showOverlay)}
                        className={`w-12 h-6 rounded-full transition-all relative border ${
                          showOverlay ? 'bg-blue-600 border-blue-400' : 'bg-white/5 border-white/10'
                        }`}
                      >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${
                          showOverlay ? 'left-7' : 'left-1'
                        }`}></div>
                      </div>
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 group-hover:text-slate-300 transition-colors">Nałóż poprzedni okres</span>
                    </label>
                  </div>
                </div>

                <AdvancedMultiChart 
                  entries={chartData} 
                  overlayEntries={overlayData} 
                  metrics={compareMetrics} 
                />

                {/* Individual Insight Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {compareMetrics.includes('weight') && chartData.length > 1 && (
                    <div className="premium-card p-6 rounded-3xl border border-white/5">
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Trend Wagi</p>
                      <p className="text-xl font-black text-blue-400">
                        {(chartData[chartData.length-1].weight - chartData[0].weight).toFixed(1)} kg
                      </p>
                      <p className="text-[9px] text-slate-600 mt-1 uppercase font-bold">W wybranym okresie</p>
                    </div>
                  )}
                  {compareMetrics.includes('bodyFat') && chartData.filter(e => e.bodyFat).length > 1 && (
                    <div className="premium-card p-6 rounded-3xl border border-white/5">
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Trend Tkanki Tłuszczowej</p>
                      <p className="text-xl font-black text-green-400">
                        {(chartData.filter(e => e.bodyFat).slice(-1)[0].bodyFat! - chartData.filter(e => e.bodyFat)[0].bodyFat!).toFixed(1)} %
                      </p>
                      <p className="text-[9px] text-slate-600 mt-1 uppercase font-bold">W wybranym okresie</p>
                    </div>
                  )}
                  {compareMetrics.includes('waist') && chartData.filter(e => e.waist).length > 1 && (
                    <div className="premium-card p-6 rounded-3xl border border-white/5">
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Trend Obwodu Pasa</p>
                      <p className="text-xl font-black text-orange-400">
                        {(chartData.filter(e => e.waist).slice(-1)[0].waist! - chartData.filter(e => e.waist)[0].waist!).toFixed(1)} cm
                      </p>
                      <p className="text-[9px] text-slate-600 mt-1 uppercase font-bold">W wybranym okresie</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeProgressTab === 'history' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-12">
                {[...progressData].reverse().map((entry) => (
                  <div key={entry.id} className="bg-white/5 border border-white/5 rounded-[1.5rem] p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:bg-white/[0.08] transition-colors group">
                    <div className="flex items-center gap-6 min-w-[140px]">
                      <div className="w-12 h-12 rounded-2xl bg-slate-900 flex items-center justify-center text-[10px] font-black text-slate-500 border border-white/10">{entry.date.split('.')[0]}.{entry.date.split('.')[1]}</div>
                      <div>
                        <p className="text-lg font-black text-white">{entry.weight} kg</p>
                        <p className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Waga</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:flex items-center gap-10 flex-1">
                      {entry.bodyFat && (
                        <div>
                          <p className="text-lg font-black text-green-400">{entry.bodyFat}%</p>
                          <p className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Body Fat</p>
                        </div>
                      )}
                      {entry.waist && (
                        <div>
                          <p className="text-lg font-black text-orange-400">{entry.waist} cm</p>
                          <p className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Pas</p>
                        </div>
                      )}
                      <div className="col-span-2 md:col-span-1 border-l border-white/5 pl-8 flex-1">
                        <p className="text-xs text-slate-400 leading-relaxed italic group-hover:text-slate-300 transition-colors">{entry.notes || 'Brak uwag technicznych dla tego pomiaru.'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeProgressTab === 'stats' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="premium-card rounded-[2.5rem] p-10 flex flex-col">
                  <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-500 mb-8 border-b border-white/5 pb-6">Dynamika Transformacji</h3>
                  <div className="space-y-8 flex-1">
                    {[
                      { label: 'Waga Startowa', val: progressData[0]?.weight || activeClient.weight, unit: 'kg' },
                      { label: 'Waga Aktualna', val: activeClient.weight, unit: 'kg', color: 'text-blue-400' },
                      { label: 'Bilans Całkowity', val: activeClient.weight - (progressData[0]?.weight || activeClient.weight), unit: 'kg', diff: true }
                    ].map((s, i) => (
                      <div key={i} className="flex justify-between items-center bg-white/[0.02] p-5 rounded-2xl border border-white/5">
                        <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{s.label}</span>
                        <span className={`text-lg font-black ${s.color || 'text-white'} ${s.diff ? (s.val <= 0 ? 'text-green-400' : 'text-red-400') : ''}`}>
                          {s.diff && s.val > 0 ? '+' : ''}{typeof s.val === 'number' ? s.val.toFixed(1) : s.val} {s.unit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="premium-card rounded-[2.5rem] p-10 flex flex-col">
                  <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-500 mb-8 border-b border-white/5 pb-6">Założenia Operacyjne</h3>
                  <div className="flex-1 space-y-8">
                    <div className="p-6 bg-blue-600/5 border border-blue-500/20 rounded-3xl">
                      <div className="flex items-center gap-3 mb-4">
                         <i className={`fas ${getGoalIcon(activeClient.goal)} text-blue-400`}></i>
                         <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Cel Priorytetowy</p>
                      </div>
                      <p className="text-white text-lg leading-relaxed font-black tracking-tight">{activeClient.goal}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {isProgressModalOpen && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
            <div className="bg-[#0f172a] w-full max-w-lg rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10">
              <div className="p-8 md:p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h2 className="text-lg font-black tracking-tight uppercase">Logowanie Danych</h2>
                <button onClick={() => setIsProgressModalOpen(false)} className="w-10 h-10 rounded-full hover:bg-white/5 text-slate-500 transition-all"><i className="fas fa-times"></i></button>
              </div>
              <form onSubmit={handleAddProgress} className="p-8 md:p-10 space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Waga Bieżąca (KG)</label>
                  <input required type="number" step="0.1" value={progressFormData.weight || ''} onChange={e => setProgressFormData({...progressFormData, weight: parseFloat(e.target.value)})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Body Fat (%)</label>
                    <input type="number" step="0.1" value={progressFormData.bodyFat || ''} onChange={e => setProgressFormData({...progressFormData, bodyFat: parseFloat(e.target.value)})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Obwód Pasa (CM)</label>
                    <input type="number" step="0.1" value={progressFormData.waist || ''} onChange={e => setProgressFormData({...progressFormData, waist: parseFloat(e.target.value)})} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Notatka Operacyjna</label>
                  <textarea value={progressFormData.notes} onChange={e => setProgressFormData({...progressFormData, notes: e.target.value})} rows={3} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 resize-none text-sm" placeholder="..." />
                </div>
                <div className="pt-6">
                  <button type="submit" className="w-full py-5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black uppercase tracking-widest transition-all shadow-2xl shadow-blue-900/40 border border-blue-400/20 active:scale-[0.98]">Zapisz Parametry</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-6 md:p-12 max-w-7xl mx-auto w-full h-full overflow-y-auto scrollbar-hide view-enter pb-24 md:pb-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight mb-3">Baza Podopiecznych</h1>
          <p className="text-slate-500 font-medium text-sm">Zarządzanie parametrami i historią Twoich klientów.</p>
        </div>
        <button 
          onClick={openAddModal}
          className="bg-white text-black hover:bg-slate-200 px-10 py-5 rounded-2xl font-black uppercase tracking-widest transition-all shadow-2xl flex items-center justify-center gap-3 active:scale-95 text-[10px]"
        >
          <i className="fas fa-plus text-[10px]"></i> Nowy Profil
        </button>
      </div>

      <div className="mb-12 relative max-w-lg">
        <i className="fas fa-search absolute left-6 top-1/2 -translate-y-1/2 text-slate-600 text-xs"></i>
        <input 
          type="text"
          placeholder="Szukaj podopiecznego..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-slate-900/50 border border-white/5 rounded-2xl py-5 pl-14 pr-6 focus:outline-none focus:ring-1 focus:ring-blue-500/50 text-sm transition-all shadow-inner"
        />
      </div>

      {filteredClients.length === 0 ? (
        <div className="premium-card rounded-[2.5rem] p-24 flex flex-col items-center text-center">
          <div className="w-24 h-24 bg-slate-800/30 rounded-[2rem] flex items-center justify-center mb-10 border border-white/5">
            <i className="fas fa-users-slash text-3xl text-slate-700"></i>
          </div>
          <h3 className="text-2xl font-black mb-4 tracking-tight">Lista jest pusta</h3>
        </div>
      ) : (
        <div className="space-y-4 max-w-4xl mx-auto">
          {filteredClients.map((client) => {
            const isExpanded = expandedClientIds.has(client.id);
            return (
              <div 
                key={client.id} 
                className={`premium-card rounded-[1.5rem] md:rounded-[2rem] overflow-hidden transition-all duration-300 border border-white/5 ${
                  isExpanded ? 'p-8 md:p-10' : 'p-0'
                }`}
              >
                {/* Collapsed Header / Always Visible Strip */}
                <div 
                  onClick={() => toggleExpand(client.id)}
                  className={`flex items-center justify-between cursor-pointer group transition-all ${
                    isExpanded ? 'mb-8 pb-8 border-b border-white/5' : 'py-5 px-8 md:px-10 hover:bg-white/[0.02]'
                  }`}
                >
                  <div className="flex items-center gap-4 md:gap-6 min-w-0">
                    <div className={`flex-shrink-0 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center text-white font-black transition-all ${
                      isExpanded ? 'w-14 h-14 text-xl' : 'w-10 h-10 text-xs'
                    }`}>
                      {client.name.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <h3 className={`font-black tracking-tight truncate ${isExpanded ? 'text-2xl md:text-3xl' : 'text-sm md:text-base'}`}>
                        {client.name}
                      </h3>
                      {!isExpanded && (
                         <p className="text-[10px] text-slate-600 font-black uppercase tracking-widest mt-0.5 flex items-center gap-2">
                           <i className={`fas ${getGoalIcon(client.goal)} text-blue-500/50`}></i>
                           {client.goal}
                         </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {!isExpanded && (
                      <div className="hidden sm:flex items-center gap-6 mr-4">
                         <div className="text-right">
                           <p className="text-[9px] font-black text-slate-700 uppercase tracking-widest">Waga</p>
                           <p className="text-xs font-black text-blue-400">{client.weight}kg</p>
                         </div>
                         <div className="text-right">
                           <p className="text-[9px] font-black text-slate-700 uppercase tracking-widest">Wiek</p>
                           <p className="text-xs font-black text-slate-300">{client.age}l</p>
                         </div>
                      </div>
                    )}
                    <button className={`w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center transition-all ${
                      isExpanded ? 'bg-blue-600 text-white' : 'bg-white/5 text-slate-600 group-hover:text-white group-hover:bg-white/10'
                    }`}>
                      <i className={`fas ${isExpanded ? 'fa-chevron-up' : 'fa-chevron-down'} text-[10px]`}></i>
                    </button>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="animate-in fade-in slide-in-from-top-4 duration-300">
                    <div className="flex justify-between items-start mb-8">
                       <div className="w-11 h-11 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
                          <i className={`fas ${getGoalIcon(client.goal)} text-blue-400 text-lg`}></i>
                       </div>
                       <div className="flex gap-2">
                         <button onClick={(e) => { e.stopPropagation(); openEditModal(client); }} className="w-11 h-11 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all border border-white/5"><i className="fas fa-pen text-xs"></i></button>
                         <button onClick={(e) => { e.stopPropagation(); setClientToDelete(client); }} className="w-11 h-11 flex items-center justify-center rounded-xl bg-white/5 hover:bg-red-500/10 text-slate-500 hover:text-red-500 transition-all border border-white/5"><i className="fas fa-trash-alt text-xs"></i></button>
                       </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-8">
                      <div className="bg-white/5 rounded-3xl p-6 border border-white/5">
                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Parametry Bieżące</p>
                        <p className="text-xl font-black text-blue-400">{client.weight} <span className="text-[10px] text-slate-600 font-bold">KG</span></p>
                      </div>
                      <div className="bg-white/5 rounded-3xl p-6 border border-white/5">
                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Informacje Wiekowe</p>
                        <p className="text-xl font-black text-slate-300">{client.age} <span className="text-[10px] text-slate-600 font-bold">LAT</span></p>
                      </div>
                    </div>

                    <button 
                      onClick={(e) => { e.stopPropagation(); setViewingProgressId(client.id); }}
                      className="w-full py-5 mb-8 rounded-2xl bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white text-[10px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all border border-blue-500/20 active:scale-95 shadow-xl"
                    >
                      <i className="fas fa-chart-line"></i> Pełna Analiza Postępów
                    </button>

                    <div className="space-y-5 bg-black/20 p-6 rounded-3xl border border-white/5">
                       <div className="flex items-start gap-5">
                         <div className="w-10 h-10 rounded-2xl bg-red-500/10 flex items-center justify-center flex-shrink-0 text-red-500 border border-red-500/20"><i className="fas fa-bullseye text-xs"></i></div>
                         <div className="min-w-0">
                           <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Strategia Operacyjna</p>
                           <p className="text-sm font-bold text-slate-300 leading-relaxed">{client.goal}</p>
                         </div>
                       </div>
                       {client.notes && (
                         <div className="pt-4 border-t border-white/5">
                           <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-2">Uwagi Techniczne</p>
                           <p className="text-xs text-slate-500 leading-relaxed italic">{client.notes}</p>
                         </div>
                       )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modern Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-xl rounded-[3rem] overflow-hidden shadow-2xl border border-white/10">
            <div className="p-8 md:p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="text-xl font-black uppercase tracking-tight">{editingClient ? 'Edytuj Parametry' : 'Nowy Podopieczny'}</h2>
              <button onClick={closeModal} className="w-12 h-12 rounded-full hover:bg-white/5 text-slate-500 transition-all"><i className="fas fa-times"></i></button>
            </div>
            <form onSubmit={handleSubmit} className="p-8 md:p-10 space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Identyfikacja</label>
                <div className="relative">
                  <i className="fas fa-user absolute left-5 top-1/2 -translate-y-1/2 text-slate-600 text-xs"></i>
                  <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl py-5 pl-12 pr-6 text-white focus:outline-none focus:border-blue-500/50 font-bold" placeholder="Imię i nazwisko" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Wiek</label>
                  <input required type="number" value={formData.age || ''} onChange={e => setFormData({...formData, age: parseInt(e.target.value)})} className="w-full bg-white/5 border border-white/10 rounded-2xl py-5 px-6 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Waga Start (KG)</label>
                  <input required type="number" step="0.1" value={formData.weight || ''} onChange={e => setFormData({...formData, weight: parseFloat(e.target.value)})} className="w-full bg-white/5 border border-white/10 rounded-2xl py-5 px-6 text-white focus:outline-none focus:border-blue-500/50 font-bold" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center px-1">
                   <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Cel strategiczny</label>
                   <div className="flex items-center gap-2 text-[10px] font-black text-blue-400 uppercase tracking-widest bg-blue-600/10 px-3 py-1 rounded-lg">
                      <i className={`fas ${getGoalIcon(formData.goal)}`}></i>
                      <span>Typ: {getGoalIcon(formData.goal).split('-').pop()}</span>
                   </div>
                </div>
                <input required type="text" value={formData.goal} onChange={e => setFormData({...formData, goal: e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-2xl py-5 px-6 text-white focus:outline-none focus:border-blue-500/50 font-bold" placeholder="np. Redukcja tkanki tłuszczowej" />
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest ml-1">Notatki techniczne</label>
                <textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} rows={3} className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white focus:outline-none focus:border-blue-500/50 resize-none text-sm font-medium leading-relaxed" placeholder="..." />
              </div>
              <div className="pt-8">
                <button type="submit" className="w-full py-6 rounded-3xl bg-blue-600 hover:bg-blue-500 text-white font-black uppercase tracking-[0.2em] transition-all shadow-2xl shadow-blue-900/40 border border-blue-400/20 active:scale-[0.98]">Zapisz w Bazie Danych</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {clientToDelete && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-6 bg-black/95 backdrop-blur-2xl animate-in zoom-in-95 duration-200">
          <div className="bg-[#0f172a] p-12 rounded-[3rem] max-w-sm w-full text-center border border-red-500/20 shadow-2xl">
            <div className="w-24 h-24 bg-red-500/10 text-red-500 rounded-[2rem] flex items-center justify-center mx-auto mb-8 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
              <i className="fas fa-user-xmark text-3xl"></i>
            </div>
            <h2 className="text-2xl font-black mb-4 tracking-tight">Usunąć profil?</h2>
            <p className="text-slate-500 mb-10 text-sm font-medium leading-relaxed">Usunięcie profilu <b>{clientToDelete.name}</b> spowoduje bezpowrotną utratę wszystkich logów i historii postępów.</p>
            <div className="flex gap-4">
              <button onClick={() => setClientToDelete(null)} className="flex-1 py-5 rounded-2xl bg-white/5 font-black uppercase tracking-widest text-slate-400 hover:bg-white/10 transition-all text-[10px]">Anuluj</button>
              <button onClick={() => { onDelete(clientToDelete.id); setClientToDelete(null); }} className="flex-1 py-5 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black uppercase tracking-widest transition-all shadow-xl shadow-red-900/30 text-[10px]">Usuń Trwale</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsManager;
