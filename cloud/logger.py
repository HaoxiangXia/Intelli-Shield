import logging
import json
import os
from datetime import datetime

try:
    from backend.repositories import database as repo
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.repositories import database as repo

# =========================
# 日志存储配置
# =========================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "ops.log")
READABLE_LOG_FILE = os.path.join(LOG_DIR, "readable.log")

# =========================
# logger 对象
# =========================
logger = logging.getLogger("forklift")
logger.setLevel(logging.DEBUG)  # DEBUG 级别可在开发时打开
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def append_readable_log(ts, level, event, category, module, message, device_id=None,
                        request_id=None, sid=None, topic=None, error=None, extra=None):
    """追加一份便于直接阅读的纯文本日志。"""
    parts = [
        f"[{ts}]",
        level,
        f"{category}/{module}",
        event,
    ]
    if device_id:
        parts.append(f"device={device_id}")
    if request_id:
        parts.append(f"request_id={request_id}")
    if sid:
        parts.append(f"sid={sid}")
    if topic:
        parts.append(f"topic={topic}")

    line = " | ".join(parts) + f" | {message}"
    if error:
        line += f" | error={error}"
    if extra:
        line += f" | extra={json.dumps(extra, ensure_ascii=False, sort_keys=True)}"

    with open(READABLE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def save_log(ts, level, event, category, device_id, message, extra=None):
    """兼容旧调用：日志持久化委托给 repository 层。"""
    repo.save_log(ts, level, event, category, device_id, message, extra)

def get_latest_biz_logs(limit=100):
    payload = repo.get_logs_by_page(1, limit, category="biz")
    return payload["logs"]

def get_logs_by_page(page=1, page_size=20, level=None, device_id=None, category=None):
    return repo.get_logs_by_page(page, page_size, level, device_id, category)


# 兼容旧接口别名
def get_biz_logs_by_page(page=1, page_size=20, level=None, device_id=None):
    """兼容旧接口：默认查询 biz 日志"""
    return repo.get_biz_logs_by_page(page, page_size, level, device_id)

# =========================
# 统一日志接口
# =========================
def log_event(level, event, category, module, message, device_id=None, request_id=None,
              sid=None, topic=None, error=None, extra=None):
    ts = datetime.utcnow().isoformat() + "Z"
    log_data = {
        "ts": ts,
        "level": level,
        "event": event,
        "category": category,
        "module": module,
        "message": message
    }
    if device_id:
        log_data["device_id"] = device_id
    if request_id:
        log_data["request_id"] = request_id
    if sid:
        log_data["sid"] = sid
    if topic:
        log_data["topic"] = topic
    if error:
        log_data["error"] = str(error)
    if extra:
        log_data.update(extra)

    # 写到日志文件
    getattr(logger, level.lower(), logger.info)(json.dumps(log_data, ensure_ascii=False))
    append_readable_log(
        ts,
        level,
        event,
        category,
        module,
        message,
        device_id=device_id,
        request_id=request_id,
        sid=sid,
        topic=topic,
        error=error,
        extra=extra,
    )

    # 所有分类日志都写入 SQLite（ops/biz/sec）
    save_log(ts, level, event, category, device_id, message, extra)
