import React from 'react';
import { Brain } from 'lucide-react';

export default function ThinkingConsole({ activeThinking, councilorLookup }) {
    // activeThinking: map of cid -> { title, history }

    const activities = Object.entries(activeThinking)
        .filter(([_, state]) => state.title)
        .map(([cid, state]) => {
            const councilor = councilorLookup ? councilorLookup[cid] : null;
            return {
                id: cid,
                name: councilor ? councilor.name : cid,
                title: state.title
            };
        });

    if (activities.length === 0) return null;

    return (
        <div className="border-t border-border bg-card/95 backdrop-blur-sm p-3 text-xs transition-all duration-300 shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-muted-foreground text-[10px] uppercase font-bold tracking-wider">
                <Brain className="w-3 h-3" />
                <span>Thinking Process</span>
            </div>
            <div className="space-y-2 pl-1">
                {activities.map(act => (
                    <div key={act.id} className="flex gap-2 items-start animate-in fade-in slide-in-from-bottom-1 duration-300">
                        <div className="flex-shrink-0 flex items-center gap-1.5 min-w-[80px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-pulse"></span>
                            <span className="font-semibold text-foreground/80">{act.name}</span>
                        </div>
                        <span className="text-muted-foreground break-words leading-tight flex-1">{act.title}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
