import React, { useState, useEffect } from 'react';

import ReactMarkdown from 'react-markdown';

import { X, Maximize2, Minimize2 } from 'lucide-react';

import { getCouncilorUIConfig } from '@/config/councilors';



// å»¶è¿æ¾ç¤º review çæ¶é´ï¼æ¯«ç§ï¼

const REVIEW_DISPLAY_DELAY_MS = 1500;



/**

 * è·åå½ååºå±ç¤ºçè¯¦æåå®¹

 */

function getDetailContent(stage, activeTab, evaluationComments, synthesisSteps, stage2ThinkingByJudge) {

    // Consensus Tab -> show grouped Stage 2 reviews

    if (activeTab === 'final') {

        return {

            type: 'consensus_reviews',

            title: 'Peer Reviews',

            // data: evaluationComments, (access directly in component)

        };

    }



    // Stage 1 -> show user prompt

    if (stage === 'stage1') {

        return {

            type: 'user_prompt',

            title: 'User Question',

        };

    }



    // Stage 2 -> use stage2_mixed view to blend thinking and reviews

    if (stage === 'stage2') {

        return {

            type: 'stage2_mixed',

            title: 'Judge Analysis',

            thinkingData: stage2ThinkingByJudge,

            reviewData: evaluationComments,

            targetId: activeTab, // å½åéä¸­çè®®å ID

        };

    }



    // Stage 3 -> show evaluations for active councilor

    if (stage === 'stage3') {

        const comments = evaluationComments[activeTab] || [];

        return {

            type: 'evaluation',

            title: 'Peer Reviews',

            data: comments,

        };

    }



    return { type: 'empty', title: '', data: [] };

}



/**

 * åä¸ª Judge å¡çç»ä»¶

 * æ ¹æ®ç¶æåæ¶é´å³å®æ¾ç¤º thinking è¿æ¯ review

 */

function JudgeCard({ judgeId, judgeData, targetId, reviewComments, now }) {

    const uiConfig = getCouncilorUIConfig(judgeId);

    const status = judgeData.status;

    const doneAt = judgeData.doneAt;



    // è·åéå¯¹å½å targetId çæèæ­¥éª¤

    const targetSteps = judgeData.stepsByTarget?.[targetId] || [];

    const latestStep = targetSteps[targetSteps.length - 1];



    // è·åè¯¥ judge å¯¹å½å target ç review

    const reviewFromJudge = reviewComments?.find(r => r.fromId === judgeId);



    // å¤æ­æ¯å¦åºè¯¥æ¾ç¤º reviewï¼å®æåå»¶è¿ 1.5 ç§ï¼

    const shouldShowReview = status === 'done' && doneAt && (now - doneAt >= REVIEW_DISPLAY_DELAY_MS) && reviewFromJudge;



    // å¦æè¿ä¸ª judge æ²¡æéå¯¹å½å target ç thinking ä¸ä¸è¯¥æ¾ç¤º reviewï¼è·³è¿

    if (targetSteps.length === 0 && status !== 'thinking' && !shouldShowReview) {

        return null;

    }



    return (

        <div className="relative p-3 transition-all duration-500"

            style={{ backgroundColor: 'rgba(8, 12, 24, 0.85)', border: '1px solid rgba(6, 182, 212, 0.25)' }}>

            {/* Left accent line */}

            <div className="absolute top-0 left-0 w-[2px] h-full" style={{ backgroundColor: 'rgba(6, 182, 212, 0.6)' }}></div>



            {/* Judge Header */}

            <div className="flex items-center gap-2 mb-2 pb-2 px-2" style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.2)', backgroundColor: 'rgba(6, 182, 212, 0.08)' }}>

                <div className="w-2 h-2 rounded-full" style={{ background: `var(--accent-${uiConfig.color})` }}></div>

                <span className="text-xs font-bold font-hud" style={{ color: 'var(--hud-text)' }}>{judgeId.toUpperCase()}</span>

                {status === 'thinking' && (

                    <span className="text-xs animate-pulse ml-auto" style={{ color: 'var(--hud-amber)' }}>ANALYZING...</span>

                )}

                {status === 'done' && !shouldShowReview && (

                    <span className="text-xs ml-auto" style={{ color: '#10b981' }}>COMPLETE</span>

                )}

                {shouldShowReview && reviewFromJudge?.score && (

                    <div className="text-xs font-mono font-bold ml-auto" style={{ color: 'var(--hud-cyan)' }}>

                        RANK #{reviewFromJudge.score}

                    </div>

                )}

            </div>



            {/* Content area */}

            <div className="transition-opacity duration-500">

                {shouldShowReview ? (

                    <div className="text-sm leading-relaxed animate-fadeIn" style={{ color: 'var(--hud-muted)' }}>

                        {reviewFromJudge.comment}

                    </div>

                ) : latestStep ? (

                    <div className="space-y-1">

                        <div className="text-sm font-medium" style={{ color: 'var(--hud-text)' }}>

                            {latestStep.title}

                        </div>

                        {latestStep.detail && (

                            <div className="text-xs leading-relaxed opacity-80" style={{ color: 'var(--hud-muted)' }}>

                                {latestStep.detail}

                            </div>

                        )}

                    </div>

                ) : (

                    <div className="text-xs font-mono animate-pulse" style={{ color: 'var(--hud-muted)' }}>

                        Initializing analysis...

                    </div>

                )}

            </div>

        </div>

    );

}



export function DetailPanel({

    stage,

    activeTab,

    evaluationComments,

    synthesisSteps,

    stage2ThinkingByJudge,

    stage2AnonMap,

    aggregateRankings = [],

    stage2Skipped = false,

    onClose,

    userPrompt,

    isPanelFullscreen = false,

    onToggleFullscreen

}) {

    // ç¨äºè§¦åéæ°æ¸²æçæ¶é´æ³

    const [now, setNow] = useState(Date.now());



    // çå¬ stage2ThinkingByJudge ååï¼æ£æ¥æ¯å¦æ judge åå®æ

    useEffect(() => {

        if (stage !== 'stage2' || !stage2ThinkingByJudge) return;



        // æ£æ¥æ¯å¦æ judge å¤äº"åå®æä½è¿æªæ¾ç¤º review"çç¶æ

        const needsUpdate = Object.values(stage2ThinkingByJudge).some(judgeData => {

            if (judgeData.status === 'done' && judgeData.doneAt) {

                const elapsed = Date.now() - judgeData.doneAt;

                return elapsed < REVIEW_DISPLAY_DELAY_MS;

            }

            return false;

        });



        if (needsUpdate) {

            // è®¾ç½®å®æ¶å¨å¨å»¶è¿åè§¦åéæ°æ¸²æ

            const timer = setTimeout(() => {

                setNow(Date.now());

            }, REVIEW_DISPLAY_DELAY_MS);



            return () => clearTimeout(timer);

        }

    }, [stage, stage2ThinkingByJudge]);



    const content = getDetailContent(

        stage,

        activeTab,

        evaluationComments,

        synthesisSteps,

        stage2ThinkingByJudge

    );



    const { type, title, data, thinkingData, reviewData, targetId } = content;



    // å½å target ç review åè¡¨

    const currentReviews = reviewData?.[activeTab] || [];



    // æ£æ¥æ¯å¦ææ judge é½å·²å®æä¸è¿äºå»¶è¿æ¶é´ï¼ç¨äºåæ¢æ é¢ï¼

    const allReviewsReady = thinkingData && Object.values(thinkingData).every(j => {

        if (j.status !== 'done') return false;

        if (!j.doneAt) return true;

        return (now - j.doneAt) >= REVIEW_DISPLAY_DELAY_MS;

    }) && Object.keys(thinkingData).length > 0;



    // å¨ææ é¢

    const displayTitle = type === 'stage2_mixed'

        ? (allReviewsReady ? 'Peer Reviews' : 'Judge Analysis')

        : title;



    return (

        <div className="h-full flex flex-col backdrop-blur-md" style={{ backgroundColor: 'rgba(5, 10, 20, 0.92)', borderLeft: '1px solid rgba(6, 182, 212, 0.25)', boxShadow: 'inset 0 0 40px rgba(0, 0, 0, 0.35)' }}>

            {/* Drag Handle (Mobile only, visual only) */}

            <div className="md:hidden flex justify-center py-2">

                <div className="w-10 h-1 rounded-full" style={{ backgroundColor: 'var(--hud-cyan-soft)' }}></div>

            </div>

            {/* Header */}

            <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'rgba(6, 182, 212, 0.25)', backgroundColor: 'rgba(5, 10, 20, 0.95)' }}>

                <h2 className={`text-sm font-bold tracking-widest uppercase font-hud ${stage === 'stage2' ? 'animate-breathe' : ''}`}

                    style={{ color: 'var(--hud-cyan)', textShadow: '0 0 8px var(--hud-cyan)' }}>

                    {displayTitle || "UNIT_STATUS"}

                </h2>

                <div className="flex items-center gap-2">

                    {/* Fullscreen Button (Stage 3 only) */}

                    {stage === 'stage3' && onToggleFullscreen && (

                        <button

                            onClick={onToggleFullscreen}

                            className="p-1.5 border border-transparent transition-colors hover:text-cyan-200"

                            style={{ color: 'var(--hud-muted)' }}

                            title={isPanelFullscreen ? "Exit Fullscreen" : "Fullscreen"}

                        >

                            {isPanelFullscreen ? (

                                <Minimize2 className="w-4 h-4" />

                            ) : (

                                <Maximize2 className="w-4 h-4" />

                            )}

                        </button>

                    )}

                    {/* Close Button */}

                    <button

                        onClick={onClose}

                        className="p-1.5 border border-transparent transition-colors hover:text-cyan-200"

                        style={{ color: 'var(--hud-muted)' }}

                        title="Close Panel"

                    >

                        <X className="w-4 h-4 transition-transform duration-300" />

                    </button>

                </div>

            </div>



            {/* Content */}

            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">

                {type === 'empty' && (

                    <div className="flex items-center justify-center h-full text-xs font-mono" style={{ color: 'var(--hud-muted)' }}>

                        NO DATA AVAILABLE

                    </div>

                )}



                {type === 'user_prompt' && (

                    <div className="space-y-2">

                        <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--hud-cyan)' }}>User Question</div>

                        <div className="text-sm leading-relaxed p-3 rounded"

                            style={{ backgroundColor: 'rgba(8, 12, 24, 0.85)', border: '1px solid rgba(6, 182, 212, 0.25)', color: 'var(--hud-text)' }}>

                            {userPrompt || 'No question available'}

                        </div>

                    </div>

                )}



                {type === 'thinking' && (

                    <div className="space-y-4">

                        {data.map(step => (

                            <div key={step.id} className="font-mono text-xs">

                                <div className="flex items-center gap-2 mb-1 opacity-50">

                                    <span style={{ color: 'var(--hud-cyan)' }}>[{step.time}]</span>

                                    <span className="uppercase" style={{ color: 'var(--hud-muted)' }}>{step.status}</span>

                                </div>

                                <div className="leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--hud-text)' }}>

                                    {step.text}

                                </div>

                            </div>

                        ))}

                        {data.length === 0 && (

                            <div className="text-xs font-mono animate-pulse" style={{ color: 'var(--hud-muted)' }}>Initializing neural link...</div>

                        )}

                    </div>

                )}



                {type === 'stage2_mixed' && (

                    <div className="space-y-4">

                        {thinkingData && Object.entries(thinkingData).map(([judgeId, judgeData]) => (

                            <JudgeCard

                                key={judgeId}

                                judgeId={judgeId}

                                judgeData={judgeData}

                                targetId={targetId}

                                reviewComments={currentReviews}

                                now={now}

                            />

                        ))}

                        {(!thinkingData || Object.keys(thinkingData).length === 0) && (

                            <div className="text-xs font-mono animate-pulse" style={{ color: 'var(--hud-muted)' }}>Waiting for judges...</div>

                        )}

                    </div>

                )}



                {type === 'evaluation' && (

                    <div className="space-y-6">

                        {data.map((review, idx) => {

                            // We need judge name/avatar if possible. 'review.fromId' is available.

                            // Ideally passed in or verified.

                            // Assuming review.fromId is the councilor ID.

                            const uiConfig = getCouncilorUIConfig(review.fromId);

                            return (

                                <div
                                    key={idx}
                                    className="p-3 border"
                                    style={{ backgroundColor: 'rgba(8, 12, 24, 0.85)', borderColor: 'rgba(6, 182, 212, 0.25)' }}
                                >

                                    <div className="flex items-center justify-between mb-2 pb-2 border-b" style={{ borderColor: 'rgba(6, 182, 212, 0.2)' }}>

                                        <div className="flex items-center gap-2">

                                            <div className="w-2 h-2 rounded-full" style={{ background: `var(--accent-${uiConfig.color})` }}></div>

                                            <span className="text-xs font-bold" style={{ color: 'var(--hud-text)' }}>{review.fromId.toUpperCase()}</span>

                                        </div>

                                        {review.score && (

                                            <div className="text-xs font-mono font-bold" style={{ color: 'var(--hud-cyan)' }}>

                                                RANK #{review.score}

                                            </div>

                                        )}

                                    </div>

                                    <div className="text-sm leading-relaxed" style={{ color: 'var(--hud-muted)' }}>

                                        {/* Assuming plain text or markdown */}

                                        {review.comment}

                                    </div>

                                </div>

                            );

                        })}

                        {data.length === 0 && (

                            <div className="text-xs font-mono" style={{ color: 'var(--hud-muted)' }}>Waiting for peer reviews...</div>

                        )}

                    </div>

                )}



                {type === 'consensus_reviews' && (

                    <div className="space-y-8">

                        {stage2Skipped ? (

                            <div
                                className="flex flex-col items-center justify-center p-8 border border-dashed"
                                style={{ color: 'var(--hud-muted)', borderColor: 'rgba(6, 182, 212, 0.25)', backgroundColor: 'rgba(8, 12, 24, 0.6)' }}
                            >

                                <span className="text-sm font-mono mb-2">STAGE 2 SKIPPED</span>

                                <span className="text-xs text-center" style={{ color: 'var(--hud-muted)' }}>Insufficient candidates or expedited process.</span>

                            </div>

                        ) : (

                            // Iterate based on ranking order

                            (aggregateRankings.length > 0 ? aggregateRankings : Object.keys(evaluationComments).map(id => ({ councilor_id: id }))).map(item => {

                                const targetId = item.councilor_id;

                                const reviews = evaluationComments?.[targetId] || [];

                                if (reviews.length === 0) return null;



                                const targetConfig = getCouncilorUIConfig(targetId);



                                // Sort reviews: Score high to low, null last

                                const sortedReviews = [...reviews].sort((a, b) => {

                                    const sA = a.score ?? -1;

                                    const sB = b.score ?? -1;

                                    if (sA === -1 && sB === -1) return 0;

                                    if (sA === -1) return 1;

                                    if (sB === -1) return -1;

                                    return sA - sB; // Ascending (1, 2, 3...)

                                });



                                return (

                                    <div key={targetId} className="space-y-3">

                                        {/* Group Header */}

                                        <div className="flex items-center gap-2 pb-2 border-b" style={{ borderColor: 'rgba(6, 182, 212, 0.2)' }}>

                                            <div className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--accent-${targetConfig.color})` }}></div>

                                            <span className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--hud-text)' }}>

                                                To: {targetId}

                                            </span>

                                            {item.rank && (

                                                <span
                                                    className="ml-auto text-[10px] font-mono px-1.5 py-0.5 border"
                                                    style={{ color: 'var(--hud-cyan)', backgroundColor: 'rgba(6, 182, 212, 0.1)', borderColor: 'rgba(6, 182, 212, 0.3)' }}
                                                >

                                                    #{item.rank}

                                                </span>

                                            )}

                                        </div>



                                        {/* Reviews */}

                                        <div className="space-y-3">

                                            {sortedReviews.map((review, idx) => {

                                                const fromConfig = getCouncilorUIConfig(review.fromId);

                                                const isSelf = review.fromId === targetId;



                                                return (

                                                    <div
                                                        key={idx}
                                                        className="border p-3 text-sm transition-all"
                                                        style={{
                                                            backgroundColor: isSelf ? 'rgba(8, 12, 24, 0.4)' : 'rgba(8, 12, 24, 0.85)',
                                                            borderColor: isSelf ? 'rgba(6, 182, 212, 0.15)' : 'rgba(6, 182, 212, 0.25)',
                                                            color: isSelf ? 'rgba(91, 107, 122, 0.9)' : 'var(--hud-text)'
                                                        }}
                                                    >

                                                        <div className="flex items-center justify-between mb-2">

                                                            <div className="flex items-center gap-2">

                                                                <div className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--accent-${fromConfig.color})` }}></div>

                                                                <span
                                                                    className="text-[10px] font-bold uppercase"
                                                                    style={{ color: isSelf ? 'rgba(91, 107, 122, 0.9)' : 'var(--hud-muted)' }}
                                                                >

                                                                    {review.fromId} {isSelf && '(SELF)'}

                                                                </span>

                                                            </div>

                                                            {review.score && (

                                                                <span className="text-[10px] font-mono font-bold" style={{ color: 'var(--hud-cyan)' }}>

                                                                    R#{review.score}

                                                                </span>

                                                            )}

                                                        </div>

                                                        <div className={`leading-relaxed ${isSelf ? 'italic opacity-80' : ''}`}>

                                                            {review.comment}

                                                        </div>

                                                    </div>

                                                );

                                            })}

                                        </div>

                                    </div>

                                );

                            })

                        )}

                    </div>

                )}

            </div>

        </div>

    );

}



export default DetailPanel;

