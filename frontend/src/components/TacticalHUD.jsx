import React, { useMemo } from 'react';
import { Sparkles } from 'lucide-react';
import { getCouncilorUIConfig } from '@/config/councilors';
import './TacticalHUD.css';

function TacticalHUD({
    stage,
    agentProgress,
    aggregateRankings,
    resolvedCouncilors,
    consensusUnlocked,
    hasViewedConsensus,
    onConsensusClick,
    // New props for IDLE stage
    selectedAgentIds = [],
    allCouncilors = [],
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
            // 按排名排序
            return [...aggregateRankings].sort((a, b) => a.rank - b.rank);
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

        return (
            <div
                key={agent.councilor_id}
                className={`agent-slice ${hasRanking ? 'border-opacity-100' : 'border-opacity-50'}`}
                style={{ borderColor: `var(--accent-${uiConfig.color})` }}
            >
                {/* 排名徽章 */}
                {hasRanking && (
                    <div className="rank-badge">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                    </div>
                )}

                {/* Avatar + 名字 */}
                <div className="agent-avatar">{agent.avatar}</div>
                <div className="agent-name">{agent.name}</div>

                {/* 进度条 或 分数 */}
                {!hasRanking ? (
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${progress}%`, backgroundColor: `var(--accent-${uiConfig.color})` }}
                        />
                    </div>
                ) : (
                    <div className="score">平均 #{agent.average_rank?.toFixed(1)}</div>
                )}
            </div>
        );
    };

    const stageClass = stage === 'stage1' ? 'tactical-hud--stage1'
        : stage === 'stage2' ? 'tactical-hud--stage2'
            : stage === 'stage3' ? 'tactical-hud--stage3'
                : '';

    return (
        <div className={`tactical-hud ${stageClass}`}>
            {/* Stage 指示器 */}
            <div className="stage-indicator">
                STAGE [{stage === 'idle' ? 'STANDBY' : stage === 'stage1' ? '01' : stage === 'stage2' ? '02' : '03'}]
                {/* {stage === 'stage3' && consensusUnlocked ? ' CONSENSUS' : ''} */}
            </div>

            {/* Agent 卡片列表 */}
            <div className="agent-slots">
                {displaySlots.map((agent, index) => renderAgentSlice(agent, index))}
            </div>

            {/* Consensus Ready Overlay */}
            {consensusUnlocked && !hasViewedConsensus && (
                <div className="consensus-overlay" onClick={onConsensusClick}>
                    <div className="overlay-content">
                        <Sparkles className="icon" />
                        <span>CONSENSUS READY</span>
                        <span className="hint">TAP TO REVEAL</span>
                    </div>
                </div>
            )}
        </div>
    );
}

export default TacticalHUD;
