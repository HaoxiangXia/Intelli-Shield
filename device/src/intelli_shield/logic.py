"""
MaixCAM 人员入侵检测系统 - 状态机逻辑模块
中心 ROI + 外围 ROI 双状态机
"""

# -*- coding: utf-8 -*-
import time
import math
from . import config

class DebounceStateMachine:
    """
    用于将 raw 信号转换为稳定 state 的简单去抖状态机。
    """

    def __init__(self, on_frames: int, off_frames: int, initial_state: bool = False):
        self.on_frames = max(1, int(on_frames))
        self.off_frames = max(1, int(off_frames))
        self.state = bool(initial_state)
        self.on_count = 0
        self.off_count = 0

    def update(self, raw: bool) -> bool:
        """
        使用 raw 信号更新状态机，并返回状态是否发生变化。"
        """
        changed = False
        if raw:
            # Consecutive hit count
            self.on_count += 1
            self.off_count = 0
            if not self.state and self.on_count >= self.on_frames:
                self.state = True
                changed = True
        else:
            # Consecutive miss count
            self.off_count += 1
            self.on_count = 0
            if self.state and self.off_count >= self.off_frames:
                self.state = False
                changed = True
        return changed


class Track:
    """
    轻量级人员轨迹跟踪数据结构，适用于资源受限环境。
    """
    def __init__(self, track_id: int, cx: float, cy: float, timestamp_s: float, in_center_roi: bool):
        self.track_id = track_id
        
        # 当前位置与时间
        self.cx = cx
        self.cy = cy
        self.timestamp_s = timestamp_s
        
        # 上一位置与时间
        self.prev_cx = cx
        self.prev_cy = cy
        self.prev_timestamp_s = timestamp_s
        
        # 靠近速度与状态
        self.approach_speed_px_s = 0.0
        self.missing_frames = 0
        self.in_center_roi = in_center_roi

    def update(self, cx: float, cy: float, timestamp_s: float, in_center_roi: bool, frame_center_x: float, frame_center_y: float):
        self.prev_cx = self.cx
        self.prev_cy = self.cy
        self.prev_timestamp_s = self.timestamp_s
        
        self.cx = cx
        self.cy = cy
        self.timestamp_s = timestamp_s
        self.in_center_roi = in_center_roi
        self.missing_frames = 0
        
        dt = self.timestamp_s - self.prev_timestamp_s
        if dt > 0:
            prev_distance = math.sqrt((self.prev_cx - frame_center_x)**2 + (self.prev_cy - frame_center_y)**2)
            curr_distance = math.sqrt((self.cx - frame_center_x)**2 + (self.cy - frame_center_y)**2)
            raw_approach_speed = (prev_distance - curr_distance) / dt
        else:
            raw_approach_speed = 0.0
            
        alpha = config.SPEED_SMOOTH_ALPHA
        self.approach_speed_px_s = alpha * raw_approach_speed + (1.0 - alpha) * self.approach_speed_px_s


class DualROIAlarm:
    """
    中心/外围 ROI 分类 + 双去抖状态机 + 最终报警判定
    """

    def __init__(self):
        self.center_sm = DebounceStateMachine(config.CENTER_ON_FRAMES, config.CENTER_OFF_FRAMES)
        self.outer_sm = DebounceStateMachine(config.SPEED_ON_FRAMES, config.SPEED_OFF_FRAMES)
        self.alarm_state = False
        
        # 轨迹与速度跟踪状态及调试信息
        self.tracks = []
        self.next_track_id = 1
        self.active_track_count = 0
        self.max_approach_speed_px_s = 0.0

    def get_roi_rect(self, frame_w: int, frame_h: int):
        """
        根据比例计算中心 ROI 矩形区域
        """
        w = int(frame_w * config.ROI_CENTER_W_RATIO)
        h = int(frame_h * config.ROI_CENTER_H_RATIO)
        if w < 1:
            w = 1
        if h < 1:
            h = 1
        x = int((frame_w - w) / 2)
        y = int((frame_h - h) / 2)
        return x, y, w, h

    def _classify(self, boxes, frame_w: int, frame_h: int):
        """
        根据框中心点将检测框分类到中心/外围 ROI
        """
        x, y, w, h = self.get_roi_rect(frame_w, frame_h)
        x2 = x + w
        y2 = y + h
        center_raw = False
        outer_raw = False
        for box in boxes:
            cx = box.x + (box.w / 2)
            cy = box.y + (box.h / 2)
            if (x <= cx <= x2) and (y <= cy <= y2):
                center_raw = True
            else:
                outer_raw = True
            if center_raw and outer_raw:
                break
        return center_raw, outer_raw

    def _update_tracks(self, boxes, frame_w: int, frame_h: int, timestamp_s: float):
        frame_center_x = frame_w / 2.0
        frame_center_y = frame_h / 2.0
        
        x, y, w, h = self.get_roi_rect(frame_w, frame_h)
        x2 = x + w
        y2 = y + h
        
        # 提取当前帧的有效 boxes，计算中心点
        current_objects = []
        for box in boxes:
            cx = box.x + (box.w / 2.0)
            cy = box.y + (box.h / 2.0)
            in_center = (x <= cx <= x2) and (y <= cy <= y2)
            current_objects.append({'cx': cx, 'cy': cy, 'in_center': in_center, 'matched': False})
            
        # 对每个已有的 track 找最近的未匹配 box
        for track in self.tracks:
            best_idx = -1
            min_dist = float('inf')
            for i, obj in enumerate(current_objects):
                if not obj['matched']:
                    dist = math.sqrt((track.cx - obj['cx'])**2 + (track.cy - obj['cy'])**2)
                    if dist < min_dist and dist <= config.TRACK_MATCH_MAX_DISTANCE_PX:
                        min_dist = dist
                        best_idx = i
            
            if best_idx != -1:
                obj = current_objects[best_idx]
                track.update(obj['cx'], obj['cy'], timestamp_s, obj['in_center'], frame_center_x, frame_center_y)
                obj['matched'] = True
            else:
                track.missing_frames += 1
                
        # 移除丢失太久的 track
        self.tracks = [t for t in self.tracks if t.missing_frames <= config.TRACK_MAX_MISSING_FRAMES]
        
        # 为尚未匹配的 box 创建新 track
        for obj in current_objects:
            if not obj['matched']:
                new_track = Track(self.next_track_id, obj['cx'], obj['cy'], timestamp_s, obj['in_center'])
                self.tracks.append(new_track)
                self.next_track_id += 1
                
        self.active_track_count = len(self.tracks)
        current_tracks = [t for t in self.tracks if t.missing_frames == 0]
        if current_tracks:
            self.max_approach_speed_px_s = max(t.approach_speed_px_s for t in current_tracks)
        else:
            self.max_approach_speed_px_s = 0.0

    def _has_outer_speed_risk(self):
        """
        检查是否存在外围 ROI 内、当前帧有效、靠近速度超过阈值的轨迹。
        返回 True 表示存在速度风险。
        """
        threshold = config.SPEED_APPROACH_THRESHOLD_PX_S
        for track in self.tracks:
            if (not track.in_center_roi) and (track.missing_frames == 0):
                if track.approach_speed_px_s >= threshold:
                    return True
        return False

    def update(self, boxes, frame_w: int, frame_h: int, timestamp_s=None):
        """
        主API: 返回 raw、state、alarm、state_changed。
        center_raw: 中心 ROI 是否有人
        outer_raw: 是否存在外围 ROI 内、当前帧有效、靠近速度超过阈值的轨迹（速度风险 raw）
        center_state: 中心 ROI 状态机稳定状态
        outer_state: 外围速度风险状态机稳定状态
        alarm_state: 最终报警状态（中心+外围速度风险）
        state_changed: 报警状态是否发生变化
        """
        if timestamp_s is None:
            timestamp_s = time.time()
        self._update_tracks(boxes, frame_w, frame_h, timestamp_s)
        center_raw, _old_outer_raw = self._classify(boxes, frame_w, frame_h)
        outer_raw = self._has_outer_speed_risk()

        # 更新双状态机
        self.center_sm.update(center_raw)
        self.outer_sm.update(outer_raw)

        center_state = self.center_sm.state
        outer_state = self.outer_sm.state
        alarm_state = bool(center_state and outer_state)

        state_changed = (alarm_state != self.alarm_state)
        self.alarm_state = alarm_state

        return center_raw, outer_raw, center_state, outer_state, alarm_state, state_changed
