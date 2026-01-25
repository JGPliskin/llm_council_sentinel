import React from 'react';

/**
 * UnitDeckCard
 * 
 * Pure visual component for a single card in the UnitDeck.
 * Visual state is derived entirely from the `data` prop (ViewModel).
 * 
 * ViewModel Structure (data):
 * - id: string
 * - name: string
 * - role: string
 * - avatar: string
 * - state: 'linked' | 'standby' | 'skipped'
 * - progress: number (0-100)
 * - rank: number (optional)
 * - isActiveTab: boolean
 */
export const UnitDeckCard = ({
    data,
    onClick,
    onHover
}) => {
    const { id, name, role, avatar, state, progress, rank, isActiveTab } = data;
    const isLinked = state === 'linked';
    const isSkipped = state === 'skipped';

    // Interaction Handlers
    const handleClick = (e) => {
        if (onClick) onClick(id);
    };

    const handleMouseEnter = () => {
        if (onHover) onHover(id);
    };

    const handleMouseLeave = () => {
        if (onHover) onHover(null);
    };

    return (
        <button
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            style={{ WebkitTapHighlightColor: 'transparent' }}
            className={`
                group relative flex items-center gap-2 md:gap-4 p-1.5 md:p-3 overflow-hidden transition-[background-color,border-color,box-shadow,transform] duration-10 flex-shrink-0 
                w-full md:w-auto text-left
                border border-transparent rounded-sm outline-none focus:outline-none focus-visible:outline-none focus-visible:ring-0
                ${isLinked
                    ? 'bg-[rgba(6,182,212,0.1)] border-[rgba(6,182,212,0.5)] translate-y-[-2px] md:translate-y-[-4px] shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                    : 'bg-[rgba(5,10,20,0.4)] hover:bg-[rgba(5,10,20,0.6)] border-white/5 hover:border-white/10 opacity-70 hover:opacity-100'
                }
                ${isActiveTab ? 'bg-[rgba(6,182,212,0.12)] border-[rgba(6,182,212,0.7)] shadow-[0_0_20px_rgba(6,182,212,0.35)]' : ''}
            `}
        >
            {/* Connection Line Visual (Linked only) */}
            {isLinked && (
                <div className="absolute -top-10 left-1/2 w-[1px] h-20 bg-[rgba(6,182,212,0.3)] z-0"></div>
            )}

            {/* Corner Accents */}
            <div className={`absolute top-0 left-0 w-1 h-3 ${isLinked ? 'bg-hud-cyan' : 'bg-slate-600'} transition-colors`} />
            <div className={`absolute bottom-0 right-0 w-3 h-1 ${isLinked ? 'bg-hud-cyan' : 'bg-slate-600'} transition-colors`} />

            {/* Avatar */}
            <div className={`
                hidden md:flex relative w-10 h-10 md:w-12 md:h-12 flex-shrink-0 overflow-hidden
                border-t border-l border-r border-b-0
                ${isLinked ? 'border-hud-cyan shadow-[0_0_10px_rgba(6,182,212,0.3)]' : 'border-slate-600 group-hover:border-slate-400'}
            `}>
                {avatar ? (
                    <img src={avatar} alt={name} className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full bg-slate-800 flex items-center justify-center text-xs">?</div>
                )}

                {/* Status Dot */}
                <div className={`
                    absolute -top-1 -right-1 w-2 h-2 rounded-full 
                    ${isLinked ? 'bg-hud-cyan shadow-[0_0_5px_cyan]' : 'bg-yellow-500'}
                `} />
            </div>

            {/* Info Section */}
            <div className="flex-1 text-left z-10 overflow-hidden min-w-0">
                <div className="flex justify-between items-center">
                    <span className={`text-sm md:text-lg font-orbitron uppercase font-bold tracking-wider truncate mr-2 ${isLinked ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>
                        {name}
                    </span>

                    {/* State Badge */}
                    {isSkipped ? (
                        <span className="text-[8px] md:text-[10px] font-mono text-red-400 border border-red-900/50 bg-red-900/20 px-1 flex-shrink-0">SKIPPED</span>
                    ) : isLinked ? (
                        <span className="text-[8px] md:text-[10px] font-mono text-hud-cyan animate-breathe bg-[rgba(6,182,212,0.1)] px-1 border border-[rgba(6,182,212,0.3)] flex-shrink-0">LINKED</span>
                    ) : (
                        <span className="text-[8px] md:text-[10px] font-mono text-slate-600 border border-slate-700 px-1 flex-shrink-0">STANDBY</span>
                    )}
                </div>

                <div className="flex justify-between items-end mt-0.5">
                    <div className="hidden md:block text-[9px] md:text-[10px] font-mono text-slate-500 group-hover:text-[rgba(6,182,212,0.8)] truncate uppercase tracking-widest">
                        // {role || 'COUNCILOR'}
                    </div>
                    {/* Rank Badge (Stage 3) */}
                    {typeof rank === 'number' && (
                        <div className="text-[10px] font-bold font-mono text-hud-cyan bg-[rgba(6,182,212,0.1)] px-1 border-l border-[rgba(6,182,212,0.3)]">
                            #{rank}
                        </div>
                    )}
                </div>
            </div>

            {/* Horizontal Progress Bar (Stage 1 & 2) */}
            {/* Note: In Stage 3, progress should be passed as 0 or undefined to hide this */}
            {progress > 0 && (
                <div
                    className="absolute bottom-0 left-0 h-1 bg-[rgba(6,182,212,0.4)] transition-all duration-500 ease-out"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                >
                    <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
            )}

            {/* Background Shimmer (Linked only) */}
            {isLinked && (
                <div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(6,182,212,0.05)] to-transparent animate-shimmer pointer-events-none"
                    style={{ backgroundSize: '200% 100%' }}
                ></div>
            )}

        </button>
    );
};
