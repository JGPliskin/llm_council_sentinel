import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import Stage1 from "./Stage1";
import Stage2 from "./Stage2";
import Stage3 from "./Stage3";
import CouncilAvatars from "./CouncilAvatars";
import ShareButton from "./ShareButton";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { MAX_MESSAGE_LENGTH, api } from "@/api";

// Default model configuration (mirrors backend ids for graceful fallback)
const DEFAULT_COUNCILORS = [
  { id: "immanuel_kant", name: "康德", model: "openai/gpt-oss-20b:free" },
  { id: "donald_trump", name: "特朗普", model: "openai/gpt-oss-20b:free" },
  { id: "hideo_kojima", name: "小岛秀夫", model: "openai/gpt-oss-20b:free" },
];
const DEFAULT_CHAIRMAN = { id: "chairman", name: "共识主席", model: "amazon/nova-2-lite-v1:free" };

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  onNewConversation,
  conversationId,
}) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const [activeModel, setActiveModel] = useState(null);
  const [selectedCouncilorIds, setSelectedCouncilorIds] = useState(new Set());

  // Model state
  const [councilors, setCouncilors] = useState(DEFAULT_COUNCILORS);
  const [chairman, setChairman] = useState(DEFAULT_CHAIRMAN);

  const messagesEndRef = useRef(null);
  const scrollAreaRef = useRef(null);
  const stage1Ref = useRef(null);
  const stage2Ref = useRef(null);
  const stage3Ref = useRef(null);
  const textareaRef = useRef(null);
  const formRef = useRef(null);

  // Fetch model configuration from backend
  useEffect(() => {
    const fetchModels = async () => {
      try {
        // Refresh only if on home page (new conversation)
        // If viewing an existing conversation, use cached values
        const shouldRefresh = !conversationId;
        const modelConfig = await api.getCouncilors(shouldRefresh);

        if (modelConfig.councilors && modelConfig.councilors.length > 0) {
          setCouncilors(modelConfig.councilors);

          if (conversationId && conversation && conversation.active_councilor_ids) {
            // Load persisted selection
            setSelectedCouncilorIds(new Set(conversation.active_councilor_ids));
          } else if (!conversationId) {
            // New conversation: default to active AND strict healthy
            const defaultIds = (modelConfig.councilors || [])
              .filter(c => c.active !== false && c.healthy === true)
              .map(c => c.id);
            setSelectedCouncilorIds(new Set(defaultIds));
          }
        }
        if (modelConfig.chairman) {
          setChairman(modelConfig.chairman);
        }
      } catch (error) {
        console.error("Failed to fetch model configuration:", error);
      }
    };

    fetchModels();
  }, [conversationId]); // Re-run when conversationId changes (e.g. back to home)

  // Character count validation
  const charCount = input.length;
  const isOverLimit = charCount > MAX_MESSAGE_LENGTH;

  // Get character counter color based on usage
  const getCounterColor = () => {
    const ratio = charCount / MAX_MESSAGE_LENGTH;
    if (ratio > 1) return "text-red-500 font-bold";
    if (ratio > 0.95) return "text-red-500";
    if (ratio > 0.8) return "text-orange-500";
    return "text-muted-foreground";
  };

  // Handle mobile keyboard appearing - scroll input into view
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const handleFocus = () => {
      // Delay to wait for keyboard animation
      setTimeout(() => {
        // Scroll the form into view
        formRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "end",
          inline: "nearest",
        });
      }, 300);
    };

    textarea.addEventListener("focus", handleFocus);
    return () => textarea.removeEventListener("focus", handleFocus);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    e.preventDefault();
    if (input.trim() && !isLoading && !isOverLimit) {
      // If we differ from default/active, send list. Otherwise null.
      // But user requirement says: "Client should... persist selection per conversation".
      // We'll send the list if it's set.
      const idsToSend = selectedCouncilorIds.size > 0 ? Array.from(selectedCouncilorIds) : null;

      onSendMessage(input, idsToSend);
      setInput("");
      // Blur textarea on mobile to hide keyboard after sending
      if (window.innerWidth < 768) {
        textareaRef.current?.blur();
      }
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSelectModel = (modelId) => {
    setActiveModel(modelId);
  };

  const handleToggleCouncilor = (id) => {
    setSelectedCouncilorIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        if (next.size > 1) next.delete(id); // Prevent deselecting last one?
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleChairmanClick = (modelId) => {
    setActiveModel(modelId);
    // 只滚动内部的 ScrollArea,不影响外层容器
    if (stage3Ref.current && scrollAreaRef.current) {
      // 获取 Radix ScrollArea 的实际滚动视口 (Viewport)
      const viewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]",
      );
      if (viewport) {
        // 计算 stage3 相对于 viewport 的位置
        const stage3Rect = stage3Ref.current.getBoundingClientRect();
        const viewportRect = viewport.getBoundingClientRect();
        const scrollOffset =
          stage3Rect.top - viewportRect.top + viewport.scrollTop;

        // 平滑滚动到目标位置
        viewport.scrollTo({
          top: scrollOffset - 20, // 减去 20px 留一点顶部间距
          behavior: "smooth",
        });
      }
    }
  };

  const scrollToStage2 = () => {
    // 只滚动内部的 ScrollArea,不影响外层容器
    if (stage2Ref.current && scrollAreaRef.current) {
      setTimeout(() => {
        // 获取 Radix ScrollArea 的实际滚动视口 (Viewport)
        const viewport = scrollAreaRef.current.querySelector(
          "[data-radix-scroll-area-viewport]",
        );
        if (viewport) {
          // 计算 stage2 相对于 viewport 的位置
          const stage2Rect = stage2Ref.current.getBoundingClientRect();
          const viewportRect = viewport.getBoundingClientRect();
          const scrollOffset =
            stage2Rect.top - viewportRect.top + viewport.scrollTop;

          // 平滑滚动到目标位置
          viewport.scrollTo({
            top: scrollOffset - 20, // 减去 20px 留一点顶部间距
            behavior: "smooth",
          });
        }
      }, 50);
    }
  };

  const consoleLog = (type, data) => {
    // Helper for debugging
    // console.log(`[Stream] ${type}`, data);
  }

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
        metadata: {},
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
          // consoleLog(eventType, event);

          switch (eventType) {
            case "meta":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (!lastMsg) return prev;

                // Update metadata
                lastMsg.metadata = {
                  ...lastMsg.metadata,
                  resolved_councilors: event.resolved_councilors,
                  resolved_councilor_ids: event.resolved_councilor_ids
                };

                // IMMEDIATELY Initialize Stage 1 with placeholders
                if (event.resolved_councilors && event.resolved_councilors.length > 0) {
                  lastMsg.stage1 = event.resolved_councilors.map(c => ({
                    councilor_id: c.id,
                    model: c.model,
                    councilor_name: c.name,
                    status: "thinking",
                    answer_markdown: "" // Placeholder content
                  }));
                  lastMsg.loading.stage1 = true;
                }
                return { ...prev, messages };
              });
              break;

            case "stage1_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage1 = true;
                if (!lastMsg.stage1) lastMsg.stage1 = []; // Should have been init by meta
                return { ...prev, messages };
              });
              break;

            case "stage1_item":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (!lastMsg.stage1) lastMsg.stage1 = [];

                const item = event.data;
                // Robust matching: id or model
                const index = lastMsg.stage1.findIndex(
                  r => (r.councilor_id && r.councilor_id === item.councilor_id) ||
                    (r.model && r.model === item.model)
                );

                if (index !== -1) {
                  // Merge into existing placeholder/item
                  const existing = lastMsg.stage1[index];
                  lastMsg.stage1[index] = {
                    ...existing,
                    ...item,
                    status: item.status || "thinking"
                  };
                } else {
                  // Fallback: append if not found (shouldn't happen if meta synced)
                  lastMsg.stage1.push(item);
                }
                return { ...prev, messages };
              });
              break;

            case "stage1_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                // Use backend final list but try to preserve our ephemeral state if needed? 
                // Usually backend list is authoritative and sorted.
                lastMsg.stage1 = event.data;
                lastMsg.loading.stage1 = false;
                return { ...prev, messages };
              });
              break;

            case "stage2_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage2 = true;

                // Initialize Stage 2 placeholders
                // Judges usually same as resolved_councilors unless overridden
                const judges = lastMsg.metadata?.resolved_councilors || [];

                // If anon_map provided, merge it
                if (event.anon_map) {
                  lastMsg.metadata = { ...lastMsg.metadata, anon_to_councilor: event.anon_map };
                }

                // Init items with Thinking state
                lastMsg.stage2 = judges.map(c => ({
                  judge_councilor_id: c.id,
                  model: c.model,
                  councilor_name: c.name,
                  status: "thinking",
                  ranking: [],
                  scores: {}
                }));

                if (event.skipped) {
                  lastMsg.skipped = true;
                  lastMsg.skipped_reason = event.skipped_reason;
                  lastMsg.loading.stage2 = false;
                }
                return { ...prev, messages };
              });
              break;

            case "stage2_item":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (!lastMsg.stage2) lastMsg.stage2 = [];

                const item = event.data;
                // Stage 2 item key: judge_councilor_id
                const index = lastMsg.stage2.findIndex(
                  r => (r.judge_councilor_id && r.judge_councilor_id === item.judge_councilor_id) ||
                    (r.model && r.model === item.model) ||
                    // Legacy fallback if item only has councilor_id
                    (item.councilor_id && r.judge_councilor_id === item.councilor_id)
                );

                if (index !== -1) {
                  const existing = lastMsg.stage2[index];
                  lastMsg.stage2[index] = {
                    ...existing,
                    ...item,
                    status: "completed" // Got data -> completed
                  };
                } else {
                  lastMsg.stage2.push(item);
                }
                return { ...prev, messages };
              });
              break;

            case "stage2_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];

                if (event.data.skipped) {
                  // if skipped, just use what we have or empty
                  lastMsg.stage2 = event.data.reviews || [];
                  lastMsg.skipped = true;
                } else {
                  lastMsg.stage2 = event.data.reviews;
                }

                lastMsg.metadata = {
                  ...lastMsg.metadata,
                  ...event.metadata,
                  anon_to_councilor: event.data.anon_map || lastMsg.metadata.anon_to_councilor
                };
                lastMsg.loading.stage2 = false;

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

  const councilorLookup = {};
  // Merge global councilors with resolved ones from current conversation run
  // Priority: resolved_councilors > global councilors (later entries override earlier)
  const lookupSource = [...councilors, ...(conversation?.resolved_councilors || [])];

  lookupSource.forEach((c) => {
    if (c.id) councilorLookup[c.id] = c;
    if (c.model) councilorLookup[c.model] = c;
  });

  // Determine effective models (use conversation-specific ones if active, otherwise defaults)
  let effectiveCouncilIds = conversation?.active_councilor_ids || conversation?.active_models;
  if (!Array.isArray(effectiveCouncilIds) || effectiveCouncilIds.length === 0) {
    // If no explicit list in conversation, use current active councilors (fallback)
    effectiveCouncilIds = councilors.filter(c => c.active !== false).map(c => c.id);
  }
  const effectiveCouncilModels = effectiveCouncilIds.map(
    (id) => councilorLookup[id]?.model || id,
  );

  let effectiveChairmanModel = conversation?.active_chairman;
  if (effectiveChairmanModel === chairman?.id) {
    effectiveChairmanModel = chairman?.model;
  }
  if (!effectiveChairmanModel || typeof effectiveChairmanModel !== 'string') {
    effectiveChairmanModel = chairman?.model;
  }

  const getModelStatuses = (msg, msgCouncilModels, msgChairmanModel) => {
    const statuses = {};

    // Use passed models or fallback to effective ones
    const council = msgCouncilModels || effectiveCouncilModels;
    const chairman = msgChairmanModel || effectiveChairmanModel;

    // Council members status
    council.forEach((model) => {
      if (msg.loading?.stage1) {
        statuses[model] = "thinking";
      } else if (msg.stage1) {
        statuses[model] = "completed";
      }
    });

    // Chairman status
    if (msg.loading?.stage3) {
      statuses[chairman] = "thinking";
    } else if (msg.stage3) {
      statuses[chairman] = "completed";
    }

    return statuses;
  };

  if (!conversation) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex flex-1 flex-col items-center justify-center text-center text-muted-foreground p-6">
          <h2 className="mb-3 text-2xl font-bold text-foreground md:text-3xl">
            {t("welcomeTitle")}
          </h2>
          <p className="text-base md:text-lg max-w-md mb-6">
            {t("welcomeSubtitle")}
          </p>
          <Button
            onClick={onNewConversation}
            size="lg"
            className="px-8 py-6 text-base font-semibold shadow-lg hover:shadow-xl transition-all"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="mr-2"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
            {t("newConversation")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {conversation.messages.length === 0 ? (
        // Empty state: centered input with model display
        <div className="flex flex-1 flex-col items-center justify-center px-4 md:px-6">
          <div className="w-full max-w-3xl mx-auto space-y-6 md:space-y-8">
            {/* Welcome message - smaller for empty state */}
            <div className="text-center space-y-1">
              <h2 className="text-lg md:text-xl font-bold text-foreground">
                {t("welcomeTitle")}
              </h2>
              <p className="text-xs md:text-sm text-muted-foreground max-w-lg mx-auto">
                {t("welcomeSubtitle")}
              </p>
            </div>

            {/* Centered input form */}
            <form onSubmit={handleSubmit} className="w-full">
              <div className="flex flex-col gap-2">
                <div className="flex items-end gap-3 md:gap-4">
                  <div className="relative flex-1">
                    <Textarea
                      ref={textareaRef}
                      className={cn(
                        "min-h-[120px] max-h-[300px] resize-y text-sm md:text-base shadow-md border-2 focus:border-primary pr-16",
                        isOverLimit && "border-red-500 focus:border-red-500",
                      )}
                      placeholder={t("placeholder")}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      disabled={isLoading}
                      rows={5}
                    />
                    {/* Character counter */}
                    <div
                      className={cn(
                        "absolute bottom-2 right-2 text-xs",
                        getCounterColor(),
                      )}
                    >
                      {charCount}/{MAX_MESSAGE_LENGTH}
                    </div>
                  </div>
                  <Button
                    type="submit"
                    disabled={!input.trim() || isLoading || isOverLimit}
                    className="h-auto px-6 py-3 md:px-8 md:py-4 font-semibold shadow-md hover:shadow-lg transition-all"
                  >
                    {t("send")}
                  </Button>
                </div>
              </div>
            </form>

            {/* Council models display with Selection */}
            <div className="pt-4 md:pt-6">
              <div className="mb-2 text-center text-xs text-muted-foreground">
                {t("selectCouncilors") || "Select Councilors"}
              </div>
              <CouncilAvatars
                councilors={councilors} // Pass full councilor objects
                chairmanModel={effectiveChairmanModel}
                activeModel={null} // No "active" for viewing
                modelStatuses={{}}

                // Selection Props
                selectable={true}
                selectedIds={selectedCouncilorIds}
                onToggleId={handleToggleCouncilor}
              />
            </div>
          </div>
        </div >
      ) : (
        // Messages view: scrollable content with fixed input at bottom
        <>
          <ScrollArea ref={scrollAreaRef} className="flex-1">
            <div
              className={cn(
                "p-3 md:p-6",
                // Add bottom padding only if input form is visible (no stage3 completed yet)
                !conversation.messages.some(
                  (msg) => msg.role === "assistant" && msg.stage3,
                )
                  ? "pb-36 md:pb-44"
                  : "pb-20 md:pb-24", // Increased to avoid fixed footer
              )}
            >
              {conversation.messages.map((msg, index) => (
                <div key={index} className="mb-6 md:mb-8">
                  {msg.role === "user" ? (
                    <div className="mb-4">
                      <div className="mb-2 text-xs font-bold uppercase tracking-wider text-muted-foreground mono">
                        {t("you")}
                      </div>
                      <Card className="max-w-full border-primary/30 bg-primary/5 p-4 md:max-w-[80%] shadow-sm hover:shadow-md transition-shadow">
                        <div className="markdown-content text-sm md:text-base">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      </Card>
                    </div>
                  ) : (
                    <div className="mb-4">
                      <div className="mb-3 flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground mono">
                          {t("llmCouncil")}
                        </span>
                        {msg.stage3 && (
                          <ShareButton
                            conversationId={conversationId}
                            conversationTitle={conversation?.title}
                          />
                        )}
                      </div>

                      {/* Council Avatars */}
                      {(() => {
                        const messageCouncilors = msg.stage1 && msg.stage1.length > 0
                          ? msg.stage1.map(r => {
                            const known = councilorLookup[r.councilor_id] || councilorLookup[r.model];
                            return known || { id: r.councilor_id || r.model, name: r.councilor_name, model: r.model };
                          })
                          : effectiveCouncilIds.map(id => councilorLookup[id] || { id, name: councilorLookup[id]?.name, model: councilorLookup[id]?.model || id });

                        const messageCouncilModels = messageCouncilors.map(c => c.model || c.id);

                        const messageChairmanModel = msg.stage3 && msg.stage3.model
                          ? msg.stage3.model
                          : effectiveChairmanModel;

                        const getModelStatuses = (msg, councilorModels, chairmanModel) => {
                          const statuses = {};
                          if (!msg) return statuses;

                          // Default all to idle
                          councilorModels.forEach(m => statuses[m] = "idle");
                          if (chairmanModel) statuses[chairmanModel] = "idle";

                          // Stage 1 Status
                          if (msg.loading?.stage1) {
                            councilorModels.forEach(m => statuses[m] = "thinking");
                          }

                          if (msg.stage1 && Array.isArray(msg.stage1)) {
                            msg.stage1.forEach(res => {
                              // Try to match by model ID first, then councilor ID
                              const key = res.model || res.councilor_id;
                              if (key) {
                                if (res.status === "ok") statuses[key] = "completed";
                                else if (res.status === "failed") statuses[key] = "error";
                              }
                            });
                          }

                          // Stage 3 Status
                          if (msg.loading?.stage3) {
                            if (chairmanModel) statuses[chairmanModel] = "thinking";
                          }
                          if (msg.stage3) {
                            if (chairmanModel) statuses[chairmanModel] = "completed";
                          }

                          return statuses;
                        };

                        return (msg.stage1 ||
                          msg.stage2 ||
                          msg.stage3 ||
                          msg.loading) && (
                            <CouncilAvatars
                              councilors={messageCouncilors}
                              chairmanModel={messageChairmanModel}
                              activeModel={activeModel}
                              onSelectModel={handleSelectModel}
                              onChairmanClick={handleChairmanClick}
                              modelStatuses={getModelStatuses(msg, messageCouncilModels, messageChairmanModel)}
                              isChairman={messageChairmanModel === activeModel}
                            />
                          );
                      })()}

                      {/* Stage 1 */}
                      <div ref={stage1Ref}>
                        {msg.loading?.stage1 && (
                          <Card className="mb-4 flex items-center gap-3 border-muted bg-muted/50 p-4 shadow-sm">
                            <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary"></div>
                            <span className="text-sm font-medium text-muted-foreground">
                              {t("loadingStage1")}
                            </span>
                          </Card>
                        )}
                        {msg.stage1 && (
                          <Stage1
                            responses={msg.stage1}
                            activeModel={activeModel}
                            onSelectModel={handleSelectModel}
                            councilorLookup={councilorLookup}
                            metadata={msg.metadata}
                          />
                        )}
                      </div>

                      {/* Stage 2 */}
                      <div ref={stage2Ref}>
                        {msg.loading?.stage2 && (
                          <Card className="mb-4 flex items-center gap-3 border-muted bg-muted/50 p-4 shadow-sm">
                            <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary"></div>
                            <span className="text-sm font-medium text-muted-foreground">
                              {t("loadingStage2")}
                            </span>
                          </Card>
                        )}
                        {msg.stage2 && (
                          <Stage2
                            rankings={msg.stage2?.reviews || msg.stage2}
                            labelToCouncilor={msg.metadata?.label_to_councilor || msg.metadata?.anon_to_councilor || msg.stage2?.anon_map}
                            aggregateRankings={msg.metadata?.aggregate_rankings}
                            activeModel={activeModel}
                            onSelectModel={handleSelectModel}
                            scrollToStage2={scrollToStage2}
                            councilorLookup={councilorLookup}
                            metadata={msg.metadata}
                          />
                        )}
                      </div>

                      {/* Stage 3 */}
                      <div ref={stage3Ref}>
                        {msg.loading?.stage3 && (
                          <Card className="mb-4 flex items-center gap-3 border-muted bg-muted/50 p-4 shadow-sm">
                            <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary"></div>
                            <span className="text-sm font-medium text-muted-foreground">
                              {t("loadingStage3")}
                            </span>
                          </Card>
                        )}
                        {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex items-center gap-3 p-4">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary"></div>
                  <span className="text-sm font-medium text-muted-foreground">
                    {t("consultingCouncil")}
                  </span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Only show input form if conversation is not complete (no stage3 response yet) */}
          {!conversation.messages.some(
            (msg) => msg.role === "assistant" && msg.stage3,
          ) && (
              <form
                ref={formRef}
                className="flex items-end gap-3 border-t bg-card p-4 md:gap-4 md:p-6 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]"
                onSubmit={handleSubmit}
              >
                <div className="relative flex-1">
                  <Textarea
                    ref={textareaRef}
                    className={cn(
                      "min-h-[60px] max-h-[200px] resize-y text-sm md:min-h-[80px] md:max-h-[300px] md:text-base shadow-sm pr-16",
                      isOverLimit && "border-red-500 focus:border-red-500",
                    )}
                    placeholder={t("placeholder")}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    rows={3}
                  />
                  {/* Character counter */}
                  <div
                    className={cn(
                      "absolute bottom-2 right-2 text-xs",
                      getCounterColor(),
                    )}
                  >
                    {charCount}/{MAX_MESSAGE_LENGTH}
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={!input.trim() || isLoading || isOverLimit}
                  className="h-auto px-6 py-3 md:px-8 md:py-4 font-semibold shadow-sm hover:shadow-md transition-all"
                >
                  {t("send")}
                </Button>
              </form>
            )}
        </>
      )
      }
    </div >
  );
}
