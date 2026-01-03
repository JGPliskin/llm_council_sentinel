import React, { useMemo, useEffect, useRef, useState } from 'react';
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
    stage3AnswerStream = '',
    thinkingByCouncilor = {},
    thinkingExpanded = {},
    onToggleThinking,
    stage1AnswerStream = {},
    chairmanId = null, // Added Prop
    // stage2Results not directly displayed in content area ? Refactor shows Stage 1/3 content. Stage 2 evaluates.
}) {
    const isFinal = activeTab === 'final';
    const scrollRef = useRef(null);
    const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
    const [showJump, setShowJump] = useState(false);

    // Tab 切换折叠逻辑：追踪是否曾离开过 final tab
    const [hasLeftFinalTab, setHasLeftFinalTab] = useState(false);
    const prevActiveTabRef = useRef(activeTab);

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
        const fallbackId = activeTab || 'unknown';
        const fallbackName = activeTab || 'UNKNOWN';
        return found || { id: fallbackId, name: fallbackName, avatar: '?', role: 'UNKNOWN' };
    }, [activeTab, isFinal, resolvedCouncilors]);

    // Find content
    const contentData = useMemo(() => {
        if (isFinal) {
            if (!stage3Result && !stage3AnswerStream) return null;
            const finalText = stage3Result?.content
                || stage3Result?.final_answer
                || stage3Result?.response
                || stage3AnswerStream
                || '';
            return {
                title: stage3Result?.title || 'FINAL CONSENSUS',
                content: finalText, // Assuming structure
                status: stage3Result ? 'complete' : 'streaming'
            };
        }

        // Stage 1 content
        const result = stage1Results.find(r => r.councilor_id === activeTab);
        const streamText = stage1AnswerStream?.[activeTab] || '';
        if (!result && !streamText) return null;

        return {
            title: `PROPOSAL: ${activeAgent.name}`,
            content: (result?.content || result?.answer_markdown || '') || streamText,
            status: result?.status || (streamText ? 'streaming' : 'thinking')
        };
    }, [isFinal, stage3Result, stage3AnswerStream, stage1Results, stage1AnswerStream, activeTab, activeAgent]);

    // UI Colors
    const uiConfig = getCouncilorUIConfig(activeAgent.id === 'chairman' ? 'chairman' : activeAgent.id);
    const accentColor = isFinal ? 'purple' : uiConfig.color;
    // We rely on 'text-purple-400' classes etc. dynamic? No, stick to explicit sets or style.
    // Refactor used explicit 'purple' / 'orange'.
    // I will use explicit styles based on color or standard mapped classes.

    // Thinking entry: 优先显示当前 councilor 的 thinking，如果没有则显示预设 thinking
    // Stage3: Use chairman thinking
    const thinkingEntry = useMemo(() => {
        if (isFinal) {
            return thinkingByCouncilor?.[chairmanId || 'chairman'] || null;
        }
        const councilorThinking = thinkingByCouncilor?.[activeTab];
        if (councilorThinking && councilorThinking.steps && councilorThinking.steps.length > 0) {
            return councilorThinking;
        }
        // 回退到预设 thinking
        return thinkingByCouncilor?.['__preload__'] || null;
    }, [isFinal, thinkingByCouncilor, activeTab, chairmanId]);
    const hasThinkingSteps = !!(thinkingEntry && thinkingEntry.steps && thinkingEntry.steps.length > 0);

    // 简化折叠逻辑：
    // - 只要用户曾切换过 Tab（离开过当前 Tab），返回时就折叠
    // - 使用 state 追踪已访问过的 tabs，而不是 ref 比较（ref 在渲染时可能还没更新）
    const [visitedTabs, setVisitedTabs] = useState(new Set());

    // Effect: 记录访问过的 tabs
    useEffect(() => {
        if (activeTab) {
            setVisitedTabs(prev => new Set(prev).add(activeTab));
        }
    }, [activeTab]);

    // 折叠条件：该 Tab 之前访问过，且 thinking 已完成
    const thinkingKey = isFinal ? (chairmanId || 'chairman') : activeTab;
    const isThinkingDone = thinkingEntry?.status === 'done' ||
        (isFinal && stage3Result?.content) ||
        (!isFinal && stage1Results.find(r => r.councilor_id === activeTab));

    // 简单逻辑：只要访问过其他 Tab（size > 1），返回时就折叠
    // 用户点击展开只在当前会话有效，切换 Tab 再回来就折叠
    const wasVisitedBefore = visitedTabs.has(activeTab) && visitedTabs.size > 1;
    const shouldAutoFold = wasVisitedBefore && isThinkingDone;

    // 使用 thinkingExpanded 状态（由 onToggleThinking 控制）
    // 但如果应该自动折叠且用户没有在当前渲染周期内点击过，则折叠
    const isThinkingExpanded = thinkingExpanded?.[thinkingKey] ?? !shouldAutoFold;

    const hasAnswerStarted = !isFinal && Boolean(stage1AnswerStream?.[activeTab]);

    // Effect: 追踪 Tab 切换，标记是否曾离开 final tab (legacy, kept for compatibility)
    useEffect(() => {
        const prevTab = prevActiveTabRef.current;

        // 如果之前在 final，现在离开了
        if (prevTab === 'final' && activeTab !== 'final') {
            setHasLeftFinalTab(true);
        }

        prevActiveTabRef.current = activeTab;
    }, [activeTab]);

    useEffect(() => {
        const container = scrollRef.current;
        if (!container) return;

        const onScroll = () => {
            const gap = container.scrollHeight - container.scrollTop - container.clientHeight;
            if (gap > 100) {
                setAutoScrollEnabled(false);
                setShowJump(true);
            } else {
                setAutoScrollEnabled(true);
                setShowJump(false);
            }
        };

        container.addEventListener('scroll', onScroll, { passive: true });
        return () => container.removeEventListener('scroll', onScroll);
    }, []);

    useEffect(() => {
        const container = scrollRef.current;
        if (!container || !autoScrollEnabled) return;
        if (typeof container.scrollTo === 'function') {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
        } else {
            container.scrollTop = container.scrollHeight;
        }
    }, [autoScrollEnabled, contentData?.content, hasThinkingSteps, isThinkingExpanded, hasAnswerStarted]);

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
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth relative z-10 custom-scrollbar">
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
                                ID: {(activeAgent.id || 'unknown').substring(0, 8)}
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

                        {hasThinkingSteps && (
                            <div className="mb-6 border border-zinc-800 bg-zinc-950/60">
                                <button
                                    type="button"
                                    onClick={() => onToggleThinking && onToggleThinking(isFinal ? (chairmanId || 'chairman') : activeTab)}
                                    className="w-full flex items-center justify-between px-4 py-3 text-xs font-mono uppercase tracking-widest text-zinc-400 hover:text-zinc-200"
                                >
                                    <span className="flex items-center gap-2">
                                        {thinkingEntry?.status === 'done' ? (
                                            <span className="text-green-500">✓</span>
                                        ) : (
                                            <span
                                                className="inline-block w-3.5 h-3.5 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"
                                            />
                                        )}
                                        <span>
                                            Thinking Process {thinkingEntry?.status === 'done' ? '[DONE]' : '[LIVE]'}
                                        </span>
                                    </span>
                                    <span>{isThinkingExpanded ? '[-]' : '[+]'}</span>
                                </button>
                                {isThinkingExpanded && (
                                    <div className="px-4 pb-4 text-sm text-zinc-300 space-y-3">
                                        {thinkingEntry.steps.map(step => (
                                            <div key={step.bullet_id} className="border-b border-zinc-800/60 pb-3 last:border-0 last:pb-0">
                                                <div className="font-semibold text-zinc-200">- {step.title}</div>
                                                {step.detail && (
                                                    <div className="text-zinc-500 leading-relaxed mt-1">{step.detail}</div>
                                                )}
                                            </div>
                                        ))}
                                        {hasAnswerStarted && (
                                            <div className="text-xs text-zinc-500 font-mono uppercase tracking-widest">
                                                Answer started, still expanded
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}


                        {!contentData ? (
                            <div className="flex items-center justify-center h-40 text-zinc-500 font-mono animate-pulse">
                                {isFinal ? 'Awaiting Consensus...' : 'Waiting for data stream...'}
                            </div>
                        ) : !contentData.content ? (
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

                        {!isFinal && contentData && contentData.content && (
                            <div className="mt-12 flex items-center gap-4 p-4 bg-zinc-950 border border-zinc-800 text-zinc-500 font-mono text-xs">
                                <Cpu className="w-4 h-4" />
                                <span>Signature Verified // Latency: 42ms // Trust Score: 98.4%</span>
                            </div>
                        )}
                    </div>
                    <div className="h-24" />
                </div>
                {showJump && (
                    <button
                        type="button"
                        onClick={() => {
                            const container = scrollRef.current;
                            if (container) {
                                container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
                            }
                            setAutoScrollEnabled(true);
                            setShowJump(false);
                        }}
                        className="fixed bottom-6 right-6 md:right-10 z-30 px-3 py-2 text-xs font-mono uppercase tracking-widest bg-zinc-900 border border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500"
                    >
                        Jump to latest
                    </button>
                )}
            </div>

            {/* Beacon */}
            <ConsensusBeacon
                stage3Complete={stage3Result?.content != null}
                hasViewedConsensus={hasViewedConsensus}
                activeTab={activeTab}
                onClick={() => {
                    onTabSelect('final');
                    onManualConsensusView && onManualConsensusView();
                }}
            />
        </div>
    );
}

export default StageContentArea;
