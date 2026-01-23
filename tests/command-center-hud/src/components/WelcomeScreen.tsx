import React, { useState, useRef, useEffect } from 'react';
import { Councilor, Chairman } from '../types';
import { COUNCILORS, CHAIRMAN } from '../constants';
import { ChairmanWidget } from './welcome/ChairmanWidget';
import { CouncilorCard } from './welcome/CouncilorCard';
import { InfoPanel } from './welcome/InfoPanel';
import { CommandInput } from './welcome/CommandInput';

interface WelcomeScreenProps {
  onStartSession: (message: string, selectedIds: string[]) => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStartSession }) => {
  // State
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set(COUNCILORS.map(c => c.id)));
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  
  // Refs
  const carouselRef = useRef<HTMLDivElement>(null);

  // Logic: Toggle Selection
  const handleToggle = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  // Logic: Handle Scroll for Mobile Carousel Focus
  const handleScroll = () => {
    if (!carouselRef.current) return;
    
    const container = carouselRef.current;
    const center = container.scrollLeft + container.clientWidth / 2;
    
    let closestId = null;
    let minDistance = Infinity;

    Array.from(container.children).forEach((child) => {
      const el = child as HTMLElement;
      const childCenter = el.offsetLeft + el.clientWidth / 2;
      const distance = Math.abs(center - childCenter);
      
      if (distance < minDistance && distance < el.clientWidth / 2) {
        minDistance = distance;
        // Assume data-id attribute is set on wrapper
        const id = el.dataset.id;
        if (id) closestId = id;
      }
    });

    if (closestId !== focusedId) {
      setFocusedId(closestId);
    }
  };

  // Derived state for display
  const focusedCouncilor = COUNCILORS.find(c => c.id === focusedId);
  
  // Handlers
  const handleEngage = () => {
    if (selectedIds.size > 0 && inputValue.trim()) {
      onStartSession(inputValue, Array.from(selectedIds));
    }
  };

  return (
    <div className="relative w-full h-screen flex flex-col overflow-hidden bg-hud-bg text-white selection:bg-hud-cyan selection:text-black">
      
      {/* Background Ambience (Layer 0) */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Grid Floor */}
        <div className="absolute bottom-0 w-full h-[50vh] bg-[linear-gradient(to_bottom,transparent_0%,rgba(6,182,212,0.1)_100%)] [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
        {/* Subtle Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[length:40px_40px]"></div>
        {/* Vignette */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#050a14_90%)]"></div>
      </div>

      {/* Header Area */}
      <header className="relative z-20 flex-shrink-0 px-6 py-4 flex justify-between items-start">
        <div>
           <h1 className="text-hud-cyan font-orbitron font-black text-2xl tracking-[0.2em] uppercase drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]">
             Mission Logs
           </h1>
           <div className="flex items-center gap-2 mt-1">
             <div className="w-2 h-2 bg-hud-cyan rounded-full animate-ping"></div>
             <span className="text-[10px] font-mono text-hud-muted tracking-widest">DEFENSE AREA: 008% // SYSTEM ONLINE</span>
           </div>
        </div>
        
        {/* Desktop Chairman Widget */}
        <ChairmanWidget data={CHAIRMAN} />
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center">
        
        {/* Section Title */}
        <div className="text-center mb-8 hidden md:block">
            <h2 className="text-3xl font-orbitron tracking-[0.3em] text-white font-medium">HANGAR BAY</h2>
            <div className="h-[1px] w-64 mx-auto bg-gradient-to-r from-transparent via-hud-cyan to-transparent mt-2 opacity-50"></div>
            <p className="text-hud-muted font-mono text-xs mt-2 tracking-wider">COUNCIL ASSEMBLED // WAITING FOR DIRECTIVE</p>
        </div>

        {/* Hangar Container */}
        <div className="w-full relative">
            
            {/* Desktop Grid Layout */}
            <div className="hidden md:flex justify-center items-center gap-8 perspective-1000">
                {COUNCILORS.map((councilor) => (
                    <div key={councilor.id} className="transform transition-transform">
                        <CouncilorCard 
                            data={councilor}
                            isSelected={selectedIds.has(councilor.id)}
                            isFocused={focusedId === councilor.id}
                            onToggle={handleToggle}
                            onHover={setFocusedId}
                        />
                    </div>
                ))}
            </div>

            {/* Mobile Carousel Layout */}
            <div 
                ref={carouselRef}
                onScroll={handleScroll}
                className="md:hidden flex overflow-x-auto snap-x snap-mandatory gap-4 px-[calc(50vw-7rem)] py-8 no-scrollbar touch-pan-x"
            >
                {COUNCILORS.map((councilor) => (
                    <div key={councilor.id} data-id={councilor.id} className="snap-center shrink-0">
                         <CouncilorCard 
                            data={councilor}
                            isSelected={selectedIds.has(councilor.id)}
                            isFocused={focusedId === councilor.id}
                            onToggle={handleToggle}
                            // Mobile doesn't use hover
                        />
                    </div>
                ))}
            </div>
        </div>

        {/* Info Panel (Description) */}
        <InfoPanel 
            councilor={focusedCouncilor} 
            defaultData={CHAIRMAN} 
        />
        
        {/* Command Input Area */}
        <CommandInput 
            value={inputValue}
            onChange={setInputValue}
            onEngage={handleEngage}
            isReady={selectedIds.size > 0}
        />

      </main>

      {/* Decorative Footer Elements */}
      <footer className="relative z-10 px-6 py-2 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-hud-muted">
         <div className="flex gap-4">
             <span>CPU: 45%</span>
             <span>MEM: 12GB</span>
             <span>NET: SECURE</span>
         </div>
         <div className="hidden md:block">
             SESSION_ID: #9B3EEB
         </div>
      </footer>

    </div>
  );
};