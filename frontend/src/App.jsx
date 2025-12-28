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

function AppContent() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { conversationId } = useParams();

  // === Global State ===
  const [conversations, setConversations] = useState([]);
  const [allCouncilors, setAllCouncilors] = useState([]);
  const [selectedAgentIds, setSelectedAgentIds] = useState(['immanuel_kant', 'donald_trump', 'hideo_kojima']);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // === Engine Hook ===
  const engine = useParliamentEngine();

  // === Loading Data ===
  useEffect(() => {
    loadConversations();
    loadCouncilors();
  }, []);

  useEffect(() => {
    if (conversationId) {
      loadConversationAndStates(conversationId);
    } else {
      engine.reset();
    }
  }, [conversationId]);

  // Auto-open panel on stage change (Desktop)
  useEffect(() => {
    if (engine.stage !== 'idle' && window.innerWidth >= 768) {
      setIsPanelOpen(true);
    } else if (engine.stage === 'idle') {
      setIsPanelOpen(false);
    }
  }, [engine.stage]);

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
      } else if (Array.isArray(response)) {
        setAllCouncilors(response);
      } else {
        setAllCouncilors([]);
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

  const handleNewConversation = () => {
    navigate("/");
    engine.reset();
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

  const handleToggleAgent = (id) => {
    setSelectedAgentIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      return [...prev, id];
    });
  };

  // === Render ===
  return (
    <div className="flex flex-col h-screen w-full bg-zinc-950 overflow-hidden font-sans text-zinc-100">
      <div className="flex-1 flex overflow-hidden relative">

        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConversationId={conversationId}
          onSelectConversation={(id) => navigate(`/c/${id}`)}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          isOpen={isSidebarOpen}
        />

        {/* Main Content */}
        <div className="flex flex-col h-full w-full relative transition-all duration-500">
          {engine.stage === 'idle' ? (
            <div className="flex-1 overflow-hidden relative">
              <WelcomeScreen
                onStart={handleStartSession}
                councilors={allCouncilors}
                selectedIds={selectedAgentIds}
                onToggleId={handleToggleAgent}
              />
            </div>
          ) : (
            <StageContentArea
              activeTab={engine.activeTab}
              onTabSelect={engine.setActiveTab}
              stage={engine.stage}
              consensusUnlocked={engine.consensusUnlocked}
              hasViewedConsensus={engine.hasViewedConsensus}
              onManualConsensusView={engine.viewConsensus}
              resolvedCouncilors={engine.resolvedCouncilors}
              stage1Results={engine.stage1Results}
              stage3Result={engine.stage3Result}
            />
          )}

          {/* Desktop Toggle Buttons */}
          <div className="absolute bottom-6 left-6 z-20 flex gap-2 pointer-events-auto">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="hidden md:flex items-center justify-center w-10 h-10 bg-zinc-900 border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-all shadow-lg backdrop-blur-sm"
              title="Toggle Sidebar"
            >
              {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
            </button>
            {!isPanelOpen && engine.stage !== 'idle' && (
              <button
                onClick={() => setIsPanelOpen(true)}
                className="hidden md:flex items-center justify-center w-10 h-10 bg-zinc-900 border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-all shadow-lg backdrop-blur-sm"
                title="Open Detail Panel"
              >
                <PanelRightOpen size={18} />
              </button>
            )}
          </div>
        </div>

        {/* Right Detail Panel */}
        {engine.stage !== 'idle' && (
          <div className={`
                    fixed inset-y-0 right-0 z-50 w-full md:relative md:z-0 md:w-[400px] border-l border-zinc-800 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]
                    ${isPanelOpen ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 md:w-0'}
                `}>
            <DetailPanel
              stage={engine.stage}
              activeTab={engine.activeTab}
              thinkingSteps={engine.thinkingSteps}
              evaluationComments={engine.evaluationComments}
              synthesisSteps={engine.synthesisSteps}
              onClose={() => setIsPanelOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Footer HUD */}
      <TacticalHUD
        stage={engine.stage}
        agentProgress={engine.agentProgress}
        aggregateRankings={engine.aggregateRankings}
        resolvedCouncilors={engine.resolvedCouncilors}
        consensusUnlocked={engine.consensusUnlocked}
        hasViewedConsensus={engine.hasViewedConsensus}
        onConsensusClick={engine.viewConsensus}
        // IDLE props
        selectedAgentIds={selectedAgentIds}
        allCouncilors={allCouncilors}
      />
    </div>
  );
}

function App() {
  return (
    <>
      <Toaster position="top-center" richColors theme="dark" closeButton />
      <Routes>
        <Route path="/*" element={<AppContent />} />
      </Routes>
    </>
  );
}

export default App;
