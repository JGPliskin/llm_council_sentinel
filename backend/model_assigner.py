"""
模型分配引擎 - 固定模型分配功能

创建对话时为每个议员和主席分配固定模型，整个对话生命周期内不变。

设计原则:
1. 固定为主：创建即固定，Stage1/2/3 一致
2. 健康优先：healthy 优先，unknown 仅在不足时补位
3. 候选约束：不越权分配模型
4. 尽量不重复：优先分配未使用模型，耗尽后允许重复
"""

import sys
import os
import hashlib
import random
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from health import health_manager
from config import COUNCILOR_MAP, CHAIRMAN


class CandidateIntersectionEmptyError(Exception):
    """候选池与可用模型交集为空"""
    def __init__(self, councilor_id: str, candidates: List[str]):
        self.councilor_id = councilor_id
        self.candidates = candidates
        super().__init__(
            f"议员 {councilor_id} 的候选模型 {candidates} 与可用模型无交集，请重新选择议员"
        )


def _get_ranked_models_by_ttft() -> Tuple[List[str], List[str]]:
    """
    获取按 TTFT 排序的模型列表。
    
    Returns:
        (healthy_models, unknown_models) - 分别按 TTFT 排序
    """
    healthy_models = []
    unknown_models = []
    
    # 遍历所有已知模型
    for model_id, record in health_manager._records.items():
        status = record.get_effective_status()
        ttft = record.get_effective_ttft()
        
        if status == "healthy":
            healthy_models.append((model_id, ttft))
        elif status == "unknown":
            unknown_models.append((model_id, ttft))
        # cooldown 和其他状态不参与分配
    
    # 排序规则: TTFT 升序, None 排最后
    def sort_key(item):
        mid, ttft = item
        if ttft is not None:
            return (0, ttft)
        return (1, 0)
    
    healthy_models.sort(key=sort_key)
    unknown_models.sort(key=sort_key)
    
    return (
        [m[0] for m in healthy_models],
        [m[0] for m in unknown_models]
    )


def _generate_seed() -> str:
    """生成分配种子，用于复现与排查"""
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    short_uuid = uuid.uuid4().hex[:4]
    return f"{now}-{short_uuid}"


def _seed_to_int(seed: str) -> int:
    """稳定哈希，避免 Python hash 随机化导致不可复现"""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest, 16)


def assign_models_for_councilors(
    councilor_ids: List[str],
    councilor_map: Optional[Dict[str, Any]] = None,
    seed: Optional[str] = None
) -> Tuple[Dict[str, str], str, str]:
    """
    为议员分配模型。
    
    Args:
        councilor_ids: 议员 ID 列表
        councilor_map: 议员配置映射 (可选，默认使用全局 COUNCILOR_MAP)
        seed: 分配种子 (可选，用于可复现随机)
    
    Returns:
        (model_assignments, assignment_seed, assignment_strategy)
        - model_assignments: {"councilor_id": "model_id", ...}
        - assignment_seed: "2026-01-02T10:22:31Z-3f9a"
        - assignment_strategy: "healthy_first" 或 "healthy_first_then_unknown"
    
    Raises:
        CandidateIntersectionEmptyError: 候选池与可用模型无交集
    """
    if councilor_map is None:
        councilor_map = COUNCILOR_MAP
    
    # 1. 生成可复现 RNG
    if not seed:
        seed = _generate_seed()
    rng = random.Random(_seed_to_int(seed))

    # 2. 获取排序后的模型列表（先排序，再用 seed 打乱）
    ranked_healthy, ranked_unknown = _get_ranked_models_by_ttft()
    shuffled_healthy = ranked_healthy[:]
    shuffled_unknown = ranked_unknown[:]
    rng.shuffle(shuffled_healthy)
    rng.shuffle(shuffled_unknown)
    
    assignments: Dict[str, str] = {}
    used: set = set()
    used_unknown = False
    
    # 3. 遍历议员，分配模型
    for cid in councilor_ids:
        councilor = councilor_map.get(cid)
        if not councilor:
            continue
        
        # 获取候选池
        candidates = councilor.get("model_candidates", [])
        if not candidates and councilor.get("model"):
            candidates = [councilor["model"]]
        
        # 4. 在候选池内筛选可用模型
        # 先尝试 healthy
        available_healthy = [m for m in shuffled_healthy if m in candidates]
        
        # 尝试选未使用的
        pick = None
        for m in available_healthy:
            if m not in used:
                pick = m
                break
        
        # 如果 healthy 都已使用，允许重复
        if pick is None and available_healthy:
            pick = available_healthy[0]
        
        # 如果 healthy 不足，尝试 unknown
        if pick is None:
            available_unknown = [m for m in shuffled_unknown if m in candidates]
            for m in available_unknown:
                if m not in used:
                    pick = m
                    used_unknown = True
                    break
            
            if pick is None and available_unknown:
                pick = available_unknown[0]
                used_unknown = True
        
        # 4. 如果仍无可用模型，报错
        if pick is None:
            raise CandidateIntersectionEmptyError(cid, candidates)
        
        assignments[cid] = pick
        used.add(pick)
    
    # 5. 生成 strategy
    strategy = "healthy_first_then_unknown" if used_unknown else "healthy_first"
    
    return assignments, seed, strategy


def assign_chairman_model(
    chairman: Optional[Dict[str, Any]] = None
) -> str:
    """
    为主席选择最快的模型。
    
    Args:
        chairman: 主席配置 (可选，默认使用全局 CHAIRMAN)
    
    Returns:
        选中的模型 ID
    
    Raises:
        CandidateIntersectionEmptyError: 候选池与可用模型无交集
    """
    if chairman is None:
        chairman = CHAIRMAN
    
    candidates = chairman.get("model_candidates", [])
    if not candidates and chairman.get("model"):
        candidates = [chairman["model"]]
    
    ranked_healthy, ranked_unknown = _get_ranked_models_by_ttft()
    
    # 优先选 healthy 中最快的
    for m in ranked_healthy:
        if m in candidates:
            return m
    
    # 其次选 unknown 中最快的
    for m in ranked_unknown:
        if m in candidates:
            return m
    
    raise CandidateIntersectionEmptyError("chairman", candidates)


def get_or_create_assignments(
    conversation: Dict[str, Any],
    councilor_ids: List[str],
    councilor_map: Optional[Dict[str, Any]] = None,
    chairman: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, str], str, str, bool]:
    """
    获取或创建模型分配。
    
    如果对话已有 model_assignments (schema_version >= 3)，直接返回。
    否则执行补分配。
    
    Args:
        conversation: 对话对象
        councilor_ids: 议员 ID 列表
        councilor_map: 议员配置映射
        chairman: 主席配置
    
    Returns:
        (model_assignments, seed, strategy, is_new_assignment)
        - is_new_assignment: True 表示执行了新分配，需要持久化
    """
    existing = conversation.get("model_assignments")
    schema_version = conversation.get("schema_version", 1)
    
    # 已有分配且版本正确，直接返回
    if existing and schema_version >= 3:
        return (
            existing,
            conversation.get("assignment_seed", ""),
            conversation.get("assignment_strategy", "unknown"),
            False
        )
    
    # 旧对话 (schema_version < 3) 且没有 model_assignments: 不升级
    # 根据需求 REQ-10: 旧对话不升级
    if schema_version < 3 and not existing:
        # 返回空分配，让调用方使用旧逻辑
        return {}, "", "", False
    
    # 执行补分配
    assignments, seed, strategy = assign_models_for_councilors(
        councilor_ids,
        councilor_map,
        seed=conversation.get("assignment_seed")
    )
    
    # 为主席分配
    chairman_model = assign_chairman_model(chairman)
    assignments["chairman"] = chairman_model
    
    return assignments, seed, strategy, True
