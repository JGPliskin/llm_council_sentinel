import React from "react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarFallback } from "./ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Crown, ExternalLink, Check, ChevronDown, ChevronRight, AlertCircle, Ban } from "lucide-react";
import { HuggingFace, LongCat, Aws } from "@lobehub/icons";
import { useState } from "react";
import "./CouncilAvatars.css";

// Zenmux invite URL
const ZENMUX_INVITE_URL = "https://zenmux.ai/invite/ICIEEXGV14722567";

// Model configuration with brand colors and metadata
const MODEL_CONFIG = {
  "meituan/longcat-flash-chat:free": {
    name: "LongCat",
    shortName: "LC",
    color: "#FF6B35", // Orange
    Icon: LongCat,
  },
  "nvidia/nemotron-nano-9b-v2:free": {
    name: "Nemotron",
    shortName: "NT",
    color: "#76B900", // NVIDIA Green
    Icon: HuggingFace,
  },
  "kwaipilot/kat-coder-pro:free": {
    name: "Kuaipilot",
    shortName: "KP",
    color: "#FF6E30", // Kuaishou Orange
    Icon: HuggingFace,
  },
  "amazon/nova-2-lite-v1:free": {
    name: "Amazon Nova",
    shortName: "AN",
    color: "#FF9900", // Amazon Orange
    Icon: Aws,
  },
  "google/gemini-2.5-flash": {
    name: "Gemini 2.5",
    shortName: "GM",
    color: "#4285F4", // Google Blue
    Icon: null, // Fallback to initials
  },
  "mistralai/mistral-7b-instruct:free": {
    name: "Mistral 7B",
    shortName: "MI",
    color: "#5C46FF", // Mistral Purple
    Icon: null,
  },
  "arcee-ai/trinity-mini:free": {
    name: "Trinity",
    shortName: "TR",
    color: "#00CED1", // Dark Turquoise
    Icon: null,
  },
  "tngtech/tng-r1t-chimera:free": {
    name: "Chimera",
    shortName: "CH",
    color: "#FF1493", // Deep Pink
    Icon: null,
  },
  "moonshotai/kimi-k2:free": {
    name: "Kimi K2",
    shortName: "KM",
    color: "#000000", // Black
    Icon: null,
  },
  "tngtech/deepseek-r1t2-chimera:free": {
    name: "DeepSeek Chimera",
    shortName: "DC",
    color: "#4B0082", // Indigo
    Icon: null,
  },
};

// Helper to generate a consistent color from a string
const stringToColor = (str) => {
  if (!str) return "#CCCCCC";
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const c = (hash & 0x00ffffff).toString(16).toUpperCase();
  return "#" + "00000".substring(0, 6 - c.length) + c;
};

const ModelAvatar = ({
  modelId,
  item, // Full councilor object if available
  isActive,
  onClick,
  status = "idle",
  isChairman = false,
  selectable = false,
  isSelected = false
}) => {
  if (!modelId || typeof modelId !== 'string') return null;

  // Try to get config, or generate fallback
  let config = MODEL_CONFIG[modelId];

  // Logic for health/disabled state
  // If item is provided, use it. Otherwise assume healthy (legacy behavior).
  // STRICT: healthy === true. (null/undefined/false = disabled)
  const isHealthy = item ? item.healthy === true : true;
  const healthError = item?.health_error || "Unavailable";

  // If item is unhealthy, force disabled state look
  const isDisabled = !isHealthy;

  if (!config) {
    // Generate fallback config
    // Ensure safe split
    const parts = modelId.split("/");
    const shortName = parts.length > 1 ? parts[1].substring(0, 2).toUpperCase() : modelId.substring(0, 2).toUpperCase();
    const name = parts.length > 1 ? parts[1] : modelId;

    config = {
      name: item?.name || name, // Use server name if available
      shortName,
      color: stringToColor(modelId),
      Icon: null
    };
  } else if (item?.name) {
    // Override name from backend config if present
    config = { ...config, name: item.name };
  }

  const statusText = {
    idle: "",
    thinking: "Thinking...",
    completed: "✓",
    error: "Error"
  };

  const IconComponent = config.Icon;

  const handleTooltipClick = (e) => {
    e.stopPropagation();
    if (!isDisabled) {
      window.open(ZENMUX_INVITE_URL, "_blank", "noopener,noreferrer");
    }
  };

  const handleClick = (e) => {
    if (isDisabled) {
      e.stopPropagation();
      return;
    }
    onClick && onClick(e);
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={`model-avatar 
            ${isActive ? "active" : ""} 
            ${isChairman ? "chairman" : ""} 
            ${isDisabled ? "disabled" : ""}
            ${selectable && !isDisabled ? (isSelected ? "selected" : "deselected") : ""}
          `}
          onClick={handleClick}
          style={{ "--model-color": config.color }}
        >
          <div className="avatar-wrapper">
            <Avatar className="h-12 w-12 cursor-pointer transition-all">
              {IconComponent ? (
                <div className="flex h-full w-full items-center justify-center p-2">
                  <IconComponent size={32} />
                </div>
              ) : (
                <AvatarFallback
                  style={{ backgroundColor: config.color, color: "white" }}
                >
                  {config.shortName}
                </AvatarFallback>
              )}
            </Avatar>
            {isChairman && (
              <div className="chairman-badge">
                <Crown size={12} />
              </div>
            )}

            {/* Selection Checkmark */}
            {selectable && isSelected && !isDisabled && (
              <div className="selection-badge">
                <Check size={12} strokeWidth={3} />
              </div>
            )}

            {/* Disabled Icon */}
            {isDisabled && (
              <div className="disabled-badge">
                <Ban size={12} strokeWidth={3} />
              </div>
            )}

          </div>
          <div className="model-info">
            <div className="model-name">{config.name}</div>
            {status !== "idle" && (
              <div className={`model-status status-${status}`}>
                {statusText[status]}
              </div>
            )}
            {isDisabled && (
              <div className="model-status status-error flex gap-1 items-center justify-center">
                <AlertCircle size={8} /> Unavailable
              </div>
            )}
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent className="cursor-pointer max-w-[200px]" onClick={handleTooltipClick}>
        {isDisabled ? (
          <div className="text-red-400 font-semibold mb-1">
            {healthError}
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-xs">{modelId}</span>
            <ExternalLink size={10} className="opacity-60" />
          </div>
        )}
      </TooltipContent>
    </Tooltip>
  );
};

export const CouncilAvatars = ({
  councilModels, // Keep for backward compat support (array of strings)
  councilors,    // New prop: full objects
  chairmanModel,
  activeModel,
  onSelectModel,
  modelStatuses = {},
  onChairmanClick,
  selectable = false,
  selectedIds = new Set(),
  onToggleId = null
}) => {
  const { t } = useTranslation();
  const [showUnavailable, setShowUnavailable] = useState(false);

  // Normalize input: Prefer `councilors` objects. Fallback to `councilModels` strings.
  let items = [];
  if (councilors && councilors.length > 0) {
    items = councilors;
  } else if (councilModels && councilModels.length > 0) {
    items = councilModels.map(mid => ({ id: mid, model: mid, healthy: true }));
  }

  // Filter available vs unavailable (strict healthy check)
  const available = items.filter(c => c.active !== false && c.healthy === true);
  const unavailable = items.filter(c => c.active !== false && c.healthy !== true);

  // Unavailable count logic
  const hiddenCount = unavailable.length;

  return (
    <TooltipProvider delayDuration={300}>
      <div className="council-avatars flex-col items-center">
        <div className="council-section w-full items-center">
          <div className="section-label mb-2">{t("councilMembers")}</div>

          {/* Available Row */}
          <div className="avatars-row flex-wrap justify-center">
            {available.map((item) => (
              <ModelAvatar
                key={item.id}
                modelId={item.model} // Pass model string for visual lookup
                item={item}          // Pass full item for health status etc.
                isActive={activeModel === item.model}
                onClick={() => {
                  if (selectable && onToggleId) {
                    onToggleId(item.id);
                  } else {
                    onSelectModel?.(item.model);
                  }
                }}
                status={modelStatuses[item.model]}
                isChairman={item.model === chairmanModel}
                selectable={selectable && !chairmanModel}
                isSelected={selectable ? selectedIds.has(item.id) : false}
              />
            ))}
          </div>

          {/* Unavailable Toggle Section */}
          {hiddenCount > 0 && (
            <div className="unavailable-section mt-4 w-full flex flex-col items-center">
              <button
                type="button"
                onClick={() => setShowUnavailable(!showUnavailable)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2 px-3 py-1 rounded-full bg-muted/30 hover:bg-muted/50"
              >
                {showUnavailable ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {showUnavailable ? t("hideUnavailable", "Hide unavailable") : t("showUnavailable", `Show ${hiddenCount} unavailable`)}
              </button>

              {showUnavailable && (
                <div className="avatars-row flex-wrap justify-center mt-2 p-3 bg-muted/10 rounded-lg border border-dashed border-muted">
                  {unavailable.map((item) => (
                    <ModelAvatar
                      key={item.id}
                      modelId={item.model}
                      item={item}
                      isActive={false}
                      onClick={() => { }} // Disabled interaction handled in component but failsafe here
                      status="error"
                      selectable={false} // Cannot select
                      isSelected={false}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

        </div>

        {chairmanModel && (
          <div className="chairman-section mt-4 pt-4 border-t border-border/50 w-full flex flex-col items-center">
            <div className="section-label mb-2">{t("chairman")}</div>
            <ModelAvatar
              modelId={chairmanModel}
              isActive={activeModel === chairmanModel}
              onClick={() => onChairmanClick?.(chairmanModel)}
              status={modelStatuses[chairmanModel]}
              isChairman={true}
            />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
};

export default CouncilAvatars;
