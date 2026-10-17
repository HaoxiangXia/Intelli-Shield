# 智盾 Intelli Shield

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![YOLO](https://img.shields.io/badge/YOLO-000000?style=flat&logo=yolo&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-3C52F0?style=flat&logo=mqtt&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat&logo=vue.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)

</div>

智盾 Intelli Shield 是一个端云协同的人车互斥安全预警系统，面向厂区叉车、矿山运输等工业安防场景。

> 完整产品需求、目标用户、MVP 范围、里程碑与团队分工见 [`PRD.md`](PRD.md)。

## 项目定位

以“识别、划区、报警、留痕、分析”为闭环，让现场风险可视、可听、可追溯，并通过云端沉淀实现管理优化。

## 功能亮点

- 端侧与高位 CCTV 实时识别人车交互与地面红光警戒线
- 突破人类生理极限反应时间：端到端感知决策全链路仅约 113ms（严格低于人类 250~400ms 生理反应极限），实现亚秒级先验干预与动力切断
- 三向激光地表划区，物理禁行边界拓扑实时判别
- 引入中科院自动化所 OmniJev-4B 决策大模型，单前向零 Token 输出校准概率与高维危险行为归因
- 语音、声光与无线动力联锁联动报警，现场干预更直接
- 报警事件留痕上云，支持查询与复盘
- 数字孪生地图与看板呈现风险态势

## 技术栈

| 端 | 关键组件 |
|---|---|
| 设备端 | MaixCAM Pro + YOLO11n + Python（MaixPy v4.12）；UART 串口对接 STM32 控制 LED / 蜂鸣器 / OLED |
| 云端后端 | FastAPI + Uvicorn + paho-mqtt + python-socketio + SQLite；可选 LLM 多模态描述（OpenAI 兼容）；依赖由 uv 统一管理 |
| 感知流水线 | OpenCV DNN (Darknet YOLOv4) + SpatialTemporalGate 门控 + OmniJev-4B (中科院自动化所 / 中关村学院 / Zevo) 探针 + 风险仲裁机；依赖由 uv 统一管理 |
| 前端 | Vue 3 + Vite + Element Plus + ECharts（vue-echarts）+ socket.io-client + Bun/npm |

## 端云协同数据流

```
设备端 (MaixCAM)              云端 (FastAPI)                前端 (Vue 3)
─────────────────            ─────────────                ──────────
[双状态机判定报警]
   │
   │  HTTP 上传图片 ─────────▶│  images/alarms/ + alarm_images
   │                          │
   │  ◀── image_urls ─────────│
   │
   │  MQTT 报警状态 ─────────▶│  WorkerManager → SQLite
   │                          │           ↓
   │                          │  Socket.IO ────────────▶  Dashboard 实时刷新
```

## 目录结构

```text
智盾 Intelli Shield/
├── README.md          ← 本文件
├── PRD.md             ← 产品需求文档
├── device/            ← 设备端模块（MaixCAM + STM32）
│   ├── src/           ← 主程序 + intelli_shield 核心包
│   ├── docs/          ← 设备端深度文档
│   ├── export.py      ← PC 端模型导出工具
│   ├── uart_test.py   ← 串口链路联调脚本
│   └── README.md      ← 设备端 README
└── cloud/             ← 云端模块（FastAPI + Vue 3）
    ├── backend/       ← FastAPI + MQTT + Socket.IO + LLM + SQLite
    ├── frontend/      ← Vue 3 + ECharts 看板
    ├── tests/         ← 仿真演示（edge_node_client.py）
    ├── docs/          ← 云端深度文档（通信层 / 上传指南 / Bun / 仿真）
    ├── images/        ← 报警图片存储
    └── README.md      ← 云端 README
```

## 关键文档

| 文档 | 用途 |
|---|---|
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | **快速部署指南（Linux / Windows PowerShell 双版本）** |
| [`PRD.md`](PRD.md) | 产品需求、目标用户、MVP 范围、里程碑与团队分工 |
| [`device/README.md`](device/README.md) | 设备端模块说明（MaixCAM 部署、双状态机、UART 协议、云上报） |
| [`cloud/README.md`](cloud/README.md) | 云端模块说明（后端 / 前端 / 仿真 / API / 实时通道 / FAQ） |
| [`device/docs/`](device/docs/) | 设备端深度文档（`introduction.md` / `main_flow.md` / `logger.md` / `event_log_example.md`） |
| [`cloud/docs/`](cloud/docs/) | 云端深度文档（`communication-layer.md` / `image-upload-guide.md` / `bun-help.md` / `simulation-demo.md`） |

## 快速开始

> 完整的 Linux / Windows PowerShell 部署步骤（含环境变量、冒烟验证、故障排查）见 **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)**。

### 1) 依赖安装（使用 uv）
```bash
# 一键同步流水线与开发工具依赖
uv sync

# 或一键同步全部组件（流水线 + 云端后端）
uv sync --all-packages
```

### 2) 感知流水线快速运行
```bash
uv run python -m pipeline.runner \
  --video samples/cctv/videos/output_video7.mp4 \
  --replay samples/cctv/benchmarks/cctv_frames_metadata.json
```

### 3) 云端后端与看板快速启动
```bash
# 前端构建（首次需执行）
cd cloud/frontend && bun install && bun run build && cd ../..

# 启动云端服务
cd cloud && uv run python -m backend.app
```

### 4) 设备端
请参考 [device/README.md](device/README.md) 进行部署。

## 后续规划 (Roadmap)

- [ ] **多路高位 CCTV 并发与动态批处理 (Multi-Stream Dynamic Batching)**：充分利用 OmniJev-4B 单前向计算与 3090 显存裕量，支持 16~32 路摄像头通过异步批处理队列（Batch Size 4~8）并发调度，结合边缘红光几何门控，将单路平摊时延压降至 60ms 内。
- [ ] **实车 CAN 总线无线动力切断套件工程化**：实装车载无线电控继电器，落地两段式动力联锁与全厂区通道风险热力图。
- [ ] **数据不出厂的联邦微调架构 (Federated Learning)**：沉淀现场安全责任人核验样本对，在边缘节点进行 LoRA 增量对齐微调。
- [ ] **边缘端 INT4/GGUF 量化部署**：探索利用轻量工控机离线部署，进一步降低中小型工厂硬件采购门槛。
