import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, useNavigate, useParams } from "react-router-dom";
import { Toaster } from "sonner";
import { useTranslation } from "react-i18next";
import { PanelLeftClose, PanelLeftOpen, PanelRightOpen, RotateCcw } from 'lucide-react';

import { api } from "@/api";
import { useParliamentEngine } from "@/hooks/useParliamentEngine";
import Sidebar from "@/components/Sidebar";
import TacticalHUD from "@/components/TacticalHUD";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import StageContentArea from "@/components/StageContentArea";
import DetailPanel from "@/components/DetailPanel";
import { Background } from "@/components/ui/Background";

function AppContent() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { conversationId } = useParams();

  // === Global State ===
  const [conversations, setConversations] = useState([]);
  const [allCouncilors, setAllCouncilors] = useState([]);
  const [chairmanInfo, setChairmanInfo] = useState(null);
  const [selectedAgentIds, setSelectedAgentIds] = useState(['immanuel_kant', 'donald_trump', 'hideo_kojima']);
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => window.innerWidth >= 768);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [panelHeightTier, setPanelHeightTier] = useState(1); // 1, 2, 3, or 'full'
  const [isPanelFullscreen, setIsPanelFullscreen] = useState(false);

  // === Engine Hook ===
  const engine = useParliamentEngine();

  // === Loading Data ===
  useEffect(() => {
    // Force check for mobile on mount to ensure sidebar is closed
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
    loadConversations();
    loadCouncilors();
  }, []);

  useEffect(() => {
    if (conversationId) {
      // Prevent redundant reload if we just created this session locally
      if (engine.conversation?.id === conversationId && engine.stage !== 'idle') {
        return;
      }
      loadConversationAndStates(conversationId);
    } else {
      engine.reset();
    }
  }, [conversationId]);

  // Auto-open panel on stage change (Desktop only)
  useEffect(() => {
    if (engine.stage !== 'idle' && window.innerWidth >= 768) {
      setIsPanelOpen(true);
    } else if (engine.stage === 'idle') {
      setIsPanelOpen(false);
      setPanelHeightTier(1);
      setIsPanelFullscreen(false);
    }
  }, [engine.stage]);

  // Dynamic height calculation for Stage 2
  useEffect(() => {
    if (engine.stage === 'stage1') {
      setPanelHeightTier(1);
      setIsPanelFullscreen(false);
    } else if (engine.stage === 'stage3') {
      setPanelHeightTier(3);
      setIsPanelFullscreen(false);
    } else if (engine.stage === 'stage2' && !isPanelFullscreen) {
      // Debounce height changes for Stage 2
      const timer = setTimeout(() => {
        if (engine.stage2Skipped) {
          setPanelHeightTier(1);
          return;
        }

        // Count visible judge cards
        const visibleCount = countVisibleJudgeCards(engine.stage2ThinkingByJudge, engine.activeTab);
        const newTier = Math.min(Math.max(visibleCount, 1), 3);

        // Only increase, never decrease (avoid jitter)
        setPanelHeightTier(prev => Math.max(prev, newTier));
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [engine.stage, engine.stage2ThinkingByJudge, engine.activeTab, engine.stage2Skipped, isPanelFullscreen]);

  // Helper function to count visible judge cards
  const countVisibleJudgeCards = (thinkingByJudge, targetId) => {
    if (!thinkingByJudge) return 0;

    return Object.values(thinkingByJudge).filter(judgeData => {
      const targetSteps = judgeData.stepsByTarget?.[targetId] || [];
      return targetSteps.length > 0 || judgeData.status === 'thinking';
    }).length;
  };

  // === API handlers ===
  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  const loadCouncilors = async () => {
    try {
      const response = await api.getCouncilors();
      // API returns object with .councilors array, or directly array in some mocks (but backend returns object)
      // Safety check
      if (response && response.councilors && Array.isArray(response.councilors)) {
        setAllCouncilors(response.councilors);
        setChairmanInfo(response.chairman || null);
      } else if (Array.isArray(response)) {
        setAllCouncilors(response);
        setChairmanInfo(null);
      } else {
        setAllCouncilors([]);
        setChairmanInfo(null);
        console.warn("Unexpected councilors format", response);
      }
    } catch (error) {
      console.error("Failed to load councilors", error);
    }
  };

  const loadConversationAndStates = async (id) => {
    try {
      const conv = await api.getConversation(id);
      engine.loadSession(conv);
    } catch (error) {
      console.error("Failed to load conversation:", error);
    }
  };

  const handleSelectConversation = (id) => {
    navigate(`/c/${id}`);
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleNewConversation = () => {
    navigate("/");
    engine.reset();
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (conversationId === id) {
        navigate("/");
        engine.reset();
      }
    } catch (error) {
      console.error("Failed to delete", error);
    }
  };

  const handleStartSession = async (prompt) => {
    // Must have selected agents
    await engine.startSession(prompt, selectedAgentIds);
    // Wait for created conversation ID to update URL?
    // engine.conversation is set in startSession.
    // But startSession is async.
    // Actually, startSession sets conversation state.
    // We can observe engine.conversation and navigate if it's new.
  };

  // Observe conversation creation to update URL
  useEffect(() => {
    if (engine.conversation && engine.conversation.id && !conversationId) {
      navigate(`/c/${engine.conversation.id}`, { replace: true });
      loadConversations(); // Refresh list
    }
  }, [engine.conversation, conversationId, navigate]);

  // Mobile: Auto-open drawer when entering Stage 2
  useEffect(() => {
    if (engine.stage === 'stage2' && window.innerWidth < 768) {
      setIsPanelOpen(true);
    }
  }, [engine.stage]);

  const handleContentClick = () => {
    if (window.innerWidth < 768 && isPanelOpen) {
      setIsPanelOpen(false);
    }
  };

  const handleToggleAgent = (id) => {
    setSelectedAgentIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      return [...prev, id];
    });
  };

  // === Render ===
  return (
    <div className="flex flex-col h-screen w-full overflow-hidden text-hud-text" style={{ backgroundColor: 'var(--hud-bg)' }}>
      {/* HUD Background Textures */}
      <Background />

      <div className="flex-1 flex overflow-hidden relative z-10">

        {/* Mobile Overlay */}
        {isSidebarOpen && (
          <div
            className="absolute inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm transition-opacity"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          isOpen={isSidebarOpen}
        />

        {/* Main Content */}
        <div className="flex flex-col h-full flex-1 min-w-0 relative transition-all duration-500">
          {engine.stage === 'idle' ? (
            <div className="flex-1 overflow-hidden relative" onClick={handleContentClick}>
              <WelcomeScreen
                onStart={handleStartSession}
                councilors={allCouncilors}
                chairman={chairmanInfo}
                selectedIds={selectedAgentIds}
                onToggleId={handleToggleAgent}
                isSidebarOpen={isSidebarOpen}
                onToggleSidebar={() => {
                  const newState = !isSidebarOpen;
                  setIsSidebarOpen(newState);
                  if (newState && window.innerWidth < 768) setIsPanelOpen(false);
                }}
                isDetailPanelOpen={isPanelOpen}
                onToggleDetailPanel={() => {
                  const newState = !isPanelOpen;
                  setIsPanelOpen(newState);
                  if (newState && window.innerWidth < 768) setIsSidebarOpen(false);
                }}
                onResetSession={() => { if (confirm('Reset Session?')) engine.reset(); }}
              />
            </div>
          ) : (
            <div className="flex-1 min-h-0 relative flex flex-col">
              <StageContentArea
                chairmanId={engine.chairmanId}
                activeTab={engine.activeTab}
                onTabSelect={engine.setActiveTab}
                stage={engine.stage}
                consensusUnlocked={engine.consensusUnlocked}
                hasViewedConsensus={engine.hasViewedConsensus}
                onManualConsensusView={engine.viewConsensus}
                resolvedCouncilors={engine.resolvedCouncilors}
                stage1Results={engine.stage1Results}
                stage3Result={engine.stage3Result}
                stage3AnswerStream={engine.stage3AnswerStream}
                thinkingByCouncilor={engine.thinkingByCouncilor}
                thinkingExpanded={engine.thinkingExpanded}
                onToggleThinking={engine.toggleThinkingExpanded}
                stage1AnswerStream={engine.stage1AnswerStream}
                onBackgroundClick={handleContentClick}
                chairmanInfo={chairmanInfo}
              />
            </div>
          )}

          {/* Footer HUD */}
          {engine.stage !== 'idle' && (
            <TacticalHUD
              stage={engine.stage}
              agentProgress={engine.agentProgress}
              aggregateRankings={engine.aggregateRankings}
              resolvedCouncilors={engine.resolvedCouncilors}
              consensusUnlocked={engine.consensusUnlocked}
              stage3Complete={engine.stage3Complete}
              hasViewedConsensus={engine.hasViewedConsensus}
              onConsensusClick={engine.viewConsensus}
              stage2Skipped={engine.stage2Skipped}
              activeTab={engine.activeTab}
              onTabSelect={engine.setActiveTab} // Interactive Switching
              // IDLE props
              selectedAgentIds={selectedAgentIds}
              allCouncilors={allCouncilors}
              // Controls
              isSidebarOpen={isSidebarOpen}
              onToggleSidebar={() => {
                const newState = !isSidebarOpen;
                setIsSidebarOpen(newState);
                if (newState && window.innerWidth < 768) setIsPanelOpen(false);
              }}
              isDetailPanelOpen={isPanelOpen}
              onToggleDetailPanel={() => {
                const newState = !isPanelOpen;
                setIsPanelOpen(newState);
                if (newState && window.innerWidth < 768) setIsSidebarOpen(false);
              }}
              onResetSession={() => { if (confirm('Reset Session?')) engine.reset(); }}
            />
          )}
        </div>

        {/* Right Detail Panel - Outside MainContent, Fixed position */}
        {engine.stage !== 'idle' && (
          <div
            className={`
              fixed bottom-0 inset-x-0 z-50 rounded-t-2xl border-t border-zinc-800
              md:relative md:inset-auto md:rounded-none md:border-t-0 md:border-l md:block
              transition-all duration-500
              h-[var(--panel-height)] md:h-auto
              ${isPanelOpen
                ? 'translate-y-0 opacity-100 md:translate-y-0 md:translate-x-0 md:w-[400px]'
                : 'translate-y-full opacity-0 md:translate-x-full md:w-0 md:opacity-0 md:overflow-hidden'}
            `}
            style={{
              '--panel-height': isPanelFullscreen ? '90vh' : `${[30, 45, 60][panelHeightTier - 1] || 60}vh`,
              transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            <DetailPanel
              stage={engine.stage}
              activeTab={engine.activeTab}
              evaluationComments={engine.evaluationComments}
              synthesisSteps={engine.synthesisSteps}
              stage2ThinkingByJudge={engine.stage2ThinkingByJudge}
              stage2AnonMap={engine.stage2AnonMap}
              aggregateRankings={engine.aggregateRankings}
              stage2Skipped={engine.stage2Skipped}
              onClose={() => setIsPanelOpen(false)}
              userPrompt={engine.conversation?.messages?.[0]?.content}
              isPanelFullscreen={isPanelFullscreen}
              onToggleFullscreen={() => setIsPanelFullscreen(!isPanelFullscreen)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <>
      <Toaster position="top-center" richColors theme="dark" closeButton />
      <Routes>
        <Route path="/" element={<AppContent />} />
        <Route path="/c/:conversationId" element={<AppContent />} />
      </Routes>
    </>
  );
}

export default App;
