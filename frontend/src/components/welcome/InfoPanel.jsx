import React, { useEffect, useState } from 'react';
import { Link, Unlink } from 'lucide-react';

export const InfoPanel = ({ data, onToggle }) => {
    // Local state for smooth transition
    const [displayData, setDisplayData] = useState(data);
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        const shouldUpdate =
            (!data && displayData) ||
            (data && (!displayData || data.id !== displayData.id || data.state !== displayData.state));

        if (!shouldUpdate) return;

        setIsFading(true);
        const timer = setTimeout(() => {
            setDisplayData(data || null);
            setIsFading(false);
        }, 150); // Matches CSS duration
        return () => clearTimeout(timer);
    }, [data, displayData]);

    // Empty State
    if (!displayData) {
        return (
            <div className="w-full max-w-4xl min-h-[120px] flex flex-col items-center justify-center border border-white/5 bg-black/20 rounded-sm">
                <div className="text-hud-muted font-mono tracking-widest text-xs animate-pulse">NO UNIT SELECTED</div>
                <div className="text-[10px] text-[rgba(91,107,122,0.6)] font-mono mt-1 tracking-wider">SELECT A COUNCILOR TO BEGIN</div>
            </div>
        );
    }

    const { id, name, role, description, state } = displayData;
    const isLinked = state === 'linked';
    const isChairman = id === 'chairman';

    return (
        <div className="w-full max-w-4xl min-h-[120px] flex gap-4 md:gap-6 items-start py-4 px-2 md:px-0 relative">
            {/* Decorative Indicator */}
            <div className="hidden md:flex flex-col items-center gap-1 mt-1">
                <div className="w-2 h-2 bg-hud-cyan rounded-sm shadow-[0_0_8px_cyan]"></div>
                <div className="w-px h-full bg-gradient-to-b from-[rgba(6,182,212,0.5)] to-transparent min-h-[60px]"></div>
            </div>

            <div
                className={`flex-1 transition-all duration-150 ease-out flex justify-between gap-4 ${isFading ? 'opacity-0 translate-y-1' : 'opacity-100 translate-y-0'}`}
            >
                <div className="flex-1">
                    {/* Header */}
                    <div className="flex flex-wrap items-baseline gap-x-2 md:gap-x-3 mb-1 md:mb-2">
                        <h3 className="text-lg md:text-2xl font-black font-orbitron tracking-widest text-hud-text uppercase">
                            UNIT: {name}
                        </h3>
                        {role && (
                            <span className="text-[10px] md:text-xs font-mono text-hud-cyan uppercase tracking-wider bg-[rgba(6,182,212,0.1)] px-1.5 md:px-2 py-0.5 rounded border border-[rgba(6,182,212,0.2)]">
                                // {role}
                            </span>
                        )}
                    </div>

                    {/* Body */}
                    <p className="font-rajdhani text-sm md:text-xl text-hud-muted leading-relaxed max-w-2xl text-shadow-sm">
                        {description}
                    </p>
                </div>

                {/* Right Action Button (LINK/UNLINK) */}
                {!isChairman && onToggle && (
                    <button
                        onClick={() => onToggle(id)}
                        className={`
                            group flex flex-col items-center justify-center
                            w-16 h-14 md:w-20 md:h-16
                            border transition-all duration-300
                            ${isLinked
                                ? 'border-red-500/30 bg-red-900/10 hover:bg-red-900/30 text-red-400'
                                : 'border-[rgba(6,182,212,0.3)] bg-[rgba(6,182,212,0.05)] hover:bg-[rgba(6,182,212,0.1)] text-hud-cyan'
                            }
                        `}
                    >
                        {isLinked ? <Unlink size={20} className="mb-1" /> : <Link size={20} className="mb-1" />}
                        <span className="text-[9px] font-mono font-bold tracking-widest uppercase">
                            {isLinked ? 'UNLINK' : 'LINK'}
                        </span>
                    </button>
                )}
            </div>
        </div>
    );
};
