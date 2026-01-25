import React from 'react';

const isAvatarUrl = (avatar) =>
    typeof avatar === "string" && (avatar.startsWith("http") || avatar.startsWith("/"));

const renderAvatar = (avatar, alt) => {
    if (isAvatarUrl(avatar)) {
        return <img src={avatar} alt={alt || "Avatar"} className="h-full w-full object-cover opacity-80" />;
    }
    return <span aria-hidden="true" className="text-2xl">{avatar || "?"}</span>;
};

export const ChairmanWidget = ({ data }) => {
    if (!data) return null;

    return (
        <div className="hidden md:flex flex-col items-end opacity-60 hover:opacity-100 transition-opacity duration-500 group">
            <div className="flex items-center gap-3">
                <div className="text-right">
                    <div className="text-[10px] font-mono text-hud-muted uppercase tracking-widest">Overseer Link</div>
                    <div className="text-xs font-bold font-orbitron text-hud-cyan tracking-wider">{data.name}</div>
                    <div className="flex justify-end gap-1 mt-1">
                        <div className="w-1.5 h-1.5 bg-hud-cyan rounded-full animate-pulse"></div>
                        <span className="text-[9px] font-mono text-hud-cyan">MONITORING</span>
                    </div>
                </div>

                {/* Hexagon/Circle Container */}
                <div className="relative w-12 h-12">
                    <div className="absolute inset-0 border border-[rgba(6,182,212,0.3)] rounded-full animate-[spin_10s_linear_infinite]"></div>
                    <div className="absolute inset-1 border border-[rgba(6,182,212,0.1)] rounded-full"></div>
                    <div className="absolute inset-2 bg-hud-bg-soft rounded-full overflow-hidden flex items-center justify-center border border-[rgba(6,182,212,0.2)] group-hover:border-[rgba(6,182,212,0.5)] transition-colors">
                        {renderAvatar(data.avatar, data.name)}
                    </div>
                </div>
            </div>
        </div>
    );
};
