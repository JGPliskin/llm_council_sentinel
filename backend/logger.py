"""请求级计时日志模块"""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 日志目录
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 配置请求计时日志器
request_logger = logging.getLogger("request_timing")
request_logger.setLevel(logging.INFO)
request_logger.propagate = False  # 避免重复输出到 root logger

# 滚动文件处理器：10MB × 5 个备份
handler = RotatingFileHandler(
    LOG_DIR / "request.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(message)s"))
request_logger.addHandler(handler)

# 东八区时区
TZ_SHANGHAI = timezone(timedelta(hours=8))


def log_request_timing(
    stage: str,
    councilor_id: str,
    councilor_name: str,
    model: str,
    timing: dict,
    status: str = "ok",
    error: str = None,
    routing: dict = None
):
    """
    输出 JSON 格式的请求计时日志
    
    Args:
        stage: 阶段名称 (stage1, stage2, stage3)
        councilor_id: Councilor ID
        councilor_name: Councilor 名称
        model: 使用的模型 ID
        timing: 计时数据字典，包含：
            - total_ms: 总耗时
            - model_select_ms: 模型选择耗时
            - ttft_ms: 首 Token 延迟
            - generation_ms: 生成耗时
        status: 状态 (ok, failed)
        error: 错误信息 (可选)
        routing: 选路决策信息 (可选)，包含：
            - mode: 'auto_speed' | 'config_order'
            - candidates_ttft: {model_id: ttft_ms | null}
            - selected: 选中的模型
            - reason: 选路原因
    """
    now = datetime.now(TZ_SHANGHAI)
    
    data = {
        "timestamp": now.isoformat(),
        "stage": stage,
        "councilor_id": councilor_id,
        "councilor_name": councilor_name,
        "model": model,
        "timing": timing,
        "status": status,
    }
    
    if error:
        data["error"] = error
    
    if routing:
        data["routing"] = routing
    
    request_logger.info(json.dumps(data, ensure_ascii=False))
