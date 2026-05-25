# 智盾 Intelli Shield

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![YOLO](https://img.shields.io/badge/YOLO-000000?style=flat&logo=yolo&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-3C52F0?style=flat&logo=mqtt&logoColor=white)

</div>

智盾 Intelli Shield 是一个端云协同的人车互斥安全预警系统，面向厂区叉车、矿山运输等工业安防场景。

## 项目定位

以“识别、划区、报警、留痕、分析”为闭环，让现场风险可视、可听、可追溯，并通过云端沉淀实现管理优化。

## 功能亮点

- 端侧实时识别人与车辆的相对距离，毫秒级触发预警
- 三线激光划区，危险边界可视化
- 语音与声光联动报警，现场干预更直接
- 报警事件留痕上云，支持查询与复盘
- 数字孪生地图与看板呈现风险态势（持续完善中）

## 技术栈

- **设备端**：MaixCAM + Python，端侧识别与本地报警联动
- **云端后端**：FastAPI + Uvicorn，MQTT/Socket.IO 通信
- **前端**：Vue 3 + Vite + Element Plus，ECharts/Chart.js 数据可视化

## 项目结构

- **[device/](device/)**: 设备端代码（基于 MaixCAM），负责人员检测、报警逻辑、本地日志及图片上传。
- **[cloud/](cloud/)**: 云端代码，负责接收设备上报的数据、存储及前端展示。

## 快速开始

### 1) 设备端
请参考 [device/README.md](device/README.md) 进行部署。

### 2) 云端
请参考 [cloud/README.md](cloud/README.md) 进行部署。

### 3) 前端
前端位于 [cloud/frontend/](cloud/frontend/)，可按其中 `package.json` 的脚本进行开发与构建。
