"""
RuntimeStats: 运行时性能统计模块 (按 model + stage 分桶)
职责: 记录和计算 TTFT、Generation、Total 的 EMA 统计数据，用于 ETA 估算
"""

import datetime
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class RuntimeStatsRecord:
    """单个 (model, stage) 组合的运行时统计记录"""
    
    # EMA 统计字段
    ema_ttft_ms: Optional[float] = None          # 首 token 时间 EMA
    ema_generation_ms: Optional[float] = None    # 生成时间 EMA
    ema_total_ms: Optional[float] = None         # 总时间 EMA
    
    # 元数据
    sample_count: int = 0                        # 样本数量
    last_updated_at: Optional[datetime.datetime] = None  # 最后更新时间
    
    # EMA 配置常量
    EMA_ALPHA: float = 0.3                       # EMA 平滑系数
    EXPIRE_HOURS: int = 6                        # 统计过期时间 (小时)


class RuntimeStatsManager:
    """运行时性能统计管理器"""
    
    def __init__(self):
        # 存储格式: {(model, stage): RuntimeStatsRecord}
        self._stats: Dict[Tuple[str, str], RuntimeStatsRecord] = {}
        self._lock = asyncio.Lock()
    
    def _is_valid_sample(self, ttft_ms: Optional[int], total_ms: int) -> bool:
        """
        验证样本数据是否有效
        
        过滤规则 (任一命中则丢弃):
        - ttft_ms 为 None
        - total_ms <= 0
        - ttft_ms > total_ms
        """
        if ttft_ms is None:
            logger.warning(f"Invalid sample: ttft_ms is None")
            return False
        
        if total_ms <= 0:
            logger.warning(f"Invalid sample: total_ms={total_ms} <= 0")
            return False
        
        if ttft_ms > total_ms:
            logger.warning(f"Invalid sample: ttft_ms={ttft_ms} > total_ms={total_ms}")
            return False
        
        return True
    
    async def update_stats(
        self, 
        model: str, 
        stage: str,  # "stage1" / "stage2" / "stage3"
        ttft_ms: Optional[int],
        total_ms: int
    ) -> None:
        """
        更新运行时统计数据
        
        Args:
            model: 模型 ID
            stage: 阶段标识
            ttft_ms: 首 token 时间 (ms)
            total_ms: 总耗时 (ms)
        """
        # 数据校验
        if not self._is_valid_sample(ttft_ms, total_ms):
            logger.warning(f"Discarding invalid sample for {model}@{stage}")
            return
        
        generation_ms = total_ms - ttft_ms
        
        async with self._lock:
            key = (model, stage)
            
            if key not in self._stats:
                self._stats[key] = RuntimeStatsRecord()
            
            record = self._stats[key]
            now = datetime.datetime.now()
            
            # 更新 EMA
            alpha = record.EMA_ALPHA
            
            if record.ema_ttft_ms is None:
                # 首次记录，直接使用当前值
                record.ema_ttft_ms = float(ttft_ms)
                record.ema_generation_ms = float(generation_ms)
                record.ema_total_ms = float(total_ms)
            else:
                # EMA 更新
                record.ema_ttft_ms = alpha * ttft_ms + (1 - alpha) * record.ema_ttft_ms
                record.ema_generation_ms = alpha * generation_ms + (1 - alpha) * record.ema_generation_ms
                record.ema_total_ms = alpha * total_ms + (1 - alpha) * record.ema_total_ms
            
            # 更新元数据
            record.sample_count += 1
            record.last_updated_at = now
            
            logger.debug(
                f"[RuntimeStats] Updated {model}@{stage}: "
                f"ttft={record.ema_ttft_ms:.0f}ms, "
                f"gen={record.ema_generation_ms:.0f}ms, "
                f"total={record.ema_total_ms:.0f}ms, "
                f"samples={record.sample_count}"
            )
    
    def get_stats(
        self, 
        model: str, 
        stage: str
    ) -> Optional[RuntimeStatsRecord]:
        """获取指定 (model, stage) 的统计记录"""
        key = (model, stage)
        record = self._stats.get(key)
        
        if not record:
            return None
        
        # 检查是否过期
        if record.last_updated_at:
            elapsed_hours = (datetime.datetime.now() - record.last_updated_at).total_seconds() / 3600
            if elapsed_hours > record.EXPIRE_HOURS:
                logger.debug(f"[RuntimeStats] Stats for {model}@{stage} expired ({elapsed_hours:.1f}h old)")
                return None
        
        return record
    
    def get_effective_ttft(self, model: str, stage: str) -> Optional[float]:
        """获取有效的 TTFT 估算值 (用于 ETA 计算)"""
        record = self.get_stats(model, stage)
        return record.ema_ttft_ms if record else None
    
    def get_effective_generation(self, model: str, stage: str) -> Optional[float]:
        """获取有效的 Generation 估算值 (用于 ETA 计算)"""
        record = self.get_stats(model, stage)
        return record.ema_generation_ms if record else None
    
    def get_effective_total(self, model: str, stage: str) -> Optional[float]:
        """获取有效的 Total 估算值 (用于队列等待估算)"""
        record = self.get_stats(model, stage)
        return record.ema_total_ms if record else None
    
    def has_enough_samples(self, model: str, stage: str, min_samples: int = 3) -> bool:
        """检查样本数是否足够 (用于判断冷启动)"""
        record = self.get_stats(model, stage)
        return record.sample_count >= min_samples if record else False


# 全局单例
runtime_stats_manager = RuntimeStatsManager()
