import React, { useRef } from 'react';
import { Terminal, ChevronRight, Shield, Globe, Cpu } from 'lucide-react';

const PROTOCOL_PRESETS = [
    { id: 'p1', title: 'Philosophy Shield', icon: Shield, prompt: 'Analyze this ethical dilemma through deontological and utilitarian lenses.' },
    { id: 'p2', title: 'Code Review', icon: Cpu, prompt: 'Review this code for security vulnerabilities and performance bottlenecks.' },
    { id: 'p3', title: 'Global Strategy', icon: Globe, prompt: 'Propose a geopolitical strategy for this crisis scenario.' },
];

export const CommandInput = ({ value, onChange, onEngage, isReady }) => {
    const inputRef = useRef(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        onEngage(value);
    };

    const handlePresetClick = (prompt) => {
        onChange(prompt);
        // Direct engage as per V1.3 spec, but need to make sure state updates first or pass directly
        onEngage(prompt);
    };

    return (
        <div className="w-full max-w-5xl flex flex-col gap-4 z-20 animate-in slide-in-from-bottom-4 fade-in duration-700 delay-300">

            {/* Input Bar */}
            <form onSubmit={handleSubmit} className="relative group">
                {/* Label */}
                <div className="absolute -top-5 left-0 flex items-center gap-2 text-[9px] font-mono uppercase tracking-widest text-hud-muted transition-colors group-focus-within:text-hud-cyan">
                    <Terminal className="w-3 h-3" />
                    <span>Command_Line // Active</span>
                </div>

                <div
                    className={`
                        relative flex items-center border p-1 transition-all duration-300 shadow-2xl
                        ${isReady
                            ? 'bg-[rgba(5,10,20,0.9)] border-[rgba(6,182,212,0.3)] group-focus-within:border-hud-cyan group-focus-within:shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                            : 'bg-black/80 border-red-900/30 cursor-not-allowed opacity-80'
                        }
                    `}
                >
                    <div className={`px-3 ${isReady ? 'text-hud-cyan animate-pulse' : 'text-red-900'}`}>
                        <ChevronRight className="w-5 h-5" />
                    </div>

                    <input
                        ref={inputRef}
                        type="text"
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={isReady ? "Enter directive to deploy council..." : "COUNCIL OFFLINE // Select at least 1 unit"}
                        disabled={!isReady}
                        className={`
                            flex-1 bg-transparent border-none outline-none font-mono text-sm h-12
                            placeholder:text-[rgba(91,107,122,0.5)]
                            ${isReady ? 'text-hud-text' : 'text-red-900/50 cursor-not-allowed'}
                        `}
                        autoFocus
                    />

                    <button
                        type="submit"
                        disabled={!isReady || !value.trim()}
                        className={`
                            h-10 px-6 ml-2 border-l uppercase text-xs font-bold tracking-widest transition-all
                            ${isReady && value.trim()
                                ? 'border-[rgba(6,182,212,0.3)] text-hud-cyan hover:bg-hud-cyan hover:text-black cursor-pointer'
                                : 'border-white/5 text-white/10 cursor-not-allowed'
                            }
                        `}
                    >
                        Engage
                    </button>
                </div>
            </form>

            {/* Presets Chips */}
            <div className={`flex flex-wrap gap-2 justify-center md:justify-start transition-all duration-500 ${isReady ? 'opacity-100' : 'opacity-40 pointer-events-none filter grayscale'}`}>
                {PROTOCOL_PRESETS.map((preset) => (
                    <button
                        key={preset.id}
                        onClick={() => handlePresetClick(preset.prompt)}
                        className="
                            group flex items-center gap-2 px-3 py-1.5 
                            bg-[rgba(10,15,30,0.5)] border border-[rgba(6,182,212,0.2)] 
                            hover:bg-[rgba(6,182,212,0.1)] hover:border-[rgba(6,182,212,0.5)]
                            rounded-sm transition-all duration-200
                        "
                    >
                        <preset.icon className="w-3 h-3 text-[rgba(6,182,212,0.7)] group-hover:text-hud-cyan" />
                        <span className="text-[10px] font-mono text-hud-muted group-hover:text-hud-text uppercase tracking-wider">
                            {preset.title}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
};
