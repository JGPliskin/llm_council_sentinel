import React, { useState } from 'react';
import { Globe, Terminal, Shield, ChevronRight, CheckCircle2 } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';

const PROTOCOL_PRESETS = [
    { id: 'p1', title: 'Philosophy Shield', icon: 'Shield', prompt: 'Analyze this ethical dilemma through deontological and utilitarian lenses.' },
    { id: 'p2', title: 'Code Review', icon: 'Brain', prompt: 'Review this code for security vulnerabilities and performance bottlenecks.' },
    { id: 'p3', title: 'Global Strategy', icon: 'Globe', prompt: 'Propose a geopolitical strategy for this crisis scenario.' },
];

export function WelcomeScreen({ onStart, councilors = [], selectedIds = [], onToggleId }) {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputValue.trim() && selectedIds.length > 0) onStart(inputValue);
    };

    const activeCouncilors = councilors.filter(c => c.active !== false);

    return (
        <div className="flex-1 flex flex-col items-center justify-center relative overflow-y-auto overflow-x-hidden bg-zinc-950 p-4 pb-40 min-h-full">
            {/* Background */}
            <div className="absolute inset-0 bg-grid-pattern opacity-10 animate-pulse pointer-events-none"></div>

            {/* Hero Badge */}
            <div className="relative z-10 flex flex-col items-center mb-6 mt-4 md:mt-0 animate-in zoom-in fade-in duration-700">
                <h1 className="text-2xl md:text-4xl font-black text-white tracking-tighter uppercase mb-1 text-center drop-shadow-lg">
                    System Online
                </h1>
                <p className="text-orange-500 font-mono text-[10px] md:text-xs tracking-[0.3em] uppercase opacity-80 animate-pulse text-center">
                    Council Assembled // Waiting for Directive
                </p>
            </div>

            {/* --- COUNCIL SELECTION AREA --- */}
            <div className="w-full max-w-4xl z-10 mb-8">
                <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-12">

                    {/* Council Members Group */}
                    <div className="flex flex-col items-center">
                        <div className="text-[9px] font-bold text-zinc-600 mb-2 uppercase tracking-widest">Select Councilors</div>
                        <div className="flex gap-3 md:gap-5 flex-wrap justify-center">
                            {activeCouncilors.map((agent) => {
                                const isSelected = selectedIds.includes(agent.id);
                                const uiConfig = getCouncilorUIConfig(agent.id);
                                const color = uiConfig.color;

                                return (
                                    <button
                                        key={agent.id}
                                        onClick={() => onToggleId(agent.id)}
                                        className={`
                        group relative flex flex-col items-center transition-all duration-300
                        ${isSelected ? 'opacity-100 scale-100' : 'opacity-40 scale-95 grayscale hover:grayscale-0 hover:opacity-70'}
                      `}
                                    >
                                        <div
                                            className={`
                        relative w-12 h-12 md:w-16 md:h-16 rounded-full flex items-center justify-center text-xl md:text-3xl border-2 transition-all
                        ${isSelected ? 'bg-zinc-900' : 'border-zinc-700 bg-zinc-950'}
                        `}
                                            style={{
                                                borderColor: isSelected ? `var(--accent-${color})` : undefined,
                                                boxShadow: isSelected ? `0 0 15px var(--accent-${color})` : undefined
                                            }}
                                        >
                                            {agent.avatar}
                                            {isSelected && (
                                                <div className="absolute -top-1 -right-1 bg-teal-500 text-zinc-900 rounded-full p-0.5 border-2 border-zinc-900">
                                                    <CheckCircle2 className="w-3 h-3 md:w-4 md:h-4" />
                                                </div>
                                            )}
                                        </div>
                                        <span className={`mt-2 text-[9px] md:text-[10px] font-bold uppercase tracking-wide ${isSelected ? 'text-zinc-200' : 'text-zinc-600'}`}>
                                            {agent.name}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Separator */}
                    <div className="hidden md:block w-px h-16 bg-zinc-800/50"></div>

                    {/* Note: Chairman is auto-included usually or not selectable here? 
                Spec says Chairman calculates Consensus in Stage 3.
                We might display him just for show as in Refactor.
            */}
                    <div className="flex flex-col items-center">
                        <div className="text-[9px] font-bold text-zinc-600 mb-2 uppercase tracking-widest">Chairman</div>
                        <div className="flex flex-col items-center opacity-100">
                            <div className="relative w-14 h-14 md:w-20 md:h-20 rounded-full flex items-center justify-center text-2xl md:text-4xl border-2 border-yellow-500/50 bg-yellow-900/10 shadow-[0_0_20px_rgba(234,179,8,0.2)]">
                                🧠
                            </div>
                            <span className="mt-2 text-[9px] md:text-[10px] font-bold uppercase tracking-wide text-yellow-500/80">
                                Chairman
                            </span>
                        </div>
                    </div>

                </div>
            </div>

            {/* --- INPUT FIELD --- */}
            <div className="w-full max-w-2xl z-10 animate-in slide-in-from-bottom-4 fade-in duration-1000 delay-200 px-2 md:px-0 mb-6">
                <form onSubmit={handleSubmit} className="relative group">
                    <div className="absolute -top-5 left-0 flex gap-4 text-[9px] font-mono text-zinc-600 uppercase opacity-70">
                        <span className="flex items-center gap-1"><Terminal className="w-3 h-3" /> Input_Stream: Active</span>
                    </div>

                    <div className="relative flex items-center bg-black border border-zinc-700 p-1 group-focus-within:border-orange-500 transition-colors shadow-2xl">
                        <div className="px-3 text-orange-500">
                            <ChevronRight className="w-5 h-5 animate-pulse" />
                        </div>
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={selectedIds.length === 0 ? "Select at least one councilor..." : "Enter directive..."}
                            disabled={selectedIds.length === 0}
                            className="flex-1 bg-transparent border-none outline-none text-zinc-200 font-mono text-sm h-10 md:h-12 placeholder-zinc-700 disabled:cursor-not-allowed"
                            autoFocus
                        />
                        <button
                            type="submit"
                            disabled={!inputValue.trim() || selectedIds.length === 0}
                            className="px-4 py-2 bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 border-l border-zinc-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase text-xs font-bold tracking-wider"
                        >
                            Init
                        </button>
                    </div>
                </form>
            </div>

            {/* Separator / OR */}
            <div className="flex items-center gap-4 w-full max-w-2xl mb-6 z-10 opacity-40">
                <div className="h-px bg-zinc-800 flex-1"></div>
                <span className="text-[9px] font-mono text-zinc-600 uppercase tracking-widest">OR LOAD PROTOCOL</span>
                <div className="h-px bg-zinc-800 flex-1"></div>
            </div>

            {/* --- PRESET CARDS --- */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 w-full max-w-2xl z-10 px-2 md:px-0">
                {PROTOCOL_PRESETS.map((preset, idx) => (
                    <button
                        key={preset.id}
                        onClick={() => {
                            if (selectedIds.length > 0) onStart(preset.prompt);
                        }}
                        disabled={selectedIds.length === 0}
                        className="group relative bg-zinc-900/30 border border-zinc-800/80 p-3 text-left hover:border-zinc-500 hover:bg-zinc-800 transition-all animate-in slide-in-from-bottom-2 fade-in duration-500 disabled:opacity-30 disabled:cursor-not-allowed"
                        style={{ animationDelay: `${400 + (idx * 100)}ms` }}
                    >
                        <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-zinc-950 rounded border border-zinc-800 group-hover:border-zinc-600 transition-colors shrink-0">
                                {preset.icon === 'Shield' && <Shield className="w-3 h-3 text-orange-400" />}
                                {preset.icon === 'Brain' && <Terminal className="w-3 h-3 text-blue-400" />}
                                {preset.icon === 'Globe' && <Globe className="w-3 h-3 text-teal-400" />}
                            </div>
                            <div className="flex flex-col">
                                <h3 className="text-zinc-300 font-bold uppercase tracking-wide text-[10px] md:text-xs group-hover:text-white transition-colors">{preset.title}</h3>
                                <div className="text-[8px] text-zinc-600 font-mono uppercase">PROT_0{idx + 1}</div>
                            </div>
                        </div>

                        {/* Simplified Corner Accents */}
                        <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r border-zinc-800 group-hover:border-white/50 transition-colors"></div>
                        <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l border-zinc-800 group-hover:border-white/50 transition-colors"></div>
                    </button>
                ))}
            </div>
        </div>
    );
}
