/**
 * 议员 UI 配置映射表
 * Key: 后端返回的 councilor.id
 * Value: 前端专用的 UI 属性
 */
export const COUNCILOR_UI_CONFIG = {
    "immanuel_kant": { color: "orange" },
    "donald_trump": { color: "red" },
    "hideo_kojima": { color: "blue" },
    "chairman": { color: "purple" },
};

/**
 * 获取议员 UI 配置
 * @param {string} id 议员 ID
 * @returns {object} UI 配置，若无则返回默认值
 */
export function getCouncilorUIConfig(id) {
    return COUNCILOR_UI_CONFIG[id] || { color: "gray" };
}
