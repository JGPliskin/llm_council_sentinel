import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ModelAvatar } from "./CouncilAvatars";

const resolveItem = (lookup, id) => {
  return lookup?.[id] || { model: id, name: id };
}

export default function Stage1({ responses, activeModel, onSelectModel, councilorLookup = {}, metadata }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("0");

  // Determine source of truth for items list
  // Preferred: metadata.resolved_councilors (stable order) > responses (streaming)
  const resolvedCouncilors = metadata?.resolved_councilors || [];

  // Create a unified list of items to render
  // If we have resolved_councilors, use that order and lookup/merge response
  // If not (legacy/fallback), just use responses
  const renderItems = resolvedCouncilors.length > 0
    ? resolvedCouncilors.map(rc => {
      const resp = responses?.find(r =>
        (r.councilor_id && r.councilor_id === rc.id) ||
        (r.model && r.model === rc.model)
      );
      return {
        ...rc, // Base info from metadata
        ...resp, // Merge response info (answer, status)
        // Ensure essential IDs exist
        councilor_id: rc.id,
        model: rc.model,
        status: resp?.status || "thinking"
      };
    })
    : responses; // Fallback to raw responses if no meta

  // Update active tab if parent selection changes (hint only), but don't lock it
  useEffect(() => {
    if (activeModel && renderItems.length > 0) {
      const index = renderItems.findIndex(r => r.model === activeModel || r.councilor_id === activeModel);
      if (index !== -1) {
        setActiveTab(String(index));
      }
    }
  }, [activeModel, renderItems?.length]); // Only sync when activeModel specifically changes or items init

  if (!renderItems || renderItems.length === 0) {
    return null;
  }

  // Calculate Progress
  const totalCount = renderItems.length;
  const doneCount = renderItems.filter(r => r.status === 'ok' || r.status === 'completed' || r.status === 'failed').length;
  const progressPercent = totalCount > 0 ? (doneCount / totalCount) * 100 : 0;

  const handleTabChange = (value) => {
    setActiveTab(value);
    const index = parseInt(value, 10);
    // Optional: Notify parent if needed, but we don't strictly enforce parent state to avoid "locking"
    if (renderItems[index] && onSelectModel) {
      // onSelectModel(renderItems[index].model); // Uncomment to sync back to global if desired, but user complained about locking
    }
  };

  return (
    <Card className="mb-4 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold">
            {t('stage1Title')}
          </CardTitle>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mono">
            <span className={doneCount === totalCount ? "text-green-600 font-bold" : ""}>
              {doneCount}/{totalCount}
            </span>
          </div>
        </div>
        {/* Progress Bar */}
        <Progress value={progressPercent} className="h-1 mt-2" />
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-4 w-full flex-wrap justify-start h-auto gap-2 bg-muted/50 p-1">
            {renderItems.map((item, index) => {
              const isThinking = item.status === "thinking";
              const isFailed = item.status === "failed";
              const isOk = item.status === "ok" || item.status === "completed";

              return (
                <TabsTrigger
                  key={index}
                  value={String(index)}
                  className="flex items-center gap-2 text-xs md:text-sm font-semibold data-[state=active]:bg-card data-[state=active]:shadow-sm px-3 py-2"
                >
                  <div className="scale-75 origin-left relative">
                    <ModelAvatar
                      modelId={item.model}
                      item={item}
                      status={isOk ? "completed" : (isFailed ? "error" : "thinking")}
                    />
                    {isThinking && <div className="absolute inset-0 bg-background/50 animate-pulse rounded-full" />}
                  </div>
                  <span className={isThinking ? "opacity-70" : ""}>
                    {item.name || item.councilor_name || item.model}
                  </span>
                  {isThinking && <span className="animate-spin ml-1 text-muted-foreground">⟳</span>}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {renderItems.map((item, index) => {
            const isThinking = item.status === "thinking";
            return (
              <TabsContent key={index} value={String(index)}>
                <div className="mb-3 text-sm font-semibold text-muted-foreground mono flex items-center gap-2">
                  <div className="scale-75 origin-left">
                    <ModelAvatar modelId={item.model} item={item} />
                  </div>
                  <span>{item.name || item.councilor_name}</span>
                  <span className="opacity-50 text-xs">({item.model})</span>
                  {item.status === 'failed' && <span className="text-red-500 text-xs uppercase ml-2">[FAILED]</span>}
                </div>

                <div className="markdown-content rounded-lg border bg-card p-4 shadow-sm min-h-[100px]">
                  {isThinking ? (
                    <div className="flex items-center justify-center h-20 text-muted-foreground gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  ) : (
                    <ReactMarkdown>{item.answer_markdown || item.response || ""}</ReactMarkdown>
                  )}
                </div>

                {item.judge_card && (
                  <div className="mt-3 rounded-lg border bg-muted/40 p-3 shadow-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                      Judge Card
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="font-semibold">立场：{item.judge_card.stance}</div>
                      {item.judge_card.core_reasons?.length > 0 && (
                        <div>
                          <div className="font-semibold">核心理由</div>
                          <ul className="ml-4 list-disc">
                            {item.judge_card.core_reasons.map((r, i) => (
                              <li key={i}>{r}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </TabsContent>
            );
          })}
        </Tabs>
      </CardContent>
    </Card>
  );
}
