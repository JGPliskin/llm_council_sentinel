import React, { useState, useEffect } from 'react';

const renderStandingArt = (src, alt) => {
    return <img
        src={src}
        alt={alt}
        className="h-full w-full object-cover object-top mask-image-gradient relative z-10"
        style={{
            maskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)',
        }}
    />;
};

export const StandingArtDisplay = ({
    data,
    isFocused, // Used for highlighting or "Looking at" effect
    onInteraction // Click handler (Focus Lock)
}) => {
    // For now, we assume data.standing is available, or fallback to avatar
    const artSrc = data.standing || data.avatar;

    // Animation state for "appearance"
    const [isVisible, setIsVisible] = useState(false);
    useEffect(() => {
        setIsVisible(true);
    }, []);

    // Visual styles based on focus
    // If Focused: Bright, Hologram active
    // If Not Focused: Dim or standard
    // Since this component is ONLY rendered when selected (or in the "Stage" visualization),
    // it arguably should always be "Online". The 'focus' might just add an extra highlight.

    return (
        <div
            onClick={() => onInteraction && onInteraction(data.id)}
            className={`
                relative h-[70vh] md:h-[60vh] lg:h-[70vh] w-auto aspect-[3/5] 
                transition-all duration-700 ease-in-out transform cursor-pointer
                flex flex-col justify-end group
                ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}
            `}
        >
            {/* Holographic Frame (Top/Left/Right) - Visible on Focus or Hover */}
            <div className={`
                absolute inset-0 z-20 
                border-t-2 border-l-2 border-r-2 
                transition-colors duration-300
                pointer-events-none
                ${isFocused ? 'border-[rgba(6,182,212,0.6)] bg-[rgba(6,182,212,0.05)]' : 'border-transparent group-hover:border-[rgba(6,182,212,0.2)]'}
            `}>
                {/* Corner Accents */}
                <div className={`absolute top-0 left-0 w-2 h-8 ${isFocused ? 'bg-hud-cyan' : 'bg-transparent'} transition-colors`}></div>
                <div className={`absolute top-0 right-0 w-2 h-8 ${isFocused ? 'bg-hud-cyan' : 'bg-transparent'} transition-colors`}></div>

                {/* Scanner Line (Vertical) */}
                {isFocused && (
                    <div className="absolute inset-0 w-full h-[2px] bg-[rgba(6,182,212,0.3)] animate-[scanline_3s_linear_infinite]" style={{ backgroundSize: '100% 100%' }}></div>
                )}
            </div>

            {/* Character Image */}
            <div className={`
                h-full w-full relative transition-all duration-500
                ${isFocused ? 'filter drop-shadow-[0_0_10px_rgba(6,182,212,0.3)] brightness-110 saturate-120' : 'filter grayscale-[0.3] brightness-90'}
            `}>
                {renderStandingArt(artSrc, data.name)}

                {/* Hologram Scanlines Overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] pointer-events-none mix-blend-hard-light opacity-30"></div>
            </div>

            {/* Name Tag (Bottom) */}
            <div className={`
                absolute bottom-[10%] left-1/2 -translate-x-1/2 
                bg-black/80 border backdrop-blur px-3 py-1 
                text-[10px] font-mono uppercase tracking-widest z-30 whitespace-nowrap transition-colors
                ${isFocused ? 'border-hud-cyan text-hud-cyan' : 'border-white/10 text-slate-500'}
            `}>
                {data.name}
            </div>
        </div>
    );
};
