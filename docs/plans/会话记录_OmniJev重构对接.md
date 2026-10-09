# Intelli-Shield 项目重构与 OmniJev 融合方案 — 完整会话记录

**记录时间**：2026-10-09  
**协作双方**：用户（项目负责人）与 Gemini（omp AI 编程助手）  
**工程目标**：在一周内完成 Intelli-Shield 人车预警项目与 OmniJev（System 1 多模态决策模型）的融合与包装，面向导师进行汇报演示。

---

## 目录
1. [第一轮交互：方案重构与一周汇报计划制定](#第一轮交互方案重构与一周汇报计划制定)
2. [第二轮交互：远程主机连接与 Git 重构分支建立](#第二轮交互远程主机连接与-git-重构分支建立)
3. [第三轮交互：远程终端与 Herdr 工作区接入](#第三轮交互远程终端与-herdr-工作区接入)
4. [第四轮交互：Herdr 新建专属 Workspace 与会话存档](#第四轮交互herdr-新建专属-workspace-与会话存档)
5. [附录：关键文件与资源清单](#附录关键文件与资源清单)

---

## 第一轮交互：方案重构与一周汇报计划制定

### 用户需求指令：
> “看一下 行知.md，给一个把这个项目融合omnijev的计划，写成md文件，不求效果，只是为了在一周内使用Gemini（你）完成包装向老师汇报，测试和检验效果的数据是传统的厂区墙上的监控摄像头的图片和视频，可以放弃使用maixcam pro，而是转为在服务器运行yolo和omnijev”

### 核心约束与研判：
1. **时间周期**：极度紧迫（一周内交付向导师汇报）。
2. **重心取向**：不追求真实的 SOTA 指标或工业级泛化鲁棒性，核心目标是**讲通叙事逻辑、端到端演示跑通、架构高级且有理论支撑、准备好防守答辩**。
3. **硬件解耦**：彻底放弃车端 MaixCAM Pro 与 STM32 硬件联动，避免边端交叉编译、串口通信及硬件损耗的不可控风险。
4. **数据源切换**：从“车载动态镜头”全面转向“厂区墙面固定高位 CCTV 监控摄像头图片/视频”。
5. **模型选型认知**：
   - OmniJev（OneJev）为 0.8B ~ 27B 的 System 1 多模态决策模型。
   - 特点：单次前向推理（One Forward Pass），零生成 Token 开销（Zero Generated Tokens），30~60ms 毫秒级输出校准概率（Calibrated Probability），支持 `Choice`、`Noul`、`Score` 探针。
   - 相比传统自回归慢思考多模态大模型（System 2，如 GPT-4o、Qwen-VL 的 2~4 秒延迟且格式不可控），OmniJev 天然适合工业实时控制。

### 执行动作与产出文件：
- 完整编写并输出了方案文件：`OmniJev融合实施与汇报准备计划.md`。
- **包含内容**：
  1. **汇报叙事重构**：从“千台叉车逐车加装改造成本高、车载镜头剧烈颠簸”转为“厂区既有固定 CCTV 零改装成本、全盲区覆盖”；从“慢速生成大模型”转为“System 1 毫秒级校准概率快决策”。
  2. **系统技术架构**：CCTV 视频流 → 服务端 YOLOv11（人车检测与交互区动态裁剪）→ OmniJev 决策探针（碰撞概率、工人注意力分布、威胁等级）→ Intelli-Shield Web 大屏。
  3. **双轨保底策略**：轨道 A（真实 OneJev-0.8B/4B） + 轨道 B（无 GPU/低配环境下 100% 格式兼容的高保真 Mock 探针代理）。
  4. **7天敏捷实施路线图**（Day 1 架构解耦 ~ Day 7 汇报 PPT 与视频录制）。
  5. **三维对比实验矩阵**（传统规则 vs 生成大模型 vs YOLO+OmniJev 快决策）。
  6. **导师高频答辩 3 大质询及标准高情商应答话术**。
  7. **每日协同 Prompt 工具包**。

---

## 第二轮交互：远程主机连接与 Git 重构分支建立

### 用户需求指令：
> “用ssh连接到my-Mint这个主机，在～/下new一个文件夹，从GitHub或者本机把项目文件传过去都行，只要GitHub仓库里的和让你刚才写的那个计划md文件，然后新开一个git分支来进行项目重构，先不要改代码，传输完文件来请示我”

### 执行动作与核验：
1. **SSH 连通性测试**：
   - 成功连接 `my-Mint` 主机（Linux xiang-Mint，Ubuntu 24.04 内核，x86_64）。
2. **仓库克隆**：
   - 执行 `git clone -b dev git@github.com:HaoxiangXia/Intelli-Shield.git ~/Intelli-Shield`，克隆至远程 `/home/xiang/Intelli-Shield`。
3. **计划文件传输**：
   - 通过 SCP 将 `OmniJev融合实施与汇报准备计划.md` 安全复制至远程目录 `~/Intelli-Shield/`。
4. **Git 分支切换**：
   - 在远程仓库创建并检出新分支：`refactor/omnijev-fusion`。
   - 严格恪守指令：**未对代码做任何修改**，保持原始状态并汇报请示。

---

## 第三轮交互：远程终端与 Herdr 工作区接入

### 用户需求指令：
> “你能不能操作远程主机的终端，运行herdr”

### 执行动作与核验：
1. **查找定位**：
   - 在远程主机成功检索到 `herdr` 安装路径：`/home/xiang/.local/bin/herdr`（v0.9.1）。
   - 确认配置文件及 Socket 路径：`/home/xiang/.config/herdr/`。
2. **启动后台服务**：
   - 发现后台守护进程处于 `stopped` 状态，执行 `nohup ~/.local/bin/herdr server >/dev/null 2>&1 &` 启动后台服务。
   - 验证服务状态为 `running`，通信正常。
   - 识别出既有工作区（w5: `YSU-radio-association2026`, w6: `homebox`, w7: `fork-cast`）。

---

## 第四轮交互：Herdr 新建专属 Workspace 与会话存档

### 用户需求指令：
> “对，new一个workspace，然后把我和你现在这个会话的记录复制过去你可以做到吗”

### 执行动作与核验：
1. **新建 Herdr 专属工作区**：
   - 命令：`herdr workspace create --label 'Intelli-Shield' --cwd '/home/xiang/Intelli-Shield'`
   - 结果：
     - Workspace ID: `w8`
     - 标签名称: `Intelli-Shield`
     - 工作目录: `/home/xiang/Intelli-Shield`
     - 激活 Tab: `w8:t1`
     - 主 Pane: `w8:p1`
2. **终端状态核验**：
   - 通过 `herdr pane read w8:p1` 确认终端已自动进入 `/home/xiang/Intelli-Shield`，且位于 `refactor/omnijev-fusion` 分支。
3. **会话历史归档**：
   - 完整提取梳理本次对话的全部技术背景、决策依据、执行日志及实施计划，生成 `会话记录_OmniJev重构对接.md`。
   - 复制并存入远程主机 `~/Intelli-Shield/会话记录_OmniJev重构对接.md`。

---

## 附录：关键文件与资源清单

1. **远程项目根目录**：`/home/xiang/Intelli-Shield`
2. **Git 重构分支**：`refactor/omnijev-fusion`
3. **方案总揽**：`~/Intelli-Shield/OmniJev融合实施与汇报准备计划.md`
4. **会话归档**：`~/Intelli-Shield/会话记录_OmniJev重构对接.md`
5. **Herdr 工作区**：
   - 工作区编号：`w8`（名称：`Intelli-Shield`）
   - 交互连接方式：在终端运行 `herdr` 即可直观查看该工作区与实时终端。
