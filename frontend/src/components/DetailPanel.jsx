import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { X, Maximize2, Minimize2 } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';

// 延迟显示 review 的时间（毫秒）
const REVIEW_DISPLAY_DELAY_MS = 1500;

/**
 * 获取当前应展示的详情内容
 */
function getDetailContent(stage, activeTab, evaluationComments, synthesisSteps, stage2ThinkingByJudge) {
    // Consensus Tab → 显示分组的 Stage 2 评审
    if (activeTab === 'final') {
        return {
            type: 'consensus_reviews',
            title: 'Peer Reviews',
            // data: evaluationComments, (access directly in component)
        };
    }

    // Stage 1 → 显示用户提问
    if (stage === 'stage1') {
        return {
            type: 'user_prompt',
            title: 'User Question',
        };
    }

    // Stage 2 → 始终使用 stage2_mixed 类型，支持混合显示
    if (stage === 'stage2') {
        return {
            type: 'stage2_mixed',
            title: 'Judge Analysis',
            thinkingData: stage2ThinkingByJudge,
            reviewData: evaluationComments,
            targetId: activeTab, // 当前选中的议员 ID
        };
    }

    // Stage 3 → 显示对当前议员的评价
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
 * 单个 Judge 卡片组件
 * 根据状态和时间决定显示 thinking 还是 review
 */
function JudgeCard({ judgeId, judgeData, targetId, reviewComments, now }) {
    const uiConfig = getCouncilorUIConfig(judgeId);
    const status = judgeData.status;
    const doneAt = judgeData.doneAt;

    // 获取针对当前 targetId 的思考步骤
    const targetSteps = judgeData.stepsByTarget?.[targetId] || [];
    const latestStep = targetSteps[targetSteps.length - 1];

    // 获取该 judge 对当前 target 的 review
    const reviewFromJudge = reviewComments?.find(r => r.fromId === judgeId);

    // 判断是否应该显示 review（完成后延迟 1.5 秒）
    const shouldShowReview = status === 'done' && doneAt && (now - doneAt >= REVIEW_DISPLAY_DELAY_MS) && reviewFromJudge;

    // 如果这个 judge 没有针对当前 target 的 thinking 且不该显示 review，跳过
    if (targetSteps.length === 0 && status !== 'thinking' && !shouldShowReview) {
        return null;
    }

    return (
        <div className="relative p-3 rounded transition-all duration-500 clip-corner-top-right"
            style={{ backgroundColor: 'var(--hud-bg)', border: '1px solid var(--hud-cyan-soft)' }}>
            {/* Left accent line */}
            <div className="absolute top-0 left-0 w-[2px] h-full" style={{ backgroundColor: 'var(--hud-cyan)' }}></div>

            {/* Judge Header */}
            <div className="flex items-center gap-2 mb-2 pb-2" style={{ borderBottom: '1px solid var(--hud-cyan-soft)' }}>
                <div className="w-2 h-2 rounded-full" style={{ background: `var(--accent-${uiConfig.color})` }}></div>
                <span className="text-xs font-bold font-hud" style={{ color: 'var(--hud-text)' }}>{judgeId.toUpperCase()}</span>
                {status === 'thinking' && (
                    <span className="text-xs animate-pulse ml-auto" style={{ color: 'var(--hud-amber)' }}>ANALYZING...</span>
                )}
                {status === 'done' && !shouldShowReview && (
                    <span className="text-xs ml-auto" style={{ color: '#10b981' }}>✓ COMPLETE</span>
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
    // 用于触发重新渲染的时间戳
    const [now, setNow] = useState(Date.now());

    // 监听 stage2ThinkingByJudge 变化，检查是否有 judge 刚完成
    useEffect(() => {
        if (stage !== 'stage2' || !stage2ThinkingByJudge) return;

        // 检查是否有 judge 处于"刚完成但还未显示 review"的状态
        const needsUpdate = Object.values(stage2ThinkingByJudge).some(judgeData => {
            if (judgeData.status === 'done' && judgeData.doneAt) {
                const elapsed = Date.now() - judgeData.doneAt;
                return elapsed < REVIEW_DISPLAY_DELAY_MS;
            }
            return false;
        });

        if (needsUpdate) {
            // 设置定时器在延迟后触发重新渲染
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

    // 当前 target 的 review 列表
    const currentReviews = reviewData?.[activeTab] || [];

    // 检查是否所有 judge 都已完成且过了延迟时间（用于切换标题）
    const allReviewsReady = thinkingData && Object.values(thinkingData).every(j => {
        if (j.status !== 'done') return false;
        if (!j.doneAt) return true;
        return (now - j.doneAt) >= REVIEW_DISPLAY_DELAY_MS;
    }) && Object.keys(thinkingData).length > 0;

    // 动态标题
    const displayTitle = type === 'stage2_mixed'
        ? (allReviewsReady ? 'Peer Reviews' : 'Judge Analysis')
        : title;

    return (
        <div className="h-full flex flex-col backdrop-blur-md" style={{ backgroundColor: 'var(--hud-bg-soft)', borderLeft: '1px solid var(--hud-cyan-soft)' }}>
            {/* Drag Handle (Mobile only, visual only) */}
            <div className="md:hidden flex justify-center py-2">
                <div className="w-10 h-1 rounded-full" style={{ backgroundColor: 'var(--hud-cyan-soft)' }}></div>
            </div>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--hud-cyan-soft)', backgroundColor: 'var(--hud-bg)' }}>
                <h2 className={`text-sm font-bold tracking-widest uppercase font-hud ${stage === 'stage2' ? 'animate-breathe' : ''}`}
                    style={{ color: 'var(--hud-cyan)', textShadow: '0 0 8px var(--hud-cyan)' }}>
                    {displayTitle || "UNIT_STATUS"}
                </h2>
                <div className="flex items-center gap-2">
                    {/* Fullscreen Button (Stage 3 only) */}
                    {stage === 'stage3' && onToggleFullscreen && (
                        <button
                            onClick={onToggleFullscreen}
                            className="p-1.5 hover:bg-opacity-50 border border-transparent transition-all group"
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
                        className="p-1.5 hover:bg-opacity-50 border border-transparent transition-all group"
                        style={{ color: 'var(--hud-muted)' }}
                        title="Close Panel"
                    >
                        <X className="w-4 h-4 group-hover:rotate-90 transition-transform duration-300" />
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
                        <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--hud-muted)' }}>User Question</div>
                        <div className="text-sm leading-relaxed p-3 rounded"
                            style={{ backgroundColor: 'var(--hud-bg)', border: '1px solid var(--hud-cyan-soft)', color: 'var(--hud-text)' }}>
                            {userPrompt || 'No question available'}
                        </div>
                    </div>
                )}

                {type === 'thinking' && (
                    <div className="space-y-4">
                        {data.map(step => (
                            <div key={step.id} className="font-mono text-xs">
                                <div className="flex items-center gap-2 mb-1 opacity-50">
                                    <span className="text-orange-500">[{step.time}]</span>
                                    <span className="text-zinc-500 uppercase">{step.status}</span>
                                </div>
                                <div className="text-zinc-300 leading-relaxed whitespace-pre-wrap">
                                    {step.text}
                                </div>
                            </div>
                        ))}
                        {data.length === 0 && (
                            <div className="text-zinc-600 text-xs font-mono animate-pulse">Initializing neural link...</div>
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
                            <div className="text-zinc-600 text-xs font-mono animate-pulse">Waiting for judges...</div>
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
                                <div key={idx} className="bg-zinc-950/50 border border-zinc-800 p-3 rounded">
                                    <div className="flex items-center justify-between mb-2 pb-2 border-b border-zinc-800/50">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full" style={{ background: `var(--accent-${uiConfig.color})` }}></div>
                                            <span className="text-xs font-bold text-zinc-300">{review.fromId.toUpperCase()}</span>
                                        </div>
                                        {review.score && (
                                            <div className="text-xs font-mono font-bold text-zinc-400">
                                                RANK #{review.score}
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-sm text-zinc-400 leading-relaxed">
                                        {/* Assuming plain text or markdown */}
                                        {review.comment}
                                    </div>
                                </div>
                            );
                        })}
                        {data.length === 0 && (
                            <div className="text-zinc-600 text-xs font-mono">Waiting for peer reviews...</div>
                        )}
                    </div>
                )}

                {type === 'consensus_reviews' && (
                    <div className="space-y-8">
                        {stage2Skipped ? (
                            <div className="flex flex-col items-center justify-center p-8 text-zinc-500 border border-zinc-800 border-dashed bg-zinc-950/30 rounded">
                                <span className="text-sm font-mono mb-2">STAGE 2 SKIPPED</span>
                                <span className="text-xs text-zinc-600 text-center">Insufficient candidates or expedited process.</span>
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
                                        <div className="flex items-center gap-2 pb-2 border-b border-zinc-800">
                                            <div className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--accent-${targetConfig.color})` }}></div>
                                            <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">
                                                To: {targetId}
                                            </span>
                                            {item.rank && (
                                                <span className="ml-auto text-[10px] font-mono bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-400">
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
                                                        className={`
                                                            border p-3 rounded text-sm transition-all
                                                            ${isSelf
                                                                ? 'bg-zinc-900/20 border-zinc-800/50 text-zinc-500'
                                                                : 'bg-zinc-950/50 border-zinc-800 text-zinc-300'}
                                                        `}
                                                    >
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className="flex items-center gap-2">
                                                                <div className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--accent-${fromConfig.color})` }}></div>
                                                                <span className={`text-[10px] font-bold uppercase ${isSelf ? 'text-zinc-600' : 'text-zinc-400'}`}>
                                                                    {review.fromId} {isSelf && '(SELF)'}
                                                                </span>
                                                            </div>
                                                            {review.score && (
                                                                <span className="text-[10px] font-mono font-bold text-zinc-500">
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
