import ReactMarkdown from "react-markdown";
import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Stage1({ responses, activeModel, onSelectModel }) {
  const { t } = useTranslation();

  if (!responses || responses.length === 0) {
    return null;
  }

  // Find the index of the active model
  const activeIndex = activeModel
    ? responses.findIndex((r) => r.model === activeModel)
    : 0;
  const currentValue = String(activeIndex >= 0 ? activeIndex : 0);

  const handleTabChange = (value) => {
    const index = parseInt(value, 10);
    if (responses[index] && onSelectModel) {
      onSelectModel(responses[index].model);
    }
  };

  return (
    <Card className="mb-4 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-bold">
          {t('stage1Title')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={currentValue} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-4 w-full flex-wrap justify-start h-auto gap-2 bg-muted/50 p-1">
            {responses.map((resp, index) => (
              <TabsTrigger
                key={index}
                value={String(index)}
                className="text-xs md:text-sm font-semibold data-[state=active]:bg-card data-[state=active]:shadow-sm"
              >
                {resp.councilor_name || resp.model || resp.councilor_id}
              </TabsTrigger>
            ))}
          </TabsList>

          {responses.map((resp, index) => (
            <TabsContent key={index} value={String(index)}>
              <div className="mb-3 text-sm font-semibold text-muted-foreground mono">
                {resp.councilor_name && (
                  <span className="mr-2">{resp.councilor_name}</span>
                )}
                {resp.model}
              </div>
              <div className="markdown-content rounded-lg border bg-card p-4 shadow-sm">
                <ReactMarkdown>{resp.answer_markdown || resp.response}</ReactMarkdown>
              </div>

              {resp.judge_card && (
                <div className="mt-3 rounded-lg border bg-muted/40 p-3 shadow-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                    Judge Card
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="font-semibold">立场：{resp.judge_card.stance}</div>
                    {resp.judge_card.core_reasons?.length > 0 && (
                      <div>
                        <div className="font-semibold">核心理由</div>
                        <ul className="ml-4 list-disc">
                          {resp.judge_card.core_reasons.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
}
