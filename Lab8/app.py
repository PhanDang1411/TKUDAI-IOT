
"""
Lab 8 v3: LLM Reasoning & Context-aware Decision for AIoT
- Live sensor simulator
- Manual sensor control
- Three-level comparison: Sensor only / Sensor + AI models / Sensor + AI models + LLM
- Mock LLM fallback so the lab always runs without API keys or local models
"""
from __future__ import annotations

import csv
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except Exception:  # keep lab runnable even if requests is missing
    requests = None

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title='Lab 8 v3 - LLM Reasoning AIoT', version='3.0')
app.mount('/outputs', StaticFiles(directory=str(OUTPUT_DIR)), name='outputs')

# -------------------------------------------------------------------
# Scenario definitions
# -------------------------------------------------------------------
SCENARIOS: Dict[str, Dict[str, Any]] = {
    'lab_overcrowded_high_co2': {
        'title': 'Smart classroom: CO2 tăng nhanh + phòng đông người',
        'why_it_is_interesting': 'Cùng một dữ liệu, sensor-only chỉ thấy CO2 cao; AI models thấy xu hướng tăng và đông người; LLM giải thích vì sao cần hành động an toàn.',
        'editable_sensors': {
            'co2_ppm': {'type': 'number', 'min': 400, 'max': 2600, 'step': 10, 'unit': 'ppm'},
            'temperature_c': {'type': 'number', 'min': 20, 'max': 42, 'step': 0.1, 'unit': '°C'},
            'humidity_percent': {'type': 'number', 'min': 30, 'max': 95, 'step': 1, 'unit': '%'},
            'person_count': {'type': 'number', 'min': 0, 'max': 60, 'step': 1, 'unit': 'people'},
            'vision_confidence': {'type': 'number', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'unit': ''},
            'fan': {'type': 'select', 'options': ['OFF', 'ON']},
            'window': {'type': 'select', 'options': ['CLOSED', 'OPEN']},
        },
        'timeline': [
            {'co2_ppm': 780, 'temperature_c': 27.8, 'humidity_percent': 61, 'person_count': 8, 'vision_confidence': 0.84, 'fan': 'OFF', 'window': 'CLOSED'},
            {'co2_ppm': 980, 'temperature_c': 28.4, 'humidity_percent': 64, 'person_count': 18, 'vision_confidence': 0.83, 'fan': 'OFF', 'window': 'CLOSED'},
            {'co2_ppm': 1280, 'temperature_c': 29.6, 'humidity_percent': 67, 'person_count': 28, 'vision_confidence': 0.82, 'fan': 'OFF', 'window': 'CLOSED'},
            {'co2_ppm': 1680, 'temperature_c': 31.4, 'humidity_percent': 72, 'person_count': 38, 'vision_confidence': 0.82, 'fan': 'OFF', 'window': 'CLOSED'},
            {'co2_ppm': 2100, 'temperature_c': 33.0, 'humidity_percent': 76, 'person_count': 40, 'vision_confidence': 0.80, 'fan': 'OFF', 'window': 'CLOSED'},
        ],
        'safety_rules': [
            'Lab mode does not allow direct actuator control.',
            'If CO2 is above 1500 ppm and the room is occupied, recommend ventilation.',
            'If forecast trend is increasing, escalate priority.',
            'If evidence is strong but actuator control is blocked, request operator action.'
        ]
    },
    'fire_alarm_conflict': {
        'title': 'Fire alarm conflict: nghi cháy nhưng sensor không khớp',
        'why_it_is_interesting': 'Vision có thể thấy vùng màu cam giống lửa, nhưng smoke/gas sensor bình thường và máy chiếu đang bật. LLM cần phát hiện mâu thuẫn bằng chứng.',
        'editable_sensors': {
            'temperature_c': {'type': 'number', 'min': 25, 'max': 85, 'step': 0.5, 'unit': '°C'},
            'smoke_level': {'type': 'number', 'min': 0, 'max': 100, 'step': 1, 'unit': '%'},
            'gas_level': {'type': 'number', 'min': 0, 'max': 100, 'step': 1, 'unit': '%'},
            'flame_vision_confidence': {'type': 'number', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'unit': ''},
            'projector_on': {'type': 'select', 'options': ['true', 'false']},
        },
        'timeline': [
            {'temperature_c': 29.0, 'smoke_level': 0, 'gas_level': 0, 'flame_vision_confidence': 0.05, 'projector_on': 'false'},
            {'temperature_c': 31.0, 'smoke_level': 2, 'gas_level': 1, 'flame_vision_confidence': 0.28, 'projector_on': 'true'},
            {'temperature_c': 37.8, 'smoke_level': 4, 'gas_level': 3, 'flame_vision_confidence': 0.54, 'projector_on': 'true'},
            {'temperature_c': 45.0, 'smoke_level': 8, 'gas_level': 4, 'flame_vision_confidence': 0.63, 'projector_on': 'true'},
            {'temperature_c': 60.0, 'smoke_level': 75, 'gas_level': 65, 'flame_vision_confidence': 0.88, 'projector_on': 'false'},
        ],
        'safety_rules': [
            'Do not trigger emergency shutdown from low-confidence vision alone.',
            'If smoke and gas are normal but vision detects flame-like color, require human review.',
            'If smoke or gas sensor is high and vision confidence is high, raise critical alert.',
            'Projector or orange light can cause false fire-like visual evidence.'
        ]
    },
    'fall_or_bending_ambiguity': {
        'title': 'Fall ambiguity: người bị ngã hay đang cúi nhặt đồ?',
        'why_it_is_interesting': 'Một model pose/fall có thể báo bất thường, nhưng confidence chưa đủ. LLM cần giữ thái độ thận trọng, không xác nhận té ngã khi bằng chứng mơ hồ.',
        'editable_sensors': {
            'fall_confidence': {'type': 'number', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'unit': ''},
            'motion_duration_sec': {'type': 'number', 'min': 0, 'max': 30, 'step': 0.5, 'unit': 's'},
            'body_low_position': {'type': 'select', 'options': ['true', 'false']},
            'emergency_button': {'type': 'select', 'options': ['NOT_PRESSED', 'PRESSED']},
        },
        'timeline': [
            {'fall_confidence': 0.12, 'motion_duration_sec': 1.0, 'body_low_position': 'false', 'emergency_button': 'NOT_PRESSED'},
            {'fall_confidence': 0.38, 'motion_duration_sec': 2.0, 'body_low_position': 'true', 'emergency_button': 'NOT_PRESSED'},
            {'fall_confidence': 0.61, 'motion_duration_sec': 2.1, 'body_low_position': 'true', 'emergency_button': 'NOT_PRESSED'},
            {'fall_confidence': 0.78, 'motion_duration_sec': 8.5, 'body_low_position': 'true', 'emergency_button': 'NOT_PRESSED'},
            {'fall_confidence': 0.91, 'motion_duration_sec': 15.0, 'body_low_position': 'true', 'emergency_button': 'PRESSED'},
        ],
        'safety_rules': [
            'Fall confidence below 0.75 requires human review.',
            'If posture is ambiguous, do not mark as confirmed fall.',
            'If emergency button is pressed, escalate immediately.',
            'The system may recommend checking the camera but must not claim certainty from weak evidence.'
        ]
    },
    'ppe_danger_zone': {
        'title': 'PPE danger zone: người vào vùng nguy hiểm nhưng thiếu bảo hộ',
        'why_it_is_interesting': 'Detection rời rạc chưa đủ. LLM cần tổng hợp person + no helmet + no vest + danger zone + machine running thành tình huống an toàn lao động.',
        'editable_sensors': {
            'person_detected': {'type': 'select', 'options': ['true', 'false']},
            'helmet_detected': {'type': 'select', 'options': ['true', 'false']},
            'vest_detected': {'type': 'select', 'options': ['true', 'false']},
            'danger_zone_overlap': {'type': 'select', 'options': ['true', 'false']},
            'machine_status': {'type': 'select', 'options': ['STOPPED', 'RUNNING']},
            'vision_confidence': {'type': 'number', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'unit': ''},
        },
        'timeline': [
            {'person_detected': 'false', 'helmet_detected': 'false', 'vest_detected': 'false', 'danger_zone_overlap': 'false', 'machine_status': 'STOPPED', 'vision_confidence': 0.0},
            {'person_detected': 'true', 'helmet_detected': 'true', 'vest_detected': 'true', 'danger_zone_overlap': 'false', 'machine_status': 'RUNNING', 'vision_confidence': 0.85},
            {'person_detected': 'true', 'helmet_detected': 'false', 'vest_detected': 'true', 'danger_zone_overlap': 'true', 'machine_status': 'RUNNING', 'vision_confidence': 0.78},
            {'person_detected': 'true', 'helmet_detected': 'false', 'vest_detected': 'false', 'danger_zone_overlap': 'true', 'machine_status': 'RUNNING', 'vision_confidence': 0.79},
        ],
        'safety_rules': [
            'If machine is running and person is inside danger zone without PPE, raise critical alert.',
            'In lab mode, do not stop machine automatically; recommend emergency review.',
            'If vision confidence is below 0.6, require human review.'
        ]
    },
    'greenhouse_leaf_disease_risk': {
        'title': 'Smart agriculture: lá nghi bệnh + độ ẩm cao',
        'why_it_is_interesting': 'Vision model chỉ thấy dấu lá bệnh; forecasting/telemetry cho biết độ ẩm tiếp tục cao; LLM đề xuất quy trình kiểm tra, không chẩn đoán vội.',
        'editable_sensors': {
            'temperature_c': {'type': 'number', 'min': 15, 'max': 40, 'step': 0.1, 'unit': '°C'},
            'humidity_percent': {'type': 'number', 'min': 30, 'max': 100, 'step': 1, 'unit': '%'},
            'soil_moisture_percent': {'type': 'number', 'min': 10, 'max': 100, 'step': 1, 'unit': '%'},
            'leaf_spot_confidence': {'type': 'number', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'unit': ''},
            'image_quality': {'type': 'select', 'options': ['GOOD', 'BLURRY', 'LOW_LIGHT']},
        },
        'timeline': [
            {'temperature_c': 25.0, 'humidity_percent': 65, 'soil_moisture_percent': 50, 'leaf_spot_confidence': 0.18, 'image_quality': 'GOOD'},
            {'temperature_c': 27.0, 'humidity_percent': 82, 'soil_moisture_percent': 68, 'leaf_spot_confidence': 0.42, 'image_quality': 'GOOD'},
            {'temperature_c': 29.5, 'humidity_percent': 91, 'soil_moisture_percent': 76, 'leaf_spot_confidence': 0.68, 'image_quality': 'BLURRY'},
            {'temperature_c': 30.2, 'humidity_percent': 94, 'soil_moisture_percent': 82, 'leaf_spot_confidence': 0.81, 'image_quality': 'GOOD'},
        ],
        'safety_rules': [
            'Do not diagnose plant disease from one low-quality image.',
            'If leaf disease confidence is below 0.75, request more images.',
            'If humidity remains high and leaf spot confidence is high, recommend inspection and humidity control.'
        ]
    }
}

# -------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_bool(v: Any) -> bool:
    return str(v).lower() in {'true', '1', 'yes', 'on'}

def risk_order(risk: str) -> int:
    return {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}.get(risk, 0)

def max_risk(*risks: str) -> str:
    return max(risks, key=risk_order)

def write_csv_row(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(exist_ok=True)
    exists = path.exists()
    with path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)

def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')

# -------------------------------------------------------------------
# Live state
# -------------------------------------------------------------------
class LiveState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.scenario_id = 'lab_overcrowded_high_co2'
        self.step_index = 0
        self.sensors = dict(SCENARIOS[self.scenario_id]['timeline'][0])
        self.running = False
        self.interval_sec = 2.0
        self.thread: Optional[threading.Thread] = None
        self.last_updated = now_iso()
        self.history: List[Dict[str, Any]] = []

    def reset(self, scenario_id: str) -> Dict[str, Any]:
        if scenario_id not in SCENARIOS:
            raise HTTPException(status_code=404, detail=f'Unknown scenario: {scenario_id}')
        with self.lock:
            self.scenario_id = scenario_id
            self.step_index = 0
            self.sensors = dict(SCENARIOS[scenario_id]['timeline'][0])
            self.last_updated = now_iso()
            self.history = []
            self._record_locked('reset')
            return self.snapshot_locked()

    def update_sensor(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            schema = SCENARIOS[self.scenario_id]['editable_sensors']
            for key, value in updates.items():
                if key not in schema:
                    raise HTTPException(status_code=400, detail=f'Unknown sensor field: {key}')
                spec = schema[key]
                if spec['type'] == 'number':
                    value = float(value)
                    value = max(float(spec['min']), min(float(spec['max']), value))
                    # keep int-like values tidy
                    if spec.get('step') == 1:
                        value = int(value)
                else:
                    if value not in spec['options']:
                        raise HTTPException(status_code=400, detail=f'Invalid value for {key}: {value}')
                self.sensors[key] = value
            self.last_updated = now_iso()
            self._record_locked('manual_update')
            return self.snapshot_locked()

    def step(self) -> Dict[str, Any]:
        with self.lock:
            timeline = SCENARIOS[self.scenario_id]['timeline']
            self.step_index = (self.step_index + 1) % len(timeline)
            self.sensors = dict(timeline[self.step_index])
            self.last_updated = now_iso()
            self._record_locked('step')
            return self.snapshot_locked()

    def _record_locked(self, source: str) -> None:
        row = {'timestamp': self.last_updated, 'scenario_id': self.scenario_id, 'step_index': self.step_index, 'source': source, **self.sensors}
        self.history.append(row)
        if len(self.history) > 200:
            self.history = self.history[-200:]
        write_csv_row(OUTPUT_DIR / 'telemetry_timeseries.csv', row)

    def snapshot_locked(self) -> Dict[str, Any]:
        return {
            'scenario_id': self.scenario_id,
            'scenario_title': SCENARIOS[self.scenario_id]['title'],
            'step_index': self.step_index,
            'running': self.running,
            'last_updated': self.last_updated,
            'sensors': self.sensors,
            'editable_sensors': SCENARIOS[self.scenario_id]['editable_sensors'],
            'history': self.history[-30:]
        }

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return self.snapshot_locked()

STATE = LiveState()

# -------------------------------------------------------------------
# Model outputs from previous labs
# -------------------------------------------------------------------
def sensor_only_decision(sensors: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    reason = []
    risk = 'LOW'
    if scenario_id == 'lab_overcrowded_high_co2':
        co2 = float(sensors.get('co2_ppm', 0))
        if co2 >= 2000:
            risk = 'CRITICAL'
        elif co2 >= 1500:
            risk = 'HIGH'
        elif co2 >= 1000:
            risk = 'MEDIUM'
        reason.append(f'CO2 hiện tại = {co2:.0f} ppm.')
    elif scenario_id == 'fire_alarm_conflict':
        t, smoke, gas, fconf = float(sensors.get('temperature_c',0)), float(sensors.get('smoke_level',0)), float(sensors.get('gas_level',0)), float(sensors.get('flame_vision_confidence',0))
        if smoke > 60 or gas > 60 or (t > 55 and fconf > 0.7): risk = 'CRITICAL'
        elif t > 40 or fconf > 0.5: risk = 'HIGH'
        else: risk = 'LOW'
        reason.append(f'Temperature={t:.1f}, smoke={smoke:.0f}, gas={gas:.0f}, flame_conf={fconf:.2f}.')
    elif scenario_id == 'fall_or_bending_ambiguity':
        fc = float(sensors.get('fall_confidence', 0))
        if fc >= 0.85: risk = 'CRITICAL'
        elif fc >= 0.6: risk = 'HIGH'
        elif fc >= 0.35: risk = 'MEDIUM'
        reason.append(f'Fall confidence = {fc:.2f}.')
    elif scenario_id == 'ppe_danger_zone':
        if parse_bool(sensors.get('person_detected')) and parse_bool(sensors.get('danger_zone_overlap')) and sensors.get('machine_status') == 'RUNNING':
            risk = 'HIGH'
        if sensors.get('machine_status') == 'RUNNING' and parse_bool(sensors.get('danger_zone_overlap')) and (not parse_bool(sensors.get('helmet_detected')) or not parse_bool(sensors.get('vest_detected'))):
            risk = 'CRITICAL'
        reason.append('Kiểm tra person/danger_zone/machine/PPE theo rule cứng.')
    elif scenario_id == 'greenhouse_leaf_disease_risk':
        h = float(sensors.get('humidity_percent', 0)); leaf = float(sensors.get('leaf_spot_confidence', 0))
        if h >= 90 and leaf >= 0.75: risk = 'HIGH'
        elif h >= 80 or leaf >= 0.5: risk = 'MEDIUM'
        reason.append(f'Humidity={h:.0f}%, leaf_spot_confidence={leaf:.2f}.')
    return {
        'layer': 'sensor_only',
        'risk_level': risk,
        'summary': 'Rule cứng đọc giá trị cảm biến hiện tại.',
        'recommended_action': 'Hiển thị cảnh báo theo ngưỡng.' if risk != 'LOW' else 'Tiếp tục giám sát.',
        'reason': ' '.join(reason),
        'limitations': ['Không dùng anomaly model.', 'Không dùng forecasting model.', 'Không dùng vision/motion evidence từ các lab trước.', 'Không giải thích mâu thuẫn dữ liệu.']
    }

def previous_ai_model_outputs(sensors: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    """Simulate outputs from earlier labs to teach why previous AI models matter."""
    if scenario_id == 'lab_overcrowded_high_co2':
        co2 = float(sensors.get('co2_ppm', 0)); temp = float(sensors.get('temperature_c', 0)); people = int(float(sensors.get('person_count', 0)))
        anomaly_score = min(0.99, max(0.05, (co2 - 700) / 1600))
        forecast_co2 = co2 + 280 if sensors.get('fan') == 'OFF' else max(450, co2 - 100)
        return {
            'lab3_anomaly_event': {'status': 'ANOMALY' if anomaly_score > 0.55 else 'NORMAL', 'score': round(anomaly_score, 2), 'reason': 'CO2 and temperature pattern is unusual for a classroom time window.'},
            'lab4_forecast_result': {'co2_next_20_min': round(forecast_co2), 'temperature_next_20_min': round(temp + 1.2, 1), 'risk_trend': 'INCREASING' if forecast_co2 > co2 else 'DECREASING'},
            'lab6_motion_event': {'motion_detected': people > 0, 'activity_level': 'HIGH' if people > 30 else 'MEDIUM' if people > 10 else 'LOW'},
            'lab7_vision_event': {'person_count': people, 'confidence': sensors.get('vision_confidence'), 'event_type': 'CROWDED_ROOM' if people >= 30 else 'ROOM_OCCUPIED' if people > 0 else 'EMPTY_ROOM'}
        }
    if scenario_id == 'fire_alarm_conflict':
        fconf = float(sensors.get('flame_vision_confidence', 0)); smoke = float(sensors.get('smoke_level', 0)); gas = float(sensors.get('gas_level', 0)); t = float(sensors.get('temperature_c', 0))
        return {
            'lab3_anomaly_event': {'status': 'ANOMALY' if t > 42 or smoke > 30 or gas > 30 else 'NORMAL', 'score': round(min(0.99, (t-25)/55 + smoke/200 + gas/200), 2)},
            'lab4_forecast_result': {'temperature_next_5_min': round(t + (4 if smoke > 30 else 1.5), 1), 'risk_trend': 'INCREASING' if t > 38 else 'STABLE'},
            'lab6_motion_event': {'motion_detected': False, 'low_light': False},
            'lab7_vision_event': {'event_type': 'FIRE_ORANGE_REGION_DETECTED' if fconf > 0.3 else 'NO_FIRE_REGION', 'confidence': fconf, 'image_caption': 'Vùng màu cam sáng gần màn hình/máy chiếu; chưa thấy khói rõ.' if parse_bool(sensors.get('projector_on')) else 'Có vùng sáng giống lửa trong ảnh.'}
        }
    if scenario_id == 'fall_or_bending_ambiguity':
        fc = float(sensors.get('fall_confidence', 0)); dur = float(sensors.get('motion_duration_sec', 0))
        return {
            'lab3_anomaly_event': {'status': 'ANOMALY' if fc > 0.5 or dur > 6 else 'NORMAL', 'score': round(max(fc, min(0.99, dur/20)), 2)},
            'lab4_forecast_result': {'next_30_sec_state': 'PERSON_STILL_LOW_POSITION' if dur > 8 else 'UNCERTAIN', 'risk_trend': 'INCREASING' if dur > 6 else 'STABLE'},
            'lab6_motion_event': {'motion_detected': dur > 0.5, 'motion_duration_sec': dur},
            'lab7_vision_event': {'event_type': 'FALL_REVIEW' if fc >= 0.5 else 'LOW_POSTURE', 'fall_confidence': fc, 'pose_status': 'body_low_position' if parse_bool(sensors.get('body_low_position')) else 'normal_pose', 'image_caption': 'Một người ở tư thế thấp gần sàn; chưa rõ bị ngã hay cúi nhặt vật.'}
        }
    if scenario_id == 'ppe_danger_zone':
        missing = []
        if not parse_bool(sensors.get('helmet_detected')): missing.append('helmet')
        if not parse_bool(sensors.get('vest_detected')): missing.append('vest')
        return {
            'lab3_anomaly_event': {'status': 'ANOMALY' if missing and sensors.get('machine_status') == 'RUNNING' else 'NORMAL', 'score': 0.91 if missing and sensors.get('machine_status') == 'RUNNING' else 0.2},
            'lab4_forecast_result': {'risk_trend': 'INCREASING' if sensors.get('machine_status') == 'RUNNING' and parse_bool(sensors.get('danger_zone_overlap')) else 'STABLE'},
            'lab6_motion_event': {'motion_detected': parse_bool(sensors.get('person_detected')), 'zone': 'danger_zone' if parse_bool(sensors.get('danger_zone_overlap')) else 'safe_zone'},
            'lab7_vision_event': {'person_detected': parse_bool(sensors.get('person_detected')), 'missing_ppe': missing, 'danger_zone_overlap': parse_bool(sensors.get('danger_zone_overlap')), 'confidence': sensors.get('vision_confidence')}
        }
    if scenario_id == 'greenhouse_leaf_disease_risk':
        h = float(sensors.get('humidity_percent', 0)); leaf = float(sensors.get('leaf_spot_confidence', 0)); quality = sensors.get('image_quality')
        return {
            'lab3_anomaly_event': {'status': 'ANOMALY' if h > 88 or leaf > 0.65 else 'NORMAL', 'score': round(max(h/100, leaf), 2)},
            'lab4_forecast_result': {'humidity_next_6h': 'REMAIN_HIGH' if h > 85 else 'NORMAL', 'disease_risk_trend': 'INCREASING' if h > 85 and leaf > 0.5 else 'STABLE'},
            'lab6_motion_event': {'new_snapshot_saved': True, 'image_quality': quality},
            'lab7_vision_event': {'leaf_spot_detected': leaf > 0.5, 'confidence': leaf, 'image_caption': 'Một số vùng lá có đốm nâu nhỏ; ảnh hơi mờ/ánh sáng không đều.' if quality != 'GOOD' else 'Lá có vùng đốm màu bất thường.'}
        }
    return {}

def sensor_ai_decision(sensors: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    sensor_dec = sensor_only_decision(sensors, scenario_id)
    ai = previous_ai_model_outputs(sensors, scenario_id)
    risk = sensor_dec['risk_level']
    reasons = [sensor_dec['reason']]
    if ai.get('lab3_anomaly_event', {}).get('status') == 'ANOMALY':
        risk = max_risk(risk, 'HIGH')
        reasons.append('Lab 3 anomaly model báo ANOMALY.')
    trend = str(ai.get('lab4_forecast_result', {}).get('risk_trend') or ai.get('lab4_forecast_result', {}).get('disease_risk_trend') or '')
    if 'INCREASING' in trend:
        risk = max_risk(risk, 'HIGH')
        reasons.append('Lab 4 forecasting model dự báo rủi ro tăng.')
    vision = ai.get('lab7_vision_event', {})
    if vision.get('event_type') in {'CROWDED_ROOM', 'FALL_REVIEW'} or vision.get('danger_zone_overlap') or vision.get('leaf_spot_detected'):
        risk = max_risk(risk, 'HIGH')
        reasons.append('Lab 7 vision model cung cấp bằng chứng thị giác quan trọng.')
    if scenario_id == 'ppe_danger_zone' and vision.get('danger_zone_overlap') and vision.get('missing_ppe'):
        risk = 'CRITICAL'
    if scenario_id == 'fire_alarm_conflict':
        fconf = float(vision.get('confidence', 0))
        smoke = float(sensors.get('smoke_level',0)); gas = float(sensors.get('gas_level',0))
        if fconf > 0.45 and smoke < 10 and gas < 10 and parse_bool(sensors.get('projector_on')):
            risk = max_risk('MEDIUM', risk if risk_order(risk)<3 else 'MEDIUM')
            reasons.append('Bằng chứng mâu thuẫn: vision nghi lửa nhưng smoke/gas bình thường và projector_on=true.')
    return {
        'layer': 'sensor_plus_ai_models',
        'risk_level': risk,
        'summary': 'Kết hợp cảm biến với anomaly/forecasting/motion/vision models từ các lab trước.',
        'recommended_action': 'Tạo event giàu bằng chứng và chuyển sang reasoning/safety layer.' if risk != 'LOW' else 'Tiếp tục giám sát.',
        'reason': ' '.join(reasons),
        'ai_model_outputs': ai,
        'limitations': ['Có bằng chứng tốt hơn sensor-only nhưng vẫn là rule cứng.', 'Chưa diễn giải tốt cho người vận hành.', 'Chưa biết tổng hợp linh hoạt các mâu thuẫn phức tạp.']
    }

# -------------------------------------------------------------------
# LLM prompting, mock/local client, validation and safety
# -------------------------------------------------------------------
OUTPUT_SCHEMA = {
    'situation_summary': 'string',
    'risk_level': 'LOW|MEDIUM|HIGH|CRITICAL',
    'recommended_action': 'string',
    'control_allowed': 'boolean',
    'need_human_review': 'boolean',
    'blocked_reason': 'string',
    'evidence_used': ['string']
}

def build_context_packet(sensors: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    scenario = SCENARIOS[scenario_id]
    ai = previous_ai_model_outputs(sensors, scenario_id)
    context = {
        'context_id': str(uuid.uuid4()),
        'timestamp': now_iso(),
        'scenario_id': scenario_id,
        'scenario_title': scenario['title'],
        'why_it_is_interesting': scenario['why_it_is_interesting'],
        'telemetry': sensors,
        'evidence_from_previous_labs': {
            'lab3_anomaly_detection': ai.get('lab3_anomaly_event'),
            'lab4_forecasting': ai.get('lab4_forecast_result'),
            'lab6_camera_motion_metadata': ai.get('lab6_motion_event'),
            'lab7_vision_ai': ai.get('lab7_vision_event')
        },
        'safety_rules': scenario['safety_rules'],
        'output_schema': OUTPUT_SCHEMA,
        'prompt_instruction': 'Use only the provided context. Do not invent sensor values. Return JSON only. If evidence is weak or conflicting, set need_human_review=true and control_allowed=false.'
    }
    append_jsonl(OUTPUT_DIR / 'context_packet_log.jsonl', context)
    return context

def build_prompt(context: Dict[str, Any]) -> str:
    return (
        'Bạn là AIoT decision assistant.\n'
        'Nhiệm vụ: đọc context packet từ hệ thống AIoT, tổng hợp bằng chứng, giải thích tình huống và đề xuất hành động an toàn.\n'
        'Quy tắc bắt buộc:\n'
        '- Chỉ dùng dữ liệu trong CONTEXT.\n'
        '- Không bịa thêm giá trị cảm biến hoặc kết quả model.\n'
        '- Nếu bằng chứng mâu thuẫn hoặc confidence thấp, cần human review.\n'
        '- Không cho phép điều khiển tự động trong lab mode.\n'
        '- Trả về JSON đúng schema, không thêm văn bản ngoài JSON.\n\n'
        'CONTEXT:\n' + json.dumps(context, ensure_ascii=False, indent=2) + '\n'
    )

def mock_llm_reason(context: Dict[str, Any]) -> Dict[str, Any]:
    sid = context['scenario_id']; tel = context['telemetry']; ev = context['evidence_from_previous_labs']; rules = context['safety_rules']
    ai_dec = sensor_ai_decision(tel, sid)
    risk = ai_dec['risk_level']
    summary = ''
    action = ''
    review = False
    if sid == 'lab_overcrowded_high_co2':
        summary = f"Phòng lab có khoảng {tel.get('person_count')} người, CO2={tel.get('co2_ppm')} ppm và dự báo CO2 tiếp tục tăng. Đây là rủi ro vận hành, không chỉ là một giá trị vượt ngưỡng."
        action = 'Thông báo người vận hành, mở thông gió/cửa sổ nếu được phép và cân nhắc nghỉ giải lao nếu CO2 tiếp tục tăng.'
        review = True
    elif sid == 'fire_alarm_conflict':
        summary = 'Vision phát hiện vùng màu cam giống lửa nhưng smoke/gas sensor còn thấp và projector_on có thể tạo false alarm. Bằng chứng chưa đủ để xác nhận cháy.'
        action = 'Hiển thị cảnh báo REVIEW, yêu cầu người trực kiểm tra camera và cảm biến khói trước khi kích hoạt quy trình khẩn cấp.'
        review = True; risk = max_risk('MEDIUM', risk if risk_order(risk) < 4 else 'CRITICAL')
    elif sid == 'fall_or_bending_ambiguity':
        summary = 'Pose/fall model báo tư thế thấp nhưng confidence và thời gian chuyển động có thể chưa đủ để xác nhận té ngã.'
        action = 'Yêu cầu human review qua camera; nếu emergency button được nhấn hoặc người nằm bất động lâu hơn thì nâng mức cảnh báo.'
        review = True
    elif sid == 'ppe_danger_zone':
        summary = 'Người được phát hiện trong vùng nguy hiểm khi máy đang chạy và thiếu PPE. Đây là tổ hợp bằng chứng từ vision + trạng thái máy, không phải một detection đơn lẻ.'
        action = 'Phát cảnh báo an toàn mức cao/khẩn, yêu cầu người vận hành kiểm tra và xử lý theo quy trình.'
        review = True
    elif sid == 'greenhouse_leaf_disease_risk':
        summary = 'Vision nghi có đốm lá, đồng thời độ ẩm cao và dự báo tiếp tục bất lợi. Chưa nên chẩn đoán bệnh từ một ảnh duy nhất.'
        action = 'Chụp thêm ảnh rõ hơn, kiểm tra vùng lá nghi bệnh, giảm độ ẩm nếu có thể và ghi nhận để theo dõi.'
        review = True if tel.get('image_quality') != 'GOOD' or float(tel.get('leaf_spot_confidence',0)) < 0.75 else False
    else:
        summary = 'LLM tổng hợp context packet và safety rules.'; action = 'Tiếp tục giám sát.'
    return {
        'situation_summary': summary,
        'risk_level': risk,
        'recommended_action': action,
        'control_allowed': False,
        'need_human_review': bool(review),
        'blocked_reason': 'Lab mode blocks direct actuator control. LLM output is decision support, not final actuator command.',
        'evidence_used': ['telemetry', 'lab3_anomaly_detection', 'lab4_forecasting', 'lab6_camera_motion_metadata', 'lab7_vision_ai', 'safety_rules']
    }

def call_ollama(context: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    if requests is None:
        raise RuntimeError('requests is not installed')
    base = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = model or os.getenv('OLLAMA_MODEL', 'qwen3:1.7b')
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are an AIoT decision assistant. Return JSON only.'},
            {'role': 'user', 'content': build_prompt(context)}
        ],
        'stream': False,
        'format': 'json',
        'options': {'temperature': float(os.getenv('LLM_TEMPERATURE', '0.2')), 'num_ctx': int(os.getenv('LLM_NUM_CTX', '4096'))}
    }
    r = requests.post(f'{base}/api/chat', json=payload, timeout=int(os.getenv('LLM_TIMEOUT_SEC', '60')))
    r.raise_for_status()
    raw = r.json().get('message', {}).get('content', '{}')
    return json.loads(raw)

def reason_with_llm(context: Dict[str, Any], mode: str = 'mock') -> Dict[str, Any]:
    t0 = time.time()
    provider = mode
    raw = None
    try:
        if mode == 'mock':
            raw = mock_llm_reason(context)
        elif mode == 'local':
            raw = call_ollama(context)
        elif mode == 'api':
            # Placeholder: keep lab runnable; instructors can wire Gemini/OpenAI-compatible APIs later.
            raw = mock_llm_reason(context)
            provider = 'api-placeholder-using-mock'
        else:
            raise HTTPException(status_code=400, detail='mode must be mock, local, or api')
    except Exception as e:
        raw = mock_llm_reason(context)
        provider = f'{mode}-failed-fallback-mock'
        raw['blocked_reason'] = f"LLM provider failed; fallback mock used. Original error: {e}"
        raw['need_human_review'] = True
        raw['control_allowed'] = False
    latency_ms = round((time.time() - t0) * 1000, 2)
    valid, validation_msg = validate_llm_output(raw)
    if not valid:
        raw = {
            'situation_summary': 'LLM output invalid; fallback to safe review.',
            'risk_level': 'MEDIUM',
            'recommended_action': 'Request human review because LLM JSON is invalid.',
            'control_allowed': False,
            'need_human_review': True,
            'blocked_reason': validation_msg,
            'evidence_used': ['validation_error']
        }
    final = apply_safety_gate(raw, context)
    logrow = {
        'timestamp': now_iso(), 'context_id': context['context_id'], 'scenario_id': context['scenario_id'],
        'provider': provider, 'latency_ms': latency_ms, 'risk_level': final['risk_level'],
        'control_allowed': final['control_allowed'], 'need_human_review': final['need_human_review'],
        'validation': validation_msg
    }
    write_csv_row(OUTPUT_DIR / 'llm_decision_log.csv', logrow)
    write_csv_row(OUTPUT_DIR / 'latency_report.csv', logrow)
    return {'provider': provider, 'latency_ms': latency_ms, 'raw_llm_output': raw, 'validated': valid, 'validation_message': validation_msg, 'final_decision': final}

def validate_llm_output(obj: Dict[str, Any]) -> tuple[bool, str]:
    required = ['situation_summary', 'risk_level', 'recommended_action', 'control_allowed', 'need_human_review', 'blocked_reason', 'evidence_used']
    for k in required:
        if k not in obj:
            return False, f'Missing key: {k}'
    if obj['risk_level'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        return False, 'Invalid risk_level'
    if not isinstance(obj['control_allowed'], bool):
        return False, 'control_allowed must be boolean'
    if not isinstance(obj['need_human_review'], bool):
        return False, 'need_human_review must be boolean'
    if not isinstance(obj['evidence_used'], list):
        return False, 'evidence_used must be a list'
    return True, 'OK'

def apply_safety_gate(decision: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    final = dict(decision)
    reasons = []
    # Lab mode blocks actuator control
    if final.get('control_allowed'):
        final['control_allowed'] = False
        reasons.append('Blocked: lab mode does not allow direct actuator control.')
    # Low vision confidence blocks control
    tel = context.get('telemetry', {})
    confidence_fields = ['vision_confidence', 'flame_vision_confidence', 'fall_confidence', 'leaf_spot_confidence']
    for key in confidence_fields:
        if key in tel and float(tel[key]) < 0.6:
            final['need_human_review'] = True
            final['control_allowed'] = False
            reasons.append(f'Human review required: {key} < 0.6.')
    if context['scenario_id'] == 'fire_alarm_conflict' and parse_bool(tel.get('projector_on')) and float(tel.get('smoke_level',0)) < 10:
        final['need_human_review'] = True
        final['control_allowed'] = False
        reasons.append('Conflict: projector_on=true and smoke/gas evidence is weak.')
    if reasons:
        final['blocked_reason'] = (final.get('blocked_reason') or '') + ' ' + ' '.join(reasons)
    write_csv_row(OUTPUT_DIR / 'safety_audit_log.csv', {
        'timestamp': now_iso(), 'context_id': context['context_id'], 'scenario_id': context['scenario_id'],
        'risk_level': final['risk_level'], 'control_allowed': final['control_allowed'],
        'need_human_review': final['need_human_review'], 'blocked_reason': final.get('blocked_reason','')[:500]
    })
    return final

# -------------------------------------------------------------------
# API models
# -------------------------------------------------------------------
class SensorUpdate(BaseModel):
    updates: Dict[str, Any] = Field(default_factory=dict)

# -------------------------------------------------------------------
# Background timeline thread
# -------------------------------------------------------------------
def _runner() -> None:
    while True:
        time.sleep(STATE.interval_sec)
        with STATE.lock:
            if not STATE.running:
                break
        STATE.step()

def start_background(scenario_id: Optional[str] = None, interval_sec: float = 2.0) -> Dict[str, Any]:
    if scenario_id:
        STATE.reset(scenario_id)
    with STATE.lock:
        STATE.interval_sec = max(0.5, float(interval_sec))
        if not STATE.running:
            STATE.running = True
            t = threading.Thread(target=_runner, daemon=True)
            STATE.thread = t
            t.start()
        return STATE.snapshot_locked()

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get('/')
def index():
    return FileResponse(APP_DIR / 'index.html')

@app.get('/health')
def health():
    return {'status': 'ok', 'lab': 'Lab 8 v3', 'time': now_iso()}

@app.get('/scenarios')
def list_scenarios():
    return [{'scenario_id': sid, 'title': s['title'], 'why': s['why_it_is_interesting']} for sid, s in SCENARIOS.items()]

@app.get('/live/state')
def live_state():
    return STATE.snapshot()

@app.post('/live/reset')
def live_reset(scenario_id: str = 'lab_overcrowded_high_co2'):
    return STATE.reset(scenario_id)

@app.post('/live/start')
def live_start(scenario_id: Optional[str] = None, interval_sec: float = 2.0):
    return start_background(scenario_id, interval_sec)

@app.post('/live/stop')
def live_stop():
    with STATE.lock:
        STATE.running = False
        return STATE.snapshot_locked()

@app.post('/live/step')
def live_step():
    return STATE.step()

@app.post('/live/update-sensor')
def live_update_sensor(payload: SensorUpdate):
    return STATE.update_sensor(payload.updates)

@app.get('/context/{scenario_id}')
def get_context(scenario_id: str):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    return build_context_packet(sensors, scenario_id)

@app.get('/ai-models/{scenario_id}')
def ai_models(scenario_id: str):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    return previous_ai_model_outputs(sensors, scenario_id)

@app.get('/baseline/{scenario_id}')
def baseline(scenario_id: str, level: str = 'sensor'):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    if level == 'sensor':
        return sensor_only_decision(sensors, scenario_id)
    if level == 'ai':
        return sensor_ai_decision(sensors, scenario_id)
    raise HTTPException(status_code=400, detail='level must be sensor or ai')

@app.get('/reason/{scenario_id}')
def reason(scenario_id: str, mode: str = 'mock'):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    context = build_context_packet(sensors, scenario_id)
    return reason_with_llm(context, mode=mode)

@app.get('/compare-three-levels/{scenario_id}')
def compare_three_levels(scenario_id: str, mode: str = 'mock'):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    sensor_dec = sensor_only_decision(sensors, scenario_id)
    ai_dec = sensor_ai_decision(sensors, scenario_id)
    context = build_context_packet(sensors, scenario_id)
    llm_dec = reason_with_llm(context, mode=mode)
    row = {'timestamp': now_iso(), 'scenario_id': scenario_id, 'mode': mode,
           'sensor_risk': sensor_dec['risk_level'], 'ai_risk': ai_dec['risk_level'], 'llm_risk': llm_dec['final_decision']['risk_level']}
    write_csv_row(OUTPUT_DIR / 'comparison_log.csv', row)
    return {'scenario_id': scenario_id, 'telemetry': sensors, 'sensor_only': sensor_dec, 'sensor_plus_ai_models': ai_dec, 'sensor_ai_llm': llm_dec, 'why_previous_labs_matter': 'Lab 3/4/6/7 tạo evidence. Lab 8 dùng LLM để reasoning trên evidence đó; LLM không thay thế các model trước.'}

@app.post('/live/compare-three-levels')
def live_compare_three_levels(mode: str = 'mock'):
    snap = STATE.snapshot()
    return compare_three_levels(snap['scenario_id'], mode=mode)

@app.post('/vision-reason/{scenario_id}')
async def vision_reason(scenario_id: str, mode: str = 'mock', image: Optional[UploadFile] = File(default=None)):
    """Optional image-aware endpoint. In mock mode it creates an image observation from filename/metadata."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail='Unknown scenario')
    snap = STATE.snapshot()
    sensors = snap['sensors'] if snap['scenario_id'] == scenario_id else dict(SCENARIOS[scenario_id]['timeline'][0])
    context = build_context_packet(sensors, scenario_id)
    if image is not None:
        # No actual image model in the guaranteed-to-run path; image is represented as an observation.
        context['uploaded_image_observation'] = {
            'filename': image.filename,
            'content_type': image.content_type,
            'note': 'Mock vision observation. Replace this with Gemma 3 4B / cloud VLM if available.'
        }
    return reason_with_llm(context, mode=mode)

@app.get('/stream/events')
def stream_events():
    def gen():
        last = None
        while True:
            snap = STATE.snapshot()
            data = json.dumps({'time': now_iso(), 'state': snap}, ensure_ascii=False)
            if data != last:
                yield f'data: {data}\n\n'
                last = data
            time.sleep(1)
    return StreamingResponse(gen(), media_type='text/event-stream')
