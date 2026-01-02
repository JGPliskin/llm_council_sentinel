/**
 * 预设思考过程库和管理工具
 * 
 * 用于在等待后端真实思考返回期间显示预设的思考提示，
 * 提升用户体验，避免长时间空白等待。
 */

// 预设思考库
export const PRELOAD_THINKING = {
    // T=0s 立即显示的临时状态
    initial: {
        title: "让我想一想...",
        detail: null,
        bullet_id: "preload_initial"
    },

    // 阶段1: 接收问题 (7个，随机选1个)
    stage1: [
        { title: "收到您的问题", detail: "我正在仔细阅读和理解您提出的问题，确保没有遗漏任何重要信息" },
        { title: "确认需求要点", detail: "让我梳理一下您问题的核心要点，确保我准确理解了您的真实意图" },
        { title: "理解问题背景", detail: "我正在分析您问题的背景和上下文，以便给出更贴合实际的回答" },
        { title: "解析输入信息", detail: "我正在提取您问题中的关键信息和关键词，为后续思考做准备" },
        { title: "识别问题意图", detail: "我正在判断您问题的类型和目标，确定需要采用什么样的思考方式" },
        { title: "接收您的请求", detail: "我已经收到了您的问题，现在开始准备进行深入的思考和分析" },
        { title: "理解深层含义", detail: "我正在挖掘您问题背后的深层含义，而不仅仅是表面的文字表述" }
    ],

    // 阶段2: 拆解问题 (7个，随机选1个)
    stage2: [
        { title: "拆解问题结构", detail: "我正在将您的问题拆解成几个关键部分，逐一分析每个部分的含义和要求" },
        { title: "分析关键要素", detail: "我正在识别问题中的关键要素和变量，这些要素对解决问题至关重要" },
        { title: "定位核心问题", detail: "我正在从多个角度分析问题，找出最核心、最关键的部分" },
        { title: "提炼相关信息", detail: "我正在从问题中提炼出所有相关信息，排除无关的干扰因素" },
        { title: "梳理逻辑关系", detail: "我正在梳理问题中各个要素之间的逻辑关系，构建清晰的思考框架" },
        { title: "分解复杂需求", detail: "我正在将复杂的需求分解成更小、更易处理的子问题" },
        { title: "分析层次结构", detail: "我正在分析问题的层次结构，从表层到深层逐步深入" }
    ],

    // 阶段3: 准备思考 (6个，随机选1个)
    stage3: [
        { title: "评估问题复杂度", detail: "我正在评估这个问题的复杂程度，确定需要投入多少思考精力" },
        { title: "规划思考方向", detail: "我正在规划解决问题的整体方向，确保思考过程有条不紊" },
        { title: "组织思考思路", detail: "我正在组织我的思考思路，构建一个清晰的思考路径" },
        { title: "构建思考框架", detail: "我正在构建一个系统的思考框架，确保不遗漏任何重要方面" },
        { title: "设计解决路径", detail: "我正在设计解决问题的具体路径，包括需要考虑哪些因素" },
        { title: "整合相关信息", detail: "我正在整合所有相关信息，准备进行综合性的深入思考" }
    ],

    // 兜底状态 (若3个预设显示完还没收到真实思考)
    fallback: {
        title: "深度思考中",
        detail: "问题比较复杂，我正在进行更深入的分析...",
        bullet_id: "preload_fallback"
    }
};

// 定时器 ID 存储
let preloadTimerId = null;
let preloadState = {
    index: 0,
    preloads: [],
    showedFallback: false
};

/**
 * 从每个阶段随机选择1个预设
 * @returns {Array} 3个预设的数组
 */
export function selectRandomPreloads() {
    const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

    return [
        { ...pick(PRELOAD_THINKING.stage1), bullet_id: "preload_1" },
        { ...pick(PRELOAD_THINKING.stage2), bullet_id: "preload_2" },
        { ...pick(PRELOAD_THINKING.stage3), bullet_id: "preload_3" }
    ];
}

/**
 * 获取随机延迟时间 (2-3秒)
 * @returns {number} 毫秒数
 */
function getRandomDelay() {
    return (Math.random() * 1000 + 2000); // 2000-3000ms
}

/**
 * 获取初始延迟时间 (1.5-3秒)
 * @returns {number} 毫秒数
 */
function getInitialDelay() {
    return (Math.random() * 1500 + 1500); // 1500-3000ms
}

/**
 * 启动预设定时器
 * @param {Function} onPreload - 回调函数，接收预设对象 { title, detail, bullet_id }
 */
export function startPreloadTimer(onPreload) {
    // 先清除可能存在的定时器
    stopPreloadTimer();

    // 重置状态
    preloadState = {
        index: 0,
        preloads: selectRandomPreloads(),
        showedFallback: false
    };

    // T=0s 立即显示初始状态
    onPreload(PRELOAD_THINKING.initial);

    // 递归函数：显示下一个预设
    function showNext() {
        if (preloadState.index < preloadState.preloads.length) {
            // 还有预设要显示
            const preload = preloadState.preloads[preloadState.index];
            onPreload(preload);
            preloadState.index++;

            // 设置下一个定时器
            preloadTimerId = setTimeout(showNext, getRandomDelay());
        } else if (!preloadState.showedFallback) {
            // 显示兜底状态
            preloadState.showedFallback = true;
            onPreload(PRELOAD_THINKING.fallback);
            // 兜底后不再启动新的定时器
        }
    }

    // 首个预设延迟显示
    preloadTimerId = setTimeout(showNext, getInitialDelay());
}

/**
 * 停止预设定时器
 */
export function stopPreloadTimer() {
    if (preloadTimerId) {
        clearTimeout(preloadTimerId);
        preloadTimerId = null;
    }
    preloadState = {
        index: 0,
        preloads: [],
        showedFallback: false
    };
}

/**
 * 判断是否为预设 bullet
 * @param {string} bulletId - bullet_id
 * @returns {boolean}
 */
export function isPreloadBullet(bulletId) {
    return bulletId && bulletId.startsWith('preload_');
}

/**
 * 过滤预设 thinking，用于持久化
 * @param {Array} thinkingList - thinking 列表
 * @returns {Array} 过滤后的列表
 */
export function filterPreloadThinking(thinkingList) {
    if (!Array.isArray(thinkingList)) return thinkingList;
    return thinkingList.filter(t => !isPreloadBullet(t.bullet_id));
}
