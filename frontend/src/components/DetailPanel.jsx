import React from 'react';
import ReactMarkdown from 'react-markdown';
import { getCouncilorUIConfig } from '@/config/councilors';

/**
 * 获取当前应展示的详情内容
 */
function getDetailContent(stage, activeTab, thinkingSteps, evaluationComments, synthesisSteps) {
    // Consensus Tab → 显示主席思考过程
    if (activeTab === 'final') {
        return {
            type: 'thinking',
            title: 'Chairman Synthesis',
            data: synthesisSteps,
        };
    }

    // Stage 1 → 显示当前议员的思考过程
    if (stage === 'stage1') {
        const agentSteps = thinkingSteps.filter(s => s.agentId === activeTab);
        return {
            type: 'thinking',
            title: 'Thinking Process',
            data: agentSteps,
        };
    }

    // Stage 2 或 Stage 3 → 显示对当前议员的评价
    if (stage === 'stage2' || stage === 'stage3') {
        const comments = evaluationComments[activeTab] || [];
        return {
            type: 'evaluation',
            title: 'Peer Reviews',
            data: comments,
        };
    }

    return { type: 'empty', title: '', data: [] };
}

export function DetailPanel({ stage, activeTab, thinkingSteps, evaluationComments, synthesisSteps, onClose }) {
    const { type, title, data } = getDetailContent(stage, activeTab, thinkingSteps, evaluationComments, synthesisSteps);

    return (
        <div className="h-full flex flex-col bg-zinc-900/90 border-l border-zinc-800 backdrop-blur-md">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950/50">
                <h2 className="text-sm font-bold tracking-widest uppercase text-zinc-400">
                    {title || "SYSTEM LOG"}
                </h2>
                {/* Close button for mobile or just in general? (Spec says can be collapsed) */}
                {/* <button onClick={onClose} className="text-zinc-500 hover:text-white">✕</button> */}
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
