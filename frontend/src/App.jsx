import { useState, useEffect } from "react";
import { useNavigate, useParams, Routes, Route } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Toaster } from "sonner";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import PartnerFooter from "./components/PartnerFooter";
import LanguageSwitcher from "./components/LanguageSwitcher";
import { api } from "./api";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

function AppContent() {
  const { t } = useTranslation();
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigate = useNavigate();
  const { conversationId } = useParams();

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when URL changes
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    } else {
      setCurrentConversation(null);
    }
  }, [conversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error("Failed to load conversation:", error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      // Navigate to new conversation URL
      navigate(`/c/${newConv.id}`);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  const handleSelectConversation = (id) => {
    // Navigate to conversation URL
    navigate(`/c/${id}`);
  };

  const handleSendMessage = async (content, councilorIds = null) => {
    if (!conversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: "user", content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: "assistant",
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(
        conversationId,
        content,
        (eventType, event) => {
          switch (eventType) {
            case "meta":
              // Store updated councilor info for this run
              setCurrentConversation((prev) => {
                return {
                  ...prev,
                  // We can store run-specific councilors here to help UI lookup
                  // Or just update the active_councilor_ids
                  resolved_councilors: event.resolved_councilors
                };
              });
              break;

            case "stage1_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage1 = true;
                lastMsg.stage1 = []; // Init empty for accumulating items
                return { ...prev, messages };
              });
              break;

            case "stage1_item":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (!lastMsg.stage1) lastMsg.stage1 = [];
                // Deduplicate by councilor_id to prevent duplicate keys
                const existingIds = new Set(lastMsg.stage1.map(r => r.councilor_id));
                if (!existingIds.has(event.data.councilor_id)) {
                  lastMsg.stage1.push(event.data);
                }
                return { ...prev, messages };
              });
              break;

            case "stage1_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage1 = event.data; // Replace with final authoritative list
                lastMsg.loading.stage1 = false;
                return { ...prev, messages };
              });
              break;

            case "stage2_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage2 = true;
                lastMsg.stage2 = []; // Init for items
                // Handle early metadata if present
                if (event.anon_map) {
                  lastMsg.metadata = { ...lastMsg.metadata, anon_to_councilor: event.anon_map };
                }
                if (event.skipped) {
                  lastMsg.skipped = true;
                  lastMsg.skipped_reason = event.skipped_reason;
                }
                return { ...prev, messages };
              });
              break;

            case "stage2_item":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (!lastMsg.stage2) lastMsg.stage2 = [];
                // Deduplicate by judge_councilor_id
                const existingJudgeIds = new Set(lastMsg.stage2.map(r => r.judge_councilor_id));
                if (!existingJudgeIds.has(event.data.judge_councilor_id)) {
                  lastMsg.stage2.push(event.data);
                }
                return { ...prev, messages };
              });
              break;

            case "stage2_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                // Event data is the full unified dict now (with reviews field)
                // BUT my ChatInterface/Stage2 expects an array of reviews.
                // stage2_result dict structure: { skipped, skipped_reason, reviews, anon_map, judge_failures }
                // So I should assign event.data.reviews to lastMsg.stage2

                if (event.data.skipped) {
                  lastMsg.stage2 = event.data.reviews || []; // Might be empty
                  lastMsg.skipped = true;
                  lastMsg.skipped_reason = event.data.skipped_reason;
                } else {
                  lastMsg.stage2 = event.data.reviews;
                }

                lastMsg.metadata = {
                  ...lastMsg.metadata,
                  ...event.metadata,
                  // If stage2_complete brings updated anon_map, ensure it's set
                  anon_to_councilor: event.data.anon_map
                };
                lastMsg.loading.stage2 = false;

                // Update conversation active_councilor_ids if provided
                if (councilorIds) {
                  // logic to update conversation state if we want optimistic update
                  // but re-fetch on complete handles it usually.
                }
                return { ...prev, messages };
              });
              break;

            case "stage3_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage3 = true;
                return { ...prev, messages };
              });
              break;

            case "stage3_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage3 = event.data;
                lastMsg.loading.stage3 = false;
                return { ...prev, messages };
              });
              break;

            case "title_complete":
              // Reload conversations to get updated title
              loadConversations();
              break;

            case "complete":
              // Stream complete, reload conversations list
              loadConversations();
              setIsLoading(false);
              break;

            case "error":
              console.error("Stream error:", event.message);
              setIsLoading(false);
              break;

            default:
              console.log("Unknown event type:", eventType);
          }
        },
        councilorIds
      );
    } catch (error) {
      console.error("Failed to send message:", error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  const handleBulkDeleteConversations = async (ids) => {
    try {
      const result = await api.bulkDeleteConversations(ids);
      const { deletedIds, failed } = result;

      // Update state first
      if (deletedIds && deletedIds.length > 0) {
        setConversations((prev) => prev.filter(c => !deletedIds.includes(c.id)));

        // Check if current conversation is deleted
        if (conversationId && deletedIds.includes(conversationId)) {
          navigate("/");
          setCurrentConversation(null);
        }
      }

      return result; // return to sidebar for its internal logic
    } catch (error) {
      console.error("Failed to bulk delete:", error);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);

      // Remove from list
      setConversations((prev) => prev.filter((c) => c.id !== id));

      // If current was deleted, navigate away
      if (conversationId === id) {
        navigate("/");
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden md:block md:w-80 md:flex-shrink-0">
        <Sidebar
          conversations={conversations}
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onBulkDeleteConversations={handleBulkDeleteConversations}
        />
      </div>

      {/* Mobile Menu Sheet */}
      <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
        <SheetContent side="left" className="w-[320px] p-0">
          <Sidebar
            conversations={conversations}
            currentConversationId={conversationId}
            onSelectConversation={(id) => {
              handleSelectConversation(id);
              setIsMobileMenuOpen(false);
            }}
            onNewConversation={() => {
              handleNewConversation();
              setIsMobileMenuOpen(false);
            }}
            onDeleteConversation={handleDeleteConversation}
            onBulkDeleteConversations={handleBulkDeleteConversations}
          />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden pb-14">
        {/* Mobile Menu Button */}
        <div className="flex items-center justify-between gap-3 border-b bg-card p-4 md:hidden shadow-sm">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <h1 className="text-xl font-bold">{t('appTitle')}</h1>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <a
              href="https://github.com/wquguru/llm-council-zenmux"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg p-2 text-muted-foreground transition-all hover:bg-muted hover:text-foreground hover:scale-110"
              title="View on GitHub"
            >
              <svg height="20" width="20" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
              </svg>
            </a>
          </div>
        </div>

        {/* Desktop Header */}
        <div className="hidden items-center justify-between border-b bg-card px-6 py-4 md:flex shadow-sm">
          <h1 className="text-2xl font-bold">{t('appTitle')}</h1>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <a
              href="https://github.com/wquguru/llm-council-zenmux"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg p-2 text-muted-foreground transition-all hover:bg-muted hover:text-foreground hover:scale-110"
              title="View on GitHub"
            >
              <svg height="24" width="24" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
              </svg>
            </a>
          </div>
        </div>

        {/* Info banners - shown on all screen sizes */}
        <div className="flex items-center justify-center gap-2 border-b bg-primary/5 px-4 py-2.5 text-xs md:px-6 md:py-3 md:text-sm text-foreground/80 border-primary/10">
          <span>💡</span>
          <span className="line-clamp-1 md:line-clamp-none">
            {t('tagline')}
          </span>
        </div>
        <div className="flex items-center justify-center gap-2 border-b bg-warning/10 px-4 py-2.5 text-xs font-semibold text-warning md:px-6 md:py-3 md:text-sm border-warning/20">
          <span>⚠️</span>
          <span className="line-clamp-1 md:line-clamp-none">
            {t('privacyWarning')}
          </span>
        </div>

        <ChatInterface
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onNewConversation={handleNewConversation}
          conversationId={conversationId}
        />
      </div>

      {/* Fixed Footer */}
      <PartnerFooter />
    </div>
  );
}

function App() {
  return (
    <>
      <Toaster position="top-center" richColors closeButton />
      <Routes>
        <Route path="/" element={<AppContent />} />
        <Route path="/c/:conversationId" element={<AppContent />} />
      </Routes>
    </>
  );
}

export default App;
