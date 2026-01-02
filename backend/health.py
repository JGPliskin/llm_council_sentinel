import asyncio
import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
import logging

from config import (
    HEALTH_TTL_SECONDS,
    REFRESH_COOLDOWN_SECONDS,
    FAILURE_THRESHOLD,
    BACKOFF_SECONDS,
    PROBE_TIMEOUT_SECONDS,
    HEALTH_PROBE_CONCURRENCY,
    HARD_FAILURE_CODES,
    HARD_FAILURE_PATTERNS
)

# Use existing query logic or basic wrapper (we will inject dependency or import carefully)
# For probe, we use openrouter directly or injected function to avoid circular imports.
# Ideally, we inject a "probe_function" into HealthManager.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HealthRecord:
    status: str = "unknown"  # unknown, healthy, unhealthy, cooldown
    last_checked: Optional[datetime.datetime] = None
    last_success: Optional[datetime.datetime] = None
    consecutive_failures: int = 0
    cooldown_until: Optional[datetime.datetime] = None
    error: Optional[str] = None
    source: Optional[str] = None  # probe, runtime
    
    # TTFT 统计字段 (需求3)
    last_ttft_ms: Optional[int] = None  # 最近一次探测 TTFT
    ema_ttft_ms: Optional[float] = None  # 平滑 TTFT (EMA alpha=0.3)
    p50_ttft_ms: Optional[float] = None  # 中位数 TTFT (样本数>=5时有效)
    ttft_samples: List[int] = field(default_factory=list)  # 最近5次样本
    ttft_updated_at: Optional[datetime.datetime] = None  # TTFT 更新时间
    last_emergency_probe_at: Optional[datetime.datetime] = None  # 紧急探测时间 (per-model)

    # TTFT 配置常量
    TTFT_EMA_ALPHA: float = 0.3
    TTFT_MAX_SAMPLES: int = 5
    TTFT_EXPIRE_HOURS: int = 6

    def is_stale(self) -> bool:
        if not self.last_checked:
            return True
        elapsed = (datetime.datetime.now() - self.last_checked).total_seconds()
        return elapsed > HEALTH_TTL_SECONDS

    def get_effective_status(self) -> str:
        """Return status respecting cooldown."""
        if self.status == "cooldown":
            if self.cooldown_until and datetime.datetime.now() >= self.cooldown_until:
                # Cooldown expired, tentatively switch to unknown to allow retry
                # But in our logic, 'unknown' allows retry.
                # Strictly speaking, we should perhaps keep it 'cooldown' until next check proves otherwise?
                # User spec: "stale=true" but status could remain unknown.
                # Let's return "unknown" so it can be picked up.
                return "unknown" 
        return self.status

    def update_ttft(self, ttft_ms: int) -> None:
        """更新 TTFT 统计数据"""
        now = datetime.datetime.now()
        self.last_ttft_ms = ttft_ms
        self.ttft_updated_at = now
        
        # 更新 EMA
        if self.ema_ttft_ms is None:
            self.ema_ttft_ms = float(ttft_ms)
        else:
            self.ema_ttft_ms = self.TTFT_EMA_ALPHA * ttft_ms + (1 - self.TTFT_EMA_ALPHA) * self.ema_ttft_ms
        
        # 更新样本列表 (最多保留5个)
        self.ttft_samples.append(ttft_ms)
        if len(self.ttft_samples) > self.TTFT_MAX_SAMPLES:
            self.ttft_samples = self.ttft_samples[-self.TTFT_MAX_SAMPLES:]
        
        # 计算 p50 (仅当样本数>=5)
        if len(self.ttft_samples) >= self.TTFT_MAX_SAMPLES:
            sorted_samples = sorted(self.ttft_samples)
            self.p50_ttft_ms = float(sorted_samples[len(sorted_samples) // 2])
        else:
            self.p50_ttft_ms = None

    def get_effective_ttft(self) -> Optional[float]:
        """获取用于排序的有效 TTFT (按优先级: p50 > ema > last)"""
        # 检查是否过期
        if self.ttft_updated_at:
            elapsed_hours = (datetime.datetime.now() - self.ttft_updated_at).total_seconds() / 3600
            if elapsed_hours > self.TTFT_EXPIRE_HOURS:
                return None  # 过期，视为缺失
        else:
            return None  # 从未更新过
        
        # 按优先级返回
        if self.p50_ttft_ms is not None and len(self.ttft_samples) >= self.TTFT_MAX_SAMPLES:
            return self.p50_ttft_ms
        if self.ema_ttft_ms is not None:
            return self.ema_ttft_ms
        if self.last_ttft_ms is not None:
            return float(self.last_ttft_ms)
        return None

    def is_slow(self, current_ttft_ms: int, threshold_ms: int = 5000, multiplier: int = 3) -> bool:
        """检查本次 TTFT 是否异常慢"""
        # 1. 绝对阈值
        if current_ttft_ms >= threshold_ms:
            return True
        
        # 2. 相对阈值 (EMA * multiplier)
        if self.ema_ttft_ms and current_ttft_ms >= self.ema_ttft_ms * multiplier:
            return True
            
        return False

    def can_emergency_probe(self, cooldown_minutes: int = 10) -> bool:
        """检查是否可以进行紧急探测 (per-model 冷却)"""
        if self.last_emergency_probe_at is None:
            return True
        elapsed = (datetime.datetime.now() - self.last_emergency_probe_at).total_seconds()
        return elapsed >= cooldown_minutes * 60

    def mark_emergency_probed(self) -> None:
        """标记紧急探测时间"""
        self.last_emergency_probe_at = datetime.datetime.now()

class HealthManager:
    def __init__(self):
        self._records: Dict[str, HealthRecord] = {}
        self._lock = asyncio.Lock()
        self._pending_probes: Set[str] = set()
        self._last_refresh_all: Optional[datetime.datetime] = None
        self._probe_semaphore = asyncio.Semaphore(HEALTH_PROBE_CONCURRENCY)

    def get_status(self, model: str) -> Dict:
        """Get public status dict for a model."""
        record = self._records.get(model)
        if not record:
            record = HealthRecord()
            self._records[model] = record

        effective_status = record.get_effective_status()
        
        # Check cooldown expiration logic dynamically
        is_cooldown = effective_status == "cooldown"
        if is_cooldown and record.cooldown_until and datetime.datetime.now() >= record.cooldown_until:
             effective_status = "unknown"
             is_cooldown = False

        return {
            "health_status": effective_status,
            "healthy": effective_status == "healthy", # Legacy compat
            "health_error": record.error,
            "health_checked_at": record.last_checked.isoformat() if record.last_checked else None,
            "last_success_at": record.last_success.isoformat() if record.last_success else None,
            "consecutive_failures": record.consecutive_failures,
            "cooldown_until": record.cooldown_until.isoformat() if record.cooldown_until else None,
            "stale": record.is_stale(),
            "source": record.source
        }

    def update_status(self, model: str, success: bool, error_msg: Optional[str] = None, 
                      status_code: Optional[int] = None, source: str = "runtime"):
        """Update health status based on runtime or probe result."""
        if model not in self._records:
            self._records[model] = HealthRecord()
        record = self._records[model]
        now = datetime.datetime.now()

        if success:
            record.status = "healthy"
            record.last_checked = now
            record.last_success = now
            record.consecutive_failures = 0
            record.cooldown_until = None
            record.error = None
            record.source = source
        else:
            record.last_checked = now # Check happened, even if failed
            record.source = source
            record.error = error_msg
            
            # Classification
            is_hard_fail = False
            
            # Check Status Codes
            if status_code and status_code in HARD_FAILURE_CODES:
                is_hard_fail = True
            
            # Check Patterns
            if not is_hard_fail and error_msg:
                lower_msg = error_msg.lower()
                for pattern in HARD_FAILURE_PATTERNS:
                    if pattern in lower_msg:
                        is_hard_fail = True
                        break
            
            if is_hard_fail:
                record.status = "unhealthy"
                # Hard failures doesn't necessarily need backoff, just manual refresh. 
                # But spec says: "Hard: unhealthy".
            else:
                # Transient
                record.consecutive_failures += 1
                if record.status in ("unknown", "healthy"):
                    if record.consecutive_failures >= FAILURE_THRESHOLD:
                        record.status = "cooldown"
                        # Calculate backoff
                        # index 0 for 1st cooldown (failures=threshold)
                        # failures=2 -> index 0
                        idx = min(record.consecutive_failures - FAILURE_THRESHOLD, len(BACKOFF_SECONDS) - 1)
                        idx = max(0, idx) # Safety
                        backoff = BACKOFF_SECONDS[idx]
                        record.cooldown_until = now + datetime.timedelta(seconds=backoff)
                    else:
                        # Below threshold, keep current or mark unknown?
                        # User spec: "Stay unknown or healthy->unknown"
                        # We will use "unknown" to signal it's shaky but not dead
                        record.status = "unknown"

    def is_ttft_slow(self, model: str, ttft_ms: int, threshold: int = 5000, multiplier: int = 3) -> bool:
        """检查指定模型本次 TTFT 是否过慢 (需要触发紧急探测)"""
        record = self._records.get(model)
        if not record:
            return False
        return record.is_slow(ttft_ms, threshold, multiplier)

    async def trigger_emergency_refresh(self, models: List[str], probe_func, cooldown_minutes: int = 10):
        """
        触发紧急探测 (针对候选集)
        - 仅探测满足冷却条件的模型
        - 检查是否正在探测或最近已检查过 (避免资源浪费)
        - 不阻塞，Fire-and-forget 模式 (由调用方 create_task)
        """
        tasks = []
        models_to_probe = []
        now = datetime.datetime.now()

        # 获取正在进行的探测快照，避免重复触发
        async with self._lock:
            pending_snapshot = set(self._pending_probes)

        for mid in models:
            # 1. 检查是否正在探测中
            if mid in pending_snapshot:
                continue

            record = self._records.get(mid)
            if not record:
                record = HealthRecord()
                self._records[mid] = record
            
            # 2. 检查是否最近已检查过 (常规检查或探测)
            # 如果最近已更新状态，无需再次紧急探测
            if record.last_checked and \
               (now - record.last_checked).total_seconds() < REFRESH_COOLDOWN_SECONDS:
                continue

            # 3. 检查紧急探测冷却 (防止对同一模型频繁发起紧急探测)
            if record.can_emergency_probe(cooldown_minutes):
                record.mark_emergency_probed()
                tasks.append(self.probe_model(mid, probe_func))
                models_to_probe.append(mid)
        
        if tasks:
            logger.warning(f"Triggering emergency probe for {len(tasks)} models: {models_to_probe}")
            # Run concurrently
            await asyncio.gather(*tasks)

    async def probe_model(self, model: str, probe_func):
        """Run a single probe if not already running."""
        async with self._lock:
            if model in self._pending_probes:
                return # In-flight dedup
            self._pending_probes.add(model)
        
        try:
            async with self._probe_semaphore:
                # User config check (don't probe if in hard timeout? No, forced probe should allowed)
                # But typically we respect cooldown unless forced. 
                # This function implies forced or scheduled probe.
                
                # Use minimal prompt
                success, error, code = await probe_func(model)
                self.update_status(model, success, error, code, source="probe")
                
        finally:
            async with self._lock:
                self._pending_probes.remove(model)

    async def refresh_all(self, models: List[str], probe_func, force: bool = False) -> Dict:
        """Trigger refresh for all models."""
        now = datetime.datetime.now()
        
        # Global Rate Limit
        if not force and self._last_refresh_all:
            elapsed = (now - self._last_refresh_all).total_seconds()
            if elapsed < REFRESH_COOLDOWN_SECONDS:
                 return {
                     "refresh_skipped": True,
                     "next_refresh_allowed_at": (self._last_refresh_all + datetime.timedelta(seconds=REFRESH_COOLDOWN_SECONDS)).isoformat(),
                     "server_time": now.isoformat()
                 }

        self._last_refresh_all = now
        
        tasks = []
        for model in models:
            tasks.append(self.probe_model(model, probe_func))
            
        # We don't await detailed results, we fire and forget or await completion?
        # User API expects results. We should await.
        await asyncio.gather(*tasks)
        
        return {
            "refresh_skipped": False,
             "server_time": now.isoformat()
        }

# Global Instance
health_manager = HealthManager()
