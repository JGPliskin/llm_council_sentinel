"""
ConcurrencyTracker: per-model 并发追踪模块
职责: 统计每个模型的 inflight (执行中) 和 queued (等待) 数量，用于队列等待估算
"""

import asyncio
from typing import Dict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ConcurrencyTracker:
    """Per-model 并发追踪器"""
    
    def __init__(self):
        self._inflight: Dict[str, int] = defaultdict(int)  # 当前执行数
        self._queued: Dict[str, int] = defaultdict(int)    # 等待数
        self._lock = asyncio.Lock()
    
    async def acquire(self, model: str):
        """
        进入队列 (在获取 semaphore 之前调用)
        
        Args:
            model: 模型 ID
        """
        async with self._lock:
            self._queued[model] += 1
            logger.debug(f"[ConcurrencyTracker] {model}: queued={self._queued[model]}, inflight={self._inflight[model]}")
    
    async def start(self, model: str):
        """
        开始执行 (在获取 semaphore 之后调用)
        
        Args:
            model: 模型 ID
        """
        async with self._lock:
            self._queued[model] = max(0, self._queued[model] - 1)  # 从队列移出
            self._inflight[model] += 1
            logger.debug(f"[ConcurrencyTracker] {model}: queued={self._queued[model]}, inflight={self._inflight[model]}")
    
    async def release(self, model: str):
        """
        完成执行 (在释放 semaphore 时调用)
        
        Args:
            model: 模型 ID
        """
        async with self._lock:
            if self._inflight[model] > 0:
                self._inflight[model] -= 1
            elif self._queued[model] > 0:
                # 任务在进入执行前取消，回收 queued 计数
                self._queued[model] -= 1
            logger.debug(f"[ConcurrencyTracker] {model}: queued={self._queued[model]}, inflight={self._inflight[model]}")
    
    def get_queued(self, model: str) -> int:
        """获取指定模型的队列等待数"""
        return self._queued.get(model, 0)
    
    def get_inflight(self, model: str) -> int:
        """获取指定模型的执行中数量"""
        return self._inflight.get(model, 0)
    
    def get_stats(self, model: str) -> Dict[str, int]:
        """获取指定模型的完整统计信息"""
        return {
            "queued": self.get_queued(model),
            "inflight": self.get_inflight(model),
        }


# 全局单例
concurrency_tracker = ConcurrencyTracker()
