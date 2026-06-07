# Bun 前端项目管理手册

本文档汇总了在当前项目中使用 Bun 代替 npm 的常用操作。所有命令建议在 `cloud/frontend` 目录下执行。

---

### 1. 依赖管理（安装、检查、更新）

这是最常用的部分。Bun 的安装速度通常比 npm/yarn 快 10 倍以上。

| 操作 | Bun 命令 | 说明 |
| :--- | :--- | :--- |
| **安装所有依赖** | `bun install` | 相当于 `npm install`，根据 `bun.lockb` 安装 |
| **添加生产依赖** | `bun add <包名>` | 记录到 `dependencies` |
| **添加开发依赖** | `bun add -d <包名>` | 记录到 `devDependencies` |
| **移除依赖** | `bun remove <包名>` | 卸载并从 `package.json` 删除 |
| **检查更新** | `bun outdated` | **列出哪些包有新版本（常用）** |
| **安全更新** | `bun update` | 在 `package.json` 限定范围内自动更新 |
| **强制升至最新** | `bun add <包名>@latest` | **忽略版本限制，强制安装最新大版本** |

**常用示例：**
```bash
bun add axios                # 装新包
bun add -d vite@latest       # 将 Vite 强制升级到最新的第 6/8 版
bun outdated                 # 看看今天谁该更新了```

### 2. 运行脚本（开发、构建、测试）

| 操作 | Bun 命令 | 说明 |
| :--- | :--- | :--- |
| **运行开发服务器** | `bun dev` 或 `bun run dev` | `npm run dev` |
| **运行构建** | `bun run build` | `npm run build` |
| **运行任意脚本** | `bun run <脚本名>` | `npm run <脚本名>` |
| **直接执行 JS/TS 文件** | `bun index.ts` | `node index.js` (仅JS) |

**注意**：`bun dev` 是 `bun run dev` 的简写，只适用于脚本名和 Bun 内置关键字不冲突的情况。

### 3. 初始化项目

- **创建新项目（交互式）**  
  `bun init`  
  会一步步让你填项目信息，生成 `package.json` 和 `tsconfig.json`。

- **从零快速创建 Vue 项目**  
  `bun create vite frontend --template vue`  
  （Bun 也兼容 Vite 的模板创建命令）

### 4. 其他实用命令

| 操作 | 命令 | 说明 |
| :--- | :--- | :--- |
| **查看 Bun 版本** | `bun --version` | 确认安装是否成功 |
| **升级 Bun 本身** | `bun upgrade` | 升级到最新稳定版 |
| **运行 TypeScript 文件** | `bun run index.ts` | 无需 `ts-node` |
| **热重载运行脚本** | `bun --hot run dev` | 类似 `nodemon`，文件改动时自动重启 |
| **查看已安装的依赖** | `bun pm ls` | 列出项目所有依赖 |

### 5. 和你当前项目相关的提示

- **在你的 `frontend` 目录下**，现在用 `bun add` 安装新包，就会写入 `frontend/package.json`，并更新 `bun.lockb`。
- 想快速预览一个 `.ts` 或 `.js` 文件的结果，直接用 `bun 文件名` 就行，非常方便用于测试小代码片断。
