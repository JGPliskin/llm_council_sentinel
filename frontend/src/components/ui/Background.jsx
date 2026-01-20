/**
 * Background.jsx - HUD background texture layers
 * 
 * Provides the cyberpunk grid/scanline/vignette effect.
 * Place at root level with z-index below main content.
 */
import React from 'react';

export function Background() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden"
            style={{ backgroundColor: 'var(--hud-bg)' }}>
            {/* Grid floor with perspective */}
            <div className="bg-grid-floor" />

            {/* Vignette overlay */}
            <div className="bg-vignette" />

            {/* Scanline effect */}
            <div className="bg-scanline" />

            {/* Animated cyan sweep */}
            <div className="bg-cyan-sweep" />
        </div>
    );
}

export default Background;
