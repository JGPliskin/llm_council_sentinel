import React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";


const ThinkingHistory = ({ history, councilorName, modelName, onClose }) => {
    if (!history || history.length === 0) {
        return (
            <div className="p-4 text-center text-sm text-muted-foreground">
                No thinking history available.
            </div>
        );
    }

    return (
        <div className="w-[300px] md:w-[400px]">
            <div className="flex items-center justify-between border-b p-3">
                <div>
                    <h4 className="font-semibold text-sm">{councilorName}</h4>
                    <span className="text-xs text-muted-foreground">{modelName}</span>
                </div>
                {/* Close button handled by Popover usually, but layout here mostly */}
            </div>
            <ScrollArea className="h-[300px] p-3">
                <div className="space-y-3">
                    {history.map((item, index) => (
                        <div key={index} className="flex gap-2 text-sm relative pl-4 border-l border-muted">
                            {/* Timeline dot */}
                            <div className="absolute left-[-5px] top-1.5 h-2 w-2 rounded-full bg-primary/20"></div>

                            <div className="flex-1">
                                <p className="text-foreground/90 leading-tight">{item.title}</p>
                                <span className="text-[10px] text-muted-foreground">
                                    +{item.t?.toFixed(1)}s
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
};

export default ThinkingHistory;
