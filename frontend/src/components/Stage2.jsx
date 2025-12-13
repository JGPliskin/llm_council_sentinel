import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const getCouncilorDisplay = (lookup, idOrModel) => {
  const item = lookup?.[idOrModel];
  if (item) {
    return item.name || item.model || idOrModel;
  }
  return idOrModel;
};

export default function Stage2({
  rankings,
  labelToCouncilor,
  aggregateRankings,
  activeModel,
  onSelectModel,
  scrollToStage2,
  councilorLookup = {},
}) {
  const { t } = useTranslation();

  if (!rankings || rankings.length === 0) {
    return null;
  }

  const activeIndex = activeModel
    ? rankings.findIndex((r) => r.model === activeModel)
    : 0;
  const currentValue = String(activeIndex >= 0 ? activeIndex : 0);

  const handleTabChange = (value) => {
    const index = parseInt(value, 10);
    if (rankings[index] && onSelectModel) {
      onSelectModel(rankings[index].model);
      if (scrollToStage2) {
        scrollToStage2();
      }
    }
  };

  const resolveLabelName = (label) => {
    const councilorId = labelToCouncilor?.[label];
    return getCouncilorDisplay(councilorLookup, councilorId || label);
  };

  const resolveCouncilorName = (idOrModel) =>
    getCouncilorDisplay(councilorLookup, idOrModel);

  return (
    <Card className="mb-4 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-bold">
          {t('stage2Title')}
        </CardTitle>
        <CardDescription className="text-sm">
          {t('stage2Description')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-muted-foreground mono">
          {t('rawEvaluations')}
        </h4>

        <Tabs value={currentValue} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-4 w-full flex-wrap justify-start h-auto gap-2 bg-muted/50 p-1">
            {rankings.map((rank, index) => (
              <TabsTrigger
                key={index}
                value={String(index)}
                className="text-xs md:text-sm font-semibold data-[state=active]:bg-card data-[state=active]:shadow-sm"
              >
                {rank.councilor_name || rank.judge_councilor_name || resolveCouncilorName(rank.model)}
              </TabsTrigger>
            ))}
          </TabsList>

          {rankings.map((rank, index) => (
            <TabsContent key={index} value={String(index)}>
              <div className="mb-3 text-sm font-semibold text-muted-foreground mono">
                {(rank.councilor_name || rank.judge_councilor_name) && <span className="mr-2">{rank.councilor_name || rank.judge_councilor_name}</span>}
                {rank.model}
              </div>

              {rank.ranking && rank.ranking.length > 0 && (
                <div className="rounded-lg border bg-card p-4 shadow-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                    {t('extractedRanking')}
                  </div>
                  <ol className="ml-4 list-decimal space-y-1 text-sm font-medium">
                    {rank.ranking.map((label, idx) => (
                      <li key={idx}>{resolveLabelName(label)}</li>
                    ))}
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
                    {Array.isArray(rank.scores) ? rank.scores.map((item, idx) => (
                      <div key={idx} className="flex flex-col gap-1 rounded-md border bg-card/60 p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{resolveLabelName(item.label)}</span>
                          <span className="mono text-xs text-muted-foreground">{item.score}</span>
                        </div>
                        {item.rationale && <div className="text-muted-foreground text-sm">{item.rationale}</div>}
                      </div>
                    )) : Object.entries(rank.scores).map(([label, score], idx) => (
                      <div key={idx} className="flex items-center justify-between rounded-md border bg-card/60 p-3">
                        <span className="font-semibold">{resolveLabelName(label)}</span>
                        <span className="mono text-xs text-muted-foreground font-bold">{score}</span>
                      </div>
                    ))}

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
            </TabsContent>
          ))}
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
              {aggregateRankings.map((agg, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border bg-card p-4 shadow-sm hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                      #{index + 1}
                    </span>
                    <span className="font-semibold">
                      {resolveCouncilorName(agg.councilor_id)}
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
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
