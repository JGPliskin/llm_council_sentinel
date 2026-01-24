import React from 'react';
import { LogEntry } from '../types';
import { MOCK_LOGS } from '../constants';

const Sidebar: React.FC = () => {
  return (
    <div className="hidden md:flex w-64 flex-shrink-0 bg-cyber-dark/90 border-r border-cyber-panel flex-col h-full relative overflow-hidden backdrop-blur-sm">
      {/* Decorative Grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.05] pointer-events-none" />
      
      {/* Header */}
      <div className="p-6 border-b border-cyber-panel/50">
        <h1 className="font-display font-bold text-2xl tracking-widest text-cyber-primary text-shadow-glow">
          MISSION LOGS
        </h1>
        <div className="text-[10px] font-mono text-cyan-700 mt-1 flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          DEFENSE AREA: 008%
        </div>
      </div>

      {/* Action Button */}
      <div className="p-4">
        <button className="w-full bg-cyber-panel hover:bg-cyber-primary/20 border border-cyber-primary/30 text-cyber-primary font-mono text-sm py-3 px-4 transition-all duration-300 group relative overflow-hidden">
          <div className="absolute inset-0 bg-cyber-primary/10 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
          + INITIATE SESSION
        </button>
      </div>

      {/* Logs List */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-3 scrollbar-hide">
        <div className="text-xs font-mono text-cyber-secondary/50 mb-2 uppercase tracking-wider flex justify-between items-center">
            <span>Archive_Data</span>
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        </div>
        
        {MOCK_LOGS.map((log) => (
          <div 
            key={log.id} 
            className={`
              relative p-3 border-l-2 transition-all duration-200 cursor-pointer group
              ${log.active 
                ? 'border-cyber-primary bg-cyber-primary/5' 
                : 'border-slate-700 hover:border-cyber-secondary/50 hover:bg-slate-800/50'}
            `}
          >
            <div className="text-[10px] font-mono text-slate-500 mb-1 group-hover:text-cyber-primary transition-colors">
              ID {log.code}
            </div>
            <div className={`text-sm font-display truncate ${log.active ? 'text-white' : 'text-slate-400'}`}>
              {log.title}
            </div>
            
            {/* Hover Decor */}
            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyber-primary opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-cyber-panel/50 text-[10px] font-mono text-slate-600">
        <div className="flex items-center gap-2 mb-2">
           <div className="w-8 h-8 border border-slate-700 rounded-full flex items-center justify-center">
             <svg className="w-4 h-4 text-cyber-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.131A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.2-2.858.59-4.18" /></svg>
           </div>
           <div>
             <div className="text-white font-bold">ADMIN_USER</div>
             <div className="text-green-500">ACCESS_GRANTED</div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;