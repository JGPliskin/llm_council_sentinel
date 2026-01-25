/**
 * 议员 UI 配置映射表
 * Key: 后端返回的 councilor.id
 * Value: 前端专用的 UI 属性
 */
export const COUNCILOR_UI_CONFIG = {
    "immanuel_kant": {
        color: "cyan",
        role: "PHILOSOPHER",
        standing: "/avatars/standing/kant_standing.png",
        avatar: "/avatars/kant.png"
    },
    "donald_trump": {
        color: "cyan",
        role: "POLITICIAN",
        standing: "/avatars/standing/trump_standing.png",
        avatar: "/avatars/trump.png"
    },
    "hideo_kojima": {
        color: "cyan",
        role: "GAME DESIGNER",
        standing: "/avatars/standing/kojima_standing.png",
        avatar: "/avatars/kojima.png"
    },
    "chairman": {
        color: "cyan",
        role: "SYSTEM OVERSEER",
        avatar: "/avatars/chairman.png"
    },
};

/**
 * 获取议员 UI 配置
 * @param {string} id 议员 ID
 * @returns {object} UI 配置，若无则返回默认值
 */
export function getCouncilorUIConfig(id) {
    return COUNCILOR_UI_CONFIG[id] || { color: "gray" };
}
