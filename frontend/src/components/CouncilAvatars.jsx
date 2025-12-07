import React from "react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarFallback } from "./ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Crown, ExternalLink } from "lucide-react";
import { HuggingFace, LongCat, Aws } from "@lobehub/icons";
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

const ModelAvatar = ({ modelId, isActive, onClick, status = "idle", isChairman = false }) => {
  if (!modelId || typeof modelId !== 'string') return null;

  // Try to get config, or generate fallback
  let config = MODEL_CONFIG[modelId];

  if (!config) {
    // Generate fallback config
    // Ensure safe split
    const parts = modelId.split("/");
    const shortName = parts.length > 1 ? parts[1].substring(0, 2).toUpperCase() : modelId.substring(0, 2).toUpperCase();
    const name = parts.length > 1 ? parts[1] : modelId;

    config = {
      name,
      shortName,
      color: stringToColor(modelId),
      Icon: null
    };
  }

  const statusText = {
    idle: "",
    thinking: "Thinking...",
    completed: "✓",
  };

  const IconComponent = config.Icon;

  const handleTooltipClick = () => {
    window.open(ZENMUX_INVITE_URL, "_blank", "noopener,noreferrer");
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={`model-avatar ${isActive ? "active" : ""} ${isChairman ? "chairman" : ""}`}
          onClick={onClick}
          style={{ "--model-color": config.color }}
        >
          <div className="avatar-wrapper">
            <Avatar className="h-12 w-12 cursor-pointer transition-all hover:scale-110">
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
          </div>
          <div className="model-info">
            <div className="model-name">{config.name}</div>
            {status !== "idle" && (
              <div className={`model-status status-${status}`}>
                {statusText[status]}
              </div>
            )}
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent className="cursor-pointer" onClick={handleTooltipClick}>
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-xs">{modelId}</span>
          <ExternalLink size={10} className="opacity-60" />
        </div>
      </TooltipContent>
    </Tooltip>
  );
};

export const CouncilAvatars = ({
  councilModels = [],
  chairmanModel,
  activeModel,
  onSelectModel,
  modelStatuses = {},
  onChairmanClick,
}) => {
  const { t } = useTranslation();

  return (
    <TooltipProvider delayDuration={300}>
      <div className="council-avatars">
        <div className="council-section">
          <div className="section-label">{t("councilMembers")}</div>
          <div className="avatars-row">
            {councilModels.map((modelId) => (
              <ModelAvatar
                key={modelId}
                modelId={modelId}
                isActive={activeModel === modelId}
                onClick={() => onSelectModel?.(modelId)}
                status={modelStatuses[modelId]}
                isChairman={modelId === chairmanModel}
              />
            ))}
          </div>
        </div>

        {chairmanModel && (
          <div className="chairman-section">
            <div className="section-label">{t("chairman")}</div>
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
