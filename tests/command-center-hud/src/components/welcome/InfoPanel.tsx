import React from 'react';
import { Councilor, Chairman } from '../../types';

interface InfoPanelProps {
  councilor?: Councilor; // Can be null if nothing focused
  defaultData?: Chairman; // Fallback to Chairman data
}

export const InfoPanel: React.FC<InfoPanelProps> = ({ councilor, defaultData }) => {
  const activeData = councilor || defaultData;
  
  if (!activeData) return <div className="h-24 md:h-32" />;

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 px-4 md:px-0 min-h-[120px]">
      <div className="border-l-2 border-hud-cyan pl-4 bg-gradient-to-r from-hud-cyan/5 to-transparent py-2">
        <div className="flex items-baseline gap-3 mb-2">
            <h2 className="text-hud-cyan font-orbitron font-bold text-xl md:text-2xl tracking-widest uppercase">
            {councilor ? 'UNIT SPECIFICATIONS' : 'SYSTEM STATUS'}
            </h2>
            <span className="text-hud-muted font-mono text-xs">
                // {activeData.role.toUpperCase()}
            </span>
        </div>
        
        <p className="text-hud-text/90 font-rajdhani text-lg md:text-xl leading-relaxed animate-pulse-fast">
            {activeData.description}
        </p>
        
        {!councilor && (
            <div className="mt-2 text-xs font-mono text-hud-muted">
                {"> WAITING FOR INSPECTION..."}
            </div>
        )}
      </div>
    </div>
  );
};