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
