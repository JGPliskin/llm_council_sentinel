import React, { useMemo } from 'react';
import { Scale, PanelLeftClose, PanelLeftOpen, PanelRightOpen, RotateCcw } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';
import './TacticalHUD.css';

function TacticalHUD({
    stage,
    agentProgress,
    aggregateRankings,
    resolvedCouncilors,
    consensusUnlocked,
    stage3Complete = false, // Stage 3 完成状态，控制 beacon 显示
    hasViewedConsensus,
    onConsensusClick,
    stage2Skipped = false,
    activeTab = null,
    onTabSelect, // New: for interactive switching
    // New props for IDLE stage
    selectedAgentIds = [],
    allCouncilors = [],
    // Controls
    isSidebarOpen,
    onToggleSidebar,
    isDetailPanelOpen,
    onToggleDetailPanel,
    onResetSession,
}) {
    // 排序议员：Stage 2 完成后按排名排序
    const sortedAgents = useMemo(() => {
        // IDLE Stage: Show selected agents
        if (stage === 'idle') {
            const selected = allCouncilors.filter(c => selectedAgentIds.includes(c.id));
            return selected.map(c => ({
                councilor_id: c.id,
                name: c.name,
                avatar: c.avatar,
                isIdle: true
            }));
        }

        if (aggregateRankings && aggregateRankings.length > 0) {
            // 按排名排序并合并信息
            return [...aggregateRankings]
                .sort((a, b) => a.rank - b.rank)
                .map(ranking => {
                    // Try to find more info from allCouncilors or fallback
                    const info = allCouncilors.find(c => c.id === ranking.councilor_id) || {};
                    return {
                        ...ranking,
                        name: info.name || ranking.name || ranking.councilor_id,
                        avatar: info.avatar || ranking.avatar || '?'
                    };
                });
        }
        // 默认顺序
        return (resolvedCouncilors || []).map(c => ({
            councilor_id: c.id,
            name: c.name,
            avatar: c.avatar,
        }));
    }, [aggregateRankings, resolvedCouncilors, stage, selectedAgentIds, allCouncilors]);

    // Calculate slots for rendering
    const displaySlots = useMemo(() => {
        if (stage === 'idle') {
            // Fill up to 3 slots with empty if less than 3
            const slots = [...sortedAgents];
            while (slots.length < 3) {
                slots.push({ isEmpty: true });
            }
            return slots;
        }
        return sortedAgents;
    }, [sortedAgents, stage]);

    // 渲染单个 Agent 卡片
    const renderAgentSlice = (agent, index) => {
        if (agent.isEmpty) {
            return <div key={`empty-${index}`} className="agent-slice agent-slot--empty" />;
        }

        const uiConfig = getCouncilorUIConfig(agent.councilor_id);

        // IDLE Stage: Ready State
        if (agent.isIdle) {
            return (
                <div
                    key={agent.councilor_id}
                    className="agent-slice agent-slot--ready"
                    style={{ borderColor: `var(--accent-${uiConfig.color})` }}
                >
                    <div className="agent-avatar">{agent.avatar}</div>
                    <div className="agent-name">{agent.name}</div>
                    <div className="agent-status" style={{ color: `var(--accent-${uiConfig.color})` }}>READY</div>
                </div>
            );
        }

        const hasRanking = aggregateRankings && aggregateRankings.length > 0;
        const progress = agentProgress[agent.councilor_id] || 0;
        const showSkippedBadge = stage === 'stage2' && stage2Skipped;

        return (
            <div
                key={agent.councilor_id}
                onClick={(e) => {
                    if (onTabSelect) {
                        e.stopPropagation(); // Prevent main content click from closing drawer immediately if needed
                        onTabSelect(agent.councilor_id);
                    }
                }}
                className={`agent-slice ${hasRanking ? 'border-opacity-100' : 'border-opacity-50'} ${onTabSelect ? 'cursor-pointer hover:bg-white/5' : ''} ${activeTab === agent.councilor_id ? 'bg-white/10 ring-1 ring-white/20' : ''}`}
                style={{ borderColor: `var(--accent-${uiConfig.color})` }}
            >
                {/* Background Pattern & Progress Fill (Stage 1 & Stage 2) */}
                {(stage === 'stage1' || stage === 'stage2') && progress > 0 && (
                    <div
                        className="progress-fill absolute bottom-0 left-0 right-0 z-0 transition-all duration-300 overflow-hidden"
                        style={{
                            height: `${progress}%`,
                            backgroundColor: `var(--accent-${uiConfig.color})`,
                            opacity: stage === 'stage1' ? 0.2 : 0.12  // Stage2 lighter fill
                        }}
                    >
                        <div className="absolute inset-0 bg-stripe-pattern opacity-30 animate-[scanline_2s_linear_infinite]" />
                        <div className="absolute top-0 left-0 right-0 h-px bg-white/30 shadow-[0_0_10px_rgba(255,255,255,0.5)]" />
                    </div>
                )}

                {/* Identity / Role Label */}
                <div className="agent-identity font-mono text-[9px] uppercase tracking-wider text-zinc-500 mt-1 relative z-10 transition-colors duration-300"
                    style={{ color: progress > 0 ? `var(--accent-${uiConfig.color})` : undefined, opacity: 0.7 }}>
                    {uiConfig.role || 'COUNCILOR'}
                </div>

                {/* Agent Name */}
                <div className="agent-name text-xs md:text-sm font-black uppercase tracking-tight text-zinc-100 truncate mt-0.5 relative z-10 drop-shadow-md">
                    {agent.name}
                </div>

                {/* Rank / Skipped Badge */}
                {showSkippedBadge ? (
                    <div className="absolute top-0 right-0 p-1 bg-black/40 backdrop-blur z-20 border-l border-b border-zinc-700/50 rounded-bl">
                        <span className="text-[10px] font-bold text-zinc-300 font-mono">
                            SKIPPED
                        </span>
                    </div>
                ) : hasRanking ? (
                    <div className="absolute top-0 right-0 p-1 bg-black/40 backdrop-blur z-20 border-l border-b border-zinc-700/50 rounded-bl">
                        <span className="text-xs font-bold text-zinc-200 font-mono">
                            #{agent.average_rank?.toFixed(1) || index + 1}
                        </span>
                    </div>
                ) : null}
            </div>
        );
    };

    const stageClass = stage === 'stage1' ? 'tactical-hud--stage1'
        : stage === 'stage2' ? 'tactical-hud--stage2'
            : stage === 'stage3' ? 'tactical-hud--stage3'
                : '';

    const isBannerActive = stage3Complete && !hasViewedConsensus && activeTab !== 'final';

    return (
        <div className={`tactical-hud ${stageClass}`} style={isBannerActive ? { minHeight: '180px' } : {}}>
            {/* Stage Indicator / Header Line */}
            <div className="w-full flex items-center gap-4 px-6 py-2 border-b border-zinc-800 bg-black/40 backdrop-blur-md">
                {/* Controls (Integrated) */}
                <div className="flex items-center gap-3 border-r border-zinc-800 pr-4 mr-0 md:mr-2">
                    <button onClick={onToggleSidebar} className="text-zinc-500 hover:text-white transition-colors animate-breathe md:animate-none" title="Toggle Sidebar">
                        {isSidebarOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
                    </button>
                    {stage !== 'idle' && (
                        <button onClick={onToggleDetailPanel} className="text-zinc-500 hover:text-white transition-colors animate-breathe md:animate-none" title="Toggle Detail Panel">
                            {isDetailPanelOpen ? <PanelRightOpen size={14} className="rotate-180" /> : <PanelRightOpen size={14} />}
                        </button>
                    )}
                    <button onClick={onResetSession} className="text-zinc-500 hover:text-white transition-colors" title="Reset Session">
                        <RotateCcw size={14} />
                    </button>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${stage === 'idle' ? 'bg-zinc-500' : 'bg-purple-500 animate-pulse'}`}></div>
                    <span className="text-[10px] font-mono font-bold text-purple-400 tracking-[0.2em] uppercase whitespace-nowrap flex-shrink-0">
                        STAGE [{stage === 'idle' ? 'STANDBY' : stage === 'stage1' ? '01 / 03' : stage === 'stage2' ? '02 / 03' : '03 / 03'}]
                    </span>
                    <span className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest">
                        // {stage === 'idle' ? 'SYSTEM_IDLE' : stage === 'stage1' ? 'PROPOSAL_STREAM' : stage === 'stage2' ? 'PEER_REVIEW' : 'CONSENSUS'}
                    </span>
                </div>
                <div className="flex-1"></div>
                <div className="hidden md:flex text-[9px] font-mono text-zinc-700 gap-4">
                    <span>CPU: 45%</span>
                    <span>MEM: 12GB</span>
                </div>
            </div>

            {/* Main Content Area: Agents or Banner */}
            <div className="relative flex-1 w-full flex items-center justify-center p-4 overflow-hidden">

                {/* STAGE 3 CONSENSUS BEACON (The "Click to view" overlay) */}
                {/* Note: Only show when Stage 3 is COMPLETE, user not on final tab, and hasn't viewed. */}
                {stage3Complete && !hasViewedConsensus && activeTab !== 'final' && (
                    <div
                        onClick={onConsensusClick}
                        // 外部容器样式：黑色半透明背景 + 模糊效果
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm z-40 flex items-center justify-center animate-in fade-in duration-1000 cursor-pointer hover:bg-black/70 transition-colors"
                    >
                        {/* 内部卡片样式：紫色边框 + 倾斜效果 (skew-x-12) */}
                        <div className="bg-zinc-900 border-2 border-purple-500 p-3 md:p-4 transform -skew-x-12 shadow-[0_0_50px_rgba(168,85,247,0.5)] max-w-lg w-full mx-4 group">
                            <div className="transform skew-x-12 text-center group-hover:scale-105 transition-transform duration-300">
                                <div className="flex justify-center mb-1">
                                    <div className="bg-purple-500 text-white p-1.5 rounded-full"><Scale className="w-6 h-6" /></div>
                                </div>
                                <h2 className="text-xl md:text-2xl font-black text-white uppercase tracking-tighter mb-1">Consensus Ready</h2>
                                <div className="h-px w-24 bg-purple-500 mx-auto mb-2" />
                                <p className="text-purple-300 font-mono text-[10px] md:text-xs">
                                    PARLIAMENTARY DECREE #404 ISSUED.<br />TAP TO VIEW REPORT.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Agent Slots - Always rendered underneath (or when no consensus overlay) */}
                <div className="flex gap-4 w-full max-w-6xl justify-center h-full items-end pb-2">
                    {displaySlots.map((agent, index) => renderAgentSlice(agent, index))}
                </div>
            </div>
        </div>
    );
}

export default TacticalHUD;
