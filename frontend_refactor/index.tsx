import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  X, Loader2, CheckCircle2, Circle, MessageSquare, MoreHorizontal, Scale, Zap, Target,
  LayoutGrid, Plus, Fingerprint, PanelLeftClose, PanelLeftOpen, PanelRightOpen, Play, RotateCcw
} from 'lucide-react';

import { useParliamentEngine } from './hooks/useParliamentEngine';
import { TacticalHUD } from './components/TacticalHUD';
import { WelcomeScreen } from './components/WelcomeScreen';
import { StageContentArea } from './components/StageContentArea';
import { MOCK_AGENTS, CHAIRPERSON } from './mockData';
import { AgentId } from './types';

// --- SHARED SUB-COMPONENTS (Keep simple ones here for now) ---

const ThinkingProcess = ({ steps, title = "System Logs" }: any) => {
  return (
    <div className="flex flex-col gap-4 p-1">
      <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2 flex items-center gap-2">
         <Zap className="w-3 h-3 text-orange-500" />
         {title}
      </div>
      {steps.length === 0 && <div className="text-sm text-zinc-600 italic">Waiting to start...</div>}
      {steps.map((step: any) => {
        const agent = step.agentId === 'chair' ? CHAIRPERSON : MOCK_AGENTS.find(a => a.id === step.agentId);
        return (
          <div key={step.id} className="flex gap-3 items-start group animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="mt-1">
              {step.status === 'complete' && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
              {step.status === 'processing' && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
              {step.status === 'pending' && <Circle className="w-4 h-4 text-zinc-700" />}
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
                  <span>{agent?.avatar}</span> {agent?.name}
                </span>
                <span className="text-xs text-zinc-600 font-mono">{step.time}</span>
              </div>
              <div className="text-xs md:text-sm text-zinc-400 font-mono leading-relaxed bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                {step.text}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const EvaluationList = ({ evaluations }: any) => {
  return (
    <div className="flex flex-col gap-6 p-1">
      <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2 flex items-center gap-2">
        <Target className="w-3 h-3 text-red-500" /> Live Peer Reviews
      </div>
      {evaluations.length === 0 && <div className="text-sm text-zinc-600 italic">Waiting for peer reviews...</div>}
      {evaluations.map((ev: any) => {
        const fromAgent = MOCK_AGENTS.find(a => a.id === ev.from);
        const toAgent = MOCK_AGENTS.find(a => a.id === ev.to);
        return (
          <div key={ev.id} className="relative pl-4 border-l-2 border-zinc-800 hover:border-orange-500 transition-colors animate-in fade-in slide-in-from-right-4 duration-500 group">
            <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-zinc-700 group-hover:bg-orange-500 transition-colors" />
            <div className="flex items-center gap-2 mb-2 text-xs font-mono uppercase tracking-wide text-zinc-500">
              <span className="font-bold text-zinc-300 bg-zinc-800 px-1 rounded">{fromAgent?.name}</span>
              <span>► target ►</span>
              <span className="font-bold text-zinc-400 bg-zinc-800 px-1 rounded">{toAgent?.name}</span>
            </div>
            <div className="bg-zinc-800/80 p-3 rounded-md shadow-sm border border-zinc-700/50 text-sm text-zinc-300 font-serif leading-relaxed italic group-hover:border-orange-500/30 transition-colors">
              "{ev.comment}"
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Tactical Sidebar
const TacticalSidebar = ({ isOpen, history }: any) => {
  return (
    <div className={`hidden md:flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] overflow-hidden relative z-40 ${isOpen ? 'w-64 opacity-100' : 'w-0 opacity-0'}`}>
       <div className="h-14 flex items-center px-4 border-b border-zinc-800 bg-zinc-900/20">
          <LayoutGrid className="w-5 h-5 text-zinc-500 mr-2" />
          <span className="text-xs font-bold text-zinc-300 tracking-widest uppercase">Mission Logs</span>
       </div>
       <div className="p-4">
          <button 
            onClick={() => window.location.reload()}
            className="w-full group relative flex items-center justify-center gap-2 py-3 px-4 bg-teal-900/10 border border-teal-500/50 hover:bg-teal-500/20 text-teal-400 text-xs font-bold uppercase tracking-wider transition-all"
            style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}
          >
             <Plus className="w-4 h-4" />
             <span>Initiate Session</span>
             <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none group-hover:opacity-20"></div>
          </button>
       </div>
       <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 no-scrollbar">
          <div className="text-[10px] text-zinc-600 font-mono mb-2 mt-2 uppercase">Recent Archives</div>
          {history.map((item: any) => (
             <div key={item.id} className="group relative p-3 bg-zinc-900/30 border-l-2 border-zinc-800 hover:border-orange-500 hover:bg-zinc-800/50 transition-all cursor-pointer">
                <div className="flex justify-between items-start mb-1">
                   <span className="text-[10px] font-mono text-zinc-500 group-hover:text-orange-400">ID #{item.id}</span>
                   <span className="text-[9px] text-zinc-600 border border-zinc-700 px-1 rounded">{item.status}</span>
                </div>
                <div className="text-sm font-medium text-zinc-400 group-hover:text-zinc-200 truncate font-sans">
                   {item.title}
                </div>
             </div>
          ))}
       </div>
       <div className="p-4 border-t border-zinc-800 bg-zinc-900/40">
          <div className="flex items-center gap-3 mb-3">
             <div className="w-10 h-10 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                <Fingerprint className="w-6 h-6 text-zinc-500" />
             </div>
             <div>
                <div className="text-xs font-bold text-zinc-300">ADMIN_01</div>
                <div className="text-[10px] text-zinc-600 font-mono">SECURE_LEVEL_5</div>
             </div>
          </div>
       </div>
    </div>
  );
};

const UnifiedDetailPanel = ({ isOpen, onClose, stage, thinkingSteps, evaluations, synthesisSteps }: any) => {
  let title = "Thinking Process";
  let icon = <MoreHorizontal className="w-4 h-4" />;
  let content = null;

  if (stage === 'stage2') {
    title = "Evaluation Details";
    icon = <MessageSquare className="w-4 h-4" />;
    content = <EvaluationList evaluations={evaluations} />;
  } else if (stage === 'stage3') {
    title = "Synthesis Logic";
    icon = <Scale className="w-4 h-4" />;
    content = <ThinkingProcess steps={synthesisSteps} title="Chairperson Logs" />;
  } else {
    title = "System Logs";
    icon = <Zap className="w-4 h-4" />;
    content = <ThinkingProcess steps={thinkingSteps} />;
  }

  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const panelBody = (
    <>
      <div className="flex items-center justify-between px-5 h-14 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur shrink-0">
        <div className="flex items-center gap-2 text-zinc-100">
          {icon}
          <h2 className="font-bold text-xs uppercase tracking-widest">{title}</h2>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-zinc-800 rounded-md text-zinc-500 hover:text-zinc-300 transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-5 bg-zinc-900/50 scroll-smooth">
        {content}
      </div>
    </>
  );

  if (isMobile) {
    return (
      <>
        {isOpen && <div className="fixed inset-0 bg-black/60 z-40 transition-opacity backdrop-blur-sm" onClick={onClose} />}
        <div className={`fixed bottom-0 left-0 right-0 z-50 bg-zinc-900 border-t border-zinc-700 rounded-t-xl shadow-2xl transform transition-transform duration-300 ease-out h-[60vh] flex flex-col ${isOpen ? 'translate-y-0' : 'translate-y-full'}`}>
          <div className="w-full flex justify-center pt-2 pb-1" onClick={onClose}>
             <div className="w-12 h-1 bg-zinc-700 rounded-full" />
          </div>
          {panelBody}
        </div>
      </>
    );
  }

  return (
    <div className="h-full flex flex-col border-l border-zinc-800 bg-zinc-900/95 backdrop-blur shadow-xl w-full">
      {panelBody}
    </div>
  );
};

// --- MAIN APP ---

const App = () => {
  // Global State
  const [selectedAgents, setSelectedAgents] = useState<AgentId[]>(['kant', 'kojima', 'nietzsche']);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Engine Hook
  const engine = useParliamentEngine(selectedAgents);
  
  // UI Handlers
  const handleToggleAgent = (id: AgentId) => {
    if (selectedAgents.includes(id)) {
      setSelectedAgents(prev => prev.filter(x => x !== id));
    } else {
      setSelectedAgents(prev => [...prev, id]);
    }
  };

  const MOCK_HISTORY = [
    { id: '4092', title: 'The Trolley Problem', status: 'ARCHIVED' },
    { id: '4091', title: 'Digital Consciousness', status: 'ANALYZED' },
  ];

  // Auto-open panel on stage change (Desktop)
  useEffect(() => {
    if (engine.stage !== 'idle' && window.innerWidth >= 768) {
        setIsPanelOpen(true);
    }
  }, [engine.stage]);

  return (
    <div className="flex flex-col h-screen w-full bg-zinc-950 overflow-hidden font-sans text-gray-900">
      
      {/* --- Middle: Sidebar | Content | Panel --- */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Sidebar */}
        <TacticalSidebar isOpen={isSidebarOpen} history={MOCK_HISTORY} />
        
        {/* Main Content Wrapper */}
        <div className={`flex flex-col h-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] w-full relative`}>
          
          {engine.stage === 'idle' ? (
             <WelcomeScreen 
                onStart={engine.startSession} 
                selectedAgents={selectedAgents} 
                onToggleAgent={handleToggleAgent}
             />
          ) : (
             <StageContentArea 
                activeTab={engine.activeTab}
                onTabSelect={engine.setActiveTab}
                consensusUnlocked={engine.consensusUnlocked}
                hasViewedConsensus={engine.hasViewedConsensus}
                selectedAgents={selectedAgents}
             />
          )}

          {/* Floating Action Buttons */}
          {engine.stage !== 'idle' && (
             <div className="absolute bottom-6 left-6 z-20 flex gap-2">
               <button 
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="hidden md:flex items-center justify-center w-14 h-14 bg-zinc-900 border-2 border-zinc-700 text-zinc-400 rounded-none transform -skew-x-12 shadow hover:bg-zinc-800 transition-colors"
               >
                  <div className="transform skew-x-12">{isSidebarOpen ? <PanelLeftClose className="w-5 h-5"/> : <PanelLeftOpen className="w-5 h-5"/>}</div>
               </button>
               {!isPanelOpen && (
                <button 
                  onClick={() => setIsPanelOpen(true)}
                  className="flex items-center justify-center w-14 h-14 bg-zinc-900 border-2 border-zinc-700 text-zinc-400 rounded-none transform -skew-x-12 shadow hover:bg-zinc-800 transition-colors"
                >
                  <div className="transform skew-x-12"><PanelRightOpen className="w-5 h-5" /></div>
                </button>
              )}
              {engine.consensusUnlocked && (
                  <button 
                    onClick={engine.reset}
                    className="flex items-center justify-center w-14 h-14 bg-zinc-900 border-2 border-zinc-700 text-zinc-400 rounded-none transform -skew-x-12 shadow hover:bg-zinc-800 transition-colors"
                    title="Reset Simulation"
                  >
                     <div className="transform skew-x-12"><RotateCcw className="w-5 h-5" /></div>
                  </button>
              )}
             </div>
          )}

        </div>

        {/* Right Panel */}
        {engine.stage !== 'idle' && (
          <>
            <div className={`hidden md:block h-full border-l border-zinc-800 transition-all duration-500 overflow-hidden ${isPanelOpen ? 'w-[400px] opacity-100' : 'w-0 opacity-0'}`}>
              <UnifiedDetailPanel 
                isOpen={isPanelOpen} 
                onClose={() => setIsPanelOpen(false)} 
                stage={engine.stage}
                thinkingSteps={engine.thinkingSteps}
                evaluations={engine.evaluations}
                synthesisSteps={engine.synthesisSteps}
              />
            </div>
            <div className="md:hidden">
              <UnifiedDetailPanel 
                isOpen={isPanelOpen} 
                onClose={() => setIsPanelOpen(false)} 
                stage={engine.stage}
                thinkingSteps={engine.thinkingSteps}
                evaluations={engine.evaluations}
                synthesisSteps={engine.synthesisSteps}
              />
            </div>
          </>
        )}
      </div>

      {/* --- Footer: TACTICAL HUD --- */}
      <TacticalHUD 
        stage={engine.stage}
        agentProgress={engine.agentProgress}
        evaluations={engine.evaluations}
        rankings={[]} 
        consensusUnlocked={engine.consensusUnlocked}
        onConsensusClick={engine.viewConsensus}
        selectedAgents={selectedAgents}
        hasViewedConsensus={engine.hasViewedConsensus}
      />
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);

export default App;
