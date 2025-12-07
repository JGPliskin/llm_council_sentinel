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
import { Qwen, DeepSeek, HuggingFace, LongCat, Nova, Aws } from "@lobehub/icons";
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
    Icon: HuggingFace, // Using HuggingFace icon as placeholder
  },
  "kwaipilot/kat-coder-pro:free": {
    name: "Kuaipilot",
    shortName: "KP",
    color: "#FF6E30", // Kuaishou Orange
    Icon: HuggingFace, // Using HuggingFace icon as placeholder
  },
  "amazon/nova-2-lite-v1:free": {
    name: "Amazon Nova",
    shortName: "AN",
    color: "#FF9900", // Amazon Orange
    Icon: Aws, // Using AWS icon for Amazon Nova
    isChairman: true,
  },
};

const ModelAvatar = ({ modelId, isActive, onClick, status = "idle" }) => {
  const config = MODEL_CONFIG[modelId];
  if (!config) return null;

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
          className={`model-avatar ${isActive ? "active" : ""} ${config.isChairman ? "chairman" : ""}`}
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
            {config.isChairman && (
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
            />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
};

export default CouncilAvatars;
