# 通信层架构及设备对接指南

## 概述

叉车安全监测系统采用三层通信架构，实现设备数据采集、实时状态推送和前端交互。

```
┌─────────────┐     MQTT      ┌─────────────┐    Socket.IO    ┌─────────────┐
│   设备端    │ ────────────→ │   服务器    │ ────────────→ │   前端      │
│ (Forklift)  │               │  (FastAPI)  │               │  (Browser)  │
└─────────────┘               └─────────────┘               └─────────────┘
      │                             ↑
      │         HTTP POST           │
      └─────────────────────────────┘
            (图片上传)
```

---

## 1. MQTT 通信层（设备 → 服务器）

### 1.1 连接配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MQTT_BROKER` | `localhost` | MQTT 代理地址 |
| `MQTT_PORT` | `1883` | MQTT 代理端口 |
| `MQTT_TOPIC` | `factory/forklift/+/alarm` | 订阅主题（通配符 `+` 匹配设备ID） |

### 1.2 主题命名规范

```
factory/forklift/{device_id}/alarm
```

- `factory`：工厂标识（固定）
- `forklift`：设备类型（固定）
- `{device_id}`：设备唯一标识（如 `FORK-001`）
- `alarm`：消息类型（固定）

### 1.3 消息格式

#### 标准消息
```json
{
  "device_id": "FORK-001",
  "alarm": 1,
  "timestamp": "2026-03-19 14:30:00"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | string | 是 | 设备唯一标识 |
| `alarm` | integer | 是 | 报警状态：0=正常，1=报警 |
| `timestamp` | string | 是 | 设备上报时间（格式：`YYYY-MM-DD HH:mm:ss`） |

#### 扩展消息（含图片URL）
**推荐流程**：设备发现报警 -> 调用 HTTP 接口上传图片 -> 获取返回的 URL -> 发送含有 URL 的 MQTT 消息。

```json
{
  "device_id": "FORK-001",
  "alarm": 1,
  "timestamp": "2026-03-19 14:30:00",
  "image_urls": ["/images/alarms/FORK-001_2026-03-19_14-30-00_0.jpg"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_urls` | array[string] | 否 | 由 HTTP 上传接口返回的图片路径列表 |
| `image_url` | string | 否 | （兼容）单张图片路径 |

### 1.4 消息处理流程

1. **解析内容**：服务器从主题中提取 `device_id`，从 Payload 中提取状态和时间。
2. **更新状态**：在数据库中记录设备最新的 `alarm_status`、`last_seen` 和位置。
3. **关联图片**：如果 `alarm=1` 且包含图片路径，则在 `alarm_images` 表中建立关联。
4. **实时推送**：通过 Socket.IO 推送 `device_update` 事件给所有前端。

---

## 2. HTTP/REST API（设备上传与前端获取）

### 2.1 图片上传接口（设备端使用）

设备端在检测到报警后，应先通过此接口上传现场照片。

- **方法**: `POST`
- **路径**: `/api/upload-image`
- **Content-Type**: `multipart/form-data`

**请求参数（Form Data）**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `device_id` | string | 是 | 设备唯一标识 |
| `images` | file[] | 是 | 图片文件列表（支持多图） |
| `base_timestamp`| string | 否 | 基准时间（YYYY-MM-DD HH:mm:ss），缺省为系统当前时间 |
| `image_timestamps`| string | 否 | JSON 字符串数组，如 `["2026-03-19 14:30:00"]`，需与图片一一对应 |

**响应示例**:
```json
{
  "image_urls": [
    "/images/alarms/FORK-001_2026-03-19_14-30-00_0.jpg"
  ]
}
```

### 2.2 鉴权方式（若启用）

目前开发环境 `AUTH_ENABLED = False` 可跳过。若启用：
- **Header**: `Authorization: Bearer <token>` 或 `X-Auth-Token: <token>`

### 2.3 常用 API 端点列表

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/api/latest` | 获取所有设备最新状态和统计 | 是 |
| GET | `/api/devices` | 获取所有设备位置和状态（Dashboard用） | 是 |
| GET | `/api/device/<device_id>/history` | 获取设备历史记录和趋势 | 是 |
| GET | `/images/<path>` | 访问图片文件（如 `/images/alarms/xxx.jpg`） | 否 |

---

## 3. 联调建议与测试工具

### 3.1 模拟设备脚本

参考 [`tests/publish_test.py`](../tests/publish_test.py) 进行 MQTT 通信模拟：
```bash
python tests/publish_test.py
```

### 3.2 离线检测逻辑

- **间隔**: 每 5 秒检查一次。
- **超时**: 若设备超过 10 秒（`OFFLINE_TIMEOUT_SEC`）未发送任何消息，将被判定为离线。

### 3.3 图片上传测试 (CURL 示例)

```bash
curl -X POST http://localhost:5000/api/upload-image \
     -F "device_id=FORK-001" \
     -F "images=@test_alarm.jpg"
```

---

## 4. 常见问题 (FAQ)

1. **MQTT 连接不上？**
   - 检查 `backend/settings.py` 中的 `MQTT_BROKER` 和 `MQTT_PORT`。
   - 确保本地安装了 MQTT Broker (如 Mosquitto) 且已启动。
2. **图片上传报错 413？**
   - 检查 `backend/settings.py` 中的 `MAX_IMAGE_SIZE_MB` 配置。
3. **前端看不到实时更新？**
   - 检查服务器日志是否输出了 `socketio.data.pushed`。
   - 确保前端已建立 WebSocket 连接。
