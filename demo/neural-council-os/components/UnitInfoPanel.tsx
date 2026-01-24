import React from 'react';
import { Character } from '../types';

interface UnitInfoPanelProps {
  character: Character | null;
}

const UnitInfoPanel: React.FC<UnitInfoPanelProps> = ({ character }) => {
  if (!character) {
    return <div className="h-16 md:h-24 w-full max-w-4xl mx-auto mb-4"></div>; // Spacer
  }

  return (
    <div className="w-full max-w-4xl mx-auto mb-2 px-4 animate-fadeIn">
      <div className="flex items-start gap-4">
          {/* Decorative Dot */}
          <div className={`mt-2 w-2 h-2 rounded-full shadow-[0_0_8px_${character.themeColor}] flex-shrink-0`} style={{ backgroundColor: character.themeColor }}></div>
          
          <div className="flex-1">
              {/* Header: Name + Role */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 mb-2">
                  <h2 className="text-xl md:text-2xl font-display font-bold text-white tracking-wider uppercase">
                      UNIT: {character.name}
                  </h2>
                  <div className="self-start sm:self-auto px-2 py-0.5 border border-slate-600 bg-slate-800/50 text-[10px] font-mono text-cyber-secondary uppercase tracking-widest">
                      // {character.role}
                  </div>
              </div>

              {/* Description Text */}
              <div className="text-slate-400 font-mono text-xs md:text-sm leading-relaxed max-w-2xl text-shadow-sm line-clamp-3 md:line-clamp-none">
                  {character.description}
              </div>
          </div>
      </div>
      
      {/* Subtle separator line */}
      <div className="mt-4 h-[1px] w-full bg-gradient-to-r from-transparent via-slate-700/50 to-transparent"></div>
    </div>
  );
};

export default UnitInfoPanel;