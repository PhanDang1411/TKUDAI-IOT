
from fastapi.testclient import TestClient
from app import app, OUTPUT_DIR

client = TestClient(app)

checks = []

def check(name, method, path, **kwargs):
    r = getattr(client, method)(path, **kwargs)
    ok = 200 <= r.status_code < 300
    checks.append((name, ok, r.status_code, r.text[:120]))
    if not ok:
        raise AssertionError(f"{name} failed: {r.status_code} {r.text}")
    return r.json()

check('health', 'get', '/health')
scenarios = check('scenarios', 'get', '/scenarios')
assert len(scenarios) >= 5
check('reset', 'post', '/live/reset?scenario_id=lab_overcrowded_high_co2')
check('state', 'get', '/live/state')
check('step', 'post', '/live/step')
check('update_sensor', 'post', '/live/update-sensor', json={'updates': {'co2_ppm': 1850, 'person_count': 35, 'vision_confidence': 0.82}})
ctx = check('context', 'get', '/context/lab_overcrowded_high_co2')
assert 'evidence_from_previous_labs' in ctx
cmp = check('compare_three_levels', 'get', '/compare-three-levels/lab_overcrowded_high_co2?mode=mock')
assert 'sensor_only' in cmp and 'sensor_plus_ai_models' in cmp and 'sensor_ai_llm' in cmp
fire = check('fire_conflict', 'get', '/compare-three-levels/fire_alarm_conflict?mode=mock')
assert fire['sensor_ai_llm']['final_decision']['need_human_review'] is True
check('baseline_ai', 'get', '/baseline/ppe_danger_zone?level=ai')
check('vision_reason_mock', 'post', '/vision-reason/fire_alarm_conflict?mode=mock', files={'image': ('projector_orange.jpg', b'fake-image', 'image/jpeg')})

(OUTPUT_DIR / 'RUN_TEST_LOG.txt').write_text('LOCAL_PIPELINE_TEST_PASS\n' + '\n'.join([str(x) for x in checks]), encoding='utf-8')
print('LOCAL_PIPELINE_TEST_PASS')
print(f'Wrote {OUTPUT_DIR / "RUN_TEST_LOG.txt"}')
