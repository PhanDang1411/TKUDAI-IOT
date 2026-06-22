#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

checks = []
checks.append(("GET /health", client.get("/health")))
checks.append(("GET /model-info", client.get("/model-info")))
checks.append(("POST /detect-anomaly", client.post("/detect-anomaly", json={
    "target": "temperature",
    "current_value": 34.0,
    "recent_values": [27.1, 27.3, 27.2, 27.4, 27.5],
    "threshold_z": 2.5
})))
checks.append(("POST /forecast", client.post("/forecast", json={
    "target": "co2",
    "recent_values": [800, 840, 870, 910, 950],
    "horizon_minutes": 15
})))
checks.append(("GET /vision/model-info", client.get("/vision/model-info")))
checks.append(("GET /classify-image-demo", client.get("/classify-image-demo")))

all_ok = True
for name, response in checks:
    ok = response.status_code in (200, 503)
    print(name, response.status_code, "PASS" if ok else "FAIL")
    if not ok:
        print(response.text)
        all_ok = False

if not all_ok:
    raise SystemExit(1)
print("LOCAL_PIPELINE_TEST_PASS")
