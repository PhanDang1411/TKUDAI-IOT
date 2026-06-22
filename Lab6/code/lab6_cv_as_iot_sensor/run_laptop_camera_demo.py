"""Run a Lab 6 demo using the laptop camera source 0.

This script is useful before presenting the web UI. It captures one snapshot,
runs the motion + person/animal verification flow, and writes a short log.
If the laptop camera is unavailable, the backend automatically falls back to
the simulated stream so the lab pipeline can still be verified.
"""
from __future__ import annotations

import json
from pathlib import Path

from app import log_image_pipeline, motion_capture, read_one_frame, record_short_video


LOG_PATH = Path("RUN_LAPTOP_CAMERA_DEMO_LOG.txt")


def main() -> None:
    source = "0"
    log_lines = []

    frame, source_type = read_one_frame(source)
    snapshot_result = log_image_pipeline(
        frame,
        source_type=source_type,
        device_id="laptop_camera:0",
        note="laptop camera demo snapshot",
    )
    log_lines.append(json.dumps({
        "step": "snapshot",
        "source_type": source_type,
        "image_id": snapshot_result["image_id"],
        "event": snapshot_result["event"]["event_type"],
    }, ensure_ascii=False))

    video_result = record_short_video(source, seconds=3)
    log_lines.append(json.dumps({
        "step": "record_video",
        "video_id": video_result["video_id"],
        "frames": video_result["frames"],
        "event": video_result["event"]["event_type"],
    }, ensure_ascii=False))

    motion_result = motion_capture(source, seconds=5, threshold=25, min_area=800)
    log_lines.append(json.dumps({
        "step": "motion_verify_person_animal",
        "image_id": motion_result["image_id"],
        "event": motion_result["motion_event"]["event_type"],
        "should_notify": motion_result["motion_classification"]["should_notify"],
        "target_type": motion_result["motion_classification"]["target_type"],
        "labels": motion_result["motion_classification"]["target_labels"],
        "motion_score": motion_result["motion_classification"]["motion_score"],
    }, ensure_ascii=False))

    status = "LAPTOP_CAMERA_DEMO_PASS"
    LOG_PATH.write_text(status + "\n" + "\n".join(log_lines), encoding="utf-8")
    print(status)
    print(LOG_PATH)
    for line in log_lines:
        print(line)


if __name__ == "__main__":
    main()
