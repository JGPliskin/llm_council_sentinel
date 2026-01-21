import React, { useMemo, useEffect, useRef, useState } from 'react';

import ReactMarkdown from 'react-markdown';

import { Sparkles, Scale, Terminal, Cpu, Fingerprint, ChevronRight, LayoutGrid, Lock, Shield } from 'lucide-react';


import ConsensusBeacon from './ConsensusBeacon';



// Icon set for thinking bullets (cycles through)

const THINKING_ICONS = [Terminal, LayoutGrid, Lock, Shield, ChevronRight];


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

    onBackgroundClick, // New prop

    stage1AnswerStream = {},

    chairmanId = null, // Added Prop

    // stage2Results not directly displayed in content area ? Refactor shows Stage 1/3 content. Stage 2 evaluates.

}) {

    const isFinal = activeTab === 'final';

    const scrollRef = useRef(null);

    const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

    const [showJump, setShowJump] = useState(false);



    // Tab åæ¢æå é»è¾ï¼è¿½è¸ªæ¯å¦æ¾ç¦»å¼è¿?final tab

    const [hasLeftFinalTab, setHasLeftFinalTab] = useState(false);

    const prevActiveTabRef = useRef(activeTab);



    // Find active agent info

    const activeAgent = useMemo(() => {

        if (isFinal) {

            return {

                id: 'chairman',

                name: 'CHAIRMAN',

                avatar: 'ð§ ',

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





    // Thinking entry: ä¼åæ¾ç¤ºå½å councilor ç?thinkingï¼å¦ææ²¡æåæ¾ç¤ºé¢è®¾ thinking

    // Stage3: Use chairman thinking

    const thinkingEntry = useMemo(() => {

        if (isFinal) {

            return thinkingByCouncilor?.[chairmanId || 'chairman'] || null;

        }

        const councilorThinking = thinkingByCouncilor?.[activeTab];

        if (councilorThinking && councilorThinking.steps && councilorThinking.steps.length > 0) {

            return councilorThinking;

        }

        // åéå°é¢è®?thinking

        return thinkingByCouncilor?.['__preload__'] || null;

    }, [isFinal, thinkingByCouncilor, activeTab, chairmanId]);

    const hasThinkingSteps = !!(thinkingEntry && thinkingEntry.steps && thinkingEntry.steps.length > 0);



    // ç®åæå é»è¾ï¼?
    // - åªè¦ç¨æ·æ¾åæ¢è¿ Tabï¼ç¦»å¼è¿å½å?Tabï¼ï¼è¿åæ¶å°±æå 

    // - ä½¿ç¨ state è¿½è¸ªå·²è®¿é®è¿ç?tabsï¼èä¸æ?ref æ¯è¾ï¼ref å¨æ¸²ææ¶å¯è½è¿æ²¡æ´æ°ï¼?
    const [visitedTabs, setVisitedTabs] = useState(new Set());



    // Effect: è®°å½è®¿é®è¿ç tabs

    useEffect(() => {

        if (activeTab) {

            setVisitedTabs(prev => new Set(prev).add(activeTab));

        }

    }, [activeTab]);



    // æå æ¡ä»¶ï¼è¯¥ Tab ä¹åè®¿é®è¿ï¼ä¸?thinking å·²å®æ?
    const thinkingKey = isFinal ? (chairmanId || 'chairman') : activeTab;

    const isThinkingDone = thinkingEntry?.status === 'done' ||

        (isFinal && stage3Result?.content) ||

        (!isFinal && stage1Results.find(r => r.councilor_id === activeTab));



    // ç®åé»è¾ï¼åªè¦è®¿é®è¿å¶ä» Tabï¼size > 1ï¼ï¼è¿åæ¶å°±æå 

    // ç¨æ·ç¹å»å±å¼åªå¨å½åä¼è¯ææï¼åæ?Tab ååæ¥å°±æå 

    const wasVisitedBefore = visitedTabs.has(activeTab) && visitedTabs.size > 1;

    const shouldAutoFold = wasVisitedBefore && isThinkingDone;



    // ä½¿ç¨ thinkingExpanded ç¶æï¼ç?onToggleThinking æ§å¶ï¼?
    // ä½å¦æåºè¯¥èªå¨æå ä¸ç¨æ·æ²¡æå¨å½åæ¸²æå¨æåç¹å»è¿ï¼åæå?
    const isThinkingExpanded = thinkingExpanded?.[thinkingKey] ?? !shouldAutoFold;



    const hasAnswerStarted = !isFinal && Boolean(stage1AnswerStream?.[activeTab]);



    // Effect: è¿½è¸ª Tab åæ¢ï¼æ è®°æ¯å¦æ¾ç¦»å¼ final tab (legacy, kept for compatibility)

    useEffect(() => {

        const prevTab = prevActiveTabRef.current;



        // å¦æä¹åå?finalï¼ç°å¨ç¦»å¼äº?
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



    const logicProcessTitle = 'LOGIC_PROCESS';

    // Render

    return (

        <div className="flex-1 flex flex-col overflow-hidden relative">


            {/* TABS */}

            <div className="flex items-end gap-0.5 px-2 border-b backdrop-blur sticky top-0 z-20 shrink-0 overflow-x-auto no-scrollbar h-14"
                style={{
                    borderColor: 'rgba(6, 182, 212, 0.25)',
                    backgroundColor: 'rgba(5, 10, 20, 0.92)',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.45)'
                }}>
                {resolvedCouncilors.map((agent) => {
                    const isActive = activeTab === agent.id;
                    return (
                        <button
                            key={agent.id}

                            onClick={() => onTabSelect(agent.id)}

                            className={`
                              relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide font-hud
                              border-t border-x
                              ${isActive ? 'z-10 -mb-px pb-4' : 'opacity-70 hover:opacity-100'}
                            `}
                            style={{
                                borderColor: isActive ? 'var(--hud-cyan)' : 'rgba(6, 182, 212, 0.15)',
                                borderBottomColor: isActive ? 'transparent' : 'rgba(6, 182, 212, 0.2)',
                                backgroundColor: isActive ? 'rgba(5, 10, 20, 0.9)' : 'transparent',
                                color: isActive ? 'var(--hud-cyan)' : 'var(--hud-muted)',
                                textShadow: isActive ? '0 0 8px rgba(6, 182, 212, 0.6)' : 'none'
                            }}
                        >
                            <span className={`${isActive ? 'opacity-100' : 'opacity-50'}`}>{agent.avatar}</span>
                            <span className="hidden md:inline">{agent.name}</span>
                        </button>
                    );

                })}



                <div className="h-6 w-px mx-2" style={{ backgroundColor: 'rgba(6, 182, 212, 0.2)' }} />


                {/* Consensus Tab */}

                <button

                    onClick={() => consensusUnlocked && onTabSelect('final')}

                    disabled={!consensusUnlocked}

                    className={`
                        relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide
                        border-t border-x
                        ${isFinal
                            ? 'z-10 -mb-px pb-4'
                            : consensusUnlocked ? 'opacity-80 hover:opacity-100' : 'cursor-not-allowed opacity-50'}
                    `}
                    style={{
                        borderColor: isFinal ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.2)',
                        borderBottomColor: isFinal ? 'transparent' : 'rgba(6, 182, 212, 0.2)',
                        backgroundColor: isFinal ? 'rgba(5, 10, 20, 0.9)' : 'transparent',
                        color: isFinal ? 'var(--hud-cyan)' : consensusUnlocked ? 'var(--hud-muted)' : 'rgba(91, 107, 122, 0.6)'
                    }}
                >
                    {isFinal ? <Sparkles className="w-4 h-4" /> : <Scale className="w-4 h-4" />}
                    <span className="font-mono">Consensus</span>
                </button>
            </div>


            {/* MAIN CONTENT */}

            <div

                ref={scrollRef}

                onClick={(e) => {

                    // Only trigger if clicking the background directly, not interactive children

                    // But events bubble. We rely on interactive children (buttons) stopping propagation if needed.

                    // Actually, for "Tap to Stow", usually clicking anywhere that isn't a button should work. 

                    if (onBackgroundClick) onBackgroundClick(e);

                }}

                className="flex-1 overflow-y-auto p-4 md:p-8 pb-28 md:pb-32 scroll-smooth relative z-10 custom-scrollbar"

            >

                <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">



                    {/* Header Card - HUD Style */}

                    <div className="mb-8 flex items-stretch gap-0 backdrop-blur-md relative overflow-hidden hud-panel clip-corner-both">
                        {/* Corner decorations */}
                        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2" style={{ borderColor: 'rgba(6, 182, 212, 0.8)' }}></div>
                        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2" style={{ borderColor: 'rgba(6, 182, 212, 0.8)' }}></div>

                        <div className="w-24 md:w-32 flex items-center justify-center text-5xl relative overflow-hidden border-r"
                            style={{
                                borderColor: 'rgba(6, 182, 212, 0.2)',
                                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.35), rgba(120, 53, 15, 0.95))'
                            }}>
                            <div className="absolute inset-0 opacity-30 blur-xl" style={{ backgroundColor: 'rgba(245, 158, 11, 0.6)' }}></div>
                            <div className="relative z-10" style={{ filter: 'drop-shadow(0 0 12px rgba(245, 158, 11, 0.7))' }}>{activeAgent.avatar}</div>
                            <div className="absolute bottom-0 left-0 right-0 text-[10px] text-center font-mono py-1 uppercase"
                                style={{ backgroundColor: 'rgba(5, 10, 20, 0.9)', color: 'var(--hud-muted)' }}>
                                ID: {(activeAgent.id || 'unknown').substring(0, 8)}
                            </div>
                        </div>

                        <div className="flex-1 p-4 md:p-6 flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-1">
                                <Shield className="w-4 h-4" style={{ color: 'var(--hud-cyan)' }} />
                                <span className="text-[10px] font-mono uppercase tracking-[0.3em]" style={{ color: 'var(--hud-muted)' }}>
                                    Entity // {activeAgent.role || 'Councilor'} // Class A
                                </span>
                            </div>
                            <h1 className="text-3xl md:text-5xl font-black uppercase tracking-tight font-hud hud-glow"
                                style={isFinal ? { color: 'var(--hud-cyan)', textShadow: '0 0 15px rgba(6, 182, 212, 0.6)' } : { color: 'var(--hud-text)' }}>
                                {activeAgent.name}
                            </h1>
                        </div>
                    </div>



                    {/* Content Body */}

                    <div className="relative p-6 md:p-10 backdrop-blur-sm hud-panel clip-corner-both">
                        {/* Corner Brackets - Cyan */}
                        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2" style={{ borderColor: 'rgba(6, 182, 212, 0.7)' }}></div>
                        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2" style={{ borderColor: 'rgba(6, 182, 212, 0.7)' }}></div>
                        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2" style={{ borderColor: 'rgba(6, 182, 212, 0.7)' }}></div>
                        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2" style={{ borderColor: 'rgba(6, 182, 212, 0.7)' }}></div>


                        {hasThinkingSteps && (

                            <div className="mb-8 relative" style={{ border: '1px solid rgba(16, 185, 129, 0.3)', backgroundColor: 'rgba(6, 78, 59, 0.08)' }}>

                                {/* Emerald left accent line */}

                                <div className="absolute top-0 left-0 w-[2px] h-full" style={{ backgroundColor: 'rgba(16, 185, 129, 0.5)' }}></div>



                                {/* Header label */}

                                <div className="absolute -top-3 left-4 px-2 font-hud text-xs tracking-widest"

                                    style={{ backgroundColor: 'var(--hud-bg)', color: '#10b981' }}>

                                    {logicProcessTitle}

                                </div>



                                <button

                                    type="button"

                                    onClick={() => onToggleThinking && onToggleThinking(isFinal ? (chairmanId || 'chairman') : activeTab)}

                                    className="w-full flex items-center justify-between px-4 py-3 text-xs font-mono uppercase tracking-widest transition-colors"

                                    style={{ color: '#10b981' }}

                                >

                                    <span className="flex items-center gap-2">

                                        {thinkingEntry?.status === 'done' ? (

                                            <span style={{ color: '#10b981' }}>OK</span>

                                        ) : (

                                            <span

                                                className="inline-block w-3.5 h-3.5 border-2 rounded-full animate-spin"

                                                style={{ borderColor: 'rgba(16, 185, 129, 0.3)', borderTopColor: '#10b981' }}

                                            />

                                        )}

                                        <span>

                                            Thinking Process {thinkingEntry?.status === 'done' ? '[DONE]' : '[LIVE]'}

                                        </span>

                                    </span>

                                    <span>{isThinkingExpanded ? '[-]' : '[+]'}</span>

                                </button>

                                {isThinkingExpanded && (

                                    <div className="px-6 pb-4 space-y-4">

                                        {thinkingEntry.steps.map((step, index) => {

                                            const IconComponent = THINKING_ICONS[index % THINKING_ICONS.length];

                                            return (

                                                <div key={step.bullet_id} className="pb-3 last:pb-0 flex items-start gap-3" style={{ borderBottom: '1px solid rgba(16, 185, 129, 0.2)' }}>

                                                    <IconComponent className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#10b981' }} />

                                                    <div className="flex-1">

                                                        <div className="font-semibold text-sm" style={{ color: '#6ee7b7' }}>{step.title}</div>

                                                        {step.detail && (

                                                            <div className="text-sm leading-relaxed mt-1" style={{ color: 'rgba(167, 243, 208, 0.7)' }}>{step.detail}</div>

                                                        )}

                                                    </div>

                                                </div>

                                            );

                                        })}

                                    </div>

                                )}

                            </div>

                        )}





                        {!contentData ? (

                            <div className="flex items-center justify-center h-40 font-mono animate-pulse" style={{ color: 'var(--hud-muted)' }}>

                                {isFinal ? 'Awaiting Consensus...' : 'Waiting for data stream...'}

                            </div>

                        ) : !contentData.content ? (

                            <div className="flex items-center justify-center h-40 font-mono animate-pulse" style={{ color: 'var(--hud-muted)' }}>

                                Processing...

                            </div>

                        ) : (
                            <div className="prose prose-invert prose-lg max-w-none">
                                <div className="mb-6">
                                    <div className="flex items-center gap-2 mb-3">
                                        <div className="flex gap-1">
                                            <ChevronRight className="w-4 h-4" style={{ color: 'var(--hud-cyan)' }} />
                                            <ChevronRight className="w-4 h-4 opacity-60" style={{ color: 'var(--hud-cyan)' }} />
                                        </div>
                                        <h2
                                            className="text-lg md:text-xl font-bold font-hud tracking-widest"
                                            style={{
                                                color: 'var(--hud-cyan)',
                                                textShadow: '0 0 10px rgba(6, 182, 212, 0.5)'
                                            }}
                                        >
                                            {contentData.title}
                                        </h2>
                                    </div>
                                    <div className="h-px w-full" style={{ backgroundColor: 'rgba(6, 182, 212, 0.4)' }} />
                                </div>

                                <div className="font-sans leading-loose tracking-wide" style={{ color: 'var(--hud-text)' }}>
                                    <ReactMarkdown>{contentData.content}</ReactMarkdown>
                                </div>
                            </div>
                        )}


                        {isFinal && contentData && (

                            <div
                                className="mt-16 p-8 text-center relative overflow-hidden hud-panel-soft"
                                style={{ borderColor: 'rgba(6, 182, 212, 0.35)', backgroundColor: 'rgba(5, 10, 20, 0.6)' }}
                            >

                                <div className="absolute inset-0 bg-grid-pattern opacity-10"></div>

                                <div className="relative z-10 flex flex-col items-center gap-4">

                                    <Fingerprint className="w-12 h-12 opacity-80" style={{ color: 'var(--hud-cyan)' }} />

                                    <div className="text-xs font-black uppercase tracking-[0.2em] border px-2 py-1 rounded" style={{ color: "var(--hud-cyan)", borderColor: "rgba(6, 182, 212, 0.6)" }}>

                                        Session Closed // Consensus Reached

                                    </div>

                                </div>

                            </div>

                        )}



                        {!isFinal && contentData && contentData.content && (

                            <div
                                className="mt-12 flex items-center gap-4 p-4 border font-mono text-xs"
                                style={{ backgroundColor: 'rgba(5, 10, 20, 0.85)', borderColor: 'rgba(6, 182, 212, 0.2)', color: 'var(--hud-muted)' }}
                            >

                                <Cpu className="w-4 h-4" style={{ color: 'var(--hud-cyan)' }} />

                                <span>Signature Verified // Latency: 42ms // Trust Score: 98.4%</span>

                            </div>

                        )}

                    </div>


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

                        className="fixed bottom-6 right-6 md:right-10 z-30 px-3 py-2 text-xs font-mono uppercase tracking-widest border transition-colors"
                        style={{
                            backgroundColor: 'rgba(5, 10, 20, 0.9)',
                            borderColor: 'rgba(6, 182, 212, 0.3)',
                            color: 'var(--hud-cyan)'
                        }}

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



