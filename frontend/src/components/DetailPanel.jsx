import React from 'react';
import ReactMarkdown from 'react-markdown';
import { X } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';

/**
 * 获取当前应展示的详情内容
 */
function getDetailContent(stage, activeTab, evaluationComments, synthesisSteps, stage2ThinkingByJudge) {
    // Consensus Tab → 显示主席思考过程
    if (activeTab === 'final') {
        return {
            type: 'thinking',
            title: 'Chairman Synthesis',
            data: synthesisSteps,
        };
    }

    // Stage 2 → 显示 thinking 和 evaluation
    if (stage === 'stage2') {
        // 检查是否有任何 judge 仍在 thinking 状态
        const hasThinkingJudge = stage2ThinkingByJudge &&
            Object.values(stage2ThinkingByJudge).some(j => j.status === 'thinking');

        // 如果有 judge 还在 thinking，显示 thinking 面板
        if (hasThinkingJudge) {
            return {
                type: 'stage2_thinking',
                title: 'Judge Analysis',
                data: stage2ThinkingByJudge,
                targetId: activeTab, // 当前选中的议员 ID
            };
        }

        // 否则显示已完成的评价
        const comments = evaluationComments[activeTab] || [];
        return {
            type: 'evaluation',
            title: 'Peer Reviews',
            data: comments,
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

export function DetailPanel({
    stage,
    activeTab,
    evaluationComments,
    synthesisSteps,
    stage2ThinkingByJudge,
    stage2AnonMap,
    onClose
}) {
    const { type, title, data, targetId } = getDetailContent(
        stage,
        activeTab,
        evaluationComments,
        synthesisSteps,
        stage2ThinkingByJudge
    );

    return (
        <div className="h-full flex flex-col bg-zinc-900/90 border-l border-zinc-800 backdrop-blur-md">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950/50">
                <h2 className="text-sm font-bold tracking-widest uppercase text-zinc-400">
                    {title || "SYSTEM LOG"}
                </h2>
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="p-1.5 text-zinc-500 hover:text-white hover:bg-zinc-800 border border-transparent hover:border-zinc-700 transition-all group"
                    title="Close Panel"
                >
                    <X className="w-4 h-4 group-hover:rotate-90 transition-transform duration-300" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                {type === 'empty' && (
                    <div className="flex items-center justify-center h-full text-zinc-600 text-xs font-mono">
                        NO DATA AVAILABLE
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

                {type === 'stage2_thinking' && (
                    <div className="space-y-4">
                        {Object.entries(data).map(([judgeId, judgeData]) => {
                            // 获取针对当前 targetId 的思考步骤
                            const targetSteps = judgeData.stepsByTarget?.[targetId] || [];
                            const status = judgeData.status;

                            // 如果这个 judge 没有针对当前 target 的 thinking，跳过
                            if (targetSteps.length === 0 && status !== 'thinking') {
                                return null;
                            }

                            const uiConfig = getCouncilorUIConfig(judgeId);
                            // 获取最新的一条 thinking
                            const latestStep = targetSteps[targetSteps.length - 1];

                            return (
                                <div key={judgeId} className="bg-zinc-950/50 border border-zinc-800 p-3 rounded">
                                    {/* Judge Header */}
                                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-zinc-800/50">
                                        <div className="w-2 h-2 rounded-full" style={{ background: `var(--accent-${uiConfig.color})` }}></div>
                                        <span className="text-xs font-bold text-zinc-300">{judgeId.toUpperCase()}</span>
                                        {status === 'thinking' && (
                                            <span className="text-xs text-orange-500 animate-pulse ml-auto">ANALYZING...</span>
                                        )}
                                        {status === 'done' && (
                                            <span className="text-xs text-green-500 ml-auto">✓ COMPLETE</span>
                                        )}
                                    </div>

                                    {/* Latest Thinking Step */}
                                    {latestStep ? (
                                        <div className="space-y-1">
                                            <div className="text-sm font-medium text-zinc-300">
                                                {latestStep.title}
                                            </div>
                                            {latestStep.detail && (
                                                <div className="text-xs text-zinc-400 leading-relaxed opacity-80">
                                                    {latestStep.detail}
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="text-xs text-zinc-600 font-mono animate-pulse">
                                            Initializing analysis...
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                        {Object.keys(data).length === 0 && (
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
            </div>
        </div>
    );
}

export default DetailPanel;
