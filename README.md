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

- 端侧实时识别人与车辆的相对距离，毫秒级触发预警
- 三线激光划区，危险边界可视化
- 语音与声光联动报警，现场干预更直接
- 报警事件留痕上云，支持查询与复盘
- 数字孪生地图与看板呈现风险态势（持续完善中）

## 技术栈

| 端 | 关键组件 |
|---|---|
| 设备端 | MaixCAM Pro + YOLO11n + Python（MaixPy v4.12）；UART 串口对接 STM32 控制 LED / 蜂鸣器 / OLED |
| 云端后端 | FastAPI + Uvicorn + paho-mqtt + python-socketio + SQLite；可选 LLM 多模态描述（OpenAI 兼容） |
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
| [`PRD.md`](PRD.md) | 产品需求、目标用户、MVP 范围、里程碑与团队分工 |
| [`device/README.md`](device/README.md) | 设备端模块说明（MaixCAM 部署、双状态机、UART 协议、云上报） |
| [`cloud/README.md`](cloud/README.md) | 云端模块说明（后端 / 前端 / 仿真 / API / 实时通道 / FAQ） |

## 快速开始

### 1) 设备端
请参考 [device/README.md](device/README.md) 进行部署。

### 2) 云端
请参考 [cloud/README.md](cloud/README.md) 进行部署。
