import React, { useEffect, useState } from 'react';

export const InfoPanel = ({ data }) => {
    // Local state for smooth transition
    const [displayData, setDisplayData] = useState(data);
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        if (data?.id !== displayData?.id) {
            setIsFading(true);
            const timer = setTimeout(() => {
                setDisplayData(data);
                setIsFading(false);
            }, 150); // Maches CSS duration
            return () => clearTimeout(timer);
        }
    }, [data, displayData]);

    if (!displayData) return <div className="h-32 w-full invisible"></div>;

    const { name, role, description } = displayData;

    return (
        <div className="w-full max-w-4xl min-h-[120px] flex gap-4 md:gap-6 items-start py-4 px-2 md:px-0">
            {/* Decorative Indicator */}
            <div className="hidden md:flex flex-col items-center gap-1 mt-1">
                <div className="w-2 h-2 bg-hud-cyan rounded-sm shadow-[0_0_8px_cyan]"></div>
                <div className="w-px h-full bg-gradient-to-b from-hud-cyan/50 to-transparent min-h-[60px]"></div>
            </div>

            <div
                className={`flex-1 transition-all duration-150 ease-out ${isFading ? 'opacity-0 translate-y-1' : 'opacity-100 translate-y-0'}`}
            >
                {/* Header */}
                <div className="flex flex-wrap items-baseline gap-x-2 md:gap-x-3 mb-1 md:mb-2">
                    <h3 className="text-lg md:text-2xl font-black font-orbitron tracking-widest text-hud-text uppercase">
                        UNIT: {name}
                    </h3>
                    {role && (
                        <span className="text-[10px] md:text-xs font-mono text-hud-cyan uppercase tracking-wider bg-hud-cyan/10 px-1.5 md:px-2 py-0.5 rounded border border-hud-cyan/20">
                             // {role}
                        </span>
                    )}
                </div>

                {/* Body */}
                <p className="font-rajdhani text-sm md:text-xl text-hud-muted leading-relaxed max-w-2xl">
                    {description}
                </p>
            </div>
        </div>
    );
};
