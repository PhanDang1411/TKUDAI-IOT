from pathlib import Path

path = Path("vision_engines.py")
text = path.read_text(encoding="utf-8")

start = text.index("def run_pose_landmark")
end = text.index("def run_hand_gesture")

new_code = r'''
def classify_body_pose(lm):
    """
    Phan loai dang nguoi:
    STANDING: dung
    SITTING: ngoi
    HAND_UP: gio tay
    BENDING: cui nguoi
    UNKNOWN: khong xac dinh
    """
    try:
        left_shoulder = lm[11]
        right_shoulder = lm[12]
        left_wrist = lm[15]
        right_wrist = lm[16]
        left_hip = lm[23]
        right_hip = lm[24]
        left_knee = lm[25]
        right_knee = lm[26]

        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        wrist_y = min(left_wrist.y, right_wrist.y)
        hip_y = (left_hip.y + right_hip.y) / 2
        knee_y = (left_knee.y + right_knee.y) / 2

        shoulder_vis = (left_shoulder.visibility + right_shoulder.visibility) / 2
        hip_vis = (left_hip.visibility + right_hip.visibility) / 2
        knee_vis = (left_knee.visibility + right_knee.visibility) / 2

        if shoulder_vis < 0.45 or hip_vis < 0.45:
            return "UNKNOWN"

        if wrist_y < shoulder_y:
            return "HAND_UP"

        if abs(shoulder_y - hip_y) < 0.13:
            return "BENDING"

        if knee_vis >= 0.35 and abs(hip_y - knee_y) < 0.18:
            return "SITTING"

        if knee_vis >= 0.35 and hip_y < knee_y:
            return "STANDING"

        return "UNKNOWN"

    except Exception:
        return "UNKNOWN"


def run_pose_landmark(frame: np.ndarray, min_conf: float = 0.5):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    try:
        import mediapipe as mp

        mp_pose = mp.solutions.pose
        mp_draw = mp.solutions.drawing_utils

        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=min_conf,
            min_tracking_confidence=min_conf
        ) as pose:
            results = pose.process(rgb)

        if results.pose_landmarks:
            mp_draw.draw_landmarks(
                annotated,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            pose_label = classify_body_pose(results.pose_landmarks.landmark)

            cv2.putText(
                annotated,
                f"Pose: {pose_label}",
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                (0, 255, 0),
                3,
                cv2.LINE_AA
            )

            h, w = annotated.shape[:2]

            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                records.append({
                    "task": "pose",
                    "landmark_id": idx,
                    "x": int(landmark.x * w),
                    "y": int(landmark.y * h),
                    "visibility": float(landmark.visibility),
                    "pose_label": pose_label,
                    "confidence": min_conf,
                    "engine": "mediapipe_pose"
                })

            subtitle = f"{pose_label} | {len(records)} landmarks"

        else:
            cv2.putText(
                annotated,
                "No person pose detected",
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3,
                cv2.LINE_AA
            )
            subtitle = "no pose detected"

        elapsed_ms = (time.perf_counter() - start) * 1000
        annotated = add_header(
            annotated,
            "Pose Landmark",
            f"MediaPipe Pose | {subtitle} | {elapsed_ms:.1f} ms"
        )

        event = event_from_records("pose", records, "NORMAL")
        return annotated, records, event

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000

        cv2.putText(
            annotated,
            f"MediaPipe Pose error: {str(e)}",
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

        annotated = add_header(
            annotated,
            "Pose Landmark",
            f"error | {elapsed_ms:.1f} ms"
        )

        records.append({
            "task": "pose",
            "error": str(e),
            "engine": "mediapipe_pose"
        })

        event = event_from_records("pose", records, "WARNING")
        return annotated, records, event


'''

new_text = text[:start] + new_code + text[end:]
path.write_text(new_text, encoding="utf-8")

print("PATCH_POSE_DONE")