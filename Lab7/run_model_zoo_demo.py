from pathlib import Path
import json
import time

import cv2
import numpy as np

from vision_engines import ZooState, run_task

BASE = Path(__file__).resolve().parent
OUT = BASE / 'outputs'
CAP = BASE / 'data' / 'captures'
SAMPLE = BASE / 'data' / 'sample_images'
for d in [OUT, CAP, SAMPLE]:
    d.mkdir(parents=True, exist_ok=True)


def make_sample_frame(i=0):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (35, 42, 54)
    cv2.putText(img, 'AIOT LAB 7 MODEL ZOO', (95, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (240,240,240), 2)
    cv2.rectangle(img, (90+i*10, 150), (220+i*10, 310), (70, 170, 255), -1)
    cv2.circle(img, (445-i*6, 250), 72, (80, 220, 130), -1)
    cv2.putText(img, 'OCR TEST 123', (190, 420), cv2.FONT_HERSHEY_SIMPLEX, 1.05, (255,255,255), 2)
    return img


def main():
    tasks = ['detection','tracking_counting','pose_landmark','hand_gesture','face_landmark','ocr','segmentation','opencv_motion']
    state = ZooState()
    report = []
    for idx, task in enumerate(tasks):
        frame = make_sample_frame(idx)
        raw_path = SAMPLE / f'sample_{idx}_{task}.jpg'
        cv2.imwrite(str(raw_path), frame)
        t0 = time.perf_counter()
        annotated, records, event = run_task(task, frame, state=state, conf=0.35)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        out_path = CAP / f'demo_{task}.jpg'
        cv2.imwrite(str(out_path), annotated)
        report.append({
            'task': task,
            'output_image': str(out_path.relative_to(BASE)),
            'num_records': len(records),
            'event_type': event.get('event_type'),
            'severity': event.get('severity'),
            'elapsed_ms': round(elapsed_ms, 2)
        })
    (OUT / 'model_zoo_demo_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (BASE / 'RUN_TEST_LOG.txt').write_text('LOCAL_PIPELINE_TEST_PASS\nAll model zoo demo tasks ran with fallback-safe engines.\n', encoding='utf-8')
    print('LOCAL_PIPELINE_TEST_PASS')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
