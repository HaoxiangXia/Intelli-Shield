# Intelli-Shield 快速部署指南

面向“第一次拿到仓库、想尽快跑起来”的开发者。两个可独立部署的子系统：

| 子系统 | 目录 | 技术栈 | 用途 |
|---|---|---|---|
| **感知-决策流水线** | 仓库根 + `pipeline/` | Python + OpenCV DNN (YOLOv4) | 视频 → 目标检测 → 门控 → OmniJev 探针 → 风险仲裁 |
| **云端看板** | `cloud/` | FastAPI + Socket.IO + SQLite + Vue 3 | 接收报警、落库、实时推送、2D 数字孪生看板 |

两者**没有编译期依赖**：流水线可以完全离线跑（replay 模式），云端可以完全脱离 GPU 单独跑（仿真模式）。建议按“流水线 → 云端 → 仿真演示”顺序部署。

> 概念说明见 `AGENTS.md`；架构决策见 `docs/adr/`；云端细节见 `cloud/README.md`。

---

## 0. 环境要求

| 组件 | 版本 | 是否必需 | 备注 |
|---|---|---|---|
| [uv](https://docs.astral.sh/uv/) | ≥ 0.4 | **必需** | 统一管理流水线、开发工具与云端依赖（`uv sync` / `uv run`） |
| Python | 3.10 – 3.13 | 必需 | 根目录与 `cloud/` 已通过 `.python-version` 锁定 3.13；uv 可自动下载 |
| Node.js | ≥ 20 | 二选一 | npm / pnpm 用户 |
| [Bun](https://bun.sh/) | ≥ 1.0 | 二选一 | 前端依赖安装更快（仓库含 `bun.lock`） |
| OpenCV DNN 权重 | — | 必需 | `models/*.weights` 被 `.gitignore` 忽略，需单独拷贝 |
---

## 1. 获取代码与模型资产

```bash
git clone <repo-url> Intelli-Shield
cd Intelli-Shield
```

`.gitignore` 忽略了 `*.weights` / `*.pt` / `*.mp4`，**克隆后不含权重与视频**。需要从导师/项目持有者处补齐：

| 路径 | 用途 | 缺失后果 |
|---|---|---|
| `models/yolov4-custom-hebei_last.weights` | 导师训练的 YOLOv4 Darknet 权重（**唯一必须手动拷贝的模型文件**） | 检测器打印 `Warning: Could not find model files`，检测恒为空，全部帧 `NORMAL` |
| `samples/cctv/videos/output_video7.mp4` | 流水线冒烟与演示主素材（1920×1080 实景） | `runner.py` 无法启动 |
| `samples/cctv/videos/demo_forklift.mp4` | 合成素材（可选） | 不影响主流程 |
| `cloud/frontend/public/samples/cctv/videos/output_video7.mp4` | 看板视频回放 | 页面能打开，但视频区 404（详见第 7 节） |

> 已入库无需补齐：`models/yolov4-custom-hebei.cfg`、`models/voc-hebei.names`、`samples/cctv/raw_images/*.png`、`samples/cctv/benchmarks/*.json`。

---

## 2. 部署感知-决策流水线

### 2.1 Linux / macOS

```bash
cd Intelli-Shield

# 1) 使用 uv 一键同步流水线与开发依赖（自动创建 .venv 并锁定依赖）
uv sync

# 若需要同时同步云端后端与所有工具，可加 --all-packages
# uv sync --all-packages

# 2) 冒烟：跑 5 帧，确认权重加载成功（无需手动激活虚拟环境，uv run 自动托管）
uv run python -m pipeline.runner \
  --video samples/cctv/videos/output_video7.mp4 \
  --max-frames 5
```

### 2.2 Windows（PowerShell）

```powershell
cd Intelli-Shield

# 1) 使用 uv 同步依赖
uv sync

# 2) 冒烟运行
uv run python -m pipeline.runner `
  --video samples/cctv/videos/output_video7.mp4 `
  --max-frames 5
```

预期输出包含 `[YOLODetector] Loaded advisor YOLOv4 Darknet: models/yolov4-custom-hebei.cfg (14 classes)`，且逐帧打印 `Frame #0001 | [NORMAL] | Ped: 3 | Forklift: 2 | Dist: 25.8px | ...`；若是 `Warning: Could not find model files`，回到第 1 节补齐权重。

> **注意**：合成样例 `demo_forklift.mp4` 用导师 YOLOv4 权重跑出来是**零检测**（`Ped: 0 | Forklift: 0`），全帧 `NORMAL` 属正常现象，不是环境故障。冒烟请用真实素材 `output_video7.mp4`。
### 2.3 四种运行模式

| 模式 | 命令（Linux） | PowerShell 等价 | 说明 |
|---|---|---|---|
| **离线回放**（答辩推荐） | `uv run python -m pipeline.runner --video samples/cctv/videos/output_video7.mp4 --replay samples/cctv/benchmarks/cctv_frames_metadata.json` | `uv run python -m pipeline.runner --video samples\cctv\videos\output_video7.mp4 --replay samples\cctv\benchmarks\cctv_frames_metadata.json` | 不依赖 GPU 集群，回放 752 帧实测探针结果（RTX 3090，107 ms） |
| **实时探针** | `uv run python -m pipeline.runner --video <mp4> --endpoint http://<gpu-host>:8000/probe` | 同左 | 先 `sbatch slurm/serve_omnijev.sh` 拉起探针服务，再 `ssh -N -L 8000:<node>:8000 <user>@<host>` 打隧道 |
| **关闭门控（对照实验）** | `uv run python -m pipeline.runner --video <mp4> --no-gating` | 同左 | 只要画面同时有人与车就发起探针，用于对比门控省下的 GPU 开销 |
| **探针不可用（自动降级）** | 不加 `--endpoint`，或让 8000 端口不通 | 同左 | `OmniJevEngine.evaluate()` 返回 `None`，`RiskFusionEngine` 自动回退到纯像素距离规则（`<120px → CRITICAL`），不中断流水线 |

常用参数：`--fps`（默认 10）、`--conf`（默认 0.25）、`--gating-dist`（默认 250 px）、`--static-frames`（默认 3）、`--max-frames`。

> **性能预期**：YOLOv4 Darknet 在纯 CPU 上约 0.4–0.5 FPS（1920×1080，608 输入，OpenCV DNN）。整段 30 s 视频全量跑完需数十分钟——演示请用 `--max-frames` 或 `--fps 2` 抽帧，或直接用回放模式。`--fps` 只控制抽帧间隔，不改变单帧检测耗时。

> **回放日志格式**：`--replay` 读取的 JSON 必须是 `{"frames": [{"frame_id": <int>, "probes": {...}}, ...]}`。`cctv_frames_metadata.json`（752 帧）符合；`probe_real_cctv.json` / `perception_real_cctv.json` 是给渲染脚本用的单帧汇总，**不符合**，传入后回放缓存为空（未命中缓存的帧仍会走 HTTP 探针）。演示时把视频与回放日志帧号对齐即可全程离线复现，无需 GPU。

### 2.4 辅助工具（可选）

```bash
# 单图推理校验，输出标注图到 samples/cctv/keyframes/yolov4_result.png
uv run python infer_yolov4.py

# 抽帧重跑感知 + 门控，重建 benchmarks/*.json
uv run python scripts/rebuild_all_benchmarks.py

# 带 HUD 的决策可视化视频（Pillow 已默认随 uv sync 安装）
uv run python render_video_pipeline.py

后两个脚本面向数据重建与答辩素材制作，日常演示不需要。

### 2.5 流水线单元测试

```bash
uv run python -m unittest discover -s tests -v
```

> 两平台命令相同，`uv run` 自动保证虚拟环境与依赖一致性。

> **已知失败**：`tests/test_spatial_gating.py::test_driver_exclusion` 当前 FAIL（`Gate should NOT trigger for on-board driver!`）——`_is_driver_inside_vehicle` 的驾驶员排除判定与测试期望不一致。这是**部署前就存在的代码缺陷**，不是环境问题；其余 3 项通过。不要为了让测试变绿而删改断言。

---

## 3. 部署云端后端 + 前端

### 3.1 Linux

```bash
cd Intelli-Shield/cloud

# 1) 后端依赖（已纳入 uv workspace，可单独同步或在根目录 uv sync --all-packages）
uv sync
printf 'APP_HOST=0.0.0.0\nAPP_PORT=5000\nMQTT_REQUIRED=false\nLLM_ENABLED=false\n' > .env
# 编辑 .env：至少确认 MQTT_BROKER / APP_PORT（模板见 3.3 节）

# 2) 前端依赖与构建（产物必须存在，否则首页 503）
cd frontend
bun install                   # 或 npm install
bun run build                 # 产物 frontend/dist/
cd ..

# 3) 启动（默认 0.0.0.0:5000）
uv run python -m backend.app
```

### 3.2 Windows（PowerShell）

```powershell
cd Intelli-Shield\cloud

# 1) 后端依赖
uv sync
@"
APP_HOST=0.0.0.0
APP_PORT=5000
MQTT_REQUIRED=false
LLM_ENABLED=false
"@ | Set-Content -Encoding utf8 .env
notepad .env                   # 按需补充 MQTT_BROKER / OPENAI_API_KEY

# 2) 前端
cd frontend
bun install
bun run build
cd ..

# 3) 启动
uv run python -m backend.app
```

### 3.3 环境变量（完整列表见 `cloud/backend/settings.py`）

| 变量 | 默认 | 说明 |
|---|---|---|
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `5000` | 后端监听 |
| `MQTT_BROKER` / `MQTT_PORT` | `localhost` / `1883` | MQTT 代理 |
| `MQTT_TOPIC` | `factory/forklift/+/alarm` | 订阅主题 |
| `MQTT_REQUIRED` | `False` | 生产建议 `True` |
| `DB_PATH` | `alarm.db` | SQLite 路径（相对 `cloud/`） |
| `OFFLINE_TIMEOUT_SEC` | `10` | 超时判离线 |
| `LLM_ENABLED` / `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `LLM_MODEL` | 自动 / 空 / 空 / `gpt-4.1-mini` | 报警图片描述，可选 |

最小 `.env` 模板（无 MQTT 也能启动）：

```dotenv
APP_HOST=0.0.0.0
APP_PORT=5000
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_REQUIRED=false
LLM_ENABLED=false
```

### 3.4 前端开发模式（可选）

```bash
cd cloud/frontend && bun run dev      # http://localhost:3000，/api 与 /images 反代到 :5000
```

生产模式只需 `bun run build` —— 后端直接托管 `frontend/dist/index.html`，**不需要**单独跑 dev server。

---

## 4. 一键仿真演示（无硬件、无 GPU）

需要先完成 3.1/3.2 的“前端构建”，`tests/edge_node_client.py` 会校验 `frontend/dist/index.html` 存在。

```bash
cd cloud
uv run python tests/edge_node_client.py
```

```powershell
cd Intelli-Shield\cloud
uv run python tests\edge_node_client.py
```

终端会打印随机可用端口的 URL（如 `http://localhost:51247`）并自动打开浏览器，3 台叉车按剧本巡航触发预警 / 解除。使用独立数据库 `alarm_demo.db`，不污染 `alarm.db`。

调参：`DEMO_FRAME_INTERVAL_SEC`（默认 0.2 s）控制巡航速度。

---

## 5. 接入真实设备 / GPU 集群

```bash
# 1) RTX 3090 节点环境（一次性）
bash slurm/setup_env.sh

# 2) 拉起 OmniJev 探针服务（占用 compute node:8000）
sbatch slurm/serve_omnijev.sh

# 3) 本地端口转发
ssh -N -L 8000:<compute_node_name>:8000 <user>@<cluster_host>

# 4) 整段视频批量推理
sbatch slurm/run_real_3090.sh
```

设备端上报协议（MQTT payload / HTTP 上传）见 `cloud/docs/communication-layer.md`、`cloud/docs/image-upload-guide.md`。

---

## 6. 部署后自检清单

| # | 检查 | 期望 |
|---|---|---|
| 1 | `uv run python -m pipeline.runner --video samples/cctv/videos/output_video7.mp4 --max-frames 5` | 打印 `Loaded advisor YOLOv4 Darknet (14 classes)`，逐帧输出 `Frame #0001 \| [NORMAL] \| Ped: 3 \| Forklift: 2 \| ...` |
| 2 | `curl http://localhost:5000/api/latest`（PowerShell：`Invoke-RestMethod http://localhost:5000/api/latest`） | `{"devices":[...],"stats":{...}}` |
| 3 | 浏览器打开 `http://localhost:5000/` | 看板首页渲染（不是 503） |
| 4 | `cd cloud && uv run python tests/edge_node_client.py` | 打印 URL，地图上出现叉车点位与报警环 |
| 5 | `uv run python -m unittest discover -s tests` | 4 项中 3 通过；`test_driver_exclusion` 已知失败 |
---

## 7. 常见问题

**首页 503 "Frontend build not found"**
未构建前端。在 `cloud/frontend` 执行 `bun install && bun run build` 后重启后端。

**看板视频区 404，但页面正常**
`IncidentTriageDock` 与 `TacticalRadarTwin` 硬引用 `/samples/cctv/videos/output_video7.mp4`，而 `*.mp4` 被 `.gitignore` 忽略不入库。手动把视频放到 `cloud/frontend/public/samples/cctv/videos/` 后重新 `bun run build`。同目录下的 5 张 keyframe PNG 与 benchmarks JSON 已入库，不受影响。

**检测结果全为空 / 全部 NORMAL**
先看启动日志有没有 `Loaded advisor YOLOv4 Darknet`：没有则是 `models/yolov4-custom-hebei_last.weights` 缺失（被 gitignore），补齐后重跑；若已加载但视频是 `demo_forklift.mp4`，零检测是合成素材与导师权重的正常表现，换 `output_video7.mp4`。

**探针全部 `Probes Unavailable`**
GPU 服务未起或隧道未开。`curl -X POST http://127.0.0.1:8000/probe` 自检；未起时流水线会自动降级到纯几何规则，不会崩溃。

**MQTT 连接失败**
装 Mosquitto 或改 `MQTT_BROKER`。开发期保持 `MQTT_REQUIRED=false` 可让后端在无 broker 时正常启动。

**图片上传 400 / 413**
扩展名不在白名单（`png jpg jpeg gif bmp webp`）或超过 `MAX_IMAGE_SIZE_MB`（默认 16）。

**Linux 上 Windows 换行/路径问题**
所有默认路径均为相对仓库根目录；务必在仓库根执行 `python -m pipeline.runner`，或在 `cloud/` 下执行 `python -m backend.app`。

**PowerShell 执行策略拦截**
无需运行 `Activate.ps1`，直接使用 `uv run <command>` 即可无缝跨平台调用虚拟环境。

---

## 8. 演示前 5 分钟检查（答辩用）

1. 用**离线回放模式**跑一遍演示视频，确认决策序列可复现（不依赖集群网络）。
2. 云端执行 `python tests/edge_node_client.py`，确认浏览器自动打开且叉车动起来。
3. 关闭一切依赖外网的功能（LLM 描述可设 `LLM_ENABLED=false`），确保断网也能完整演示。