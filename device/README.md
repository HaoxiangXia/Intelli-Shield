# 智盾 Intelli Shield · 设备端模块 (Device)

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![YOLO](https://img.shields.io/badge/YOLO-000000?style=flat&logo=yolo&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-3C52F0?style=flat&logo=mqtt&logoColor=white)
![MaixCAM](https://img.shields.io/badge/MaixCAM-Pro-orange)

</div>

本目录是「**[智盾 Intelli Shield](../README.md)**」端云协同人车互斥安全预警系统的**设备端子模块**，承担端侧实时人员检测、双状态机去抖、本地报警联动与报警事件/快照上云。

> **项目归属说明**：本目录代码与文档源自校内大创项目「YSU2026 大创项目-基于 YOLO 的叉车作业人车互斥报警系统」，现作为智盾 Intelli Shield 的设备端模块继续迭代。
> 项目整体定位、目标用户、MVP 范围、里程碑与团队分工见根目录 [`README.md`](../README.md) 与 [`PRD.md`](../PRD.md)。
> 云端模块（事件落库、实时推送、看板、AI 分析）见 [`../cloud/README.md`](../cloud/README.md)。

### 子目录导航

- [`src/main.py`](src/main.py)：MaixCAM 主程序入口
- [`src/intelli_shield/config.py`](src/intelli_shield/config.py)：全局配置（模型/ROI/串口/云端）
- [`src/intelli_shield/detector.py`](src/intelli_shield/detector.py)：YOLO11 推理封装
- [`src/intelli_shield/logic.py`](src/intelli_shield/logic.py)：双 ROI + 双状态机报警逻辑
- [`src/intelli_shield/cloud_reporter.py`](src/intelli_shield/cloud_reporter.py)：HTTP 上传、MQTT 发布、补传队列
- [`src/intelli_shield/logger.py`](src/intelli_shield/logger.py)：运维 + 业务双通道日志
- [`docs/introduction.md`](docs/introduction.md)：设备端项目介绍与硬件参数
- [`docs/main_flow.md`](docs/main_flow.md)：`main.py` 主循环流程与时序
- [`docs/logger.md`](docs/logger.md)：事件日志与运维日志设计
- [`docs/event_log_example.md`](docs/event_log_example.md)：日志样例
- `export.py`：PC 端 YOLO 模型导出工具
- `uart_test.py`：UART 串口链路联调脚本

---

## YSU2026 大创项目-基于 YOLO 的叉车作业人车互斥报警系统

<div align="center">

[![DeepWiki](https://deepwiki.com/api/badge.svg?url=https%3A%2F%2Fdeepwiki.com%2FHaoxiangXia%2Fyolo-forklift-safety-system)](https://deepwiki.com/HaoxiangXia/yolo-forklift-safety-system)

</div>

本项目是一款基于 **MaixCAM Pro** (MaixPy v4.12) 与 **YOLO11** 模型的嵌入式边缘 AI 系统，专为厂区叉车作业安全设计。系统通过实时视觉感知与双状态机决策，实现“驾驶员在位”与“危险区入侵”的联合逻辑判断，并通过 **UART 串口** 同步信号至 **STM32** 控制终端（驱动 LED、蜂鸣器及 OLED 显示）。

---

### 核心特性

- **高效推理**：基于 YOLO11n 模型，针对 **person** 类别进行优化，支持双缓冲区推理提升帧率。
- **双 ROI 决策**：将画面划分为 **中心 ROI (驾驶员区)** 与 **外围 ROI (作业危险区)**。
- **高可靠报警（互斥逻辑）**：仅当 **司机在位** (Center=ON) 且 **外围有人** (Outer=ON) 时触发报警，有效防止虚假报警。
- **云端联动**：MaixCAM 直连云端，支持报警快照本地保存、HTTP 图片上传及 MQTT 报警状态发布。
- **回溯抓拍**：触发报警时自动提取 t-3, t-2, t-1, t 四帧关键图像上报。
- **通信保护**：STM32 端具备心跳超时检测，5 秒未收到 MaixCAM 信号即强制报警以确保故障安全。
- **可靠日志**：系统化记录状态切换、初始化故障、UART 错误及补传队列状态。

---

### 工作原理

1. **图像采集与推理**：MaixCAM Pro 实时采集画面，通过 YOLO11 推理检测所有人类目标。
2. **位置判定**：
   - 目标中心点在 **中心 ROI**：标记为可能的驾驶员。
   - 目标中心点在 **外围 ROI**：标记为可能的入侵者。
3. **双状态机去抖**：
   - **Center 状态机**：需连续 5 帧检测到驾驶员才置为 ON，连续 10 帧未见则 OFF。
   - **Outer 状态机**：需连续 5 帧检测到入侵者才置为 ON，连续 8 帧未见则 OFF。
4. **报警逻辑**：`Alarm = Center_State AND Outer_State`。
5. **信号输出**：
   - **UART**：发送加密校验包 `<ALARM:1,D8>` 或 `<ALARM:0,D7>`。
   - **云端**：MQTT 发布 `{ "device_id": "FORK-006", "status": "alarm", "image_url": "..." }`。
6. **终端动作**：STM32 接收信号后控制 GPIO（LED/蜂鸣器）并在 OLED 屏显示实时状态。

---

### 📂 项目目录结构

#### MaixCAM 端 ([src/](src/))
- [src/main.py](src/main.py): 系统入口，协调视觉、逻辑与上报模块。
- [src/intelli_shield/detector.py](src/intelli_shield/detector.py): YOLO 推理引擎，支持双缓冲。
- [src/intelli_shield/logic.py](src/intelli_shield/logic.py): 核心业务逻辑（双 ROI + 双状态机）。
- [src/intelli_shield/cloud_reporter.py](src/intelli_shield/cloud_reporter.py): 报警图像 HTTP 上传、MQTT 发布及失败重传。
- [src/intelli_shield/config.py](src/intelli_shield/config.py): 全局配置中心（UART 引脚、阈值、云端地址）。
- [src/intelli_shield/logger.py](src/intelli_shield/logger.py): 分级日志系统。

#### STM32 接收端
STM32 端固件（主控源码 / OLED 驱动 / 凭据模板）维护在独立仓库，未纳入本仓。MaixCAM → STM32 的串口协议与心跳机制保持不变。

---

### 串口通信协议

数据采用 ASCII 格式，通过校验和确保完整性：
- **格式**：`<DATA,CHECKSUM>`
- **校验和算法**：所有字符 ASCII 值累加后对 256 取模。
- **心跳包**：`<HB,8A>`（每 1.5 秒发送）。

### 镜头参数

30fps @ 2560*1440

1/3" CMOS

3.05mm

F2.5

