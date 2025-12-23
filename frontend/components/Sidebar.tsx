
import React from 'react';
import { AppView } from '../types';

interface SidebarProps {
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  activeView, 
  onViewChange, 
  isCollapsed, 
  onToggleCollapse 
}) => {
  const navItems = [
    { id: AppView.CHAT, icon: 'fa-terminal', label: 'Panel AI' },
    { id: AppView.SAVED, icon: 'fa-folder-closed', label: 'Biblioteka' },
    { id: AppView.CLIENTS, icon: 'fa-user-group', label: 'Ludzie' },
    { id: AppView.CALENDAR, icon: 'fa-calendar-day', label: 'Kalendarz' },
    { id: AppView.SETTINGS, icon: 'fa-sliders', label: 'Konfiguracja' },
  ];

  return (
    <aside className={`h-full bg-[#020617] border-r border-white/5 flex flex-col transition-all duration-500 ease-in-out relative z-50 ${
      isCollapsed ? 'w-20' : 'w-72'
    }`}>
      <div className={`p-8 mb-4 flex items-center gap-4 ${isCollapsed ? 'justify-center' : ''}`}>
        <div onClick={onToggleCollapse} className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center cursor-pointer shadow-2xl hover:scale-105 transition-all">
          <i className="fas fa-bolt text-black text-xl"></i>
        </div>
        {!isCollapsed && (
          <div className="animate-in fade-in duration-700">
            <h1 className="text-lg font-black tracking-tighter uppercase leading-none">Coach<span className="text-blue-500">OS</span></h1>
            <p className="text-[8px] font-black tracking-[0.3em] text-slate-600 uppercase mt-1">Personal Assistant</p>
          </div>
        )}
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center rounded-2xl transition-all duration-300 ${isCollapsed ? 'justify-center p-4' : 'gap-5 p-4'} ${
                isActive ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20' : 'text-slate-600 hover:text-white hover:bg-white/5'
              }`}
            >
              <i className={`fas ${item.icon} text-sm w-5 flex-shrink-0 flex justify-center`}></i>
              {!isCollapsed && <span className="text-sm font-bold tracking-tight">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {!isCollapsed && (
        <div className="p-8">
          <div className="bg-white/5 p-6 rounded-[1.5rem] border border-white/5">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Status</p>
            <p className="text-xs font-bold text-blue-400">System aktywny</p>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;