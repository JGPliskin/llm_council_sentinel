import React, { useState, useRef, useEffect } from 'react';
import { ChairmanWidget } from './welcome/ChairmanWidget';
import { CouncilorCard } from './welcome/CouncilorCard';
import { InfoPanel } from './welcome/InfoPanel';
import { CommandInput } from './welcome/CommandInput';

export function WelcomeScreen({ onStart, councilors = [], chairman = null, selectedIds: initialSelectedIds, onToggleId }) {
    // -------------------------------------------------------------------------
    // 1. State Management
    // -------------------------------------------------------------------------
    // Local UI State
    const [focusedId, setFocusedId] = useState(null);
    const [stickyId, setStickyId] = useState(null);
    const [inputValue, setInputValue] = useState('');

    const carouselRef = useRef(null);

    // -------------------------------------------------------------------------
    // 2. Interaction Handlers
    // -------------------------------------------------------------------------

    // Update stickyId when focusedId changes to a valid ID
    useEffect(() => {
        if (focusedId) {
            setStickyId(focusedId);
        }
    }, [focusedId]);

    // PC Hover
    const handleHover = (id) => {
        setFocusedId(id);
    };

    // Mobile Scroll Snap Logic
    const handleScroll = () => {
        if (!carouselRef.current) return;
        const container = carouselRef.current;
        const center = container.scrollLeft + container.clientWidth / 2;

        let closestId = null;
        let minDistance = Infinity;

        Array.from(container.children).forEach((child) => {
            // Find the card container
            const childCenter = child.offsetLeft + child.clientWidth / 2;
            const distance = Math.abs(center - childCenter);

            if (distance < minDistance) {
                minDistance = distance;
                closestId = child.getAttribute('data-id');
            }
        });

        // Threshold to trigger focus (e.g., within 50% of card width)
        if (closestId && closestId !== focusedId) {
            setFocusedId(closestId);
        }
    };

    // Engage
    const handleEngage = (finalInput) => {
        if (initialSelectedIds.length > 0) {
            onStart(finalInput, initialSelectedIds);
        }
    };

    // -------------------------------------------------------------------------
    // 3. InfoPanel Data Resolution
    // -------------------------------------------------------------------------
    // Priority: focused > sticky > firstSelected > default > chairman
    const getActiveData = () => {
        let idToFind = focusedId || stickyId;

        if (!idToFind && initialSelectedIds.length > 0) {
            // Use first selected
            idToFind = Array.from(initialSelectedIds)[0];
        }

        let data = councilors.find(c => c.id === idToFind);

        if (!data && councilors.length > 0) {
            data = councilors[0]; // Default to first available
        }

        return data || chairman;
    };

    return (
        <div className="relative w-full h-full flex flex-col overflow-hidden bg-hud-bg text-white">

            {/* Background Ambience */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-grid-floor"></div>
                <div className="absolute inset-0 bg-vignette"></div>
                <div className="absolute inset-0 bg-scanline"></div>
                <div className="absolute inset-0 bg-cyan-sweep opacity-30"></div>
            </div>

            {/* Header */}
            <header className="relative z-20 flex-shrink-0 px-4 md:px-6 py-2 md:py-4 flex justify-between items-start">
                <div>
                    <h1 className="text-hud-cyan font-orbitron font-black text-xl md:text-2xl tracking-[0.2em] uppercase text-shadow-glow">
                        Mission Logs
                    </h1>
                    <div className="flex items-center gap-2 mt-0.5 md:mt-1">
                        <div className="w-1.5 h-1.5 bg-hud-cyan rounded-full animate-pulse"></div>
                        <span className="text-[9px] md:text-[10px] font-mono text-hud-muted tracking-widest">SYSTEM ONLINE // {initialSelectedIds.length} UNITS ENGAGED</span>
                    </div>
                </div>
                <ChairmanWidget data={chairman} />
            </header>

            {/* Main Content (Hangar) */}
            <main className="relative z-10 flex-1 flex flex-col items-center justify-start pt-4 md:justify-center md:pt-0 w-full max-w-7xl mx-auto">

                {/* Desktop Grid */}
                <div className="hidden md:flex flex-wrap justify-center gap-6 lg:gap-8 perspective-1000 my-4">
                    {councilors.map(c => (
                        <CouncilorCard
                            key={c.id}
                            data={c}
                            isSelected={initialSelectedIds.includes(c.id)}
                            isFocused={focusedId === c.id}
                            onToggle={(id) => onToggleId(id)}
                            onHover={handleHover}
                        />
                    ))}
                </div>

                {/* Mobile Carousel - Resized & Re-spaced for Input Visibility */}
                <div
                    ref={carouselRef}
                    onScroll={handleScroll}
                    className="md:hidden w-full flex overflow-x-auto snap-x snap-mandatory gap-4 px-[50vw] py-4 no-scrollbar scroll-smooth"
                    style={{ paddingLeft: 'calc(50vw - 88px)', paddingRight: 'calc(50vw - 88px)' }} // Centering allowance for 176px card
                >
                    {councilors.map(c => (
                        <div key={c.id} data-id={c.id} className="snap-center shrink-0">
                            <CouncilorCard
                                key={c.id}
                                data={c}
                                isSelected={initialSelectedIds.includes(c.id)}
                                isFocused={focusedId === c.id}
                                onToggle={(id) => onToggleId(id)}
                                onHover={() => { }} // Mobile doesn't hover
                            />
                        </div>
                    ))}
                </div>

                {/* Bottom Control Deck - Added background and z-index to prevent underlap issues */}
                <div className="w-full flex flex-col items-center mt-2 md:mt-4 pb-6 md:pb-12 px-4 gap-4 md:gap-6 z-20 bg-gradient-to-t from-hud-bg via-hud-bg to-transparent">
                    {/* Info Panel */}
                    <InfoPanel data={getActiveData()} />

                    {/* Input */}
                    <CommandInput
                        value={inputValue}
                        onChange={setInputValue}
                        onEngage={handleEngage}
                        isReady={initialSelectedIds.length > 0}
                    />
                </div>

            </main>

        </div>
    );
}
