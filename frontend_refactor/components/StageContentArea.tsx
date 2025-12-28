import React from 'react';
import { Sparkles, Scale, Terminal, Cpu, Fingerprint } from 'lucide-react';
import { MOCK_AGENTS, CHAIRPERSON, MOCK_ANSWERS } from '../mockData';
import { AgentId } from '../types';

interface ContentProps {
  activeTab: string;
  onTabSelect: (id: string) => void;
  consensusUnlocked: boolean;
  hasViewedConsensus: boolean;
  selectedAgents: AgentId[];
}

export const StageContentArea = ({ activeTab, onTabSelect, consensusUnlocked, hasViewedConsensus, selectedAgents }: ContentProps) => {
  const isFinal = activeTab === 'final';
  // Use selected agents for tabs, plus "Consensus"
  const agents = MOCK_AGENTS.filter(a => selectedAgents.includes(a.id));
  
  const activeAgent = isFinal ? CHAIRPERSON : agents.find(a => a.id === activeTab);
  const answer = isFinal ? MOCK_ANSWERS['chair'] : MOCK_ANSWERS[activeTab as AgentId];

  // Fallback if no answer yet (Stage 1 generating)
  if (!answer) {
      return (
        <div className="flex-1 flex flex-col h-full bg-zinc-950 p-10 items-center justify-center text-zinc-600 font-mono animate-pulse">
            Waiting for data stream...
        </div>
      );
  }

  const glowColor = isFinal ? "purple" : activeAgent?.color || "gray";

  return (
    <div className="flex-1 flex flex-col h-full bg-zinc-950 overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
      
      {/* TABS */}
      <div className="flex items-end gap-0.5 px-2 border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-20 shrink-0 overflow-x-auto no-scrollbar h-14">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => onTabSelect(agent.id)}
            className={`
              relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide
              border-t-2 border-x border-zinc-800 hover:bg-zinc-800/50
              ${activeTab === agent.id 
                ? 'bg-zinc-800 text-white border-t-orange-500 border-x-zinc-700 z-10 -mb-px pb-4' 
                : 'bg-zinc-900/50 text-zinc-500'}
            `}
          >
            <span className={`${activeTab === agent.id ? 'opacity-100' : 'opacity-50'}`}>{agent.avatar}</span>
            <span className="hidden md:inline font-mono">{agent.name}</span>
          </button>
        ))}
        
        <div className="h-6 w-px bg-zinc-800 mx-2" />
        
        {/* Consensus Tab */}
        <button
          onClick={() => consensusUnlocked && onTabSelect('final')}
          disabled={!consensusUnlocked}
          className={`
            relative px-5 py-3 text-xs md:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 outline-none uppercase tracking-wide
            border-t-2 border-x border-zinc-800
            ${activeTab === 'final' 
              ? 'bg-zinc-800 text-purple-400 border-t-purple-500 border-x-zinc-700 z-10 -mb-px pb-4' 
              : consensusUnlocked ? 'text-zinc-400 hover:text-purple-400' : 'text-zinc-700 cursor-not-allowed opacity-50'}
          `}
        >
          {activeTab === 'final' ? <Sparkles className="w-4 h-4"/> : <Scale className="w-4 h-4" />}
          <span className="font-mono">Consensus</span>
        </button>
      </div>

      {/* TERMINAL CONTENT */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth relative z-10">
        <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Header Card */}
          <div className="mb-8 flex items-stretch gap-0 bg-zinc-900/50 border border-zinc-700 backdrop-blur-md relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-1">
                <div className="w-16 h-1 bg-zinc-700/50 rotate-45 transform translate-x-6 -translate-y-2"></div>
             </div>
             
             <div className={`w-24 md:w-32 flex items-center justify-center text-5xl relative overflow-hidden border-r border-zinc-700 bg-zinc-900`}>
               <div className={`absolute inset-0 opacity-20 bg-${glowColor}-500 blur-xl`}></div>
               <div className="relative z-10">{activeAgent?.avatar}</div>
               <div className="absolute bottom-0 left-0 right-0 text-[10px] text-center font-mono text-zinc-600 bg-zinc-950/80 py-1 uppercase">
                 Subject 0{activeAgent?.id.length}
               </div>
             </div>
             
             <div className="flex-1 p-4 md:p-6 flex flex-col justify-center">
               <div className="flex items-center gap-2 mb-1">
                  <Terminal className="w-4 h-4 text-zinc-500" />
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
                    Identify Friend/Foe // {activeAgent?.role} // Class A Entity
                  </span>
               </div>
               <h1 className={`text-3xl md:text-5xl font-black uppercase tracking-tighter ${isFinal ? 'text-purple-400 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]' : 'text-zinc-100'}`}>
                 {activeAgent?.name}
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

            <div className="prose prose-invert prose-lg max-w-none">
              <h2 className={`text-xl font-bold font-mono mb-6 pb-2 border-b border-zinc-800 ${isFinal ? 'text-purple-300' : 'text-orange-400'}`}>
                <span className="mr-2 opacity-50">>></span>{answer.title}
              </h2>
              
              <div className="space-y-6 text-zinc-300 font-sans leading-loose tracking-wide">
                {answer.content.map((paragraph, idx) => (
                  <div key={idx} className="relative pl-4 border-l-2 border-zinc-800 hover:border-zinc-600 transition-colors">
                    {paragraph.split('\n').map((line, i) => (
                      <span key={i} className="block mb-2 last:mb-0">
                        {line.startsWith('-') || line.startsWith('1.') ? (
                           <span className="ml-4 block text-zinc-400 font-mono text-base">{line}</span>
                        ) : (
                           line
                        )}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
              
              {isFinal && (
                <div className="mt-16 bg-purple-900/10 border border-purple-500/30 p-8 text-center relative overflow-hidden">
                   <div className="absolute inset-0 bg-dot-pattern opacity-20"></div>
                   <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-purple-500 to-transparent"></div>
                   <div className="relative z-10 flex flex-col items-center gap-4">
                     <Fingerprint className="w-12 h-12 text-purple-500 opacity-80" />
                     <p className="text-purple-200 font-mono italic text-lg tracking-wider">
                       "We do not lie to please, but we deliver the truth with kindness."
                     </p>
                     <div className="text-purple-500 text-xs font-black uppercase tracking-[0.2em] border px-2 py-1 border-purple-500 rounded">
                       Auth: Chairperson // Session Closed
                     </div>
                   </div>
                </div>
              )}
              
              {!isFinal && (
                <div className="mt-12 flex items-center gap-4 p-4 bg-zinc-950 border border-zinc-800 text-zinc-500 font-mono text-xs">
                  <Cpu className="w-4 h-4 animate-pulse" />
                  <span>Processing Node: {activeAgent?.id.toUpperCase()}-X7 // Latency: 42ms // Trust Score: 98.4%</span>
                </div>
              )}
            </div>
          </div>
          <div className="h-24" />
        </div>
      </div>

      {/* --- TACTICAL DATA BEACON --- */}
      {/* Appears when Consensus is unlocked but not currently viewing it */}
      {consensusUnlocked && !isFinal && (
         <button
            onClick={() => onTabSelect('final')}
            className="absolute bottom-6 right-6 z-30 group animate-in slide-in-from-bottom-4 duration-500"
         >
            <div className="relative">
               {/* Pulsing Aura - Only if NOT viewed yet */}
               {!hasViewedConsensus && (
                  <div className="absolute inset-0 bg-purple-500 rounded-full animate-ping opacity-75"></div>
               )}
               
               {/* Main Button */}
               <div className="relative flex items-center justify-center w-14 h-14 bg-purple-600 border-2 border-purple-400 rounded-full shadow-[0_0_20px_rgba(168,85,247,0.6)] text-white hover:scale-110 transition-transform">
                  <Scale className="w-6 h-6" />
               </div>
               
               {/* Tooltip Label */}
               <div className="absolute bottom-full right-0 mb-2 whitespace-nowrap bg-purple-900 text-purple-100 text-[10px] font-mono px-2 py-1 rounded border border-purple-500 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  CONSENSUS READY // TAP TO READ
               </div>
            </div>
         </button>
      )}
    </div>
  );
};
