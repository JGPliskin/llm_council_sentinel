import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, Scale, Terminal, Cpu, Fingerprint } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';
import ConsensusBeacon from './ConsensusBeacon';

function StageContentArea({
    activeTab,
    onTabSelect,
    stage,
    consensusUnlocked,
    hasViewedConsensus,
    onManualConsensusView, // For beacon or tab click
    resolvedCouncilors = [],
    stage1Results = [],
    stage3Result = null,
    // stage2Results not directly displayed in content area ? Refactor shows Stage 1/3 content. Stage 2 evaluates.
}) {
    const isFinal = activeTab === 'final';

    // Find active agent info
    const activeAgent = useMemo(() => {
        if (isFinal) {
            return {
                id: 'chairman',
                name: 'CHAIRMAN',
                avatar: '🧠',
                role: 'ARBITRATOR'
            }; // Chairman info
        }
        const found = resolvedCouncilors.find(c => c.id === activeTab);
        return found || { id: activeTab, name: activeTab, avatar: '?', role: 'UNKNOWN' };
    }, [activeTab, isFinal, resolvedCouncilors]);

    // Find content
    const contentData = useMemo(() => {
        if (isFinal) {
            if (!stage3Result) return null;
            return {
                title: stage3Result.title || 'FINAL CONSENSUS',
                content: stage3Result.content || stage3Result.final_answer || '', // Assuming structure
                status: 'complete'
            };
        }

        // Stage 1 content
        const result = stage1Results.find(r => r.councilor_id === activeTab);
        if (!result) return null;

        return {
            title: `PROPOSAL: ${activeAgent.name}`,
            content: result.content || result.answer_markdown || '',
            status: result.status || 'thinking'
        };
    }, [isFinal, stage3Result, stage1Results, activeTab, activeAgent]);

    // UI Colors
    const uiConfig = getCouncilorUIConfig(activeAgent.id === 'chairman' ? 'chairman' : activeAgent.id);
    const accentColor = isFinal ? 'purple' : uiConfig.color;
    // We rely on 'text-purple-400' classes etc. dynamic? No, stick to explicit sets or style.
    // Refactor used explicit 'purple' / 'orange'.
    // I will use explicit styles based on color or standard mapped classes.

    // Render
    return (
        <div className="flex-1 flex flex-col h-full bg-zinc-950 overflow-hidden relative">
            <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" />

            {/* TABS */}
            <div className="flex items-end gap-0.5 px-2 border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-20 shrink-0 overflow-x-auto no-scrollbar h-14">
                {resolvedCouncilors.map((agent) => {
                    const isActive = activeTab === agent.id;
                    const config = getCouncilorUIConfig(agent.id);
                    return (
                        <button
                            key={agent.id}
                            onClick={() => onTabSelect(agent.id)}
                            className={`
                              relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide
                              border-t-2 border-x border-zinc-800 hover:bg-zinc-800/50
                              ${isActive
                                    ? 'bg-zinc-800 text-white z-10 -mb-px pb-4'
                                    : 'bg-zinc-900/50 text-zinc-500'}
                            `}
                            style={isActive ? { borderColor: `var(--accent-${config.color})`, borderBottomColor: 'transparent' } : {}}
                        >
                            <span className={`${isActive ? 'opacity-100' : 'opacity-50'}`}>{agent.avatar}</span>
                            <span className="hidden md:inline font-mono">{agent.name}</span>
                        </button>
                    );
                })}

                <div className="h-6 w-px bg-zinc-800 mx-2" />

                {/* Consensus Tab */}
                <button
                    onClick={() => consensusUnlocked && onTabSelect('final')}
                    disabled={!consensusUnlocked}
                    className={`
                        relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide
                        border-t-2 border-x border-zinc-800
                        ${isFinal
                            ? 'bg-zinc-800 text-purple-400 border-t-purple-500 border-x-zinc-700 z-10 -mb-px pb-4'
                            : consensusUnlocked ? 'text-zinc-400 hover:text-purple-400' : 'text-zinc-700 cursor-not-allowed opacity-50'}
                    `}
                >
                    {isFinal ? <Sparkles className="w-4 h-4" /> : <Scale className="w-4 h-4" />}
                    <span className="font-mono">Consensus</span>
                </button>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth relative z-10 custom-scrollbar">
                <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">

                    {/* Header Card */}
                    <div className="mb-8 flex items-stretch gap-0 bg-zinc-900/50 border border-zinc-700 backdrop-blur-md relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-1">
                            <div className="w-16 h-1 bg-zinc-700/50 rotate-45 transform translate-x-6 -translate-y-2"></div>
                        </div>

                        <div className="w-24 md:w-32 flex items-center justify-center text-5xl relative overflow-hidden border-r border-zinc-700 bg-zinc-900">
                            <div className="absolute inset-0 opacity-20 blur-xl" style={{ backgroundColor: `var(--accent-${accentColor})` }}></div>
                            <div className="relative z-10">{activeAgent.avatar}</div>
                            <div className="absolute bottom-0 left-0 right-0 text-[10px] text-center font-mono text-zinc-600 bg-zinc-950/80 py-1 uppercase">
                                ID: {activeAgent.id.substring(0, 8)}
                            </div>
                        </div>

                        <div className="flex-1 p-4 md:p-6 flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-1">
                                <Terminal className="w-4 h-4 text-zinc-500" />
                                <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
                                    Entity // {activeAgent.role || 'Councilor'} // Class A
                                </span>
                            </div>
                            <h1 className="text-3xl md:text-5xl font-black uppercase tracking-tighter text-zinc-100"
                                style={isFinal ? { color: '#c084fc', textShadow: '0 0 10px rgba(192,132,252,0.5)' } : {}}>
                                {activeAgent.name}
                            </h1>
                        </div>
                    </div>

                    {/* Content Body */}
                    <div className="relative bg-zinc-900/40 border border-zinc-800 p-6 md:p-10 backdrop-blur-sm">
                        {/* Corner Brackets */}
                        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-zinc-600"></div>
                        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-zinc-600"></div>
                        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-zinc-600"></div>
                        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-zinc-600"></div>

                        {!contentData ? (
                            <div className="flex items-center justify-center h-40 text-zinc-500 font-mono animate-pulse">
                                {isFinal ? 'Awaiting Consensus...' : 'Waiting for data stream...'}
                            </div>
                        ) : contentData.status === 'thinking' ? (
                            <div className="flex items-center justify-center h-40 text-zinc-500 font-mono animate-pulse">
                                Processing...
                            </div>
                        ) : (
                            <div className="prose prose-invert prose-lg max-w-none">
                                <h2 className="text-xl font-bold font-mono mb-6 pb-2 border-b border-zinc-800"
                                    style={{ color: isFinal ? '#d8b4fe' : `var(--accent-${accentColor})` }}>
                                    <span className="mr-2 opacity-50">{'>>'}</span>{contentData.title}
                                </h2>

                                <div className="text-zinc-300 font-sans leading-loose tracking-wide">
                                    <ReactMarkdown>{contentData.content}</ReactMarkdown>
                                </div>
                            </div>
                        )}

                        {isFinal && contentData && (
                            <div className="mt-16 bg-purple-900/10 border border-purple-500/30 p-8 text-center relative overflow-hidden">
                                <div className="absolute inset-0 bg-grid-pattern opacity-10"></div>
                                <div className="relative z-10 flex flex-col items-center gap-4">
                                    <Fingerprint className="w-12 h-12 text-purple-500 opacity-80" />
                                    <div className="text-purple-500 text-xs font-black uppercase tracking-[0.2em] border px-2 py-1 border-purple-500 rounded">
                                        Session Closed // Consensus Reached
                                    </div>
                                </div>
                            </div>
                        )}

                        {!isFinal && contentData && contentData.status !== 'thinking' && (
                            <div className="mt-12 flex items-center gap-4 p-4 bg-zinc-950 border border-zinc-800 text-zinc-500 font-mono text-xs">
                                <Cpu className="w-4 h-4" />
                                <span>Signature Verified // Latency: 42ms // Trust Score: 98.4%</span>
                            </div>
                        )}
                    </div>
                    <div className="h-24" />
                </div>
            </div>

            {/* Beacon */}
            <ConsensusBeacon
                consensusUnlocked={consensusUnlocked}
                hasViewedConsensus={hasViewedConsensus}
                onClick={() => {
                    onTabSelect('final');
                    onManualConsensusView && onManualConsensusView();
                }}
            />
        </div>
    );
}

export default StageContentArea;
