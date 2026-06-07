"""Compatibility MQTT client facade.

The application entrypoint starts MQTT through ``WorkerManager``. This module
keeps the older ``start_mqtt`` API available without duplicating message
processing logic.
"""

from __future__ import annotations

import inspect
import json

import paho.mqtt.client as mqtt

from logger import log_event

from .services import app_service
from .settings import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC

socketio_inst = None


def _is_mqtt_success(reason_code):
    value = getattr(reason_code, "value", reason_code)
    return value == 0 or str(reason_code).lower() == "success"


def set_socketio(sio):
    global socketio_inst
    socketio_inst = sio


def _push_device_update():
    if socketio_inst is None:
        return
    emit = socketio_inst.emit
    if inspect.iscoroutinefunction(emit):
        log_event(
            "WARNING",
            "socketio.legacy.async_emit_skipped",
            "ops",
            "mqtt",
            "Legacy mqtt_client cannot await AsyncServer.emit; use WorkerManager instead",
        )
        return
    result = emit("device_update", app_service.get_latest_payload())
    if inspect.isawaitable(result) and hasattr(result, "close"):
        result.close()


def _handle_message(msg):
    payload = json.loads(msg.payload.decode())
    app_service.process_mqtt_payload(msg.topic, payload)
    _push_device_update()


def start_mqtt(required=True):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if _is_mqtt_success(reason_code):
            client.subscribe(MQTT_TOPIC)
            log_event("INFO", "mqtt.client.connected", "ops", "mqtt", "Connected to MQTT broker successfully", topic=MQTT_TOPIC)
        else:
            log_event("ERROR", "mqtt.client.connect_failed", "ops", "mqtt", f"Failed to connect to MQTT broker, return code {reason_code}", topic=MQTT_TOPIC)

    def on_message(client, userdata, msg):
        try:
            _handle_message(msg)
        except Exception as exc:
            log_event("ERROR", "mqtt.message.parse_failed", "ops", "mqtt", "Failed to process MQTT message", topic=msg.topic, error=str(exc))

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        log_event("INFO", "mqtt.client.started", "ops", "mqtt", "MQTT client started successfully", extra={"broker": MQTT_BROKER, "port": MQTT_PORT})
        return client
    except Exception as exc:
        level = "CRITICAL" if required else "WARNING"
        log_event(
            level,
            "mqtt.client.start_failed",
            "ops",
            "mqtt",
            "MQTT client failed to start",
            extra={"broker": MQTT_BROKER, "port": MQTT_PORT, "required": required},
            error=str(exc),
        )
        if required:
            raise
        return None
