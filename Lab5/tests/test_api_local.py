from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service_status"] == "ok"


def test_forecast():
    r = client.post("/forecast", json={"recent_values": [1, 2, 3, 4, 5], "horizon_minutes": 15})
    assert r.status_code == 200
    assert "predicted_value" in r.json()["model_output"]


def test_vision_info():
    r = client.get("/vision/model-info")
    assert r.status_code == 200
    assert r.json()["task"] == "image_classification"


def test_image_demo_page():
    r = client.get("/classify-image-demo")
    assert r.status_code == 200
    assert "Upload ảnh" in r.text
    assert "classify-image-annotated" in r.text
