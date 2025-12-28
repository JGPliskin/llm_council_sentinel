import { useState, useEffect, useRef, useCallback } from 'react';
import { SimulationStage, AgentId, LogStep, PeerReview } from '../types';
import { STAGE1_STEPS, STAGE2_EVALUATIONS, STAGE3_STEPS } from '../mockData';

export const useParliamentEngine = (selectedAgents: AgentId[]) => {
  const [stage, setStage] = useState<SimulationStage>('idle');
  
  // Track progress for each agent individually (0-100)
  const [agentProgress, setAgentProgress] = useState<Partial<Record<AgentId, number>>>({});
  
  // Track global stage progress (0-100)
  const [stageProgress, setStageProgress] = useState(0);

  // Data Logs
  const [thinkingSteps, setThinkingSteps] = useState<LogStep[]>([]);
  const [evaluations, setEvaluations] = useState<PeerReview[]>([]);
  const [synthesisSteps, setSynthesisSteps] = useState<LogStep[]>([]);
  
  // View State
  const [activeTab, setActiveTabState] = useState<string>('kant');
  const [consensusUnlocked, setConsensusUnlocked] = useState(false);
  const [hasViewedConsensus, setHasViewedConsensus] = useState(false);

  // Custom setter for activeTab to track if user viewed consensus
  const setActiveTab = useCallback((tab: string) => {
    setActiveTabState(tab);
    if (tab === 'final') {
      setHasViewedConsensus(true);
    }
  }, []);

  // --- STAGE 1: PARALLEL GENERATION ---
  useEffect(() => {
    if (stage === 'stage1') {
      const activeIds = selectedAgents.length > 0 ? selectedAgents : (['kant'] as AgentId[]); // fallback
      
      // Reset
      const initialProgress = activeIds.reduce((acc, id) => ({ ...acc, [id]: 0 }), {} as Record<AgentId, number>);
      setAgentProgress(initialProgress);
      setThinkingSteps([]);

      // Create an interval for EACH agent to simulate parallel thinking
      const intervals = activeIds.map(id => {
        // Random speed for each agent
        const speed = Math.random() * 100 + 50; 
        
        return setInterval(() => {
          setAgentProgress(prev => {
            const current = prev[id] || 0;
            if (current >= 100) {
              return prev; // Already done
            }
            const next = Math.min(100, current + (Math.random() * 15));
            
            // Trigger a log if we crossed a threshold (simulated)
            if (next > 50 && current <= 50) {
               const step = STAGE1_STEPS.find(s => s.agentId === id);
               if (step) {
                 setThinkingSteps(prevSteps => {
                   if(prevSteps.some(s => s.id === step.id)) return prevSteps;
                   return [...prevSteps, step];
                 });
               }
            }
            return { ...prev, [id]: next };
          });
        }, speed);
      });

      return () => intervals.forEach(clearInterval);
    }
  }, [stage, selectedAgents]);

  // Check Stage 1 Completion
  useEffect(() => {
    if (stage === 'stage1' && selectedAgents.length > 0) {
      const allDone = selectedAgents.every(id => (agentProgress[id] || 0) >= 100);
      if (allDone) {
        // AUTO TRANSITION TO STAGE 2
        setTimeout(() => setStage('stage2'), 500);
      }
    }
  }, [agentProgress, stage, selectedAgents]);


  // --- STAGE 2: AUTO EVALUATION ---
  useEffect(() => {
    if (stage === 'stage2') {
      setStageProgress(0);
      setEvaluations([]);
      
      // Simple linear simulation for Stage 2 (Global Progress)
      let progress = 0;
      const interval = setInterval(() => {
        progress += 2;
        setStageProgress(Math.min(100, progress));
        
        // Inject evaluations at intervals
        if (progress === 20) setEvaluations(prev => [...prev, STAGE2_EVALUATIONS[0]]);
        if (progress === 40) setEvaluations(prev => [...prev, STAGE2_EVALUATIONS[1]]);
        if (progress === 60) setEvaluations(prev => [...prev, STAGE2_EVALUATIONS[2]]);
        if (progress === 80) setEvaluations(prev => [...prev, STAGE2_EVALUATIONS[3]]);

        if (progress >= 100) {
          clearInterval(interval);
          // AUTO TRANSITION TO STAGE 3 (Engine State only)
          setTimeout(() => {
             setStage('stage3');
          }, 800);
        }
      }, 50);

      return () => clearInterval(interval);
    }
  }, [stage]);


  // --- STAGE 3: SYNTHESIS (Background) ---
  useEffect(() => {
    if (stage === 'stage3') {
       // Reset for stage 3
       setStageProgress(0);
       
       let progress = 0;
       const interval = setInterval(() => {
         progress += 5;
         setStageProgress(Math.min(100, progress));
         
         if (progress === 20) setSynthesisSteps(prev => [...prev, STAGE3_STEPS[0]]);
         if (progress === 50) setSynthesisSteps(prev => [...prev, STAGE3_STEPS[1]]);
         if (progress === 80) setSynthesisSteps(prev => [...prev, STAGE3_STEPS[2]]);

         if (progress >= 100) {
           clearInterval(interval);
           setConsensusUnlocked(true); // Now the user can click
         }
       }, 100);
       
       return () => clearInterval(interval);
    }
  }, [stage]);


  const startSession = useCallback((prompt: string) => {
    setStage('stage1');
    setConsensusUnlocked(false);
    setHasViewedConsensus(false);
    // Default to first selected agent view
    if (selectedAgents.length > 0) setActiveTab(selectedAgents[0]);
  }, [selectedAgents, setActiveTab]);

  const viewConsensus = useCallback(() => {
    setActiveTab('final');
  }, [setActiveTab]);

  const reset = useCallback(() => {
    setStage('idle');
    setHasViewedConsensus(false);
    setAgentProgress({});
  }, []);

  return {
    stage,
    agentProgress,
    stageProgress,
    thinkingSteps,
    evaluations,
    synthesisSteps,
    activeTab,
    setActiveTab,
    consensusUnlocked,
    hasViewedConsensus,
    startSession,
    viewConsensus,
    reset
  };
};