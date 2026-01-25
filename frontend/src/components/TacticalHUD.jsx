import React, { useMemo } from 'react';
import { Scale, PanelLeftClose, PanelLeftOpen, PanelRightOpen, RotateCcw } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';
import { UnitDeckList } from './UnitDeckList';
import './TacticalHUD_v2.css';

/**
 * TacticalHUD
 * 
 * The Bottom Panel Container for Stage views (Stage 1, 2, 3).
 * Renders Status Bar + UnitDeckList.
 */
function TacticalHUD({
    stage,
    agentProgress,
    aggregateRankings,
    resolvedCouncilors,
    consensusUnlocked,
    stage3Complete = false,
    hasViewedConsensus,
    onConsensusClick,
    stage2Skipped = false,
    activeTab = null,
    onTabSelect,
    selectedAgentIds = [],
    allCouncilors = [],
    // Controls
    isSidebarOpen,
    onToggleSidebar,
    isDetailPanelOpen,
    onToggleDetailPanel,
    onResetSession,
}) {
    // -------------------------------------------------------------------------
    // 1. Data Preparation (ViewModels)
    // -------------------------------------------------------------------------
    const deckItems = useMemo(() => {
        // IDLE Stage: Show selected agents or placeholders?
        // Usually TacticalHUD is only for Active Stages. "idle" might be legacy or specific.
        // Assuming "idle" means just show selected.
        if (stage === 'idle') {
            return (selectedAgentIds || []).map(id => {
                const c = allCouncilors.find(x => x.id === id);
                if (!c) return null;
                const uiConfig = getCouncilorUIConfig(id);
                return {
                    id: c.id,
                    name: c.name,
                    role: uiConfig.role || c.role || 'COUNCILOR',
                    avatar: c.avatar,
                    state: 'standby', // Idle -> Standby
                    progress: 0,
                    rank: undefined,
                    isActiveTab: activeTab === c.id
                };
            }).filter(Boolean);
        }

        // Active Stages (1, 2, 3)
        // Determine order:
        // Stage 3 -> Sorted by Rank
        // Others -> resolvedCouncilors order (usually fixed)
        let sortedList = [...(resolvedCouncilors || [])];

        if (stage === 'stage3' && aggregateRankings && aggregateRankings.length > 0) {
            // Sort by rank
            sortedList = [...aggregateRankings]
                .sort((a, b) => a.rank - b.rank)
                .map(ranking => {
                    // Merge with standard info
                    const info = resolvedCouncilors.find(c => c.id === ranking.councilor_id) || {};
                    return { ...info, ...ranking };
                });
        }

        return sortedList.map(c => {
            const id = c.id || c.councilor_id; // handle ranking object vs councilor object divergence
            const uiConfig = getCouncilorUIConfig(id);
            const name = c.name || uiConfig.name || id;
            const avatar = c.avatar || uiConfig.avatar; // Ranking might lack avatar, fallback to UI config or Prop

            // State Logic
            // In stages, they are "Active" / "Linked" effectively if present.
            // We can use 'standby' if they are present but inactive?
            // Let's use 'standby' as base, and maybe 'linked' if they are currently "speaking" or activeTab?
            // Spec doesn't strictly define state mapping for stages other than "appearance".
            // Let's assume they are "standby" style but with Progress/Rank overlays.
            // OR, if activeTab is selected, maybe highlight that one?
            // UnitDeckCard highlights activeTab via `isActiveTab` prop separately from state.
            // Let's set state to 'standby' effectively, unless we want the "Linked" glow for everyone?
            // Demo likely keeps them "Standard".

            // Check if Skipped (Stage 2)
            const isSkippedEntry = stage === 'stage2' && stage2Skipped;
            // Note: `stage2Skipped` is a global flag usually? Or per agent? 
            // Existing code used `showSkippedBadge` based on global `stage2Skipped`.
            // But existing code applied it to *every* agent?
            // "showSkippedBadge = stage === 'stage2' && stage2Skipped;"
            // Yes, it seems global. If stage 2 is skipped, everyone is marked skipped?

            // Progress
            // Stage 1/2: Show progress. Stage 3: Hide progress (0).
            const progressVal = (stage === 'stage1' || stage === 'stage2') ? (agentProgress[id] || 0) : 0;

            // Rank
            // Stage 3 only.
            const rankVal = (stage === 'stage3') ? (c.rank || c.average_rank) : undefined;

            return {
                id: id,
                name: name,
                role: uiConfig.role || 'COUNCILOR',
                avatar: avatar,
                state: isSkippedEntry ? 'skipped' : 'standby', // Default to standby style, let overlays do the work
                progress: progressVal,
                rank: rankVal,
                isActiveTab: activeTab === id
            };
        });
    }, [stage, resolvedCouncilors, aggregateRankings, agentProgress, activeTab, selectedAgentIds, allCouncilors, stage2Skipped]);

    // -------------------------------------------------------------------------
    // 2. Interaction
    // -------------------------------------------------------------------------
    const handleDeckClick = (id) => {
        if (onTabSelect) onTabSelect(id);
    };

    // -------------------------------------------------------------------------
    // 3. Render
    // -------------------------------------------------------------------------
    const stageClass = stage === 'stage1' ? 'border-orange-600/50'
        : stage === 'stage2' ? 'border-blue-600/50'
            : stage === 'stage3' ? 'border-hud-cyan'
                : 'border-hud-cyan-soft';

    return (
        <div className={`
            absolute bottom-0 left-0 w-full z-30 md:static
            bg-hud-bg-soft border-t backdrop-blur-md
            flex flex-col
            min-h-[120px] md:min-h-[140px]
            pb-[env(safe-area-inset-bottom)]
            transition-colors duration-500
            ${stageClass}
        `}>
            {/* ---------------------------------------------------------------------------
                STATUS BAR
               --------------------------------------------------------------------------- */}
            <div className={`
                w-full flex items-center gap-4 px-4 md:px-6 py-1.5 md:py-2 
                border-b backdrop-blur-md bg-black/60
                ${stage === 'stage1' ? 'border-orange-900/30' : 'border-hud-cyan-soft'}
            `}>
                {/* Controls */}
                <div className="flex items-center gap-3 border-r border-white/10 pr-4 mr-0 md:mr-2">
                    <button onClick={onToggleSidebar} className="text-hud-muted hover:text-white transition-colors" title="Toggle Sidebar">
                        {isSidebarOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
                    </button>
                    {stage !== 'idle' && (
                        <button onClick={onToggleDetailPanel} className="text-hud-muted hover:text-white transition-colors" title="Toggle Detail Panel">
                            {isDetailPanelOpen ? <PanelRightOpen size={14} className="rotate-180" /> : <PanelRightOpen size={14} />}
                        </button>
                    )}
                    <button onClick={onResetSession} className="text-hud-muted hover:text-white transition-colors" title="Reset Session">
                        <RotateCcw size={14} />
                    </button>
                </div>

                {/* Stage Indicator */}
                <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${stage === 'stage1' ? 'bg-orange-500 shadow-[0_0_5px_orange]' : 'bg-hud-cyan shadow-[0_0_5px_cyan]'}`}></div>
                    <span className={`text-[9px] md:text-[10px] font-mono font-bold tracking-[0.2em] uppercase whitespace-nowrap ${stage === 'stage1' ? 'text-orange-500' : 'text-hud-cyan'}`}>
                        STAGE [{stage === 'idle' ? 'STANDBY' : stage === 'stage1' ? '01 / 03' : stage === 'stage2' ? '02 / 03' : '03 / 03'}]
                    </span>
                    <span className="hidden sm:inline text-[9px] font-mono tracking-widest text-hud-muted">
                        // {stage === 'idle' ? 'SYSTEM_IDLE' : stage === 'stage1' ? 'PROPOSAL_STREAM' : stage === 'stage2' ? 'PEER_REVIEW' : 'CONSENSUS'}
                    </span>
                </div>

                <div className="flex-1"></div>

                {/* System Info */}
                <div className="hidden md:flex text-[9px] font-mono gap-4 text-hud-muted">
                    <span>CPU: 45%</span>
                    <span>MEM: 12GB</span>
                </div>
            </div>

            {/* ---------------------------------------------------------------------------
                UNIT DECK OR CONSENSUS OVERLAY
               --------------------------------------------------------------------------- */}
            <div className="relative flex-1 w-full flex items-center py-2">

                {/* Consensus Banner Overlay (Stage 3 Complete) */}
                {stage3Complete && !hasViewedConsensus && activeTab !== 'final' && (
                    <div
                        onClick={onConsensusClick}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm z-40 flex items-center justify-center cursor-pointer animate-in fade-in duration-500"
                    >
                        <div className="
                            border-2 border-[rgba(6,182,212,0.8)] bg-[rgba(5,10,20,0.9)] 
                            p-3 md:p-4 transform -skew-x-12 
                            shadow-[0_0_40px_rgba(6,182,212,0.5)] 
                            group hover:scale-105 transition-transform duration-300
                        ">
                            <div className="transform skew-x-12 flex flex-col items-center">
                                <div className="rounded-full bg-hud-cyan p-1.5 mb-2 text-black"><Scale size={20} /></div>
                                <h2 className="text-xl font-black text-white uppercase tracking-tighter">Consensus Ready</h2>
                                <p className="font-mono text-[9px] text-hud-cyan mt-1">TAP TO VIEW REPORT</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* The Unit Deck */}
                <UnitDeckList
                    items={deckItems}
                    onItemClick={handleDeckClick}
                    onItemHover={() => { }} // No hover effect needed in HUD usually, or add if desired
                />
            </div>
        </div>
    );
}

export default TacticalHUD;
