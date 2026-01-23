import React from 'react';

interface CommandInputProps {
  value: string;
  onChange: (val: string) => void;
  onEngage: () => void;
  isReady: boolean;
}

export const CommandInput: React.FC<CommandInputProps> = ({ value, onChange, onEngage, isReady }) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isReady && value.trim()) {
      onEngage();
    }
  };

  const isActive = isReady && value.trim().length > 0;

  return (
    <div className="w-full max-w-3xl mx-auto mt-6 md:mt-10 px-4 pb-8 md:pb-0">
      <div className="relative group">
        
        {/* Decorative Grid Lines */}
        <div className="absolute -top-4 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-hud-cyan/30 to-transparent"></div>
        
        <div className="flex items-stretch shadow-lg shadow-black/50">
          {/* Prefix Decoration */}
          <div className="hidden md:flex items-center px-4 bg-hud-bg-soft border-y border-l border-hud-muted/30 text-hud-cyan font-mono text-sm select-none">
            <span>{'>_'}</span>
          </div>

          {/* Text Input */}
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isReady ? "AWAITING COMMAND..." : "SELECT A UNIT FIRST"}
            disabled={!isReady}
            className={`
              flex-1 bg-hud-bg-soft/80 border-y border-l md:border-l-0 border-r-0 border-hud-muted/30 
              text-hud-text font-rajdhani text-lg tracking-wide
              placeholder:text-hud-muted/50
              px-4 py-4 md:py-5 focus:outline-none focus:border-hud-cyan focus:ring-0
              transition-all uppercase
              ${!isReady ? 'cursor-not-allowed opacity-50' : ''}
            `}
            autoComplete="off"
            spellCheck="false"
          />

          {/* Engage Button */}
          <button
            onClick={onEngage}
            disabled={!isActive}
            className={`
              relative px-6 md:px-10 font-orbitron font-bold tracking-widest text-sm md:text-base clip-path-slant
              transition-all duration-300 overflow-hidden
              ${isActive 
                ? 'bg-hud-cyan text-black hover:bg-white hover:shadow-[0_0_20px_rgba(6,182,212,0.6)]' 
                : 'bg-hud-muted/20 text-hud-muted cursor-not-allowed'
              }
            `}
          >
            {/* Inner border effect for clipped button */}
            <span className={`absolute inset-0 bg-gradient-to-b from-white/20 to-transparent opacity-0 transition-opacity ${isActive ? 'group-hover:opacity-50' : ''}`}></span>
            ENGAGE
          </button>
        </div>

        {/* Bottom Helper Text */}
        <div className="flex justify-between mt-2 text-[10px] md:text-xs font-mono text-hud-muted uppercase tracking-widest">
            <span>Protocol: Secure_V1</span>
            <span className={`transition-colors duration-300 ${isReady ? 'text-hud-cyan animate-pulse' : 'text-red-900'}`}>
                {isReady ? 'SYSTEM READY' : 'NO UNITS SELECTED'}
            </span>
        </div>
      </div>
    </div>
  );
};