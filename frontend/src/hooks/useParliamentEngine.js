import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { api } from '@/api';
import { startPreloadTimer, stopPreloadTimer, isPreloadBullet } from '@/utils/preloadThinking';

/**
 * Parliament Engine Hook
 * 管理三阶段流程的状态机
 */
export function useParliamentEngine() {
    // === 核心状态 ===
    const [stage, setStage] = useState('idle'); // 'idle' | 'stage1' | 'stage2' | 'stage3'
    const [isLoading, setIsLoading] = useState(false);

    // === 数据状态 ===
    const [conversation, setConversation] = useState(null);
    const [resolvedCouncilors, setResolvedCouncilors] = useState([]);
    const [stage1Results, setStage1Results] = useState([]);
    const [stage2Results, setStage2Results] = useState(null); // Array of review items
    const [stage3Result, setStage3Result] = useState(null);

    // === 进度状态 ===
    const [agentProgress, setAgentProgress] = useState({}); // { [councilor_id]: 0~100 }
    const [stageProgress, setStageProgress] = useState(0);  // 0~100
    const [etaByCouncilor, setEtaByCouncilor] = useState({}); // { [councilor_id]: eta_ms_remaining }
    const [stage2Skipped, setStage2Skipped] = useState(false);

    // === Thinking 状态 ===
    const [thinkingByCouncilor, setThinkingByCouncilor] = useState({}); // { [id]: { status, steps[] } }
    const [thinkingExpanded, setThinkingExpanded] = useState({}); // { [id]: boolean }
    const [stage1AnswerStream, setStage1AnswerStream] = useState({}); // { [id]: text }
    const [stage3AnswerStream, setStage3AnswerStream] = useState('');
    const [evaluationComments, setEvaluationComments] = useState({}); // Stage 2 评价映射 { [target_id]: comments[] }
    const [synthesisSteps, setSynthesisSteps] = useState([]); // Stage 3 日志

    // Stage2 思考状态 (按评审员和目标分组)
    const [stage2ThinkingByJudge, setStage2ThinkingByJudge] = useState({}); // { [judgeId]: { status, stepsByTarget: { [targetId]: steps[] } } }

    // === UI 状态 ===
    const [activeTab, setActiveTab] = useState(null);
    const [consensusUnlocked, setConsensusUnlocked] = useState(false);
    const [hasViewedConsensus, setHasViewedConsensus] = useState(false);
    const [aggregateRankings, setAggregateRankings] = useState([]);

    // === 定时器引用 (用于进度平滑) ===
    const progressTimers = useRef({});
    const stage2AnonMapRef = useRef(null);

    /**
      * 计算汇总排名
      */
    const calculateAggregateRankings = (reviews, anonMap) => {
        if (!reviews || !anonMap) return [];

        const scoreMap = {}; // anonId -> [scores]

        reviews.forEach(review => {
            if (review.ranking && Array.isArray(review.ranking)) {
                review.ranking.forEach((anonId, index) => {
                    if (!scoreMap[anonId]) scoreMap[anonId] = [];
                    scoreMap[anonId].push(index + 1); // Rank 1 = score 1
                });
            }
        });

        const results = Object.keys(scoreMap).map(anonId => {
            const scores = scoreMap[anonId];
            const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
            return {
                anonId,
                councilor_id: anonMap[anonId],
                average_rank: avg
            };
        });

        // Sort: Lowest average rank is best
        results.sort((a, b) => a.average_rank - b.average_rank);

        // Assign rank
        return results.map((item, index) => ({
            ...item,
            rank: index + 1
        }));
    };

    const buildEvaluationComments = useCallback((reviews, anonMap) => {
        if (!reviews || !anonMap) return {};

        const newComments = {};

        reviews.forEach(review => {
            const comments = review.per_candidate_comments || {};
            const fromId = review.judge_councilor_id || review.model;
            const fromName = review.judge_councilor_name;

            Object.entries(comments).forEach(([anonId, comment]) => {
                const targetId = anonMap[anonId];
                if (!targetId) return;
                if (!newComments[targetId]) newComments[targetId] = [];
                newComments[targetId].push({
                    fromId,
                    fromName,
                    comment,
                    score: review.scores?.[anonId]
                });
            });
        });

        return newComments;
    }, []);

    const applyStage2ReviewComments = useCallback((review, anonMap) => {
        if (!review || !anonMap) return;
        const comments = review.per_candidate_comments;
        if (!comments || typeof comments !== 'object') return;

        const fromId = review.judge_councilor_id || review.model;
        const fromName = review.judge_councilor_name;

        setEvaluationComments(prev => {
            const next = { ...prev };
            Object.entries(comments).forEach(([anonId, comment]) => {
                const targetId = anonMap[anonId];
                if (!targetId) return;
                const existing = Array.isArray(next[targetId])
                    ? next[targetId].filter(entry => entry.fromId !== fromId)
                    : [];
                existing.push({
                    fromId,
                    fromName,
                    comment,
                    score: review.scores?.[anonId]
                });
                next[targetId] = existing;
            });
            return next;
        });
    }, []);

    const restoreThinking = useCallback((thinkingMeta) => {
        if (!thinkingMeta || !thinkingMeta.stage1) return {};
        const restored = {};
        Object.entries(thinkingMeta.stage1).forEach(([cid, entry]) => {
            const steps = Array.isArray(entry?.steps) ? entry.steps.map(step => ({
                bullet_id: step.bullet_id || step.id || step.title,
                title: step.title || "",
                detail: step.detail || null,
                t: step.t
            })) : [];
            if (steps.length > 0) {
                restored[cid] = {
                    status: entry.status || "done",
                    steps
                };
            }
        });
        return restored;
    }, []);

    /**
     * 恢复会话 (History View)
     */
    const loadSession = useCallback((conv) => {
        if (!conv) {
            console.warn("[loadSession] No conversation provided");
            return;
        }

        console.log("[loadSession] Loading:", conv.id, conv);

        // Hard reset internal states first, but keep conversation
        // setStage('idle'); // Don't reset to idle immediately, set to correct stage below
        // cancel timers
        Object.values(progressTimers.current).forEach(clearInterval);
        progressTimers.current = {};

        setConversation(conv);
        setResolvedCouncilors(conv.metadata?.resolved_councilors || []);
        setAgentProgress({}); // No progress for history
        const lastMsg = conv.messages?.[conv.messages.length - 1];
        const restoredThinking = restoreThinking(lastMsg?.metadata?.thinking || conv.metadata?.thinking);
        setThinkingByCouncilor(restoredThinking);
        setThinkingExpanded(() => {
            const expanded = {};
            Object.keys(restoredThinking).forEach(cid => {
                expanded[cid] = true;
            });
            return expanded;
        });
        setStage1AnswerStream({});
        setStage3AnswerStream('');
        setEvaluationComments({});
        setSynthesisSteps([]);
        setStage2ThinkingByJudge({}); // 历史加载时不需要 thinking 状态
        setStage1Results([]);
        setStage2Results(null);
        setStage3Result(null);
        setAggregateRankings([]);
        setStage2Skipped(false);

        // Determine Stage
        console.log("[loadSession] Last msg:", lastMsg);

        // If no assistant message, it's just a new conversation or user only?
        if (!lastMsg || lastMsg.role !== 'assistant') {
            console.warn("[loadSession] No assistant message found, defaulting to IDLE");
            setStage('idle');
            return;
        }

        // Restore Resolved Councilors (Robust Fallback)
        let resolved = conv.metadata?.resolved_councilors || [];
        if (resolved.length === 0 && lastMsg.stage1 && lastMsg.stage1.length > 0) {
            console.log("[loadSession] Metadata missing resolved_councilors, extracting from stage1...");
            resolved = lastMsg.stage1.map(item => ({
                id: item.councilor_id,
                name: item.councilor_name || item.councilor_id,
                avatar: '?', // Best effort
                model: item.model
            }));
        }
        setResolvedCouncilors(resolved);

        // Restore Stage 1
        if (lastMsg.stage1 && lastMsg.stage1.length > 0) {
            setStage1Results(lastMsg.stage1);
            setStage('stage1');
        }

        // Restore Stage 2
        // Backend v2 returns { reviews: [], anon_map: {} }, Legacy returned [].
        // We need to handle both.
        let stage2Data = lastMsg.stage2;
        let reviews = [];
        let anonMap = lastMsg.metadata?.anon_to_councilor;
        const skipped = !!(stage2Data && typeof stage2Data === 'object' && stage2Data.skipped);
        setStage2Skipped(skipped);

        if (stage2Data) {
            if (Array.isArray(stage2Data)) {
                // Legacy Array format
                reviews = stage2Data;
                if (!anonMap && stage2Data.length > 0) {
                    // Try to infer or check if anon_map is embedded (unlikely in legacy, usually inside metadata)
                }
            } else if (typeof stage2Data === 'object' && stage2Data.reviews) {
                // v2 Object format
                reviews = stage2Data.reviews;
                if (stage2Data.anon_map) {
                    anonMap = stage2Data.anon_map;
                }
            }
        }

        if (reviews && reviews.length > 0) {
            setStage2Results(reviews);
            // If we are fully done, show stage2 or stage3. If stage3 exists, we overwrite stage anyway.
            // If only stage2 is done, set stage2.
            if (!lastMsg.stage3) {
                setStage('stage2');
            }

            if (anonMap) {
                stage2AnonMapRef.current = anonMap || null;
                const newComments = {};
                reviews.forEach(review => {
                    const comments = review.per_candidate_comments || {};
                    Object.entries(comments).forEach(([anonId, comment]) => {
                        const targetId = anonMap[anonId];
                        if (targetId) {
                            if (!newComments[targetId]) newComments[targetId] = [];
                            newComments[targetId].push({
                                fromId: review.judge_councilor_id,
                                fromName: review.judge_councilor_name, // If available
                                comment,
                                score: review.scores?.[anonId]
                            });
                        }
                    });
                });
                setEvaluationComments(newComments);

                // Restore Rankings
                const rankings = calculateAggregateRankings(reviews, anonMap);
                setAggregateRankings(rankings);
            }
        }

        // Restore Stage 3
        if (lastMsg.stage3) {
            setStage3Result(lastMsg.stage3);
            setStage('stage3');
            setConsensusUnlocked(true);
            // Ensure user can view consensus overlay first
            setHasViewedConsensus(false);
        } else {
            setConsensusUnlocked(false);
            setHasViewedConsensus(false);
        }

        // Set default tab (Use the resolved local variable)
        if (resolved.length > 0) {
            setActiveTab(resolved[0].id);
        } else {
            console.warn("[loadSession] No councilors resolved, activeTab not set");
        }

        setIsLoading(false);
    }, []);

    /**
     * 启动新会话
     * @param {string} prompt 用户输入
     * @param {string[]} councilorIds 选中的议员 ID
     */
    const startSession = useCallback(async (prompt, councilorIds) => {
        try {
            // 1. 创建对话
            const newConv = await api.createConversation(councilorIds);
            setConversation(newConv);

            // 2. 重置状态
            setStage('stage1');
            setIsLoading(true);
            setConsensusUnlocked(false);
            setHasViewedConsensus(false);
            setThinkingByCouncilor({});
            setThinkingExpanded({});
            setStage1AnswerStream({});
            setStage3AnswerStream('');
            setEvaluationComments({});
            setSynthesisSteps([]);
            setStage2ThinkingByJudge({});
            setAgentProgress({});
            setStageProgress(0);
            setStage1Results([]);
            setStage2Results(null);
            setStage3Result(null);
            setAggregateRankings([]);
            stage2AnonMapRef.current = null;

            // 2.5 启动预设思考定时器
            // 使用特殊的 councilor_id "__preload__" 来存储预设 thinking
            startPreloadTimer((preload) => {
                setThinkingByCouncilor(prev => {
                    const preloadKey = '__preload__';
                    const existing = prev[preloadKey] || { status: 'thinking', steps: [] };
                    const newStep = {
                        bullet_id: preload.bullet_id,
                        title: preload.title,
                        detail: preload.detail,
                        t: null
                    };
                    return {
                        ...prev,
                        [preloadKey]: {
                            status: 'thinking',
                            steps: [...existing.steps, newStep]
                        }
                    };
                });
                // 自动展开预设 thinking
                setThinkingExpanded(prev => ({
                    ...prev,
                    '__preload__': true
                }));
            });

            // 3. 发送消息并订阅 SSE
            // Note: councilorIds here are passed to backend. The backend resolves them and sends back 'meta' event.
            await api.sendMessageStream(
                newConv.id,
                prompt,
                handleSSEEvent,
                councilorIds,
                true // enableThinking
            );
        } catch (error) {
            console.error("Failed to start session:", error);
            stopPreloadTimer(); // 确保出错时也停止预设定时器
            setIsLoading(false);
        }
    }, []);

    // === 事件处理函数 定义 ===

    const handleMeta = useCallback((event) => {
        setResolvedCouncilors(event.resolved_councilors || []);
        // 初始化进度
        const initialProgress = {};
        (event.resolved_councilors || []).forEach(c => {
            initialProgress[c.id] = 0;
            // 启动进度定时器 (平滑效果)
            startProgressTimer(c.id);
        });
        setAgentProgress(initialProgress);
        // 设置默认 Tab
        if (event.resolved_councilors?.length > 0) {
            setActiveTab(event.resolved_councilors[0].id);
        }
    }, []);

    const startProgressTimer = useCallback((id) => {
        // 清除已有定时器
        if (progressTimers.current[id]) {
            clearInterval(progressTimers.current[id]);
        }
        // 启动新定时器，每 100ms 增长 2%，最多到 90%
        progressTimers.current[id] = setInterval(() => {
            setAgentProgress(prev => {
                const current = prev[id] || 0;
                if (current >= 90) {
                    clearInterval(progressTimers.current[id]);
                    return prev;
                }
                return { ...prev, [id]: current + 2 };
            });
        }, 100);
    }, []);

    const handleStage1Start = useCallback(() => {
        setStage1AnswerStream({});
    }, []);

    const handleStage1Item = useCallback((item) => {
        // 停止该议员的进度定时器
        if (progressTimers.current[item.councilor_id]) {
            clearInterval(progressTimers.current[item.councilor_id]);
        }
        // 设置进度为 100%
        setAgentProgress(prev => ({ ...prev, [item.councilor_id]: 100 }));
        // 更新结果
        setStage1Results(prev => {
            const index = prev.findIndex(r => r.councilor_id === item.councilor_id);
            if (index >= 0) {
                const copy = [...prev];
                copy[index] = item;
                return copy;
            }
            return [...prev, item];
        });
    }, []);

    const handleStage1AnswerDelta = useCallback((event) => {
        const cid = event.councilor_id;
        if (!cid) return;
        setStage1AnswerStream(prev => ({
            ...prev,
            [cid]: (prev[cid] || "") + (event.delta || "")
        }));
    }, []);

    const handleStage1AnswerDone = useCallback((event) => {
        const cid = event.councilor_id;
        if (!cid) return;
        setThinkingByCouncilor(prev => {
            if (!prev[cid]) return prev;
            return {
                ...prev,
                [cid]: {
                    ...prev[cid],
                    status: 'done'
                }
            };
        });
    }, []);

    const handleStage3AnswerDelta = useCallback((event) => {
        setStage3AnswerStream(prev => prev + (event.delta || ""));
    }, []);

    const handleThinking = useCallback((event) => {
        // 检测到真实思考到达时，停止预设定时器
        const bulletId = event.bullet_id || '';
        if (!isPreloadBullet(bulletId)) {
            // 这是真实思考，停止预设定时器
            stopPreloadTimer();
        }

        if (event.stage === 'stage1') {
            const cid = event.councilor_id;
            if (!cid) return;

            const newBulletId = bulletId || `${cid}-${Date.now()}-${Math.random()}`;
            const title = event.title || event.delta || '';
            const detail = event.detail || null;
            const op = event.op || 'append';
            const t = typeof event.t === 'number' ? event.t : null;

            setThinkingByCouncilor(prev => {
                const existing = prev[cid] || { status: 'thinking', steps: [] };
                const steps = [...existing.steps];
                if (op === 'update') {
                    const index = steps.findIndex(s => s.bullet_id === newBulletId);
                    if (index >= 0) {
                        steps[index] = {
                            ...steps[index],
                            title: title || steps[index].title,
                            detail: detail !== null ? detail : steps[index].detail,
                            t: t ?? steps[index].t
                        };
                    } else {
                        steps.push({ bullet_id: newBulletId, title, detail, t });
                    }
                } else {
                    steps.push({ bullet_id: newBulletId, title, detail, t });
                }
                return {
                    ...prev,
                    [cid]: { status: 'thinking', steps }
                };
            });

            setThinkingExpanded(prev => (
                prev[cid] === undefined ? { ...prev, [cid]: true } : prev
            ));
        } else if (event.stage === 'stage2') {
            // Stage2 thinking 处理
            const judgeId = event.councilor_id;
            const targetAnonId = event.target_anon_id;
            if (!judgeId) return;

            // 通过 anon_map 映射到真实 councilor_id
            const anonMap = stage2AnonMapRef.current;
            let targetId = null;
            if (targetAnonId && anonMap) {
                targetId = anonMap[targetAnonId];
            }

            // 如果没有 targetId，将此 thinking 标记为 global（或忽略）
            if (!targetId) {
                console.warn('[handleThinking] Stage2 thinking 缺少有效的 target_anon_id:', event);
                return;
            }

            const newBulletId = bulletId || `${judgeId}-stage2-${Date.now()}-${Math.random()}`;
            const title = event.title || event.delta || '';
            const detail = event.detail || null;
            const op = event.op || 'append';
            const t = typeof event.t === 'number' ? event.t : null;

            setStage2ThinkingByJudge(prev => {
                const judgeEntry = prev[judgeId] || { status: 'thinking', stepsByTarget: {} };
                const targetSteps = judgeEntry.stepsByTarget[targetId] || [];
                const newSteps = [...targetSteps];

                if (op === 'update') {
                    const index = newSteps.findIndex(s => s.bullet_id === newBulletId);
                    if (index >= 0) {
                        newSteps[index] = {
                            ...newSteps[index],
                            title: title || newSteps[index].title,
                            detail: detail !== null ? detail : newSteps[index].detail,
                            t: t ?? newSteps[index].t
                        };
                    } else {
                        newSteps.push({ bullet_id: newBulletId, title, detail, t });
                    }
                } else {
                    newSteps.push({ bullet_id: newBulletId, title, detail, t });
                }

                return {
                    ...prev,
                    [judgeId]: {
                        status: 'thinking',
                        stepsByTarget: {
                            ...judgeEntry.stepsByTarget,
                            [targetId]: newSteps
                        }
                    }
                };
            });
        } else if (event.stage === 'stage3') {
            const step = {
                id: Date.now() + Math.random(),
                agentId: event.councilor_id,
                text: event.title || event.delta || '',
                time: `${event.t?.toFixed ? event.t.toFixed(1) : '0.0'}s`,
                status: 'complete'
            };
            setSynthesisSteps(prev => [...prev, step]);
        }
    }, []);

    const handleStage1Complete = useCallback((data) => {
        // Stage 1 Complete logic if needed
    }, []);

    const handleStage2Start = useCallback((event) => {
        setStage('stage2');
        setStage2Results([]);
        setEvaluationComments({});
        setAggregateRankings([]);
        setStage2ThinkingByJudge({}); // 重置 Stage2 thinking 状态
        stage2AnonMapRef.current = event?.anon_map || null;
        setStage2Skipped(!!event?.skipped);

        // 重置进度与 ETA，避免 Stage1 残留
        Object.values(progressTimers.current).forEach(clearInterval);
        progressTimers.current = {};
        setEtaByCouncilor({});
        const resetProgress = {};
        resolvedCouncilors.forEach(c => {
            resetProgress[c.id] = 0;
        });
        setAgentProgress(resetProgress);

        if (event.skipped) {
            // Stage 2 被跳过
        }
    }, [resolvedCouncilors]);

    const handleStage2Item = useCallback((item) => {
        setStage2Results(prev => {
            if (!prev || prev.length === 0) return [item];
            const key = item.judge_councilor_id || item.councilor_id || item.model;
            const index = prev.findIndex(r =>
                (r.judge_councilor_id || r.councilor_id || r.model) === key
            );
            if (index >= 0) {
                const copy = [...prev];
                copy[index] = { ...copy[index], ...item };
                return copy;
            }
            return [...prev, item];
        });

        const anonMap = stage2AnonMapRef.current;
        if (anonMap) {
            applyStage2ReviewComments(item, anonMap);
        }

        // 标记该 judge 的 thinking 状态为 'done'
        const judgeId = item.judge_councilor_id || item.councilor_id;
        if (judgeId) {
            setStage2ThinkingByJudge(prev => {
                if (!prev[judgeId]) return prev;
                return {
                    ...prev,
                    [judgeId]: {
                        ...prev[judgeId],
                        status: 'done'
                    }
                };
            });
        }
    }, [applyStage2ReviewComments]);

    const handleStage2Complete = useCallback((data) => {
        // data contains { reviews: [], anon_map: {} }
        const anonMap = data.anon_map || stage2AnonMapRef.current;
        if (anonMap) {
            stage2AnonMapRef.current = anonMap;
        }

        if (data.reviews) {
            setStage2Results(data.reviews);
            if (anonMap) {
                setEvaluationComments(buildEvaluationComments(data.reviews, anonMap));
            }
            const rankings = calculateAggregateRankings(data.reviews, anonMap);
            setAggregateRankings(rankings);
        }
    }, [buildEvaluationComments, calculateAggregateRankings]);

    const handleStage3Start = useCallback(() => {
        setStage('stage3');
        setStage3AnswerStream('');
    }, []);

    const handleStage3Complete = useCallback((data) => {
        setStage3Result(data);
        setConsensusUnlocked(true);
    }, []);

    const handleEtaUpdate = useCallback((event) => {
        const cid = event.councilor_id;
        const etaMs = event.eta_ms_remaining || 0;

        if (!cid) return;

        // 更新 ETA 状态
        setEtaByCouncilor(prev => ({
            ...prev,
            [cid]: etaMs
        }));

        // 停止旧的进度定时器（防止与 ETA 冲突）
        if (progressTimers.current[cid]) {
            clearInterval(progressTimers.current[cid]);
            delete progressTimers.current[cid];
        }

        if (event.reason === 'done') {
            // 完成：设置为 100%
            setAgentProgress(prev => ({ ...prev, [cid]: 100 }));
        } else if (event.reason === 'queue_start' && etaMs > 0) {
            // 基于 ETA 启动平滑进度定时器（Stage1/Stage2 通用）
            // 进度从 0% 涨到 90%，用时 = etaMs * 0.9
            const targetProgress = 90;
            const updateInterval = 100; // 100ms 更新一次
            const totalSteps = (etaMs * 0.9) / updateInterval;
            const progressPerStep = totalSteps > 0 ? targetProgress / totalSteps : 2;

            setAgentProgress(prev => ({ ...prev, [cid]: 0 }));

            progressTimers.current[cid] = setInterval(() => {
                setAgentProgress(prev => {
                    const current = prev[cid] || 0;
                    if (current >= targetProgress) {
                        clearInterval(progressTimers.current[cid]);
                        return prev;
                    }
                    return { ...prev, [cid]: Math.min(current + progressPerStep, targetProgress) };
                });
            }, updateInterval);
        }
    }, []);

    const stageEtaMs = useMemo(() => {
        const values = Object.values(etaByCouncilor).filter(v => typeof v === 'number' && v > 0);
        return values.length > 0 ? Math.max(...values) : 0;
    }, [etaByCouncilor]);

    // === SSE 事件分发 ===
    const handleSSEEvent = useCallback((eventType, event) => {
        switch (eventType) {
            case 'meta':
                handleMeta(event);
                break;
            case 'stage1_start':
                handleStage1Start();
                break;
            case 'stage1_item':
                handleStage1Item(event.data);
                break;
            case 'thinking':
                handleThinking(event);
                break;
            case 'eta_update':
                handleEtaUpdate(event);
                break;
            case 'stage1_answer_delta':
                handleStage1AnswerDelta(event);
                break;
            case 'stage1_answer_done':
                handleStage1AnswerDone(event);
                break;
            case 'stage3_answer_delta':
                handleStage3AnswerDelta(event);
                break;
            case 'stage1_complete':
                handleStage1Complete(event.data);
                break;
            case 'stage2_start':
                handleStage2Start(event);
                break;
            case 'stage2_item':
                handleStage2Item(event.data);
                break;
            case 'stage2_complete':
                handleStage2Complete(event.data);
                break;
            case 'stage3_start':
                handleStage3Start();
                break;
            case 'stage3_complete':
                handleStage3Complete(event.data);
                break;
            case 'complete':
                stopPreloadTimer(); // 停止预设定时器
                // 清理预设 thinking（不保存到历史）
                setThinkingByCouncilor(prev => {
                    const { __preload__, ...rest } = prev;
                    return rest;
                });
                setIsLoading(false);
                break;
            case 'error':
                stopPreloadTimer(); // 停止预设定时器
                console.error('SSE Error:', event.message);
                setIsLoading(false);
                break;
            default:
                break;
        }
    }, [
        handleMeta,
        handleStage1Start,
        handleStage1Item,
        handleThinking,
        handleEtaUpdate,
        handleStage1AnswerDelta,
        handleStage1AnswerDone,
        handleStage3AnswerDelta,
        handleStage1Complete,
        handleStage2Start,
        handleStage2Item,
        handleStage2Complete,
        handleStage3Start,
        handleStage3Complete
    ]);


    const viewConsensus = useCallback(() => {
        setActiveTab('final');
        setHasViewedConsensus(true);
    }, []);

    const toggleThinkingExpanded = useCallback((cid) => {
        if (!cid) return;
        setThinkingExpanded(prev => ({
            ...prev,
            [cid]: !(prev[cid] ?? true)
        }));
    }, []);

    const reset = useCallback(() => {
        stopPreloadTimer(); // 停止预设定时器
        setStage('idle');
        setConversation(null);
        setResolvedCouncilors([]);
        setStage1Results([]);
        setStage2Results(null);
        setStage3Result(null);
        setAgentProgress({});
        setStageProgress(0);
        setThinkingByCouncilor({});
        setThinkingExpanded({});
        setStage1AnswerStream({});
        setStage3AnswerStream('');
        setEvaluationComments({});
        setSynthesisSteps({});
        setStage2ThinkingByJudge({});
        setStage2Skipped(false);
        setConsensusUnlocked(false);
        setHasViewedConsensus(false);
        setAggregateRankings([]);
        stage2AnonMapRef.current = null;
        // 清理定时器
        Object.values(progressTimers.current).forEach(clearInterval);
        progressTimers.current = {};
    }, []);

    // === 清理 ===
    useEffect(() => {
        return () => {
            Object.values(progressTimers.current).forEach(clearInterval);
        };
    }, []);

    return {
        // 状态
        stage,
        isLoading,
        conversation,
        resolvedCouncilors,
        stage1Results,
        stage2Results,
        stage3Result,
        agentProgress,
        stageProgress,
        etaByCouncilor, // ETA 状态
        stageEtaMs,
        stage2Skipped,
        thinkingByCouncilor,
        thinkingExpanded,
        stage1AnswerStream,
        stage3AnswerStream,
        evaluationComments,
        synthesisSteps,
        activeTab,
        setActiveTab, // Added setter
        consensusUnlocked,
        hasViewedConsensus,
        aggregateRankings,
        stage2ThinkingByJudge, // Stage2 thinking state
        stage2AnonMap: stage2AnonMapRef.current, // Stage2 anon map

        // 操作
        startSession,
        loadSession,
        viewConsensus,
        toggleThinkingExpanded,
        reset,
    };
}
