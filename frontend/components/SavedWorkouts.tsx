
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { SavedWorkout } from '../types';
import { exportToPDF, exportAllToPDF } from '../utils/pdfExport';

interface SavedWorkoutsProps {
  items: SavedWorkout[];
  onDelete: (id: string) => void;
  onUpdate: (item: SavedWorkout) => void;
}

const THEME_COLORS = [
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Green', value: '#10b981' },
  { name: 'Red', value: '#ef4444' },
  { name: 'Yellow', value: '#f59e0b' },
  { name: 'Purple', value: '#8b5cf6' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Cyan', value: '#06b6d4' },
];

type SortOption = 'date-desc' | 'date-asc' | 'title-asc' | 'title-desc';

const INITIAL_BATCH = 20;
const BATCH_SIZE = 10;

const SavedWorkouts: React.FC<SavedWorkoutsProps> = ({ items, onDelete, onUpdate }) => {
  const [editingItem, setEditingItem] = useState<SavedWorkout | null>(null);
  const [itemToDelete, setItemToDelete] = useState<SavedWorkout | null>(null);
  const [sharingItem, setSharingItem] = useState<SavedWorkout | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('date-desc');
  const [copyFeedback, setCopyFeedback] = useState<'link' | 'content' | null>(null);
  const [visibleCount, setVisibleCount] = useState(INITIAL_BATCH);
  
  // Export Modal States
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Ref for the editor textarea to handle cursor positioning
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset pagination when search or sort changes
  useEffect(() => {
    setVisibleCount(INITIAL_BATCH);
  }, [searchTerm, sortBy]);

  const handleEditClick = (item: SavedWorkout) => {
    setEditingItem({ ...item, color: item.color || '#3b82f6' });
  };

  const handleSaveEdit = () => {
    if (editingItem) {
      onUpdate(editingItem);
      setEditingItem(null);
    }
  };

  const confirmDelete = () => {
    if (itemToDelete) {
      onDelete(itemToDelete.id);
      setItemToDelete(null);
    }
  };

  // Markdown Formatting Helper
  const applyFormatting = (prefix: string, suffix: string = '', block: boolean = false) => {
    if (!textareaRef.current || !editingItem) return;

    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selectedText = text.substring(start, end);

    let replacement = '';
    if (block) {
      // For block elements like headers or lists, we ensure they start on a new line
      const before = text.substring(0, start);
      const after = text.substring(end);
      const isStartOfLine = start === 0 || before.endsWith('\n');
      replacement = `${isStartOfLine ? '' : '\n'}${prefix}${selectedText}${suffix}`;
      
      const newValue = before + replacement + after;
      setEditingItem({ ...editingItem, content: newValue });
      
      // Focus back and set selection
      setTimeout(() => {
        textarea.focus();
        const newPos = start + (isStartOfLine ? 0 : 1) + prefix.length + selectedText.length;
        textarea.setSelectionRange(newPos, newPos);
      }, 0);
    } else {
      // For inline elements like bold or italic
      replacement = `${prefix}${selectedText}${suffix}`;
      const newValue = text.substring(0, start) + replacement + text.substring(end);
      setEditingItem({ ...editingItem, content: newValue });

      setTimeout(() => {
        textarea.focus();
        const newStart = start + prefix.length;
        const newEnd = end + prefix.length;
        textarea.setSelectionRange(newStart, newEnd);
      }, 0);
    }
  };

  // Filter and Sort Logic
  const filteredAndSortedItems = useMemo(() => {
    let result = [...items];

    // Search
    if (searchTerm) {
      result = result.filter(item => 
        item.title.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'title-asc':
          return a.title.localeCompare(b.title);
        case 'title-desc':
          return b.title.localeCompare(a.title);
        case 'date-asc':
          return a.id.localeCompare(b.id);
        case 'date-desc':
        default:
          return b.id.localeCompare(a.id);
      }
    });

    return result;
  }, [items, searchTerm, sortBy]);

  // Pagination slicing
  const displayedItems = useMemo(() => {
    return filteredAndSortedItems.slice(0, visibleCount);
  }, [filteredAndSortedItems, visibleCount]);

  const hasMore = filteredAndSortedItems.length > visibleCount;

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + BATCH_SIZE);
  };

  // Open export modal with pre-selected filtered items
  const openExportModal = () => {
    setSelectedIds(new Set(filteredAndSortedItems.map(i => i.id)));
    setIsExportModalOpen(true);
  };

  // Export Selection Handlers
  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const selectAllFiltered = () => {
    setSelectedIds(new Set(filteredAndSortedItems.map(i => i.id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleExportSelected = () => {
    const itemsToExport = filteredAndSortedItems.filter(i => selectedIds.has(i.id));
    if (itemsToExport.length > 0) {
      exportAllToPDF(itemsToExport);
      setIsExportModalOpen(false);
    }
  };

  const handleShare = (item: SavedWorkout) => {
    const sharedCache = JSON.parse(localStorage.getItem('fitcoach_shared_cache') || '{}');
    sharedCache[item.id] = item;
    localStorage.setItem('fitcoach_shared_cache', JSON.stringify(sharedCache));
    setSharingItem(item);
  };

  const copyToClipboard = (text: string, type: 'link' | 'content') => {
    navigator.clipboard.writeText(text);
    setCopyFeedback(type);
    setTimeout(() => setCopyFeedback(null), 2000);
  };

  const generateShareLink = (id: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('share', id);
    return url.toString();
  };

  return (
    <div className="p-8 md:p-12 max-w-7xl mx-auto w-full h-full overflow-y-auto scrollbar-hide view-enter">
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight mb-2">Biblioteka Planów</h1>
          <p className="text-slate-500 font-medium">Archiwum wygenerowanych treningów i diet.</p>
        </div>
        <div className="flex items-center gap-4">
          {items.length > 0 && (
            <button 
              onClick={openExportModal}
              className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-6 py-4 rounded-2xl font-bold transition-all flex items-center gap-3 shadow-xl active:scale-95"
            >
              <i className="fas fa-file-export text-blue-400"></i> Eksportuj dane
            </button>
          )}
          <div className="bg-slate-900/50 border border-white/5 px-6 py-4 rounded-2xl text-sm font-bold flex items-center gap-3">
             <span className="w-2 h-2 rounded-full bg-blue-500"></span>
             {items.length} <span className="text-slate-500 font-medium uppercase tracking-widest text-[10px]">Planów</span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      {items.length > 0 && (
        <div className="flex flex-col lg:flex-row gap-6 mb-12">
          <div className="relative flex-1">
            <i className="fas fa-search absolute left-5 top-1/2 -translate-y-1/2 text-slate-600"></i>
            <input 
              type="text"
              placeholder="Szukaj po nazwie..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900/50 border border-white/5 rounded-2xl py-4 pl-14 pr-6 focus:outline-none focus:ring-1 focus:ring-blue-500/50 text-sm transition-all"
            />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest ml-1">Sortowanie</span>
            <select 
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="bg-slate-900/50 border border-white/5 rounded-2xl px-6 py-4 text-sm font-bold focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all text-white appearance-none cursor-pointer pr-12 min-w-[180px]"
            >
              <option value="date-desc">Najnowsze</option>
              <option value="date-asc">Najstarsze</option>
              <option value="title-asc">A-Z</option>
              <option value="title-desc">Z-A</option>
            </select>
          </div>
        </div>
      )}

      {displayedItems.length === 0 ? (
        <div className="premium-card rounded-[2.5rem] p-24 flex flex-col items-center text-center">
          <div className="w-24 h-24 bg-slate-800/30 rounded-[2rem] flex items-center justify-center mb-8 border border-white/5">
            <i className={`fas ${searchTerm ? 'fa-search' : 'fa-box-open'} text-3xl text-slate-700`}></i>
          </div>
          <h3 className="text-2xl font-bold mb-3">
            {searchTerm ? 'Brak wyników' : 'Biblioteka jest pusta'}
          </h3>
          <p className="text-slate-500 max-w-sm mx-auto font-medium">
            {searchTerm 
              ? `Nie znaleźliśmy planów pasujących do "${searchTerm}".` 
              : 'Twoje wygenerowane plany pojawią się tutaj po ich zapisaniu w panelu AI.'}
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            {displayedItems.map((item) => (
              <div 
                key={item.id} 
                className="premium-card rounded-[2.5rem] flex flex-col group overflow-hidden animate-in fade-in zoom-in-95 duration-500"
                style={{ borderTop: `6px solid ${item.color || '#3b82f6'}` }}
              >
                <div className="p-8 flex-1">
                  <div className="flex justify-between items-start mb-6">
                    <span 
                      className="text-[10px] uppercase font-black tracking-[0.2em] px-3 py-1.5 rounded-xl border"
                      style={{ 
                        backgroundColor: `${item.color || '#3b82f6'}10`, 
                        borderColor: `${item.color || '#3b82f6'}30`,
                        color: item.color || '#3b82f6' 
                      }}
                    >
                      Trening
                    </span>
                    <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">{item.date}</span>
                  </div>
                  <h3 className="text-xl font-bold mb-4 group-hover:text-blue-400 transition-colors line-clamp-2 leading-tight">{item.title}</h3>
                  <div className="text-slate-400 text-sm line-clamp-5 overflow-hidden leading-relaxed">
                    {item.content}
                  </div>
                </div>
                <div className="p-6 border-t border-white/5 flex items-center justify-between bg-white/[0.02] gap-4">
                  <div className="flex gap-1">
                    <button 
                      onClick={() => exportToPDF(item)}
                      title="Eksportuj do PDF"
                      className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-blue-600/10 text-slate-500 hover:text-blue-400 transition-all border border-transparent hover:border-blue-500/20"
                    >
                      <i className="fas fa-file-pdf"></i>
                    </button>
                    <button 
                      onClick={() => handleShare(item)}
                      title="Udostępnij"
                      className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-green-600/10 text-slate-500 hover:text-green-400 transition-all border border-transparent hover:border-green-500/20"
                    >
                      <i className="fas fa-share-alt"></i>
                    </button>
                    <button 
                      onClick={() => handleEditClick(item)}
                      title="Edytuj treść"
                      className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all border border-transparent hover:border-white/10"
                    >
                      <i className="fas fa-edit"></i>
                    </button>
                  </div>
                  <button 
                    onClick={() => setItemToDelete(item)}
                    className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-red-500/10 text-slate-500 hover:text-red-500 transition-all border border-transparent hover:border-red-500/20"
                  >
                    <i className="fas fa-trash-alt text-xs"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="mt-16 flex justify-center pb-12">
              <button 
                onClick={handleLoadMore}
                className="bg-slate-900 hover:bg-slate-800 text-white font-bold py-5 px-12 rounded-[2rem] border border-white/5 transition-all shadow-2xl hover:scale-105 active:scale-95 flex items-center gap-4 group"
              >
                <i className="fas fa-arrow-down text-blue-500 group-hover:translate-y-1 transition-transform"></i>
                Więcej planów
              </button>
            </div>
          )}
        </>
      )}

      {/* Share Modal */}
      {sharingItem && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-lg rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10">
            <div className="p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="text-2xl font-bold tracking-tight">Udostępnij</h2>
              <button onClick={() => setSharingItem(null)} className="w-10 h-10 rounded-full hover:bg-white/5 text-slate-500 transition-all"><i className="fas fa-times"></i></button>
            </div>
            <div className="p-10 space-y-8">
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-600/10 text-blue-500 rounded-[2rem] flex items-center justify-center mx-auto mb-6 border border-blue-500/20 shadow-inner">
                  <i className="fas fa-link text-2xl"></i>
                </div>
                <h3 className="font-bold text-xl mb-2">{sharingItem.title}</h3>
                <p className="text-sm text-slate-500 font-medium">Wygeneruj bezpośredni link do tego planu.</p>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-3 ml-1">Unikalny URL</label>
                  <div className="flex gap-3">
                    <input 
                      type="text" 
                      readOnly 
                      value={generateShareLink(sharingItem.id)}
                      className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs text-slate-400 focus:outline-none"
                    />
                    <button 
                      onClick={() => copyToClipboard(generateShareLink(sharingItem.id), 'link')}
                      className={`px-6 py-4 rounded-2xl text-xs font-bold transition-all shadow-xl ${
                        copyFeedback === 'link' ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-500 text-white'
                      }`}
                    >
                      {copyFeedback === 'link' ? 'Skopiowano!' : 'Kopiuj'}
                    </button>
                  </div>
                </div>

                <div className="pt-6 border-t border-white/5">
                  <button 
                    onClick={() => copyToClipboard(sharingItem.content, 'content')}
                    className={`w-full py-5 rounded-2xl text-sm font-bold flex items-center justify-center gap-3 transition-all ${
                      copyFeedback === 'content' 
                        ? 'bg-green-600/10 text-green-500 border border-green-500/30' 
                        : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'
                    }`}
                  >
                    <i className={`fas ${copyFeedback === 'content' ? 'fa-check' : 'fa-copy'}`}></i>
                    {copyFeedback === 'content' ? 'Treść skopiowana' : 'Kopiuj pełną treść'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selective Export Modal */}
      {isExportModalOpen && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-4xl rounded-[3rem] overflow-hidden flex flex-col max-h-[85vh] shadow-2xl border border-white/10">
            <div className="p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Kreator Dokumentacji</h2>
                <p className="text-sm text-slate-500 font-medium mt-1">Zaznacz plany do wygenerowania zbiorczego PDF</p>
              </div>
              <button 
                onClick={() => setIsExportModalOpen(false)}
                className="w-12 h-12 flex items-center justify-center rounded-full hover:bg-white/5 text-slate-500 transition-all"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
            
            <div className="px-10 py-6 border-b border-white/5 bg-slate-900/30 flex flex-wrap justify-between items-center gap-6">
              <div className="flex gap-3">
                <button 
                  onClick={selectAllFiltered}
                  className="text-xs font-bold px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all"
                >
                  Zaznacz widoczne
                </button>
                <button 
                  onClick={deselectAll}
                  className="text-xs font-bold px-5 py-3 rounded-xl border border-white/5 hover:bg-red-500/10 text-slate-500 hover:text-red-500 transition-all"
                >
                  Wyczyść wybór
                </button>
              </div>
              <div className="text-sm font-bold bg-blue-600/10 text-blue-400 px-6 py-3 rounded-2xl border border-blue-500/20">
                Wybrane: <span className="text-white ml-2">{selectedIds.size}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-10 space-y-4 scrollbar-hide bg-black/[0.05]">
              {filteredAndSortedItems.length === 0 ? (
                <p className="text-center text-slate-600 py-12 italic">Brak elementów do wyświetlenia.</p>
              ) : (
                filteredAndSortedItems.map((item) => (
                  <div 
                    key={item.id}
                    onClick={() => toggleSelection(item.id)}
                    className={`flex items-center gap-6 p-6 rounded-[1.5rem] border cursor-pointer transition-all ${
                      selectedIds.has(item.id) 
                        ? 'bg-blue-600/10 border-blue-500/50 shadow-inner' 
                        : 'bg-white/[0.02] border-white/5 hover:border-white/10 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-xl border-2 flex items-center justify-center transition-all ${
                      selectedIds.has(item.id) ? 'bg-blue-600 border-blue-600 shadow-lg shadow-blue-900/40' : 'border-slate-800'
                    }`}>
                      {selectedIds.has(item.id) && <i className="fas fa-check text-xs text-white"></i>}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="font-bold text-lg truncate">{item.title}</h4>
                        <span className="text-[10px] text-slate-600 font-bold uppercase">{item.date}</span>
                      </div>
                      <p className="text-xs text-slate-500 truncate font-medium">{item.content.substring(0, 100)}...</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-10 border-t border-white/5 bg-white/[0.02] flex justify-end gap-4">
              <button 
                onClick={() => setIsExportModalOpen(false)}
                className="px-8 py-4 rounded-2xl text-slate-500 hover:text-white hover:bg-white/5 transition-all font-bold"
              >
                Anuluj
              </button>
              <button 
                onClick={handleExportSelected}
                disabled={selectedIds.size === 0}
                className="px-10 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 disabled:opacity-20 disabled:pointer-events-none text-white font-bold transition-all shadow-2xl shadow-blue-900/40 flex items-center gap-3 border border-blue-400/20"
              >
                <i className="fas fa-file-pdf"></i> Generuj PDF ({selectedIds.size})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Inline Editor Modal with WYSIWYG-like Markdown Toolbar */}
      {editingItem && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-[#0f172a] w-full max-w-4xl rounded-[3rem] overflow-hidden flex flex-col max-h-[90vh] border border-white/10 shadow-2xl">
            <div className="p-10 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="text-3xl font-bold tracking-tight">Edytuj Treść Planu</h2>
              <button onClick={() => setEditingItem(null)} className="w-12 h-12 rounded-full hover:bg-white/5 text-slate-500 transition-all"><i className="fas fa-times"></i></button>
            </div>
            
            <div className="p-10 space-y-8 overflow-y-auto scrollbar-hide">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-slate-600 uppercase tracking-widest ml-1">Nazwa Dokumentu</label>
                  <input 
                    type="text"
                    value={editingItem.title}
                    onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-blue-500/50 transition-all font-bold"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-slate-600 uppercase tracking-widest ml-1">Etykieta Kolorystyczna</label>
                  <div className="flex flex-wrap gap-3 py-1">
                    {THEME_COLORS.map((color) => (
                      <button
                        key={color.value}
                        onClick={() => setEditingItem({ ...editingItem, color: color.value })}
                        className={`w-9 h-9 rounded-xl border-2 transition-all ${editingItem.color === color.value ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105 opacity-60 hover:opacity-100'}`}
                        style={{ backgroundColor: color.value }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Markdown WYSIWYG Toolbar */}
              <div className="space-y-3">
                <label className="text-[10px] font-bold text-slate-600 uppercase tracking-widest ml-1">Edytor Treści</label>
                <div className="bg-slate-900/50 border border-white/10 rounded-[2rem] overflow-hidden flex flex-col group focus-within:border-blue-500/30 transition-all shadow-inner">
                  
                  {/* Toolbar Row */}
                  <div className="bg-white/5 border-b border-white/5 p-3 flex flex-wrap items-center gap-2">
                    <div className="flex items-center gap-1 pr-3 border-r border-white/5 mr-1">
                      <button onClick={() => applyFormatting('# ', '', true)} title="Nagłówek 1" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 font-bold flex items-center justify-center transition-colors">H1</button>
                      <button onClick={() => applyFormatting('## ', '', true)} title="Nagłówek 2" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 font-bold flex items-center justify-center transition-colors">H2</button>
                    </div>
                    <div className="flex items-center gap-1 pr-3 border-r border-white/5 mr-1">
                      <button onClick={() => applyFormatting('**', '**')} title="Pogrubienie" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 flex items-center justify-center transition-colors"><i className="fas fa-bold"></i></button>
                      <button onClick={() => applyFormatting('*', '*')} title="Kursywa" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 flex items-center justify-center transition-colors"><i className="fas fa-italic"></i></button>
                    </div>
                    <div className="flex items-center gap-1 pr-3 border-r border-white/5 mr-1">
                      <button onClick={() => applyFormatting('- ', '', true)} title="Lista punktowana" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 flex items-center justify-center transition-colors"><i className="fas fa-list-ul"></i></button>
                      <button onClick={() => applyFormatting('1. ', '', true)} title="Lista numerowana" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 flex items-center justify-center transition-colors"><i className="fas fa-list-ol"></i></button>
                    </div>
                    <div className="flex items-center gap-1">
                      <button onClick={() => applyFormatting('| Kolumna 1 | Kolumna 2 |\n|---|---|\n| Dane 1 | Dane 2 |', '', true)} title="Tabela" className="w-10 h-10 rounded-xl hover:bg-white/5 text-slate-300 flex items-center justify-center transition-colors"><i className="fas fa-table"></i></button>
                    </div>
                  </div>

                  {/* Textarea */}
                  <textarea 
                    ref={textareaRef}
                    value={editingItem.content}
                    onChange={(e) => setEditingItem({ ...editingItem, content: e.target.value })}
                    rows={12}
                    className="w-full bg-transparent px-8 py-6 text-slate-300 focus:outline-none resize-none font-mono text-sm leading-relaxed min-h-[400px]"
                    placeholder="Tu wpisz treść planu lub użyj narzędzi powyżej..."
                  />
                  
                  {/* Status Bar */}
                  <div className="bg-white/[0.02] px-6 py-2 border-t border-white/5 flex justify-between items-center">
                    <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">Tryb: Markdown Engine</span>
                    <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">Znaki: {editingItem.content.length}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-10 border-t border-white/5 bg-white/[0.02] flex justify-end gap-4">
              <button onClick={() => setEditingItem(null)} className="px-8 py-4 rounded-2xl text-slate-500 font-bold hover:bg-white/5 transition-all">Porzuć zmiany</button>
              <button onClick={handleSaveEdit} className="px-10 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-2xl shadow-blue-900/40 border border-blue-400/20">Aktualizuj Plan</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {itemToDelete && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in zoom-in-95 duration-200">
          <div className="bg-[#0f172a] p-12 rounded-[3rem] max-w-sm w-full text-center border border-red-500/20 shadow-2xl">
            <div className="w-20 h-20 bg-red-500/10 text-red-500 rounded-[1.5rem] flex items-center justify-center mx-auto mb-8">
              <i className="fas fa-trash-alt text-3xl"></i>
            </div>
            <h2 className="text-2xl font-bold mb-3 tracking-tight">Usunąć plan?</h2>
            <p className="text-slate-500 mb-10 text-sm font-medium leading-relaxed">Operacja usunięcia planu <b>{itemToDelete.title}</b> jest nieodwracalna.</p>
            <div className="flex gap-4">
              <button onClick={() => setItemToDelete(null)} className="flex-1 py-4 rounded-2xl bg-white/5 font-bold hover:bg-white/10 transition-all">Wróć</button>
              <button onClick={confirmDelete} className="flex-1 py-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-bold transition-all shadow-xl shadow-red-900/30">Usuń</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SavedWorkouts;
