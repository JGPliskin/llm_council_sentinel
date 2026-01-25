import React, { useState, useEffect, useMemo } from 'react';
import { ChairmanWidget } from './welcome/ChairmanWidget';
import { StandingArtDisplay } from './welcome/StandingArtDisplay';
import { InfoPanel } from './welcome/InfoPanel';
import { CommandInput } from './welcome/CommandInput';
import { UnitDeckList } from './UnitDeckList';
import { PanelLeftClose, PanelLeftOpen, PanelRightOpen, RotateCcw } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';

export function WelcomeScreen({
    onStart,
    councilors = [],
    chairman = null,
    selectedIds: initialSelectedIds,
    onToggleId,
    isSidebarOpen = false,
    onToggleSidebar,
    isDetailPanelOpen = false,
    onToggleDetailPanel,
    onResetSession
}) {
    // -------------------------------------------------------------------------
    // 1. State Management
    // -------------------------------------------------------------------------
    const [focusedId, setFocusedId] = useState(null); // Hover focus
    const [stickyId, setStickyId] = useState(null);   // Click "Lock" focus
    const [inputValue, setInputValue] = useState('');

    // Clear sticky focus if the stickied unit is deselected? 
    // Spec says: "Click InfoPanel 'UNLINK' -> Unit deselects." 
    // If it deselects, it disappears from stage. Sticky focus usually implies looking at the art.
    // If art is gone, maybe sticky focus should clear or fallback?
    // Let's keep it simple: Sticky is just a preference for InfoPanel.

    // -------------------------------------------------------------------------
    // 2. Data Preparation (ViewModels)
    // -------------------------------------------------------------------------
    const deckItems = useMemo(() => {
        return councilors.map(c => {
            const isSelected = initialSelectedIds.includes(c.id);
            const uiConfig = getCouncilorUIConfig(c.id);
            return {
                id: c.id,
                name: c.name,
                role: uiConfig.role || c.role || 'COUNCILOR',
                avatar: c.avatar, // standard avatar for deck
                state: isSelected ? 'linked' : 'standby',
                progress: 0, // Welcome screen has no progress
                rank: undefined,
                isActiveTab: false // or use this to indicate looking at? No, keep it simple.
            };
        });
    }, [councilors, initialSelectedIds]);

    const activeStandingArts = useMemo(() => {
        return initialSelectedIds
            .map(id => {
                const c = councilors.find(x => x.id === id);
                if (!c) return null;
                const uiConfig = getCouncilorUIConfig(c.id);
                return {
                    ...c,
                    standing: uiConfig.standing || c.avatar, // Fallback logic
                    role: uiConfig.role || c.role
                };
            })
            .filter(Boolean);
    }, [initialSelectedIds, councilors]);

    // -------------------------------------------------------------------------
    // 3. Interaction Handlers
    // -------------------------------------------------------------------------
    const handleDeckHover = (id) => {
        setFocusedId(id);
    };

    const handleDeckClick = (id) => {
        // Toggle selection
        onToggleId(id);
        // If we just clicked (selected/deselected), we might want to sticky it?
        // Spec says: UnitDeck Click -> Toggle selection.
        // It doesn't explicitly say focus it, but usually clicking implies interest.
        // Let's set sticky to this id so InfoPanel shows it immediately.
        setStickyId(id);
    };

    const handleArtClick = (id) => {
        // Spec: Focus Lock InfoPanel (No selection toggle)
        setStickyId(id);
    };

    const handleEngage = (finalInput) => {
        if (initialSelectedIds.length > 0) {
            onStart(finalInput, initialSelectedIds);
        }
    };

    // -------------------------------------------------------------------------
    // 4. InfoPanel Logic
    // Priority: Hover (focused) > Focus Locked (sticky) > Last Selected
    // -------------------------------------------------------------------------
    const getActiveData = () => {
        // 1. Hover
        if (focusedId) return councilors.find(c => c.id === focusedId);

        // 2. Sticky (Focused Lock)
        if (stickyId) return councilors.find(c => c.id === stickyId);

        // 3. Last Selected (if any)
        if (initialSelectedIds.length > 0) {
            const lastId = initialSelectedIds[initialSelectedIds.length - 1];
            return councilors.find(c => c.id === lastId);
        }

        // 4. Empty Fallback (or Chairman?)
        // Spec says "Show NO UNIT SELECTED", handled by InfoPanel passing null.
        return null;
    };

    const activeInfoData = getActiveData();

    // Augment InfoPanel data with UI config and state for properly rendering the button
    const infoPanelData = activeInfoData ? {
        ...activeInfoData,
        description: activeInfoData.description || "Waiting for neural link...",
        role: getCouncilorUIConfig(activeInfoData.id).role || activeInfoData.role,
        state: initialSelectedIds.includes(activeInfoData.id) ? 'linked' : 'standby'
    } : null;

    return (
        <div className="relative w-full h-[100dvh] flex flex-col overflow-hidden bg-hud-bg text-white selection:bg-[rgba(6,182,212,0.3)]">

            {/* Background Ambience (Deepest Layer) */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-grid-floor opacity-50"></div>
                <div className="absolute inset-0 bg-vignette"></div>
                <div className="absolute inset-0 bg-scanline opacity-30"></div>
            </div>

            {/* Header / Top Bar */}
            <header className="relative z-20 flex-shrink-0 px-4 md:px-6 py-2 md:py-4 flex justify-between items-start pointer-events-none md:pointer-events-auto">
                <div className="pointer-events-auto">
                    <h1 className="text-hud-cyan font-orbitron font-black text-xl md:text-2xl tracking-[0.2em] uppercase text-shadow-glow">
                        Mission Logs
                    </h1>
                </div>
                <div className="pointer-events-auto">
                    <ChairmanWidget data={chairman} />
                </div>
            </header>

            {/* ---------------------------------------------------------------------------
                CENTER STAGE: Standing Art
               --------------------------------------------------------------------------- */}
            <main className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
                {/* 
                  Standing Art Container 
                  - We center it vertically/horizontally.
                  - On keyboard open (mobile), we rely on CSS media queries or Height clamping 
                    but since we use absolute centering, it might overlap input if not careful.
                    Plan says: "Shrink StandingArtStage (e.g. to 20vh)".
                    We can use flex layout for the main container to push it up?
                    Actually current layout is absolute inset-0.
                */}
                <div className="
                    relative w-full max-w-6xl h-full flex items-end justify-center pb-[280px] md:pb-[240px] gap-2 lg:gap-8
                    transition-all duration-300
                    pointer-events-none
                ">
                    {/* Empty State Message in Stage */}
                    {activeStandingArts.length === 0 && (
                        <div className="absolute top-1/3 text-center opacity-50 animate-pulse">
                            <h2 className="text-2xl font-mono tracking-widest text-hud-muted">NO UNIT SELECTED</h2>
                            <p className="text-xs text-[rgba(91,107,122,0.5)] mt-2">SELECT AGENTS FROM DECK TO INITIALIZE</p>
                        </div>
                    )}

                    {activeStandingArts.map((art, index) => (
                        <div key={art.id} className="pointer-events-auto z-10 relative">
                            <StandingArtDisplay
                                data={art}
                                isFocused={focusedId === art.id || stickyId === art.id}
                                onInteraction={handleArtClick}
                            />
                        </div>
                    ))}
                </div>
            </main>

            {/* ---------------------------------------------------------------------------
                MIDDLE LAYER: InfoPanel + Input overlay
                Positioned absolutely or Flex above the bottom panel?
                Plan: "Center: StandingArt, Top Layer: InfoPanel, Bottom: Bottom Panel"
                Let's use a Column Flex for the UI layers above the stage.
               --------------------------------------------------------------------------- */}
            <div className="absolute inset-0 z-20 flex flex-col justify-end pb-[140px] md:pb-[140px] pointer-events-none">
                <div className="w-full max-w-4xl mx-auto px-4 flex flex-col gap-4 pointer-events-auto transition-all duration-300">

                    {/* Info Panel */}
                    <div className="min-h-[120px]">
                        <InfoPanel
                            data={infoPanelData}
                            onToggle={(id) => onToggleId(id)}
                        />
                    </div>

                    {/* Command Input */}
                    <div className="w-full">
                        <CommandInput
                            value={inputValue}
                            onChange={setInputValue}
                            onEngage={handleEngage}
                            isReady={initialSelectedIds.length > 0} // Disabled if 0
                        />
                    </div>
                </div>
            </div>

            {/* ---------------------------------------------------------------------------
                BOTTOM PANEL CONTAINER (Status Bar + UnitDeck)
                Fixed at bottom. Same markup structure as TacticalHUD (Stages).
               --------------------------------------------------------------------------- */}
            <div className="
                absolute bottom-0 left-0 w-full z-30
                bg-hud-bg-soft border-t border-hud-cyan-soft backdrop-blur-md
                flex flex-col
                pb-[env(safe-area-inset-bottom)]
                min-h-[120px] md:min-h-[140px]
            ">
                {/* Status Bar */}
                <div className="
                    w-full flex items-center gap-4 px-4 md:px-6 py-1.5 md:py-2 
                    border-b border-hud-cyan-soft bg-black/60
                ">
                    {/* Controls */}
                    <div className="flex items-center gap-3 border-r border-white/10 pr-4 mr-0 md:mr-2">
                        <button
                            onClick={() => onToggleSidebar && onToggleSidebar()}
                            className="text-hud-muted hover:text-white transition-colors"
                            title="Toggle Sidebar"
                        >
                            {isSidebarOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
                        </button>
                        <button
                            onClick={() => onToggleDetailPanel && onToggleDetailPanel()}
                            className="text-hud-muted hover:text-white transition-colors"
                            title="Toggle Detail Panel"
                        >
                            {isDetailPanelOpen ? <PanelRightOpen size={14} className="rotate-180" /> : <PanelRightOpen size={14} />}
                        </button>
                        <button
                            onClick={() => onResetSession && onResetSession()}
                            className="text-hud-muted hover:text-white transition-colors"
                            title="Reset Session"
                        >
                            <RotateCcw size={14} />
                        </button>
                    </div>

                    {/* System Status */}
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-hud-cyan animate-pulse shadow-[0_0_5px_cyan]"></div>
                        <span className="text-[9px] md:text-[10px] font-mono font-bold tracking-[0.2em] uppercase text-hud-cyan">
                            STAGE [STANDBY]
                        </span>
                        <span className="hidden md:inline text-[9px] font-mono tracking-widest text-hud-muted">
                            // SYSTEM_IDLE
                        </span>
                    </div>

                    <div className="flex-1"></div>

                    {/* Decoration right */}
                    <div className="hidden md:flex text-[9px] font-mono gap-4 text-hud-muted">
                        <span>CPU: 12%</span>
                        <span>MEM: 4GB</span>
                        <span>NET: OK</span>
                    </div>
                </div>

                {/* Unit Deck Area */}
                <div className="flex-1 flex items-center w-full py-2">
                    <UnitDeckList
                        items={deckItems}
                        onItemClick={handleDeckClick}
                        onItemHover={handleDeckHover}
                    />
                </div>
            </div>

        </div>
    );
}
