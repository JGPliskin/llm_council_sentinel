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
        <div
            className="flex-1 flex flex-col items-center justify-center relative overflow-y-auto overflow-x-hidden p-4 pb-40 min-h-full"
            style={{ backgroundColor: 'var(--hud-bg)' }}
        >
            {/* Background */}
            <div className="absolute inset-0 bg-grid-pattern opacity-20 animate-pulse pointer-events-none"></div>

            {/* Hero Badge */}
            <div className="relative z-10 flex flex-col items-center mb-6 mt-4 md:mt-0 animate-in zoom-in fade-in duration-700">
                <h1 className="text-2xl md:text-4xl font-black uppercase mb-1 text-center hud-title text-shadow-glow" style={{ color: 'var(--hud-text)' }}>
                    System Online
                </h1>
                <p className="font-mono text-[10px] md:text-xs tracking-[0.3em] uppercase opacity-80 animate-pulse text-center" style={{ color: 'var(--hud-cyan)' }}>
                    Council Assembled // Waiting for Directive
                </p>
            </div>

            {/* --- COUNCIL SELECTION AREA --- */}
            <div className="w-full max-w-4xl z-10 mb-8">
                <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-12">

                    {/* Council Members Group */}
                    <div className="flex flex-col items-center">
                        <div className="text-[9px] font-bold mb-2 uppercase tracking-widest" style={{ color: 'var(--hud-cyan)' }}>Select Councilors</div>
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
                        ${isSelected ? 'opacity-100 scale-100' : 'opacity-50 scale-95 hover:opacity-80'}
                      `}
                                    >
                                        <div
                                            className="relative w-12 h-12 md:w-16 md:h-16 rounded-full flex items-center justify-center text-xl md:text-3xl border-2 transition-all"
                                            style={{
                                                borderColor: isSelected ? 'var(--hud-cyan)' : 'rgba(6, 182, 212, 0.2)',
                                                backgroundColor: isSelected ? 'rgba(5, 10, 20, 0.85)' : 'rgba(5, 10, 20, 0.7)',
                                                boxShadow: isSelected ? '0 0 12px rgba(6, 182, 212, 0.4)' : 'none'
                                            }}
                                        >
                                            {agent.avatar}
                                            {isSelected && (
                                                <div
                                                    className="absolute -top-1 -right-1 rounded-full p-0.5 border"
                                                    style={{ backgroundColor: `var(--accent-${color})`, borderColor: 'var(--hud-bg)' }}
                                                >
                                                    <CheckCircle2 className="w-3 h-3 md:w-4 md:h-4" style={{ color: 'var(--hud-bg)' }} />
                                                </div>
                                            )}
                                        </div>
                                        <span className="mt-2 text-[9px] md:text-[10px] font-bold uppercase tracking-wide" style={{ color: isSelected ? 'var(--hud-text)' : 'var(--hud-muted)' }}>
                                            {agent.name}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Separator */}
                    <div className="hidden md:block w-px h-16" style={{ backgroundColor: 'rgba(6, 182, 212, 0.2)' }}></div>

                    {/* Note: Chairman is auto-included usually or not selectable here? 
                Spec says Chairman calculates Consensus in Stage 3.
                We might display him just for show as in Refactor.
            */}
                    <div className="flex flex-col items-center">
                        <div className="text-[9px] font-bold mb-2 uppercase tracking-widest" style={{ color: 'var(--hud-cyan)' }}>Chairman</div>
                        <div className="flex flex-col items-center opacity-100">
                            <div
                                className="relative w-14 h-14 md:w-20 md:h-20 rounded-full flex items-center justify-center text-2xl md:text-4xl border-2"
                                style={{ borderColor: 'rgba(6, 182, 212, 0.3)', backgroundColor: 'rgba(5, 10, 20, 0.7)', boxShadow: '0 0 20px rgba(6, 182, 212, 0.2)' }}
                            >
                                🧠
                            </div>
                            <span className="mt-2 text-[9px] md:text-[10px] font-bold uppercase tracking-wide" style={{ color: 'var(--hud-muted)' }}>
                                Chairman
                            </span>
                        </div>
                    </div>

                </div>
            </div>

            {/* --- INPUT FIELD --- */}
            <div className="w-full max-w-2xl z-10 animate-in slide-in-from-bottom-4 fade-in duration-1000 delay-200 px-2 md:px-0 mb-6">
                <form onSubmit={handleSubmit} className="relative group">
                    <div
                        className="absolute -top-5 left-0 flex gap-4 text-[9px] font-mono uppercase opacity-70"
                        style={{ color: 'var(--hud-muted)' }}
                    >
                        <span className="flex items-center gap-1"><Terminal className="w-3 h-3" /> Input_Stream: Active</span>
                    </div>

                    <div
                        className="relative flex items-center border p-1 group-focus-within:border-cyan-400 transition-colors shadow-2xl"
                        style={{ backgroundColor: 'rgba(5, 10, 20, 0.9)', borderColor: 'rgba(6, 182, 212, 0.25)' }}
                    >
                        <div className="px-3" style={{ color: 'var(--hud-cyan)' }}>
                            <ChevronRight className="w-5 h-5 animate-pulse" />
                        </div>
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={selectedIds.length === 0 ? "Select at least one councilor..." : "Enter directive..."}
                            disabled={selectedIds.length === 0}
                            className="flex-1 bg-transparent border-none outline-none font-mono text-sm h-10 md:h-12 disabled:cursor-not-allowed hud-input"
                            style={{ color: 'var(--hud-text)' }}
                            autoFocus
                        />
                        <button
                            type="submit"
                            disabled={!inputValue.trim() || selectedIds.length === 0}
                            className="px-4 py-2 border-l transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase text-xs font-bold tracking-wider hud-button"
                        >
                            Init
                        </button>
                    </div>
                </form>
            </div>

            {/* Separator / OR */}
            <div className="flex items-center gap-4 w-full max-w-2xl mb-6 z-10 opacity-60">
                <div className="h-px flex-1" style={{ backgroundColor: 'rgba(6, 182, 212, 0.2)' }}></div>
                <span className="text-[9px] font-mono uppercase tracking-widest" style={{ color: 'var(--hud-muted)' }}>OR LOAD PROTOCOL</span>
                <div className="h-px flex-1" style={{ backgroundColor: 'rgba(6, 182, 212, 0.2)' }}></div>
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
                        className="group relative p-3 text-left transition-all animate-in slide-in-from-bottom-2 fade-in duration-500 disabled:opacity-30 disabled:cursor-not-allowed clip-corner-top-right"
                        style={{
                            backgroundColor: 'rgba(5, 10, 20, 0.75)',
                            border: '1px solid rgba(6, 182, 212, 0.25)',
                            animationDelay: `${400 + (idx * 100)}ms`
                        }}
                    >
                        <div className="flex items-center gap-3">
                            <div
                                className="p-1.5 rounded border transition-colors shrink-0"
                                style={{ backgroundColor: 'rgba(5, 10, 20, 0.9)', borderColor: 'rgba(6, 182, 212, 0.25)' }}
                            >
                                {preset.icon === 'Shield' && <Shield className="w-3 h-3" style={{ color: 'var(--hud-cyan)' }} />}
                                {preset.icon === 'Brain' && <Terminal className="w-3 h-3" style={{ color: 'var(--hud-cyan)' }} />}
                                {preset.icon === 'Globe' && <Globe className="w-3 h-3" style={{ color: 'var(--hud-cyan)' }} />}
                            </div>
                            <div className="flex flex-col">
                                <h3 className="font-bold uppercase tracking-wide text-[10px] md:text-xs transition-colors" style={{ color: 'var(--hud-text)' }}>{preset.title}</h3>
                                <div className="text-[8px] font-mono uppercase" style={{ color: 'var(--hud-muted)' }}>PROT_0{idx + 1}</div>
                            </div>
                        </div>

                        {/* Simplified Corner Accents */}
                        <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r transition-colors" style={{ borderColor: 'rgba(6, 182, 212, 0.3)' }}></div>
                        <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l transition-colors" style={{ borderColor: 'rgba(6, 182, 212, 0.3)' }}></div>
                    </button>
                ))}
            </div>
        </div>
    );
}
