from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import List, Dict, Any


def detect_anomaly_rule(current_value: float, recent_values: List[float], threshold_z: float = 2.5) -> Dict[str, Any]:
    """Simple fallback anomaly logic for deployment lab.

    This is intentionally not a strong anomaly model. It keeps Lab 5 focused
    on inference service packaging; Lab 3 already covered the anomaly model.
    """
    if len(recent_values) < 3:
        score = 0.0
        is_anomaly = False
        explanation = "Not enough recent history; using safe fallback."
    else:
        mu = mean(recent_values)
        sigma = pstdev(recent_values) or 1e-6
        score = abs((current_value - mu) / sigma)
        is_anomaly = score >= threshold_z
        explanation = f"z-score={score:.3f}, mean={mu:.3f}, std={sigma:.3f}"

    if not is_anomaly:
        severity = "NORMAL"
        decision = "NO_ALERT"
    elif score < threshold_z * 1.5:
        severity = "WARNING"
        decision = "CREATE_WARNING_EVENT"
    else:
        severity = "HIGH"
        decision = "CREATE_ALERT_AND_REQUIRE_HUMAN_CHECK"

    return {
        "model_output": {
            "anomaly_score": round(float(score), 6),
            "threshold_used": threshold_z,
            "is_anomaly": bool(is_anomaly),
            "model_version": "zscore_fallback_v1"
        },
        "event": {
            "severity": severity,
            "decision": decision,
            "explanation": explanation,
            "safety_note": "Không tự động điều khiển thiết bị chỉ dựa trên một điểm anomaly."
        }
    }


def forecast_moving_average(recent_values: List[float], horizon_minutes: int = 15) -> Dict[str, Any]:
    if not recent_values:
        raise ValueError("recent_values must not be empty")
    window = recent_values[-min(5, len(recent_values)):]
    predicted = sum(window) / len(window)
    last_value = recent_values[-1]
    delta = predicted - last_value
    return {
        "model_output": {
            "predicted_value": round(float(predicted), 6),
            "last_value": round(float(last_value), 6),
            "forecast_delta": round(float(delta), 6),
            "forecast_horizon_minutes": horizon_minutes,
            "model_version": "moving_average_baseline_v1"
        },
        "evaluation_hint": {
            "note": "Lab 5 dùng baseline inference demo. Metric đầy đủ đã học ở Lab 4."
        }
    }


def risk_from_forecast(predicted_value: float, warning_threshold: float, high_threshold: float) -> Dict[str, Any]:
    if predicted_value >= high_threshold:
        risk_level = "HIGH"
        recommendation = "REQUIRE_HUMAN_CHECK_BEFORE_ACTUATOR_CONTROL"
    elif predicted_value >= warning_threshold:
        risk_level = "WARNING"
        recommendation = "IMPROVE_MONITORING_OR_PREPARE_ACTION"
    else:
        risk_level = "NORMAL"
        recommendation = "CONTINUE_MONITORING"
    return {
        "decision": {
            "risk_level": risk_level,
            "recommendation": recommendation,
            "safety_note": "Forecast output must pass decision and safety rules before controlling devices."
        }
    }
