import React, { useState } from 'react';

const renderAvatar = (avatar, alt) => {
    // Basic check, assume backend sends valid paths starting with /
    return <img src={avatar} alt={alt} className="w-full h-full object-cover object-[center_20%]" />;
};

export const CouncilorCard = ({
    data,
    isSelected,
    isFocused,
    onToggle,
    onHover
}) => {
    const [isRippling, setIsRippling] = useState(false);

    const handleClick = () => {
        // Trigger Ripple
        setIsRippling(true);
        setTimeout(() => setIsRippling(false), 300);
        onToggle(data.id);
    };

    const isOnline = isSelected;

    // Status Styles
    let borderStyle = "";
    let glowStyle = "";
    let imageStyle = "";
    let opacityStyle = "";

    if (isOnline) {
        borderStyle = "border-hud-cyan";
        // REMOVED: animate-pulse from the container to avoid "scary" flashing
        // Added: stronger shadow and keeping the border solid/bright
        glowStyle = "shadow-[0_0_20px_rgba(6,182,212,0.5)]";
        imageStyle = "grayscale-0 contrast-100";
        opacityStyle = "opacity-100";
    } else if (isFocused) {
        borderStyle = "border-hud-cyan/60 bg-hud-cyan/5";
        glowStyle = "shadow-[0_0_10px_rgba(6,182,212,0.2)]"; // Static Highlight
        // Keep unselected focused cards somewhat desaturated but brighter than idle
        imageStyle = "grayscale opacity-80 contrast-125";
        opacityStyle = "opacity-100";
    } else {
        borderStyle = "border-white/10";
        glowStyle = "";
        // IDLE STATE: 
        // 1. Fully desaturated (grayscale)
        // 2. Lower opacity to look "dim"
        imageStyle = "grayscale brightness-50 contrast-125 sepia-[.3]";
        opacityStyle = "opacity-40 group-hover:opacity-60";
    }

    return (
        <div
            className={`
                group relative flex-shrink-0 cursor-pointer select-none transition-all duration-300
                w-[176px] h-[240px] md:w-[270px] md:h-[360px]
                snap-center
                ${isFocused ? 'scale-105 z-10' : 'scale-100 z-0'}
            `}
            onMouseEnter={() => onHover && onHover(data.id)}
            onMouseLeave={() => onHover && onHover(null)}
            onClick={handleClick}
        >
            {/* Main Frame */}
            <div
                className={`
                    absolute inset-0 border-2 bg-hud-bg-soft 
                    transition-all duration-300 overflow-hidden
                    ${borderStyle} ${glowStyle} ${opacityStyle}
                `}
            >
                {/* Avatar */}
                <div className={`absolute inset-0 transition-all duration-500 ${imageStyle}`}>
                    {renderAvatar(data.avatar, data.name)}
                </div>

                {/* Scanline Overlay (Always on but subtle) */}
                <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.6)_50%)] bg-[length:100%_4px] opacity-10 pointer-events-none"></div>

                {/* Status Overlay UI */}
                <div className="absolute inset-x-0 bottom-0 p-3 md:p-4 bg-gradient-to-t from-black/90 via-black/60 to-transparent flex flex-col items-center">
                    {/* Role Label (Bottom) */}
                    <div className={`
                        text-[8px] md:text-[9px] font-mono tracking-[0.2em] uppercase mb-0.5 md:mb-1
                        ${isOnline ? 'text-hud-cyan' : 'text-hud-muted'}
                    `}>
                        {data.role || "COUNCILOR"}
                    </div>
                    {/* Name */}
                    <h3 className={`
                        text-base md:text-xl font-bold font-orbitron tracking-widest uppercase
                        ${isOnline ? 'text-white' : 'text-zinc-500'}
                    `}>
                        {data.name}
                    </h3>

                    {/* Status Dot */}
                    <div className="flex items-center gap-1.5 mt-1.5 md:mt-2">
                        <div className={`w-1 md:w-1.5 h-1 md:h-1.5 rounded-full ${isOnline ? 'bg-hud-cyan shadow-[0_0_5px_cyan] animate-pulse' : 'bg-red-900/50'}`} />
                        <span className={`text-[7px] md:text-[8px] font-bold ${isOnline ? 'text-hud-cyan' : 'text-red-900/50'}`}>
                            {isOnline ? 'ONLINE' : 'OFFLINE'}
                        </span>
                    </div>
                </div>

                {/* Corner Decorations */}
                <div className={`absolute top-0 left-0 w-2 h-2 md:w-3 md:h-3 border-t-2 border-l-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-white/10'}`} />
                <div className={`absolute top-0 right-0 w-2 h-2 md:w-3 md:h-3 border-t-2 border-r-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-white/10'}`} />
                <div className={`absolute bottom-0 left-0 w-2 h-2 md:w-3 md:h-3 border-b-2 border-l-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-white/10'}`} />
                <div className={`absolute bottom-0 right-0 w-2 h-2 md:w-3 md:h-3 border-bottom-2 border-r-2 transition-colors ${isOnline ? 'border-hud-cyan' : 'border-white/10'}`} />
            </div>

            {/* Mobile Ripple Effect */}
            {isRippling && (
                <div className="absolute inset-0 animate-ping border-2 border-hud-cyan rounded-sm opacity-50 z-20 pointer-events-none"></div>
            )}
        </div>
    );
};
