import React from 'react';
import { Character } from '../types';

interface UnitDeckProps {
  characters: Character[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  onHover: (id: string | null) => void;
}

const UnitDeck: React.FC<UnitDeckProps> = ({ characters, selectedIds, onToggle, onHover }) => {
  return (
    <div className="w-full bg-[#0a0f14]/95 backdrop-blur-md border-t border-cyber-panel z-20 relative shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
      {/* Decorative top line with markers */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyber-primary/50 to-transparent"></div>
      
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 md:py-4">
        {/* Mobile: Horizontal Snap Carousel. Desktop: Grid */}
        <div className="flex flex-nowrap overflow-x-auto snap-x snap-mandatory md:grid md:grid-cols-3 gap-3 md:gap-4 lg:gap-8 pb-1 md:pb-0 scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0">
          {characters.map((char) => {
            const isSelected = selectedIds.includes(char.id);
            
            return (
              <button
                key={char.id}
                onClick={() => onToggle(char.id)}
                onMouseEnter={() => onHover(char.id)}
                onMouseLeave={() => onHover(null)}
                className={`
                  group relative flex items-center gap-3 md:gap-4 p-2 md:p-3 overflow-hidden transition-all duration-300 flex-shrink-0 
                  w-[280px] md:w-auto snap-center text-left
                  border border-transparent rounded-sm
                  ${isSelected 
                    ? 'bg-cyber-primary/10 border-cyber-primary/50 translate-y-[-2px] md:translate-y-[-4px] shadow-[0_0_15px_rgba(0,240,255,0.15)]' 
                    : 'bg-cyber-panel/40 hover:bg-cyber-panel/60 border-white/5 hover:border-white/10 opacity-70 hover:opacity-100'}
                `}
              >
                {/* Connection Line Visual */}
                {isSelected && (
                    <div className="absolute -top-10 left-1/2 w-[1px] h-20 bg-cyber-primary/30 z-0"></div>
                )}

                {/* Corner Accents */}
                <div className={`absolute top-0 left-0 w-1 h-3 ${isSelected ? 'bg-cyber-primary' : 'bg-slate-600'} transition-colors`} />
                <div className={`absolute bottom-0 right-0 w-3 h-1 ${isSelected ? 'bg-cyber-primary' : 'bg-slate-600'} transition-colors`} />
                
                {/* Avatar (Left side of card) */}
                {/* UPDATED: Border on Top, Left, Right only. Bottom is transparent/open. */}
                <div className={`
                    relative w-10 h-10 md:w-12 md:h-12 flex-shrink-0 overflow-hidden
                    border-t border-l border-r border-b-0
                    ${isSelected ? 'border-cyber-primary shadow-[0_0_10px_rgba(0,240,255,0.3)]' : 'border-slate-600 group-hover:border-slate-400'}
                `}>
                  <img src={char.avatarUrl} alt={char.name} className="w-full h-full object-cover" />
                  {/* Status Dot */}
                  <div className={`absolute -top-1 -right-1 w-2 h-2 rounded-full ${isSelected ? 'bg-cyber-primary shadow-[0_0_5px_cyan]' : (char.status === 'ONLINE' ? 'bg-green-500' : 'bg-yellow-500')}`} />
                </div>

                {/* Info */}
                <div className="flex-1 text-left z-10 overflow-hidden min-w-0">
                    <div className="flex justify-between items-center">
                        <span className={`text-base md:text-lg font-display uppercase font-bold tracking-wider truncate mr-2 ${isSelected ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>
                        {char.name}
                        </span>
                        {isSelected ? (
                             <span className="text-[9px] md:text-[10px] font-mono text-cyber-primary animate-pulse bg-cyber-primary/10 px-1 border border-cyber-primary/30 flex-shrink-0">LINKED</span>
                        ) : (
                             <span className="text-[9px] md:text-[10px] font-mono text-slate-600 border border-slate-700 px-1 flex-shrink-0">STANDBY</span>
                        )}
                    </div>
                    
                    <div className="text-[9px] md:text-[10px] font-mono text-slate-500 group-hover:text-cyber-primary/80 truncate uppercase tracking-widest mt-0.5">
                        // {char.role}
                    </div>
                </div>

                {/* Background Scan Effect */}
                {isSelected && (
                     <div className="absolute inset-0 bg-gradient-to-r from-cyber-primary/0 via-cyber-primary/5 to-cyber-primary/0 animate-shimmer pointer-events-none" style={{backgroundSize: '200% 100%'}}></div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default UnitDeck;