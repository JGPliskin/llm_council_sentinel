import React from 'react';
import { Councilor } from '../../types';

interface CouncilorCardProps {
  data: Councilor;
  isSelected: boolean;
  isFocused: boolean;
  onToggle: (id: string) => void;
  onHover?: (id: string | null) => void; // Optional for mobile
}

export const CouncilorCard: React.FC<CouncilorCardProps> = ({
  data,
  isSelected,
  isFocused,
  onToggle,
  onHover,
}) => {
  // Visual state calculation
  const isOnline = isSelected;
  
  return (
    <div
      className={`
        relative group cursor-pointer transition-all duration-300 ease-out
        ${isFocused ? 'scale-105 z-10' : 'scale-100 z-0'}
        md:w-48 md:h-72 w-56 h-80
        flex-shrink-0 snap-center
      `}
      onMouseEnter={() => onHover && onHover(data.id)}
      onMouseLeave={() => onHover && onHover(null)}
      onClick={() => onToggle(data.id)}
    >
      {/* Card Border / Frame */}
      <div 
        className={`
            absolute inset-0 border-2 clip-path-chamfer
            transition-all duration-300
            ${isOnline 
                ? 'border-hud-cyan shadow-cyan-glow bg-hud-bg-soft/80' 
                : 'border-hud-muted/30 bg-black/60'
            }
        `}
        style={{
             // Simple chamfer effect via clip-path if needed, or CSS borders. 
             // Using box-shadow for glow.
        }}
      >
        {/* Decorative Corner Markers */}
        <div className={`absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-hud-muted'}`} />
        <div className={`absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-hud-muted'}`} />
        <div className={`absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-hud-muted'}`} />
        <div className={`absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-hud-muted'}`} />

        {/* Content Container */}
        <div className="w-full h-full flex flex-col relative overflow-hidden">
            
            {/* Status Header */}
            <div className="h-8 flex items-center justify-between px-2 bg-black/40 backdrop-blur-sm z-20 border-b border-white/5">
                <span className={`font-mono text-[10px] tracking-widest ${isOnline ? 'text-hud-cyan' : 'text-hud-muted'}`}>
                    ID: {data.id.substring(0, 4).toUpperCase()}
                </span>
                <div className="flex items-center gap-1">
                     <span className={`text-[9px] font-bold ${isOnline ? 'text-hud-cyan animate-pulse' : 'text-red-900'}`}>
                         {isOnline ? 'ONLINE' : 'OFFLINE'}
                     </span>
                     <div className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-hud-cyan shadow-[0_0_5px_cyan]' : 'bg-red-900'}`} />
                </div>
            </div>

            {/* Avatar Image */}
            <div className="flex-1 relative w-full overflow-hidden">
                <img 
                    src={data.avatarUrl} 
                    alt={data.name} 
                    className={`
                        w-full h-full object-cover transition-all duration-500
                        ${isOnline ? 'grayscale-0 opacity-100' : 'grayscale opacity-40 contrast-125'}
                    `}
                />
                
                {/* Scanline Overlay (Decorative) */}
                <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] opacity-20 pointer-events-none"></div>
                
                {/* Active Overlay Tint */}
                {isOnline && (
                    <div className="absolute inset-0 bg-hud-cyan/10 pointer-events-none mix-blend-overlay" />
                )}
                
                {/* Selection Check Badge */}
                {isOnline && (
                    <div className="absolute top-2 right-2 bg-hud-cyan text-black p-1 rounded-sm shadow-lg animate-zoom-in">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                            <path fillRule="evenodd" d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-9a.75.75 0 011.06-1.06l5.353 8.03 8.493-12.739a.75.75 0 011.04-.208z" clipRule="evenodd" />
                        </svg>
                    </div>
                )}
            </div>

            {/* Footer Name */}
            <div className={`
                p-3 text-center transition-colors duration-300
                ${isOnline ? 'bg-hud-cyan/20' : 'bg-black/80'}
            `}>
                <h3 className={`font-orbitron font-bold tracking-[0.15em] text-lg ${isOnline ? 'text-white' : 'text-hud-muted'}`}>
                    {data.name}
                </h3>
                <p className="text-[10px] font-mono text-hud-muted uppercase tracking-wider truncate">
                    {data.role}
                </p>
            </div>
        </div>
      </div>
    </div>
  );
};