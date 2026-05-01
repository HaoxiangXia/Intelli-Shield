from __future__ import annotations

import asyncio
import json
import math
import os
import socket
import sqlite3
import sys
import threading
import time
import webbrowser
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from backend import settings
from backend.repositories import database as db

DEMO_DB_PATH = ROOT / "alarm_demo.db"
DEMO_DB_FILES = (DEMO_DB_PATH, ROOT / "alarm_demo.db-shm", ROOT / "alarm_demo.db-wal")
MAP_WIDTH = 1920
MAP_HEIGHT = 1080
TICK_SEC = 0.5

FORKLIFT_PATHS = {
    "FORK-001": [(630.0, 760.0), (630.0, 150.0), (150.0, 150.0), (150.0, 760.0), (630.0, 760.0)],
    "FORK-002": [(630.0, 760.0), (1417.0, 760.0), (1417.0, 950.0), (630.0, 950.0), (630.0, 760.0)],
    "FORK-003": [(630.0, 760.0), (1417.0, 760.0), (1417.0, 150.0), (630.0, 150.0), (630.0, 760.0)],
}
FORKLIFT_SPEEDS = {
    "FORK-001": 36.0,
    "FORK-002": 42.0,
    "FORK-003": 48.0,
}
INITIAL_ROUTE_ADVANCE_SEC = {
    "FORK-001": 0.0,
    "FORK-002": 3.0,
    "FORK-003": 6.0,
}
DEMO_PHASES = [
    ("normal", 15.0, "正常巡航：三台叉车沿固定路线匀速行驶"),
    ("forklift_collision", 10.0, "作业交叉点预警：两台叉车接近 [630,760]"),
    ("person_warning", 8.0, "行人进入叉车安全预警区"),
    ("person_danger", 10.0, "行人进入叉车报警区"),
    ("clearing", 10.0, "行人远离，警报解除，叉车继续行驶"),
]


@dataclass
class ForkliftState:
    device_id: str
    path: list[tuple[float, float]]
    speed: float
    x: float
    y: float
    target_index: int = 1

    @classmethod
    def from_path(cls, device_id: str) -> "ForkliftState":
        path = FORKLIFT_PATHS[device_id]
        state = cls(
            device_id=device_id,
            path=list(path),
            speed=FORKLIFT_SPEEDS[device_id],
            x=path[0][0],
            y=path[0][1],
            target_index=1,
        )
        state.move(INITIAL_ROUTE_ADVANCE_SEC.get(device_id, 0.0))
        return state

    def move(self, dt: float) -> None:
        remaining = self.speed * dt
        while remaining > 0:
            tx, ty = self.path[self.target_index]
            dx = tx - self.x
            dy = ty - self.y
            distance = math.hypot(dx, dy)
            if distance <= 0.001:
                self.target_index = (self.target_index + 1) % len(self.path)
                continue
            step = min(remaining, distance)
            self.x += (dx / distance) * step
            self.y += (dy / distance) * step
            remaining -= step
            if step >= distance - 0.001:
                self.x = tx
                self.y = ty
                self.target_index = (self.target_index + 1) % len(self.path)

    def place_at_path_vertex(self, vertex: tuple[float, float], next_index: int) -> None:
        self.x, self.y = vertex
        self.target_index = next_index % len(self.path)


class UvicornThreadRunner:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.server: object | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        import uvicorn

        config = uvicorn.Config(
            "backend.main:app",
            host=self.host,
            port=self.port,
            reload=False,
            log_level="info",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, name="demo-uvicorn", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            print("正在停止 APP...")
            self.server.should_exit = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=8)

    def monitor(self) -> int:
        if self.thread is None:
            return 1
        try:
            while self.thread.is_alive():
                time.sleep(0.5)
            return 0
        except KeyboardInterrupt:
            print("\n检测到 Ctrl + C，准备退出...")
            return 0


class DemoSimulator:
    def __init__(self, tick_sec: float = TICK_SEC) -> None:
        self.tick_sec = tick_sec
        self.states = {device_id: ForkliftState.from_path(device_id) for device_id in FORKLIFT_PATHS}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._phase_started_at = 0.0
        self._phase_index = -1
        self._active_sessions: dict[str, str] = {}
        self._last_broadcast_at = 0.0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="demo-simulator", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        start = time.monotonic()
        while not self._stop_event.is_set():
            elapsed = time.monotonic() - start
            phase_index, phase_name = self._phase_for_elapsed(elapsed)
            if phase_index != self._phase_index:
                self._phase_index = phase_index
                self._phase_started_at = elapsed
                self._on_phase_enter(phase_name)
                print(f"[DEMO] {DEMO_PHASES[phase_index][2]}")

            phase_elapsed = elapsed - self._phase_started_at
            self._step(phase_name, phase_elapsed)
            self._write_devices(phase_name)
            self._broadcast_if_due()
            self._stop_event.wait(self.tick_sec)

    def _phase_for_elapsed(self, elapsed: float) -> tuple[int, str]:
        total = sum(duration for _, duration, _ in DEMO_PHASES)
        cursor = elapsed % total
        for index, (name, duration, _) in enumerate(DEMO_PHASES):
            if cursor < duration:
                return index, name
            cursor -= duration
        return 0, DEMO_PHASES[0][0]

    def _on_phase_enter(self, phase_name: str) -> None:
        if phase_name == "forklift_collision":
            self.states["FORK-001"].place_at_path_vertex((630.0, 760.0), 1)
            self.states["FORK-003"].place_at_path_vertex((630.0, 760.0), 1)
            self._start_alarm("FORK-001", "两台叉车驶入作业交叉点，触发碰撞预警", "forklift_forklift")
            self._start_alarm("FORK-003", "两台叉车驶入作业交叉点，触发碰撞预警", "forklift_forklift")
        elif phase_name == "person_warning":
            self._clear_alarm("FORK-001", "交叉点碰撞预警解除")
            self._clear_alarm("FORK-003", "交叉点碰撞预警解除")
            self._start_alarm("FORK-002", "行人进入叉车安全预警区", "person_warning")
        elif phase_name == "person_danger":
            self._start_alarm("FORK-002", "行人进入叉车报警区，距离进一步缩短", "person_forklift")
        elif phase_name == "clearing":
            self._clear_alarm("FORK-002", "行人远离，警报解除")
        elif phase_name == "normal":
            for device_id in list(self._active_sessions):
                self._clear_alarm(device_id, "仿真循环复位，设备恢复正常")

    def _step(self, phase_name: str, phase_elapsed: float) -> None:
        for state in self.states.values():
            state.move(self.tick_sec)

        if phase_name == "forklift_collision":
            pulse = math.sin(phase_elapsed * math.pi * 2 / 4.0) * 8.0
            self.states["FORK-001"].x = 630.0
            self.states["FORK-001"].y = 760.0 - pulse
            self.states["FORK-003"].x = 630.0 + pulse
            self.states["FORK-003"].y = 760.0
        elif phase_name in {"person_warning", "person_danger"}:
            state = self.states["FORK-002"]
            if phase_name == "person_warning":
                state.x = 930.0 + math.sin(phase_elapsed * 1.4) * 12.0
                state.y = 760.0
            else:
                state.x = 980.0 + math.sin(phase_elapsed * 1.8) * 8.0
                state.y = 760.0

    def _write_devices(self, phase_name: str) -> None:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alarm_devices = self._alarm_devices_for_phase(phase_name)
        with sqlite3.connect(DEMO_DB_PATH) as conn:
            cursor = conn.cursor()
            rows = []
            for device_id, state in self.states.items():
                rows.append(
                    (
                        1 if device_id in alarm_devices else 0,
                        now_str,
                        now_str,
                        1,
                        round(state.x, 2),
                        round(state.y, 2),
                        device_id,
                    )
                )
            cursor.executemany(
                """
                UPDATE devices
                SET alarm_status = ?,
                    last_seen = ?,
                    update_time = ?,
                    online_status = ?,
                    pos_x = ?,
                    pos_y = ?
                WHERE device_id = ?
                """,
                rows,
            )
            conn.commit()

    def _alarm_devices_for_phase(self, phase_name: str) -> set[str]:
        if phase_name == "forklift_collision":
            return {"FORK-001", "FORK-003"}
        if phase_name in {"person_warning", "person_danger"}:
            return {"FORK-002"}
        return set()

    def _start_alarm(self, device_id: str, message: str, category: str) -> None:
        if device_id in self._active_sessions:
            self._log("WARNING", "device.alarm.escalated", "biz", device_id, message, {"category": category})
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DEMO_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO alarms (device_id, alarm, timestamp) VALUES (?, 1, ?)", (device_id, now_str))
            cursor.execute(
                """
                INSERT INTO alarm_sessions (device_id, start_time, status)
                VALUES (?, ?, 0)
                """,
                (device_id, now_str),
            )
            cursor.execute(
                """
                UPDATE devices
                SET alarm_status = 1, error_count = error_count + 1
                WHERE device_id = ?
                """,
                (device_id,),
            )
            conn.commit()
        self._active_sessions[device_id] = now_str
        self._log("WARNING", "device.alarm.raised", "biz", device_id, message, {"category": category})

    def _clear_alarm(self, device_id: str, message: str) -> None:
        if device_id not in self._active_sessions:
            return

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        start_str = self._active_sessions.pop(device_id)
        try:
            duration_sec = max(0.0, (now - datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")).total_seconds())
        except ValueError:
            duration_sec = 0.0

        with sqlite3.connect(DEMO_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO alarms (device_id, alarm, timestamp) VALUES (?, 0, ?)", (device_id, now_str))
            cursor.execute(
                """
                UPDATE alarm_sessions
                SET end_time = ?, duration_sec = ?, status = 1
                WHERE device_id = ? AND status = 0
                """,
                (now_str, duration_sec, device_id),
            )
            cursor.execute("UPDATE devices SET alarm_status = 0 WHERE device_id = ?", (device_id,))
            conn.commit()
        self._log("INFO", "device.alarm.cleared", "biz", device_id, message, {"duration_sec": duration_sec})

    def _log(
        self,
        level: str,
        event: str,
        category: str,
        device_id: str | None,
        message: str,
        extra: dict[str, object] | None = None,
    ) -> None:
        ts = datetime.now().isoformat(timespec="seconds") + "Z"
        with sqlite3.connect(DEMO_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO all_logs (ts, level, event, category, device_id, message, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, level, event, category, device_id, message, json.dumps(extra or {}, ensure_ascii=False)),
            )
            conn.commit()

    def _broadcast_if_due(self) -> None:
        now = time.monotonic()
        if now - self._last_broadcast_at < 1.0:
            return
        self._last_broadcast_at = now
        try:
            from backend.main import worker_manager
            from backend.services import app_service

            if worker_manager.loop is None:
                return
            payload = app_service.get_latest_payload()
            asyncio.run_coroutine_threadsafe(worker_manager.sio.emit("device_update", payload), worker_manager.loop)
        except Exception:
            pass


def configure_demo_database() -> None:
    demo_path = str(DEMO_DB_PATH)
    settings.DB_PATH = demo_path
    db.DB_PATH = demo_path
    settings.OFFLINE_TIMEOUT_SEC = 7200
    settings.POSITION_MOVE_RANGE = 0
    settings.POSITION_UPDATE_INTERVAL_SEC = 86400
    settings.LLM_ENABLED = False


def remove_demo_database_files() -> None:
    for path in DEMO_DB_FILES:
        with suppress(FileNotFoundError):
            path.unlink()


def find_available_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def ensure_demo_assets() -> tuple[str, str]:
    primary = ROOT / "images" / "alarms" / "FORK-003_20260408_003836.png"
    secondary = ROOT / "images" / "alarms" / "MANUAL-TEST_20260408_002811.png"
    if not primary.exists() or not secondary.exists():
        raise FileNotFoundError("缺少演示图片资源")
    return (
        "images/alarms/FORK-003_20260408_003836.png",
        "images/alarms/MANUAL-TEST_20260408_002811.png",
    )


def ensure_frontend_build() -> None:
    index_file = ROOT / "frontend" / "dist" / "index.html"
    if index_file.exists():
        return
    raise FileNotFoundError(
        "缺少前端构建产物：frontend/dist/index.html\n"
        "请先执行：\n"
        "  cd frontend\n"
        "  npm install\n"
        "  npm run build\n"
        "  cd .."
    )


def rebuild_demo_database() -> None:
    image_primary, image_secondary = ensure_demo_assets()
    remove_demo_database_files()
    db.init_db()

    now = datetime.now().replace(second=0, microsecond=0)
    today = now.replace(hour=8, minute=0)
    yesterday = today - timedelta(days=1)

    device_rows = []
    for index, (device_id, state) in enumerate((device_id, ForkliftState.from_path(device_id)) for device_id in FORKLIFT_PATHS):
        device_rows.append(
            {
                "device_id": device_id,
                "alarm_status": 0,
                "error_count": index + 1,
                "boot_time": (now - timedelta(hours=6 + index)).strftime("%Y-%m-%d %H:%M:%S"),
                "last_seen": now.strftime("%Y-%m-%d %H:%M:%S"),
                "online_status": 1,
                "update_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "pos_x": state.x,
                "pos_y": state.y,
            }
        )

    alarm_rows = [
        ("FORK-001", 1, (yesterday + timedelta(hours=9, minutes=20)).strftime("%Y-%m-%d %H:%M:%S")),
        ("FORK-001", 0, (yesterday + timedelta(hours=9, minutes=28)).strftime("%Y-%m-%d %H:%M:%S")),
        ("FORK-002", 1, (today + timedelta(hours=1, minutes=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("FORK-002", 0, (today + timedelta(hours=1, minutes=16)).strftime("%Y-%m-%d %H:%M:%S")),
        ("FORK-003", 1, (today + timedelta(hours=2, minutes=35)).strftime("%Y-%m-%d %H:%M:%S")),
        ("FORK-003", 0, (today + timedelta(hours=2, minutes=43)).strftime("%Y-%m-%d %H:%M:%S")),
    ]

    image_rows = [
        (
            "FORK-001",
            image_secondary,
            (yesterday + timedelta(hours=9, minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
            "历史演示记录：通道转角处视线受阻",
            "done",
            "demo-simulator",
            (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
        ),
        (
            "FORK-002",
            image_primary,
            (today + timedelta(hours=1, minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "历史演示记录：行人进入叉车安全预警区",
            "done",
            "demo-simulator",
            (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
        ),
    ]

    session_rows = [
        ("FORK-001", alarm_rows[0][2], alarm_rows[1][2], 480.0, 1),
        ("FORK-002", alarm_rows[2][2], alarm_rows[3][2], 360.0, 1),
        ("FORK-003", alarm_rows[4][2], alarm_rows[5][2], 480.0, 1),
    ]

    log_rows = [
        (
            now.isoformat(timespec="seconds") + "Z",
            "INFO",
            "system.demo.seeded",
            "ops",
            None,
            "Loaded isolated simulation demo database",
            {"database": str(DEMO_DB_PATH), "devices": 3},
        ),
    ]

    with sqlite3.connect(DEMO_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alarm_sessions")
        cursor.execute("DELETE FROM alarm_images")
        cursor.execute("DELETE FROM alarms")
        cursor.execute("DELETE FROM devices")
        cursor.execute("DELETE FROM biz_logs")
        cursor.execute("DELETE FROM all_logs")
        cursor.executemany(
            """
            INSERT INTO devices (
                device_id, alarm_status, error_count, boot_time,
                last_seen, online_status, update_time, pos_x, pos_y
            ) VALUES (
                :device_id, :alarm_status, :error_count, :boot_time,
                :last_seen, :online_status, :update_time, :pos_x, :pos_y
            )
            """,
            device_rows,
        )
        cursor.executemany("INSERT INTO alarms (device_id, alarm, timestamp) VALUES (?, ?, ?)", alarm_rows)
        cursor.executemany(
            """
            INSERT INTO alarm_images (
                device_id, image_path, timestamp, description,
                description_status, description_model, description_updated_at, description_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            image_rows,
        )
        cursor.executemany(
            """
            INSERT INTO alarm_sessions (device_id, start_time, end_time, duration_sec, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            session_rows,
        )
        cursor.executemany(
            """
            INSERT INTO all_logs (ts, level, event, category, device_id, message, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [(ts, level, event, category, device_id, message, json.dumps(extra, ensure_ascii=False)) for ts, level, event, category, device_id, message, extra in log_rows],
        )
        conn.commit()


def wait_for_server(url: str, timeout_sec: float = 20.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.5) as response:
                if 200 <= response.status < 500:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> int:
    if not (ROOT / "backend" / "app.py").exists():
        print("未找到文件：backend/app.py")
        return 1

    runner: UvicornThreadRunner | None = None
    simulator: DemoSimulator | None = None
    try:
        ensure_frontend_build()
        configure_demo_database()
        rebuild_demo_database()

        os.environ["OFFLINE_TIMEOUT_SEC"] = "7200"
        os.environ["POSITION_MOVE_RANGE"] = "0"
        os.environ["POSITION_UPDATE_INTERVAL_SEC"] = "86400"

        app_host = "127.0.0.1"
        app_port = find_available_port(app_host)
        service_url = f"http://localhost:{app_port}"

        runner = UvicornThreadRunner(app_host, app_port)
        runner.start()
        if not wait_for_server(service_url + "/"):
            print("服务启动失败")
            runner.stop()
            return 1

        simulator = DemoSimulator()
        simulator.start()

        print(f"仿真演示系统已启动，数据库: {DEMO_DB_PATH}")
        print(service_url)
        with suppress(Exception):
            webbrowser.open(service_url + "/", new=2, autoraise=True)

        return runner.monitor()
    except Exception as exc:
        print(f"运行失败: {exc}")
        return 1
    finally:
        if simulator is not None:
            simulator.stop()
        if runner is not None:
            runner.stop()


if __name__ == "__main__":
    raise SystemExit(main())
