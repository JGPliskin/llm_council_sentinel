import React from 'react';
import { Scale } from 'lucide-react'; // 图标：天平
import './ConsensusBeacon.css';

function ConsensusBeacon({ stage3Complete = false, hasViewedConsensus, activeTab = null, onClick }) {
    // 不显示条件：Stage 3 未完成，或用户已经在 final tab
    if (!stage3Complete) return null;
    if (activeTab === 'final') return null; // 用户已在 Consensus tab，不需要提示

    // 如果已经解锁，且用户未查看，或者用户曾经查看过但现在不在 Final Tab (implicit usage pattern)
    // Spec: "首次出现：Stage 3 完成，用户尚未点击" -> Pinging
    // "已查看后：切回其他 Tab" -> Static

    // Logic from parent: 
    // If consensusUnlocked is true, we render.
    // Style depends on hasViewedConsensus.

    const isPinging = !hasViewedConsensus;
    const className = `consensus-beacon ${isPinging ? 'consensus-beacon--pinging' : 'consensus-beacon--static'}`;

    return (
        <div className={className} onClick={onClick}>
            <Scale size={24} />
        </div>
    );
}

export default ConsensusBeacon;
