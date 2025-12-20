import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ModelAvatar } from "./CouncilAvatars";

const getCouncilorDisplay = (lookup, idOrModel) => {
  const item = lookup?.[idOrModel];
  if (item) {
    return item.name || item.model || idOrModel;
  }
  return idOrModel;
};

const resolveItem = (lookup, idOrModel) => {
  return lookup?.[idOrModel] || { model: idOrModel, name: idOrModel };
}

export default function Stage2({
  rankings,
  labelToCouncilor,
  aggregateRankings,
  activeModel,
  onSelectModel,
  scrollToStage2,
  councilorLookup = {},
  metadata
}) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("0");

  const resolvedCouncilors = metadata?.resolved_councilors || [];

  // Prefer metadata.resolved_councilors to drive order
  const renderItems = resolvedCouncilors.length > 0
    ? resolvedCouncilors.map(rc => {
      // Find matching ranking item
      const rank = rankings?.find(r =>
        (r.judge_councilor_id === rc.id) ||
        (r.councilor_id === rc.id) || // Legacy backcompat
        (r.model === rc.model)
      );
      return {
        ...rc,
        ...rank,
        judge_councilor_id: rc.id, // Enforce key
        model: rc.model,
        status: rank?.status || "thinking"
      };
    })
    : rankings; // Fallback

  useEffect(() => {
    if (activeModel && renderItems.length > 0) {
      const index = renderItems.findIndex(r => r.model === activeModel || r.judge_councilor_id === activeModel);
      if (index !== -1) {
        setActiveTab(String(index));
      }
    }
  }, [activeModel, renderItems?.length]);

  if (!renderItems || renderItems.length === 0) {
    return null;
  }

  // Progress
  const totalCount = renderItems.length;
  // A judge is "done" if status is completed/ok/failed, OR if they have ranking data
  const doneCount = renderItems.filter(r =>
    r.status === 'completed' ||
    r.status === 'ok' ||
    r.status === 'failed' ||
    (r.ranking && r.ranking.length > 0) // Implicit completion
  ).length;
  const progressPercent = totalCount > 0 ? (doneCount / totalCount) * 100 : 0;

  const handleTabChange = (value) => {
    setActiveTab(value);
    const index = parseInt(value, 10);
    if (renderItems[index] && onSelectModel) {
      // onSelectModel(renderItems[index].model); // Optional sync
      if (scrollToStage2) {
        scrollToStage2();
      }
    }
  };

  const resolveLabelName = (label) => {
    const councilorId = labelToCouncilor?.[label];
    return getCouncilorDisplay(councilorLookup, councilorId || label);
  };

  const resolveLabelItem = (label) => {
    const councilorId = labelToCouncilor?.[label];
    return resolveItem(councilorLookup, councilorId || label);
  }

  const resolveCouncilorName = (idOrModel) =>
    getCouncilorDisplay(councilorLookup, idOrModel);

  return (
    <Card className="mb-4 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-bold">
              {t('stage2Title')}
            </CardTitle>
            <CardDescription className="text-sm">
              {t('stage2Description')}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mono">
            <span className={doneCount === totalCount ? "text-green-600 font-bold" : ""}>
              {doneCount}/{totalCount}
            </span>
          </div>
        </div>
        <Progress value={progressPercent} className="h-1 mt-2" />
      </CardHeader>
      <CardContent>
        <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-muted-foreground mono">
          {t('rawEvaluations')}
        </h4>

        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-4 w-full flex-wrap justify-start h-auto gap-2 bg-muted/50 p-1">
            {renderItems.map((rank, index) => {
              const judgeId = rank.judge_councilor_id || rank.councilor_id;
              const judgeItem = resolveItem(councilorLookup, judgeId || rank.model);
              const isThinking = rank.status === "thinking";

              return (
                <TabsTrigger
                  key={index}
                  value={String(index)}
                  className="flex items-center gap-2 text-xs md:text-sm font-semibold data-[state=active]:bg-card data-[state=active]:shadow-sm px-3 py-2"
                >
                  <div className="scale-75 origin-left relative">
                    <ModelAvatar
                      modelId={rank.model}
                      item={judgeItem}
                      status={!isThinking ? "completed" : "thinking"}
                    />
                    {isThinking && <div className="absolute inset-0 bg-background/50 animate-pulse rounded-full" />}
                  </div>
                  <span className={isThinking ? "opacity-70" : ""}>{judgeItem.name || rank.councilor_name || rank.model}</span>
                  {isThinking && <span className="animate-spin ml-1 text-muted-foreground">⟳</span>}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {renderItems.map((rank, index) => {
            const judgeId = rank.judge_councilor_id || rank.councilor_id;
            const judgeItem = resolveItem(councilorLookup, judgeId || rank.model);
            const isThinking = rank.status === "thinking";

            return (
              <TabsContent key={index} value={String(index)}>
                <div className="mb-3 text-sm font-semibold text-muted-foreground mono flex items-center gap-2">
                  <div className="scale-75 origin-left">
                    <ModelAvatar modelId={rank.model} item={judgeItem} />
                  </div>
                  <span>{judgeItem.name || rank.councilor_name}</span>
                  <span className="opacity-50 text-xs">({rank.model})</span>
                </div>

                {isThinking ? (
                  <div className="flex items-center justify-center h-20 text-muted-foreground gap-2 border rounded-lg bg-muted/20">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    <span className="text-sm">Judging...</span>
                  </div>
                ) : (
                  <>
                    {rank.ranking && rank.ranking.length > 0 && (
                      <div className="rounded-lg border bg-card p-4 shadow-sm">
                        <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                          {t('extractedRanking')}
                        </div>
                        <ol className="ml-4 space-y-2 text-sm font-medium">
                          {rank.ranking.map((label, idx) => {
                            const targetItem = resolveLabelItem(label);
                            return (
                              <li key={idx} className="flex items-center gap-2">
                                <span className="w-4 text-muted-foreground">{idx + 1}.</span>
                                <div className="scale-75 origin-center">
                                  <ModelAvatar modelId={targetItem.model} item={targetItem} />
                                </div>
                                <span>{targetItem.name || label}</span>
                              </li>
                            );
                          })}
                        </ol>
                      </div>
                    )}

                    {rank.scores && (
                      <div className="mt-3 rounded-lg border bg-muted/40 p-4 shadow-sm">
                        <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                          {t('rawEvaluations')}
                        </div>
                        <div className="space-y-2 text-sm">
                          {/* Handle scores as simple key-value pairs if it's an object */}
                          {Array.isArray(rank.scores) ? rank.scores.map((item, idx) => {
                            const targetItem = resolveLabelItem(item.label);
                            return (
                              <div key={idx} className="flex flex-col gap-1 rounded-md border bg-card/60 p-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <div className="scale-75 origin-center">
                                      <ModelAvatar modelId={targetItem.model} item={targetItem} />
                                    </div>
                                    <span className="font-semibold">{targetItem.name || item.label}</span>
                                  </div>
                                  <span className="mono text-xs text-muted-foreground">{item.score}</span>
                                </div>
                                {item.rationale && <div className="text-muted-foreground text-sm">{item.rationale}</div>}
                              </div>
                            );
                          }) : Object.entries(rank.scores).map(([label, score], idx) => {
                            const targetItem = resolveLabelItem(label);
                            return (
                              <div key={idx} className="flex items-center justify-between rounded-md border bg-card/60 p-3">
                                <div className="flex items-center gap-2">
                                  <div className="scale-75 origin-center">
                                    <ModelAvatar modelId={targetItem.model} item={targetItem} />
                                  </div>
                                  <span className="font-semibold">{targetItem.name || label}</span>
                                </div>
                                <span className="mono text-xs text-muted-foreground font-bold">{score}</span>
                              </div>
                            );
                          })}

                          {/* Display Rationale separately if it exists at top level */}
                          {rank.rationale && (
                            <div className="mt-2 rounded-md border bg-card/60 p-3 text-sm text-muted-foreground">
                              <span className="font-semibold block mb-1 text-xs uppercase">Rationale</span>
                              {rank.rationale}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </TabsContent>
            );
          })}
        </Tabs>

        {aggregateRankings && aggregateRankings.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="mb-3 text-sm font-bold uppercase tracking-wider text-muted-foreground mono">
              {t('aggregateRankings')}
            </h4>
            <p className="mb-4 text-sm text-muted-foreground">
              {t('aggregateDescription')}
            </p>
            <div className="space-y-2">
              {aggregateRankings.map((agg, index) => {
                const targetItem = resolveItem(councilorLookup, agg.councilor_id);
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border bg-card p-4 shadow-sm hover:shadow-md transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                        #{index + 1}
                      </span>
                      <div className="scale-75 origin-center">
                        <ModelAvatar modelId={targetItem.model} item={targetItem} />
                      </div>
                      <span className="font-semibold">
                        {targetItem.name || agg.councilor_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mono">
                      <span>
                        {t('avg')}: {" "}
                        <span className="font-bold text-foreground">
                          {agg.average_rank.toFixed(2)}
                        </span>
                      </span>
                      <span className="text-xs">
                        ({agg.rankings_count} {t('votes')})
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
