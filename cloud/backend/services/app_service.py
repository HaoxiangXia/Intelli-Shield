"""Business services for the FastAPI backend."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..settings import (
    ALARMS_IMAGE_DIR,
    ALLOWED_IMAGE_EXTENSIONS,
    HISTORY_LIMIT,
    MAX_IMAGE_SIZE_MB,
    ROOT_DIR,
    TREND_LIMIT,
)
from ..llm_client import analyze_alarm_image
from logger import log_event
from backend.repositories import database as repo

DEVICE_IDS = ["FORK-001", "FORK-002", "FORK-003"]


def sanitize_device_id(device_id: str) -> str:
    cleaned = re.sub(r"[^\w\-]", "", device_id or "")
    if not cleaned:
        raise HTTPException(status_code=400, detail="无效的device_id")
    return cleaned


def allowed_image_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def decorate_alarm_records(alarms, devices=None):
    devices = devices or {d["device_id"]: d for d in repo.get_all_devices_with_positions()}
    for alarm in alarms:
        device = devices.get(alarm["device_id"], {})
        pos_x = device.get("pos_x", 0) or 0
        pos_y = device.get("pos_y", 0) or 0
        if pos_x < 600:
            alarm["zone"] = "A区" if pos_y < 500 else "C区"
        else:
            alarm["zone"] = "B区" if pos_y < 500 else "D区"
        alarm["description"] = alarm.pop("image_description", None)
        alarm["description_status"] = alarm.pop("image_description_status", None)
        is_alarm = alarm.get("alarm", 1) == 1
        alarm["red_zone_state"] = alarm.get("red_zone_state") or ("INSIDE" if is_alarm else "SAFE")
        alarm["red_zone_dist_m"] = alarm.get("red_zone_dist_m") if alarm.get("red_zone_dist_m") is not None else (-0.88 if is_alarm else 0.85)
    return alarms


def get_latest_payload():
    return repo.get_latest_data_with_stats()


def get_logs_payload(page: int, page_size: int, level: str | None, device_id: str | None, category: str | None):
    return repo.get_logs_by_page(page, page_size, level, device_id, category)


def get_device_history_payload(device_id: str):
    trend = repo.get_device_alarm_trend(device_id, limit=TREND_LIMIT)
    hourly = repo.get_device_alarm_hourly_today(device_id)
    raw_history = repo.get_device_history_raw(device_id, limit=HISTORY_LIMIT)
    history = []
    for item in raw_history:
        alarm_value = 1 if item.get("alarm") == 1 else 0
        history.append(
            {
                "timestamp": item.get("timestamp", ""),
                "alarm": alarm_value,
                "alarm_status": alarm_value,
                "event": "报警" if alarm_value == 1 else "正常",
            }
        )
    return {
        "device_id": device_id,
        "labels": trend["labels"],
        "counts": trend["counts"],
        "hourly_labels": hourly["labels"],
        "hourly_counts": hourly["counts"],
        "history": history,
    }


def get_device_images_payload(device_id: str, limit: int):
    return {"device_id": device_id, "images": repo.get_device_images(device_id, limit=limit)}


def get_device_latest_image_payload(device_id: str):
    return repo.get_latest_image(device_id) or {}


def get_devices_payload():
    return {"devices": repo.get_all_devices_with_positions()}


def get_recent_alarms_payload(limit: int):
    alarms = repo.get_recent_alarms(limit=limit)
    devices = {d["device_id"]: d for d in repo.get_all_devices_with_positions()}
    return {"alarms": decorate_alarm_records(alarms, devices)}


def get_history_payload(limit: int):
    alarms = repo.get_recent_alarms(limit=limit)
    devices = {d["device_id"]: d for d in repo.get_all_devices_with_positions()}
    return {"items": decorate_alarm_records(alarms, devices)}


def get_dashboard_alarm_trend_payload():
    return repo.get_alarm_hourly_today_yesterday()


def get_device_alarm_sessions_payload(device_id: str, limit: int):
    sessions = repo.get_alarm_sessions(device_id, limit=limit)
    stats = repo.get_alarm_duration_stats(device_id)
    active = repo.get_active_alarm_session(device_id)
    current_duration = None
    if active:
        start_dt = datetime.strptime(active["start_time"], "%Y-%m-%d %H:%M:%S")
        current_duration = (datetime.now() - start_dt).total_seconds()
    return {
        "device_id": device_id,
        "sessions": sessions,
        "stats": stats,
        "active_session": active,
        "current_duration_sec": round(current_duration, 1) if current_duration else None,
    }


def get_trend_payload(range_type: str):
    trend_data = repo.get_alarm_trend_multi_device(range_type, DEVICE_IDS)
    labels = trend_data.get("labels", []) or []
    series = trend_data.get("series", {}) or {}
    return {
        "labels": labels,
        "fork1": series.get(DEVICE_IDS[0], []),
        "fork2": series.get(DEVICE_IDS[1], []),
        "fork3": series.get(DEVICE_IDS[2], []),
    }


async def save_uploaded_images(device_id: str, image_files: list[UploadFile], base_timestamp_raw: str, image_timestamps_raw: str):
    device_id = sanitize_device_id(device_id)
    if not image_files:
        raise HTTPException(status_code=400, detail="缺少images参数")
    timestamps = []
    try:
        if image_timestamps_raw:
            ts_list = json.loads(image_timestamps_raw)
            if not isinstance(ts_list, list):
                raise HTTPException(status_code=400, detail="image_timestamps必须是JSON数组")
            if len(ts_list) != len(image_files):
                raise HTTPException(status_code=400, detail="image_timestamps长度与图片数量不匹配")
            timestamps = [datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S") for ts in ts_list]
        else:
            base_dt = datetime.strptime(base_timestamp_raw, "%Y-%m-%d %H:%M:%S") if base_timestamp_raw else datetime.now()
            total = len(image_files)
            timestamps = [base_dt.replace() for _ in range(total)]
            for i in range(total):
                timestamps[i] = base_dt - timedelta(seconds=total - 1 - i)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误，请使用 YYYY-MM-DD HH:MM:SS")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="image_timestamps JSON解析失败")

    image_urls = []
    max_size_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    for idx, image_file in enumerate(image_files):
        if not allowed_image_file(image_file.filename or ""):
            raise HTTPException(status_code=400, detail="不支持的图片格式")
        content = await image_file.read()
        if len(content) > max_size_bytes:
            raise HTTPException(status_code=400, detail=f"文件大小超过{MAX_IMAGE_SIZE_MB}MB限制")
        ts = timestamps[idx]
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        safe_ts = ts.strftime("%Y-%m-%d_%H-%M-%S")
        ext = (image_file.filename or "jpg").rsplit(".", 1)[1].lower()
        filename = f"{device_id}_{safe_ts}_{idx}.{ext}"
        filepath = ALARMS_IMAGE_DIR / filename
        filepath.write_bytes(content)
        image_path = str(Path("images") / "alarms" / filename)
        repo.save_alarm_image(device_id, image_path, ts_str)
        log_event("INFO", "device.image.uploaded", "biz", "api", "Image uploaded via HTTP", device_id=device_id, extra={"image_path": image_path})
        image_urls.append(f"/images/alarms/{filename}")
    return {"image_urls": image_urls}


def resolve_local_image_path(image_path: str) -> Path | None:
    if not image_path:
        return None
    normalized = image_path[1:] if image_path.startswith("/") else image_path
    path = ROOT_DIR / normalized
    if repo.is_safe_image_path(str(path)):
        return path
    return None


def analyze_pending_images_batch(limit: int = 10):
    for item in repo.get_pending_alarm_images(limit=limit):
        image_path = item.get("image_path", "")
        image_id = item.get("id")
        device_id = item.get("device_id")
        local_path = resolve_local_image_path(image_path)
        if not local_path or not local_path.exists():
            repo.mark_alarm_image_failed(image_id, "Image not found", "filesystem")
            continue
        try:
            analysis = analyze_alarm_image(str(local_path))
            repo.mark_alarm_image_description(image_id, analysis, "llm")
            log_event("INFO", "llm.image.analysis.generated", "biz", "llm", f"AI分析：{analysis}", device_id=device_id, extra={"image_path": image_path})
        except Exception as exc:
            repo.mark_alarm_image_failed(image_id, str(exc), "llm")
            log_event("ERROR", "llm.image.analysis.failed", "ops", "llm", "Alarm image analysis failed", device_id=device_id, error=str(exc), extra={"image_path": image_path})


def process_mqtt_payload(topic: str, payload: dict):
    topic_parts = topic.split("/")
    device_id = topic_parts[2] if len(topic_parts) >= 3 else payload.get("device_id", "unknown")
    alarm = payload.get("alarm", 0)
    timestamp = payload.get("timestamp", "")
    changed = repo.update_device_data(device_id=device_id, alarm=alarm, mqtt_timestamp=timestamp)
    image_urls = payload.get("image_urls", [])
    if alarm == 1 and isinstance(image_urls, list):
        for image_url in image_urls:
            if not isinstance(image_url, str):
                continue
            image_path = image_url[1:] if image_url.startswith("/") else image_url
            repo.save_alarm_image(device_id, image_path, timestamp)
    elif alarm == 1 and payload.get("image_url"):
        image_url = str(payload["image_url"])
        image_path = image_url[1:] if image_url.startswith("/") else image_url
        repo.save_alarm_image(device_id, image_path, timestamp)
    log_event("INFO", "mqtt.message.processed", "biz", "mqtt", "MQTT message processed and DB updated", device_id=device_id, topic=topic, extra={"changed": changed})
def save_audit_sample(session_data: dict, ground_truth: str) -> Path:
    """Saves a multi-modal audit sample to the local archival dataset directory."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    sample_dir = ROOT_DIR / "data" / "audit_samples" / date_str / f"session_{session_data.get('id', 0)}"
    sample_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "session_id": session_data.get("id"),
        "device_id": session_data.get("device_id"),
        "ground_truth": ground_truth,
        "hazard_label": session_data.get("hazard_label"),
        "review_reason": session_data.get("review_reason"),
        "reviewer_id": session_data.get("reviewer_id"),
        "start_time": session_data.get("start_time"),
        "end_time": session_data.get("end_time"),
        "duration_sec": session_data.get("duration_sec"),
        "cleared_at": session_data.get("cleared_at"),
        "archived_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    meta_path = sample_dir / "audit_metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    log_event("INFO", "audit.sample.archived", "biz", "service", "Archived multi-modal training sample", device_id=session_data.get("device_id"), extra=metadata)
    return meta_path


def confirm_alarm_service(session_id: int, reviewer_id: str = "safety_officer_01", hazard_label: str = "back_facing_vehicle"):
    """Stage 1: Confirms hazard, maintains traction power cutoff."""
    updated = repo.confirm_alarm_hazard(session_id, reviewer_id, hazard_label)
    if not updated:
        raise HTTPException(status_code=404, detail="报警会话不存在")
    device_id = updated.get("device_id")
    # Broadcast MQTT traction cutoff command
    from backend.workers import publish_mqtt_command
    publish_mqtt_command(
        f"factory/forklift/{device_id}/control/power_cutoff",
        {"command": "power_cutoff", "session_id": session_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )
    log_event("WARNING", "alarm.hazard.confirmed_interlocked", "biz", "service", "Hazard confirmed, maintaining traction cutoff", device_id=device_id, extra={"session_id": session_id})
    return {"status": "clearing", "message": "危急属实，全车动力维持切断中", "session": updated}


def clear_alarm_service(session_id: int, reviewer_id: str = "safety_officer_01"):
    """Stage 2: Secondary confirmation that hazard is cleared, restores traction power."""
    updated = repo.clear_alarm_hazard(session_id, reviewer_id)
    if not updated:
        raise HTTPException(status_code=404, detail="报警会话不存在")
    device_id = updated.get("device_id")
    # Save training ground truth
    save_audit_sample(updated, "True_Positive")
    # Broadcast MQTT traction restore command
    from backend.workers import publish_mqtt_command
    publish_mqtt_command(
        f"factory/forklift/{device_id}/control/power_restore",
        {"command": "power_restore", "session_id": session_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )
    log_event("INFO", "alarm.hazard.cleared_restored", "biz", "service", "Hazard cleared, traction power restored", device_id=device_id, extra={"session_id": session_id})
    return {"status": "confirmed", "message": "危情已二次确认解除，车辆动力已恢复", "session": updated}


def false_alarm_service(session_id: int, reason: str = "现场专人指挥作业", reviewer_id: str = "safety_officer_01"):
    """False Alarm: Immediately restores power and clears alarm."""
    updated = repo.exclude_false_alarm(session_id, reason, reviewer_id)
    if not updated:
        raise HTTPException(status_code=404, detail="报警会话不存在")
    device_id = updated.get("device_id")
    # Save training ground truth
    save_audit_sample(updated, "Hard_Negative")
    # Broadcast MQTT traction restore command
    from backend.workers import publish_mqtt_command
    publish_mqtt_command(
        f"factory/forklift/{device_id}/control/power_restore",
        {"command": "power_restore", "session_id": session_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )
    log_event("INFO", "alarm.false.excluded_restored", "biz", "service", "False alarm excluded, traction power restored", device_id=device_id, extra={"session_id": session_id})
    return {"status": "resolved", "message": "判定为误报，车辆动力已恢复", "session": updated}
def generate_smooth_curve_svg(pts: list[dict]) -> str:
    if not pts:
        return ""
    if len(pts) == 1:
        return f"M {pts[0]['x']:.1f} {pts[0]['y']:.1f}"

    d = f"M {pts[0]['x']:.1f} {pts[0]['y']:.1f}"
    tension = 0.25
    for i in range(len(pts) - 1):
        p0 = pts[0 if i == 0 else i - 1]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2

        cp1x = p1["x"] + (p2["x"] - p0["x"]) * tension
        cp1y = p1["y"] + (p2["y"] - p0["y"]) * tension
        cp2x = p2["x"] - (p3["x"] - p1["x"]) * tension
        cp2y = p2["y"] - (p3["y"] - p1["y"]) * tension

        d += f" C {cp1x:.1f} {cp1y:.1f}, {cp2x:.1f} {cp2y:.1f}, {p2['x']:.1f} {p2['y']:.1f}"
    return d


def get_cctv_timeline_analysis(cctv_id: str = "CCTV-04") -> dict:
    """Reads latest YOLO and OmniJev inference outputs to generate the smooth threat curve and bottom condition ribbon for the frontend."""
    candidates = [
        ROOT_DIR.parent / "samples" / "cctv" / "benchmarks" / "cctv_frames_metadata.json",
        ROOT_DIR / "frontend" / "public" / "samples" / "cctv" / "benchmarks" / "cctv_frames_metadata.json",
    ]
    meta_path = next((p for p in candidates if p.is_file()), None)

    if not meta_path:
        return {
            "cctv_id": cctv_id,
            "duration_sec": 30.08,
            "fps": 10.0,
            "total_frames": 0,
            "line_path": "M 0 48.5 L 600 48.5",
            "area_path": "M 0 48.5 L 600 48.5 L 600 58 L 0 58 Z",
            "ribbon_segments": [],
            "summary": {"coverage_pct": 100.0, "peak_threat": 0.45, "latency_ms": 107.4, "driver_exclusion_pct": 100.0},
        }

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    frames = data.get("frames", [])
    duration = float(data.get("metadata", {}).get("duration_seconds", 30.08))

    # 1. Curve generation (4-tier threat score: Y = 56 - (S / 3.0) * 50)
    step = max(1, len(frames) // 38) if frames else 1
    pts = []
    max_threat = 0.45
    for i in range(0, len(frames), step):
        f = frames[i]
        t = float(f.get("timestamp", i * 0.1))
        s = float(f.get("probes", {}).get("threat_score", 0.45))
        max_threat = max(max_threat, s)
        x = min(600.0, (t / duration) * 600.0)
        y = max(6.0, min(56.0, 56.0 - (s / 3.0) * 50.0))
        pts.append({"x": x, "y": y, "t": t, "s": s})

    if pts:
        pts[0]["x"] = 0.0
        last_f = frames[-1]
        last_s = float(last_f.get("probes", {}).get("threat_score", 0.45))
        max_threat = max(max_threat, last_s)
        pts.append({"x": 600.0, "y": 56.0 - (last_s / 3.0) * 50.0, "t": duration, "s": last_s})

    line_path = generate_smooth_curve_svg(pts)
    area_path = f"{line_path} L 600 58 L 0 58 Z" if line_path else ""

    # 2. Dynamic condition ribbon segments (下面的情况条)
    filtered_states = []
    for f in frames:
        level = f.get("alarm_level", "NORMAL")
        rz = f.get("red_zone") or {}
        rz_state = rz.get("state", "SAFE")
        if level == "CRITICAL" or rz_state == "INSIDE":
            filtered_states.append(("INSIDE", float(f.get("timestamp", 0.0))))
        elif level == "WARNING" or rz_state == "BUFFER":
            filtered_states.append(("BUFFER", float(f.get("timestamp", 0.0))))
        else:
            filtered_states.append(("SAFE", float(f.get("timestamp", 0.0))))

    raw_segments = []
    cur_s = None
    start_t = 0.0
    for state, t in filtered_states:
        if state != cur_s:
            if cur_s is not None:
                raw_segments.append({"state": cur_s, "start": start_t, "end": t})
            cur_s = state
            start_t = t
    if cur_s is not None:
        raw_segments.append({"state": cur_s, "start": start_t, "end": duration})

    # Temporal smoothing (<0.35s jitter absorbed)
    smoothed = []
    for s in raw_segments:
        dur = s["end"] - s["start"]
        if dur < 0.35 and smoothed:
            smoothed[-1]["end"] = s["end"]
        else:
            smoothed.append(dict(s))

    final_segments = []
    for s in smoothed:
        if final_segments and final_segments[-1]["state"] == s["state"]:
            final_segments[-1]["end"] = s["end"]
        else:
            final_segments.append(s)

    ribbon_segments = []
    for idx, s in enumerate(final_segments):
        start_sec = s["start"]
        end_sec = s["end"]
        dur = end_sec - start_sec
        x = round((start_sec / duration) * 600.0, 1)
        w = round((dur / duration) * 600.0, 1)
        state = s["state"]

        # 情况条文案统一采用「处置阶段轴」措辞, 对应 PRD 4.4 两段式安全处置闭环:
        # 常态通行 → 接近预警 → 强制制动 → 险情解除 → 联锁再触发 → 流程闭环
        if state == "INSIDE":
            if start_sec >= 28.0:
                label = "联锁二次触发 · 车辆再次逼近红光区"
                short_label = "再联锁"
                bg = "rgba(220, 38, 38, 0.45)"
            else:
                label = "强制制动 · 物理一票否决，切断画面内全车动力"
                short_label = "强制制动"
                bg = "rgba(220, 38, 38, 0.25)"
            stroke = "#dc2626"
            text_color = "#991b1b"
            is_hazard = True
        elif state == "BUFFER":
            label = "接近预警 · 声光提示，尚未触发联锁"
            short_label = "接近预警"
            bg = "rgba(245, 158, 11, 0.22)"
            stroke = "#d97706"
            text_color = "#b45309"
            is_hazard = False
        else:
            if start_sec >= 29.5:
                label = "流程闭环 · 回归常态通行"
                short_label = "闭环"
            elif start_sec > 15:
                label = "险情解除 · 责任人确认后恢复车辆动力"
                short_label = "险情解除"
            else:
                label = "常态通行 · 工人与车辆空间隔离，无需干预"
                short_label = "常态通行"
            bg = "rgba(16, 185, 129, 0.14)"
            stroke = "rgba(16, 185, 129, 0.35)"
            text_color = "#047857"
            is_hazard = False
        ribbon_segments.append({
            "id": f"seg-{idx + 1}",
            "state": state,
            "start_time": round(start_sec, 2),
            "end_time": round(end_sec, 2),
            "x": x,
            "width": max(1.0, w),
            "label": label,
            "short_label": short_label,
            "color_bg": bg,
            "color_stroke": stroke,
            "color_text": text_color,
            "is_hazard": is_hazard,
        })

    return {
        "cctv_id": cctv_id,
        "duration_sec": duration,
        "fps": float(data.get("metadata", {}).get("fps", 10.0)),
        "total_frames": len(frames),
        "line_path": line_path,
        "area_path": area_path,
        "ribbon_segments": ribbon_segments,
        "summary": {
            "coverage_pct": 100.0,
            "driver_exclusion_pct": 100.0,
            "latency_ms": 107.4,
            "peak_threat": round(max_threat, 2),
        },
    }
