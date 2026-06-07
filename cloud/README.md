# 智盾 Intelli Shield · 云端 (Cloud)

<div align="center">

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat&logo=vue.js&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-3C52F0?style=flat&logo=mqtt&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-010101?style=flat&logo=socket.io&logoColor=white)

</div>

本目录是「**[智盾 Intelli Shield](../README.md)**」端云协同人车互斥安全预警系统的**云端子模块**，负责接收设备端上报的报警事件、落库留存、实时推送给前端看板，并提供数字孪生地图、管理看板与 AI 辅助分析。

> **项目归属说明**：本目录是智盾 Intelli Shield 的云端部分。项目整体定位、目标用户、MVP 范围、里程碑与团队分工见根目录 [`README.md`](../README.md) 与 [`PRD.md`](../PRD.md)。
> 设备端模块（MaixCAM 视觉检测 + 双状态机 + UART 联动）见 [`../device/README.md`](../device/README.md)。

---

## 子目录导航

- `backend/`：FastAPI 后端（REST + MQTT + Socket.IO + LLM + SQLite）
- `frontend/`：Vue 3 + Vite 前端（5 个看板页面 + ECharts 可视化）
- `tests/`：测试与仿真脚本；`edge_node_client.py` 是仿真演示入口
- `docs/`：深度文档（通信层、图片上传、Bun 手册、仿真指南）
- `images/alarms/`：设备端上传的报警图片存储目录
- `alarm.db`：默认 SQLite 数据库（演示用独立库 `alarm_demo.db`）
- `create_ui.py`：前端 UI 初始化脚本（生成默认 Vue 组件/样式）
- `logger.py`：顶层日志工具（被 `backend/` 复用）
- `.env`：环境变量配置（MQTT / LLM / 离线阈值等）
- `pyproject.toml` / `uv.lock`：Python 项目元数据与依赖锁定

---

## 技术栈

### 后端 (backend/)

| 组件 | 选型 |
|---|---|
| Web 框架 | FastAPI + Uvicorn |
| 实时推送 | python-socketio (ASGI 模式) |
| MQTT 客户端 | paho-mqtt (Callback API v2) |
| 数据库 | SQLite（`alarm.db`，5s busy_timeout） |
| LLM 多模态（可选） | OpenAI 兼容接口（默认 `gpt-4.1-mini`） |
| 包管理 | uv（Python ≥ 3.13，参见 `pyproject.toml`） |
| 分层结构 | `repositories/` (DB) + `services/` (业务) + `api.py` (路由) + `workers.py` (后台) |

### 前端 (frontend/)

| 组件 | 选型 |
|---|---|
| 框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 可视化 | ECharts (vue-echarts) |
| 实时通信 | socket.io-client + axios |
| 路由 | vue-router |
| 包管理 | Bun（推荐）或 npm，详见 `docs/bun-help.md` |

### 页面清单

| 路由 | 页面 | 主要内容 |
|---|---|---|
| `/` | Dashboard | 厂区数字孪生地图、设备点位、报警环、近期报警 |
| `/devices` | Devices | 设备列表 / 在线状态 / 报警会话与持续时长 |
| `/history` | History | 报警记录筛选与回放 |
| `/logs` | Logs | 运维 + 业务日志分页查询 |
| `/trend` | Trend | 多设备报警趋势对比 |

---

## 快速开始

### 1) 后端

依赖：Python ≥ 3.13。`cloud/` 目录下：

```powershell
uv sync                                         # 同步依赖（首次或 pyproject 变更后）
# 按需修改 .env（MQTT broker、端口、可选 LLM 配置等）
.\.venv\Scripts\python.exe -m backend.app       # 启动（默认 0.0.0.0:5000）
```

启动后访问 `http://localhost:5000` 即可看到前端 SPA（前提是已经构建过前端，详见下文）。

### 2) 前端

```powershell
cd frontend
bun install          # 或 npm install
bun run dev          # 开发模式，默认 http://localhost:5173
bun run build        # 生产构建，产物输出到 frontend/dist/
```

> **重要**：后端默认从 `frontend/dist/index.html` 提供 SPA 页面。**部署前必须先 `bun run build`**，否则首页会返回 503 提示构建产物缺失（见 `backend/api.py` 的 `_index_response`）。

### 3) 仿真演示（无需真实设备）

```powershell
.\.venv\Scripts\python.exe tests\edge_node_client.py
```

启动后会在终端打印访问 URL（如 `http://localhost:51247`），自动在厂区地图上演示 3 台叉车按剧本巡航、触发碰撞预警、行人预警与报警解除。详细剧本、路线与调参说明见 [`docs/simulation-demo.md`](docs/simulation-demo.md)。

> 演示使用独立数据库 `alarm_demo.db`，不会影响正式数据库 `alarm.db`。

### 4) 主要环境变量

完整项见 [`backend/settings.py`](backend/settings.py)；以下为最常用配置：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | 后端监听地址 |
| `APP_PORT` | `5000` | 后端监听端口 |
| `MQTT_BROKER` | `localhost` | MQTT 代理地址 |
| `MQTT_PORT` | `1883` | MQTT 代理端口 |
| `MQTT_TOPIC` | `factory/forklift/+/alarm` | 订阅主题（`+` 匹配设备 ID） |
| `MQTT_REQUIRED` | `False` | 启动时是否强依赖 MQTT；生产建议 `True` |
| `OFFLINE_TIMEOUT_SEC` | `10` | 设备多久未上报判为离线 |
| `LLM_ENABLED` | 自动（依 `OPENAI_API_KEY`） | 是否启用 LLM 报警图片描述 |
| `OPENAI_API_KEY` | 空 | OpenAI 兼容 Key |
| `OPENAI_BASE_URL` | 空 | 自定义 LLM 网关 |
| `LLM_MODEL` | `gpt-4.1-mini` | LLM 模型名 |

---

## 端到端数据流

```
设备端 (MaixCAM)                  云端 (cloud/)                       前端 (Vue 3)
─────────────────                ─────────────────                ─────────────
[检测到报警]
   │
   │  HTTP POST /api/upload-image ─▶│  保存到 images/alarms/
   │                                  │  写入 alarm_images
   │  ◀─────── {image_urls} ─────────│
   │
   │  MQTT Publish ────────────────▶│  WorkerManager.mqtt-worker
   │   factory/forklift/             │   ├ 解析 payload
   │     {device_id}/alarm           │   ├ 更新 devices / alarms / sessions
   │   {alarm, timestamp,            │   └ Socket.IO emit("device_update")
   │    image_urls}                  │
   │                                  │
   │                                  │  /api/devices ────────────▶  Dashboard 实时刷新
   │                                  │  /api/recent-alarms ──────▶  报警列表
   │                                  │  /api/history ────────────▶  历史/趋势页
```

---

## 关键 REST API 概览

完整字段、参数与示例见 [`docs/communication-layer.md`](docs/communication-layer.md) 与 [`docs/image-upload-guide.md`](docs/image-upload-guide.md)。

| 方法 | 路径 | 用途 | 主要调用方 |
|---|---|---|---|
| POST | `/api/upload-image` | 批量上传报警图片 | 设备端 |
| GET | `/api/latest` | 最新设备状态 + 统计聚合 | 前端看板 |
| GET | `/api/devices` | 设备列表 + 位置 + 在线状态 | 前端 Dashboard |
| GET | `/api/recent-alarms?limit=N` | 最近 N 条报警 | 前端 |
| GET | `/api/history?limit=N` | 报警历史（按时间倒序） | 前端 |
| GET | `/api/trend?type=day` | 多设备报警趋势 | 前端 Trend |
| GET | `/api/dashboard/alarm-trend` | 今日 vs 昨日小时分布 | 前端 Dashboard |
| GET | `/api/device/{id}/history` | 单设备历史 + 小时趋势 | 前端 |
| GET | `/api/device/{id}/images?limit=N` | 单设备最近图片 | 前端 |
| GET | `/api/device/{id}/latest-image` | 单设备最近一张图 | 前端 |
| GET | `/api/device/{id}/alarm-sessions` | 单设备报警会话与持续时长 | 前端 |
| GET | `/api/logs` | 运维 + 业务日志分页 | 前端 Logs |
| GET | `/api/biz_logs` | 仅业务日志 | 前端 |
| GET | `/images/{path}` | 报警图片静态访问 | 前端 / 浏览器 |

---

## 实时通道

### MQTT 订阅

- 主题：`factory/forklift/+/alarm`（`+` 通配任意设备 ID）
- 推荐流程：先 HTTP 上传图片 → 拿到 `image_urls` → 再 MQTT 发布报警状态
- Payload 示例：

  ```json
  {
    "device_id": "FORK-001",
    "alarm": 1,
    "timestamp": "2026-03-19 14:30:00",
    "image_urls": ["/images/alarms/FORK-001_2026-03-19_14-30-00_0.jpg"]
  }
  ```

### Socket.IO 事件

| 事件 | 方向 | Payload | 触发时机 |
|---|---|---|---|
| `device_update` | 服务器 → 前端 | `app_service.get_latest_payload()` | MQTT 收消息 / 离线检测 / 周期广播 |
| `position_update` | 服务器 → 前端 | 设备位置列表 | 位置模拟协程（演示） |

---

## 后台协程（`backend/workers.py`）

由 FastAPI `lifespan` 在启动时拉起，统一由 `WorkerManager` 管理：

- **`mqtt-worker`（线程）**：MQTT 订阅，命中后调用 `app_service.process_mqtt_payload` 并向 Socket.IO 推送 `device_update`。
- **`offline-check`（协程）**：每 5 秒检查一次，超过 `OFFLINE_TIMEOUT_SEC`（默认 10s）未上报的设备标记为离线。
- **`position-broadcast`（协程）**：演示用，按 `POSITION_UPDATE_INTERVAL_SEC` 周期微调设备坐标并推送 `position_update`。
- **`llm-analysis`（协程，仅 `LLM_ENABLED=True`）**：轮询 `alarm_images` 中 `pending` 项，调用 LLM 生成报警图片描述。

---

## 关键数据模型（SQLite）

主要表参见 `backend/repositories/database.py`：

- **`devices`**：设备名 / 在线状态 / 最近心跳 / 坐标 / 版本
- **`alarms`**：报警事件（`device_id` `alarm` `timestamp` `image_description` …）
- **`alarm_images`**：报警图片元数据（`image_path` `description_status`：pending / done / failed）
- **`alarm_sessions`**：报警会话起止与持续时长
- **`logs`**：运维 + 业务日志（分页查询见 `/api/logs`）

---

## 深度文档

- [`docs/communication-layer.md`](docs/communication-layer.md)：MQTT / HTTP / Socket.IO 三层通信与设备对接指南（含 FAQ）
- [`docs/image-upload-guide.md`](docs/image-upload-guide.md)：图片上传流程、接口字段、Python 设备端示例
- [`docs/bun-help.md`](docs/bun-help.md)：Bun 替代 npm 的常用命令速查
- [`docs/simulation-demo.md`](docs/simulation-demo.md)：仿真演示运行方式、剧本与调参

---

## 常见问题

1. **首页返回 503 "Frontend build not found"**
   未构建前端。`cd frontend && bun run build` 后重启后端。

2. **MQTT 连接失败 / 收不到设备消息**
   检查 `.env` 或 `backend/settings.py` 中的 `MQTT_BROKER` / `MQTT_PORT`；本地需安装并启动 Mosquitto 等 broker；生产环境建议将 `MQTT_REQUIRED` 设为 `True` 强依赖。

3. **图片上传 400 / 413**
   400 通常是格式不在 `ALLOWED_IMAGE_EXTENSIONS`（`png jpg jpeg gif bmp webp`）内；413 是超过 `MAX_IMAGE_SIZE_MB`（默认 16MB）。

4. **前端看不到实时更新**
   确认后端日志中有 `socket.client.connected` 与 `device_update` 推送；浏览器控制台检查 WebSocket / Socket.IO 连接状态；防火墙是否放行了对应端口。

5. **仿真数据污染了正式库？**
   不会。`tests/edge_node_client.py` 使用独立数据库 `alarm_demo.db`，不会触碰 `alarm.db`。若仍不放心，启动仿真前可手动备份 `alarm.db`。

6. **如何接入一台新的真实设备？**
   在 `device/src/intelli_shield/config.py` 中修改 `DEVICE_ID` / `SERVER_BASE_URL` / `MQTT_BROKER` / `MQTT_PORT` 后重新部署；并确保该 `device_id` 在云端 `backend/services/app_service.py::DEVICE_IDS` 与 `repositories/database.py::init_device_positions` 中存在（演示环境默认预置 `FORK-001/002/003`）。

---

## 许可证与免责

仓库内的地图底图（`frontend/public/map.jpg`）、`logo.png` 与示例报警数据**仅用于教学与演示**，请勿用于真实工业部署。生产环境请完成威胁评估、鉴权启用（`AUTH_ENABLED=True`）与数据脱敏。
