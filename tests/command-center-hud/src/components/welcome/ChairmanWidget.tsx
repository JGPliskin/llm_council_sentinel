import React from 'react';
import { Chairman } from '../../types';

interface ChairmanWidgetProps {
  data: Chairman;
}

export const ChairmanWidget: React.FC<ChairmanWidgetProps> = ({ data }) => {
  return (
    <div className="absolute top-4 right-4 z-10 hidden md:flex flex-col items-end pointer-events-none opacity-80">
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="text-hud-cyan font-orbitron text-xs tracking-[0.2em] uppercase">
            System Overseer
          </div>
          <div className="text-hud-text font-rajdhani font-bold text-sm tracking-wider">
            {data.name}
          </div>
        </div>
        <div className="relative w-10 h-10 rounded-full border border-hud-cyan/50 p-[2px]">
            <img 
                src={data.avatarUrl} 
                alt="Chairman" 
                className="w-full h-full rounded-full object-cover grayscale opacity-80"
            />
            {/* Online Dot */}
            <div className="absolute bottom-0 right-0 w-2 h-2 bg-green-500 rounded-full shadow-[0_0_5px_#22c55e]"></div>
        </div>
      </div>
      <div className="mt-1 flex gap-1">
        <div className="w-16 h-[2px] bg-hud-cyan/30"></div>
        <div className="w-4 h-[2px] bg-hud-cyan"></div>
      </div>
    </div>
  );
};