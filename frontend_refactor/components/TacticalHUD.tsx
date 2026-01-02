import React, { useState, useEffect } from 'react';
import { AgentProfile, SimulationStage, PeerReview, Ranking, AgentId } from '../types';
import { MOCK_AGENTS } from '../mockData';
import { Zap, Target, ShieldAlert, Scale, Lock } from 'lucide-react';

// --- SUB-COMPONENT: AgentSlice ---
const AgentSlice = ({ agent, status, progress, isReviewer, isTarget, ranking }: any) => {
  let borderColor = "border-zinc-800";
  let glowClass = "";
  let statusColor = "bg-zinc-900";
  let textColor = "text-zinc-500";
  let icon = null;
  
  if (status === 'standby') {
     // STAGING AREA LOOK
     borderColor = "border-zinc-800"; // Low profile
     glowClass = "";
     statusColor = "bg-zinc-900"; // Darker background
     textColor = "text-zinc-600";
     icon = <Lock className="w-3 h-3 text-zinc-700" />;
  } else if (status === 'generating') {
    borderColor = "border-orange-500/50";
    glowClass = "shadow-[inset_0_0_20px_rgba(249,115,22,0.2)]";
    statusColor = "bg-orange-900/40";
    textColor = "text-orange-500";
    icon = <Zap className="w-3 h-3 text-orange-500 animate-pulse" />;
  } else if (isReviewer) {
    borderColor = "border-blue-500/50";
    glowClass = "shadow-[inset_0_0_20px_rgba(59,130,246,0.2)]";
    statusColor = "bg-blue-900/40";
    textColor = "text-blue-400";
    icon = <Target className="w-3 h-3 text-blue-400" />;
  } else if (isTarget) {
    borderColor = "border-red-500/50";
    glowClass = "shadow-[inset_0_0_20px_rgba(239,68,68,0.2)]";
    statusColor = "bg-red-900/40";
    textColor = "text-red-500";
    icon = <ShieldAlert className="w-3 h-3 text-red-500 animate-bounce" />;
  } else if (status === 'complete') {
    borderColor = "border-teal-600/50";
    statusColor = "bg-teal-900/20";
    textColor = "text-teal-500";
  }

  return (
    <div className={`relative group flex-1 h-full min-w-[80px] md:min-w-[90px] mx-1 transition-all duration-300 flex flex-col ${status === 'standby' ? 'animate-in fade-in zoom-in-95 duration-300' : ''}`}>
      {/* Top Connection Ports */}
      <div className={`w-full h-1 mb-0.5 flex justify-between px-2 opacity-50 transition-colors ${status === 'generating' ? 'text-orange-500' : 'text-zinc-800'}`}>
         <div className="w-1 h-full bg-current"></div>
         <div className="w-1 h-full bg-current"></div>
      </div>

      {/* Main Card Body */}
      <div className={`relative flex-1 backdrop-blur-sm overflow-hidden ${glowClass} transition-all duration-300`}
        style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}>
        
        {status !== 'standby' && <div className="absolute inset-0 opacity-20 bg-dot-pattern" />}
        <div className={`absolute inset-0 opacity-30 bg-gradient-to-b from-transparent to-black/80 ${statusColor}`} />
        
        {/* Parallel Progress Fill */}
        {status !== 'standby' && (
            <div className="absolute bottom-0 left-0 right-0 bg-orange-500/20 transition-all duration-300 ease-linear border-t border-orange-500/50"
            style={{ height: `${progress}%`, opacity: progress > 0 ? 1 : 0 }}>
            <div className="absolute inset-0 bg-stripe-pattern opacity-30 animate-[scanline_2s_linear_infinite]" />
            </div>
        )}

        <div className="absolute inset-0 flex flex-col p-2 md:p-3">
          <div className="flex justify-between items-start mb-2">
             <span className="text-[8px] md:text-[10px] font-mono text-zinc-600 tracking-wider hidden md:block">ID_0{agent.id.length}</span>
             <div className="flex gap-1">
               {icon}
             </div>
             {ranking && (
                <div className={`absolute top-0 right-0 pl-2 pb-1 pt-1 pr-2 border-l border-b ${ranking.rank === 1 ? 'border-yellow-500/50 bg-yellow-900/20' : 'border-zinc-700 bg-zinc-800'}`}>
                   <div className="flex items-center gap-1.5">
                      <span className={`text-xs font-bold font-mono ${ranking.rank === 1 ? 'text-yellow-400' : 'text-zinc-300'}`}>{ranking.score}</span>
                      <span className="text-[10px] opacity-60">{ranking.rank === 1 ? '🥇' : `#${ranking.rank}`}</span>
                   </div>
                </div>
             )}
          </div>
          <div className="flex-1" />
          <div className="flex flex-col gap-1 z-10">
            <div className={`flex items-center gap-2 transition-colors ${status === 'standby' ? 'text-zinc-600 grayscale' : 'text-zinc-100'}`}>
               <span className="text-lg md:text-xl filter drop-shadow-md">{agent.avatar}</span>
               <span className="text-xs md:text-sm font-black uppercase tracking-tight leading-none truncate">{agent.name}</span>
            </div>
            
            {/* Status Line / Progress Bar */}
            <div className={`h-0.5 w-full mt-1 mb-1 relative overflow-hidden bg-zinc-800`}>
               {status !== 'standby' && (
                  <div className={`absolute left-0 top-0 bottom-0 w-full transform -translate-x-full transition-transform duration-1000 ${status === 'complete' ? 'translate-x-0 bg-teal-500' : 'bg-orange-500'} ${status === 'generating' ? 'animate-[slideInRight_1s_infinite]' : ''}`} />
               )}
            </div>
            
            <span className={`text-[8px] md:text-[9px] uppercase tracking-widest truncate font-mono hidden md:block ${status === 'standby' ? 'text-zinc-700' : 'text-zinc-500'}`}>
                {status === 'standby' ? 'STANDBY' : agent.role}
            </span>
          </div>
        </div>
        
        {/* Borders */}
        <div className={`absolute top-0 left-[10px] w-full h-[1px] ${borderColor}`} />
        <div className={`absolute top-[10px] left-0 h-full w-[1px] ${borderColor}`} />
        <div className={`absolute inset-0 border-2 pointer-events-none opacity-50 rounded-none ${borderColor}`} style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}></div>
      </div>
      
      {/* Bottom Connection Ports */}
      <div className={`w-full h-1 mt-0.5 flex justify-center px-4 opacity-30 ${status === 'complete' ? 'text-teal-500' : 'text-zinc-800'}`}>
         <div className="w-full h-full border-b border-x border-current"></div>
      </div>
    </div>
  );
};

// --- SUB-COMPONENT: ConnectionOverlay ---
const ConnectionOverlay = ({ evaluations, agents, selectedAgents }: { evaluations: PeerReview[], agents: AgentProfile[], selectedAgents: AgentId[] }) => {
  if (!evaluations || evaluations.length === 0) return null;
  const activeEval = evaluations[evaluations.length - 1]; 
  
  // Filter agents to only those active/selected to calculate correct SVG coordinates
  const activeAgentProfiles = agents.filter(a => selectedAgents.includes(a.id));
  const fromIndex = activeAgentProfiles.findIndex(a => a.id === activeEval.from);
  const toIndex = activeAgentProfiles.findIndex(a => a.id === activeEval.to);

  if (fromIndex === -1 || toIndex === -1) return null;
  
  // Dynamic width calculation based on active count
  const sliceWidth = 100 / activeAgentProfiles.length;
  const getX = (index: number) => `${(index * sliceWidth) + (sliceWidth / 2)}%`;
  
  const startX = getX(fromIndex);
  const endX = getX(toIndex);
  const isRight = toIndex > fromIndex;

  return (
    <div className="absolute inset-0 pointer-events-none z-30 overflow-visible h-full">
      <svg className="w-full h-full overflow-visible">
        <defs>
          <linearGradient id="beamGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
          <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
            <polygon points="0 0, 6 2, 0 4" fill="#60a5fa" />
          </marker>
        </defs>
        <path d={`M ${startX} 40 Q ${isRight ? parseInt(startX)+10 : parseInt(startX)-10}% 10, ${endX} 40`}
          fill="none" stroke="url(#beamGradient)" strokeWidth="2"
          className="animate-[dash_0.4s_linear_forwards]"
          strokeDasharray="500" strokeDashoffset="500" markerEnd="url(#arrowhead)"
        />
        <circle cx={startX} cy="40" r="3" fill="#60a5fa" className="animate-ping" />
        <circle cx={endX} cy="40" r="3" fill="#ef4444" className="animate-ping" style={{ animationDelay: '0.4s' }} />
      </svg>
    </div>
  );
};

// --- MAIN HUD COMPONENT ---
interface HUDProps {
  stage: SimulationStage;
  agentProgress: Partial<Record<AgentId, number>>; // Individual progress
  evaluations: PeerReview[];
  rankings: Ranking[];
  consensusUnlocked: boolean;
  onConsensusClick: () => void;
  selectedAgents: AgentId[];
  hasViewedConsensus: boolean;
}

export const TacticalHUD = ({ stage, agentProgress, evaluations, rankings, consensusUnlocked, onConsensusClick, selectedAgents, hasViewedConsensus }: HUDProps) => {

  const getStageDisplay = () => {
    switch(stage) {
      case 'idle': return { num: '00', name: 'STANDBY', color: 'text-zinc-500' };
      case 'stage1': return { num: '01', name: 'GENERATION', color: 'text-orange-500' };
      case 'stage2': return { num: '02', name: 'PEER REVIEW', color: 'text-blue-500' };
      case 'stage3': return { num: '03', name: 'CONSENSUS', color: 'text-purple-500' };
      default: return { num: '--', name: 'OFFLINE', color: 'text-zinc-600' };
    }
  };

  const stageInfo = getStageDisplay();

  // Filter agents based on selection
  const activeAgents = MOCK_AGENTS.filter(a => selectedAgents.includes(a.id));

  return (
    <div className={`relative h-40 md:h-48 bg-zinc-950 border-t-4 flex flex-col shadow-[0_-10px_40px_rgba(0,0,0,0.5)] z-30 font-sans shrink-0 transition-colors duration-500 ${stage === 'stage3' ? 'border-purple-600' : 'border-orange-600'}`}>
       
       {/* Status Bar */}
       <div className="h-8 bg-zinc-900 flex items-center justify-between px-4 text-[10px] md:text-xs font-mono uppercase tracking-widest border-b border-zinc-800">
          <div className="flex items-center gap-4">
             {/* Stage Indicator */}
             <div className={`flex items-center gap-2 font-bold ${stageInfo.color}`}>
                <div className={`w-2 h-2 rounded-full ${stage === 'stage1' ? 'bg-orange-500 animate-pulse' : stage === 'idle' ? 'bg-zinc-600' : stage === 'stage3' ? 'bg-purple-500' : 'bg-blue-500'}`} />
                <span>STAGE [{stageInfo.num} / 03]</span>
                <span className="opacity-40">//</span>
                <span>{stageInfo.name}</span>
             </div>
          </div>
          <div className="hidden md:flex gap-4 opacity-50 text-zinc-500">
             <span>CPU: 45%</span>
             <span>MEM: 12GB</span>
          </div>
       </div>

       {/* Agent Container */}
       <div className="relative flex-1 p-2 md:p-4 flex items-end justify-center gap-1 overflow-hidden">
          
          {/* Always show agent slices, but styling depends on stage */}
          
          {stage === 'stage2' && <ConnectionOverlay evaluations={evaluations} agents={MOCK_AGENTS} selectedAgents={selectedAgents} />}
          
          {activeAgents.length === 0 ? (
             <div className="flex items-center justify-center w-full h-full text-zinc-700 font-mono text-xs tracking-widest uppercase">
                -- No Councilors Selected --
             </div>
          ) : (
            activeAgents.map((agent, idx) => {
               // Logic for visual state of slice
               let status = 'idle';
               
               if (stage === 'idle') {
                  status = 'standby';
               } else {
                 const progress = agentProgress[agent.id] || 0;
                 if (progress > 0 && progress < 100) status = 'generating';
                 else if (progress === 100) status = 'complete';
               }

               let isReviewer = false;
               let isTarget = false;
               if (stage === 'stage2' && evaluations.length > 0) {
                  const lastEval = evaluations[evaluations.length - 1];
                  if (lastEval.from === agent.id) isReviewer = true;
                  if (lastEval.to === agent.id) isTarget = true;
               }
               
               // Rankings only show if we have 'unlocked' consensus (engine finished stage 3)
               let ranking = null;
               if (consensusUnlocked && rankings) {
                  ranking = rankings.find(r => r.id === agent.id);
               }

               return <AgentSlice 
                  key={agent.id} 
                  agent={agent} 
                  status={status} 
                  progress={agentProgress[agent.id] || 0} 
                  isReviewer={isReviewer} 
                  isTarget={isTarget} 
                  ranking={ranking} 
               />;
            })
          )}

          {/* STAGE 3 CONSENSUS BEACON (The "Click to view" overlay) */}
          {/* Note: This overlay now only appears if the user has NOT viewed consensus yet. */}
          {consensusUnlocked && !hasViewedConsensus && (
             <div 
                onClick={onConsensusClick}
                className="absolute inset-0 bg-black/80 backdrop-blur-sm z-40 flex items-center justify-center animate-in fade-in duration-1000 cursor-pointer hover:bg-black/70 transition-colors"
             >
                <div className="bg-zinc-900 border-2 border-purple-500 p-4 md:p-6 transform -skew-x-12 shadow-[0_0_50px_rgba(168,85,247,0.5)] max-w-lg w-full mx-4 group">
                   <div className="transform skew-x-12 text-center group-hover:scale-105 transition-transform duration-300">
                      <div className="flex justify-center mb-2">
                         <div className="bg-purple-500 text-white p-2 rounded-full"><Scale className="w-8 h-8" /></div>
                      </div>
                      <h2 className="text-2xl md:text-3xl font-black text-white uppercase tracking-tighter mb-2">Consensus Ready</h2>
                      <div className="h-px w-32 bg-purple-500 mx-auto mb-4" />
                      <p className="text-purple-300 font-mono text-xs md:text-sm">
                         PARLIAMENTARY DECREE #404 ISSUED.<br/>TAP TO VIEW REPORT.
                      </p>
                   </div>
                </div>
             </div>
          )}
       </div>
    </div>
  );
};
