import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


# =============================
# Global state
# =============================

@dataclass
class ZooState:
    next_id: int = 1
    tracking_objects: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    last_centroid_y: Dict[int, int] = field(default_factory=dict)
    count_in: int = 0
    count_out: int = 0
    motion_prev_gray: Optional[np.ndarray] = None


_YOLO_MODEL = None


# =============================
# Common helpers
# =============================

def resize_keep_width(frame: np.ndarray, width: int = 640) -> np.ndarray:
    h, w = frame.shape[:2]
    if w == width:
        return frame.copy()
    scale = width / float(w)
    new_h = int(h * scale)
    return cv2.resize(frame, (width, new_h))


def put_label(
    img: np.ndarray,
    text: str,
    org: Tuple[int, int],
    color: Tuple[int, int, int] = (0, 255, 0)
) -> None:
    cv2.putText(
        img,
        text,
        org,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA
    )


def add_header(img: np.ndarray, title: str, subtitle: str = "") -> np.ndarray:
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 58), (20, 20, 20), -1)
    put_label(out, title, (12, 25), (0, 255, 255))
    if subtitle:
        cv2.putText(
            out,
            subtitle,
            (12, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (230, 230, 230),
            1,
            cv2.LINE_AA
        )
    return out


def contour_boxes(
    frame: np.ndarray,
    min_area: int = 1200
) -> List[Tuple[int, int, int, int, float]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 70, 160)
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        conf = min(0.99, max(0.25, area / (frame.shape[0] * frame.shape[1])))
        boxes.append((x, y, x + w, y + h, float(conf)))

    boxes = sorted(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    return boxes[:8]


def event_from_records(
    task: str,
    records: List[Dict[str, Any]],
    severity: str = "NORMAL"
) -> Dict[str, Any]:
    return {
        "task": task,
        "num_records": len(records),
        "severity": severity,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# =============================
# Task 1: YOLO detection
# =============================

def _try_load_yolo(model_path: str = "yolov8n.pt"):
    global _YOLO_MODEL

    if _YOLO_MODEL is not None:
        return _YOLO_MODEL

    try:
        from ultralytics import YOLO
        _YOLO_MODEL = YOLO(model_path)
        return _YOLO_MODEL
    except Exception:
        return None


def run_yolo_detection(
    frame: np.ndarray,
    conf: float = 0.35,
    classes: str = "",
    model_path: str = "yolov8n.pt"
):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    model = _try_load_yolo(model_path)

    if model is not None:
        try:
            class_filter = None
            if classes.strip():
                class_filter = [int(x.strip()) for x in classes.split(",") if x.strip().isdigit()]

            results = model.predict(
                annotated,
                conf=conf,
                classes=class_filter,
                verbose=False
            )

            names = model.names

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    cls_id = int(box.cls[0].item())
                    score = float(box.conf[0].item())
                    label = str(names.get(cls_id, cls_id))

                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    put_label(annotated, f"{label} {score:.2f}", (x1, max(25, y1 - 8)))

                    records.append({
                        "task": "detection",
                        "class_id": cls_id,
                        "class_name": label,
                        "confidence": score,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "engine": "ultralytics_yolo"
                    })

            elapsed_ms = (time.perf_counter() - start) * 1000
            annotated = add_header(
                annotated,
                "Object Detection / YOLO",
                f"YOLO real | {len(records)} objects | {elapsed_ms:.1f} ms"
            )
            event = event_from_records(
                "detection",
                records,
                "WARNING" if len(records) > 0 else "NORMAL"
            )
            return annotated, records, event

        except Exception as e:
            put_label(annotated, f"YOLO error: {e}", (20, 90), (0, 0, 255))

    # fallback detection nếu chưa cài YOLO
    boxes = contour_boxes(annotated, min_area=1200)

    for idx, (x1, y1, x2, y2, score) in enumerate(boxes):
        label = "object"
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 180, 0), 2)
        put_label(annotated, f"{label} {score:.2f}", (x1, max(25, y1 - 8)), (255, 180, 0))
        records.append({
            "task": "detection",
            "class_id": -1,
            "class_name": label,
            "confidence": score,
            "bbox": [x1, y1, x2, y2],
            "engine": "opencv_fallback"
        })

    elapsed_ms = (time.perf_counter() - start) * 1000
    annotated = add_header(
        annotated,
        "Object Detection / YOLO",
        f"fallback | {len(records)} objects | {elapsed_ms:.1f} ms"
    )
    event = event_from_records("detection", records, "NORMAL")
    return annotated, records, event


# =============================
# Task 2: Tracking and counting
# =============================

def _assign_tracking_ids(
    boxes: List[Tuple[int, int, int, int, float]],
    state: ZooState
) -> List[Dict[str, Any]]:
    assigned = []
    used_ids = set()

    for x1, y1, x2, y2, score in boxes:
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        best_id = None
        best_dist = 999999

        for obj_id, (px, py) in state.tracking_objects.items():
            if obj_id in used_ids:
                continue
            dist = (cx - px) ** 2 + (cy - py) ** 2
            if dist < best_dist:
                best_dist = dist
                best_id = obj_id

        if best_id is None or best_dist > 80 ** 2:
            best_id = state.next_id
            state.next_id += 1

        used_ids.add(best_id)
        state.tracking_objects[best_id] = (cx, cy)

        assigned.append({
            "id": best_id,
            "bbox": [x1, y1, x2, y2],
            "centroid": [cx, cy],
            "confidence": score
        })

    return assigned


def run_tracking_counting(
    frame: np.ndarray,
    state: ZooState,
    line_ratio: float = 0.55
):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    h, w = annotated.shape[:2]
    line_y = int(h * line_ratio)

    boxes = contour_boxes(annotated, min_area=1000)
    tracks = _assign_tracking_ids(boxes, state)

    records: List[Dict[str, Any]] = []

    cv2.line(annotated, (0, line_y), (w, line_y), (0, 255, 255), 2)

    for tr in tracks:
        obj_id = tr["id"]
        x1, y1, x2, y2 = tr["bbox"]
        cx, cy = tr["centroid"]

        prev_y = state.last_centroid_y.get(obj_id)

        if prev_y is not None:
            if prev_y < line_y <= cy:
                state.count_in += 1
            elif prev_y > line_y >= cy:
                state.count_out += 1

        state.last_centroid_y[obj_id] = cy

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 255), 2)
        cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
        put_label(annotated, f"ID {obj_id}", (x1, max(25, y1 - 8)), (255, 0, 255))

        records.append({
            "task": "tracking_counting",
            "object_id": obj_id,
            "centroid_x": cx,
            "centroid_y": cy,
            "count_in": state.count_in,
            "count_out": state.count_out,
            "engine": "opencv_tracking_demo"
        })

    elapsed_ms = (time.perf_counter() - start) * 1000
    annotated = add_header(
        annotated,
        "Tracking & Counting",
        f"IN={state.count_in} OUT={state.count_out} | {elapsed_ms:.1f} ms"
    )
    event = event_from_records("tracking_counting", records, "NORMAL")
    return annotated, records, event


# =============================
# Task 3: Pose Landmark - nhận dáng người thật
# =============================




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


def run_hand_gesture(frame: np.ndarray, min_conf: float = 0.5):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    try:
        import mediapipe as mp

        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils

        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_conf,
            min_tracking_confidence=min_conf
        ) as hands:
            results = hands.process(rgb)

        gesture_label = "NO_HAND"

        if results.multi_hand_landmarks:
            h, w = annotated.shape[:2]

            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                mp_draw.draw_landmarks(
                    annotated,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                lm = hand_landmarks.landmark

                # Rule đơn giản để demo cử chỉ
                wrist = lm[0]
                index_tip = lm[8]
                middle_tip = lm[12]
                ring_tip = lm[16]
                pinky_tip = lm[20]
                thumb_tip = lm[4]

                fingers_up = 0
                for tip_id in [8, 12, 16, 20]:
                    if lm[tip_id].y < lm[tip_id - 2].y:
                        fingers_up += 1

                if fingers_up >= 4:
                    gesture_label = "OPEN_PALM"
                elif fingers_up == 0:
                    gesture_label = "CLOSED_FIST"
                elif fingers_up == 2 and index_tip.y < lm[6].y and middle_tip.y < lm[10].y:
                    gesture_label = "VICTORY"
                elif index_tip.y < lm[6].y and fingers_up == 1:
                    gesture_label = "POINTING_UP"
                elif thumb_tip.y < wrist.y and fingers_up <= 1:
                    gesture_label = "THUMB_UP"
                else:
                    gesture_label = "HAND_DETECTED"

                for idx, landmark in enumerate(lm):
                    records.append({
                        "task": "hand_gesture",
                        "hand_id": hand_idx,
                        "landmark_id": idx,
                        "x": int(landmark.x * w),
                        "y": int(landmark.y * h),
                        "gesture": gesture_label,
                        "confidence": min_conf,
                        "engine": "mediapipe_hands_rule_demo"
                    })

            cv2.putText(
                annotated,
                f"Gesture: {gesture_label}",
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                3,
                cv2.LINE_AA
            )

        else:
            cv2.putText(
                annotated,
                "No hand detected",
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3,
                cv2.LINE_AA
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        annotated = add_header(
            annotated,
            "Hand / Gesture",
            f"{gesture_label} | {elapsed_ms:.1f} ms"
        )
        event = event_from_records("hand_gesture", records, "NORMAL")
        return annotated, records, event

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        cv2.putText(
            annotated,
            f"MediaPipe Hand error: {str(e)}",
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )
        annotated = add_header(annotated, "Hand / Gesture", f"error | {elapsed_ms:.1f} ms")
        records.append({
            "task": "hand_gesture",
            "error": str(e),
            "engine": "mediapipe_hands"
        })
        event = event_from_records("hand_gesture", records, "WARNING")
        return annotated, records, event


# =============================
# Task 5: Face Landmark
# =============================

def run_face_landmark(frame: np.ndarray, min_conf: float = 0.5):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    try:
        import mediapipe as mp

        mp_face = mp.solutions.face_mesh
        mp_draw = mp.solutions.drawing_utils
        mp_styles = mp.solutions.drawing_styles

        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        with mp_face.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_conf,
            min_tracking_confidence=min_conf
        ) as face_mesh:
            results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            h, w = annotated.shape[:2]

            for face_idx, face_landmarks in enumerate(results.multi_face_landmarks):
                mp_draw.draw_landmarks(
                    image=annotated,
                    landmark_list=face_landmarks,
                    connections=mp_face.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_styles.get_default_face_mesh_tesselation_style()
                )

                for idx, landmark in enumerate(face_landmarks.landmark):
                    records.append({
                        "task": "face_landmark",
                        "face_id": face_idx,
                        "landmark_id": idx,
                        "x": int(landmark.x * w),
                        "y": int(landmark.y * h),
                        "confidence": min_conf,
                        "engine": "mediapipe_face_mesh"
                    })

            subtitle = f"{len(records)} landmarks"

        else:
            cv2.putText(
                annotated,
                "No face detected",
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3,
                cv2.LINE_AA
            )
            subtitle = "no face detected"

        elapsed_ms = (time.perf_counter() - start) * 1000
        annotated = add_header(
            annotated,
            "Face Landmark",
            f"MediaPipe FaceMesh | {subtitle} | {elapsed_ms:.1f} ms"
        )

        event = event_from_records("face_landmark", records, "NORMAL")
        return annotated, records, event

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        cv2.putText(
            annotated,
            f"Face error: {str(e)}",
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )
        annotated = add_header(annotated, "Face Landmark", f"error | {elapsed_ms:.1f} ms")
        records.append({
            "task": "face_landmark",
            "error": str(e),
            "engine": "mediapipe_face_mesh"
        })
        event = event_from_records("face_landmark", records, "WARNING")
        return annotated, records, event


# =============================
# Task 6: OCR
# =============================

def run_ocr(frame: np.ndarray, text_conf: float = 0.5):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    try:
        import easyocr

        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(annotated)

        for bbox, text, score in results:
            if score < text_conf:
                continue

            pts = np.array(bbox, dtype=np.int32)
            cv2.polylines(annotated, [pts], True, (0, 255, 0), 2)
            x, y = pts[0]
            put_label(annotated, f"{text} {score:.2f}", (int(x), int(y) - 6))

            records.append({
                "task": "ocr",
                "text": text,
                "confidence": float(score),
                "bbox": pts.tolist(),
                "engine": "easyocr"
            })

        subtitle = f"EasyOCR | {len(records)} texts"

    except Exception:
        # fallback OCR demo
        h, w = annotated.shape[:2]
        cv2.rectangle(annotated, (60, h // 3), (w - 60, h // 3 + 80), (0, 255, 255), 2)
        put_label(annotated, "OCR DEMO TEXT", (70, h // 3 + 45), (0, 255, 255))

        records.append({
            "task": "ocr",
            "text": "OCR DEMO TEXT",
            "confidence": text_conf,
            "bbox": [60, h // 3, w - 60, h // 3 + 80],
            "engine": "ocr_fallback_demo"
        })
        subtitle = "fallback demo"

    elapsed_ms = (time.perf_counter() - start) * 1000
    annotated = add_header(
        annotated,
        "OCR",
        f"{subtitle} | {elapsed_ms:.1f} ms"
    )
    event = event_from_records("ocr", records, "NORMAL")
    return annotated, records, event


# =============================
# Task 7: Segmentation
# =============================

def run_segmentation(frame: np.ndarray, alpha: float = 0.35):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    records: List[Dict[str, Any]] = []

    gray = cv2.cvtColor(annotated, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    _, mask = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    overlay = annotated.copy()
    overlay[mask > 0] = (0, 255, 0)
    annotated = cv2.addWeighted(overlay, alpha, annotated, 1 - alpha, 0)

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(c))
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 2)
        put_label(annotated, f"mask area={area:.0f}", (x, max(25, y - 8)), (0, 255, 255))

        records.append({
            "task": "segmentation",
            "mask_area": area,
            "region_bbox": [x, y, x + w, y + h],
            "engine": "opencv_threshold_segmentation"
        })

    elapsed_ms = (time.perf_counter() - start) * 1000
    annotated = add_header(
        annotated,
        "Segmentation",
        f"OpenCV mask | {len(records)} region | {elapsed_ms:.1f} ms"
    )
    event = event_from_records("segmentation", records, "NORMAL")
    return annotated, records, event


# =============================
# Task 8: OpenCV Motion
# =============================

def run_opencv_motion(
    frame: np.ndarray,
    state: ZooState,
    motion_threshold: int = 25,
    min_area: int = 800
):
    start = time.perf_counter()
    annotated = resize_keep_width(frame, 640)
    gray = cv2.cvtColor(annotated, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    records: List[Dict[str, Any]] = []

    if state.motion_prev_gray is None:
        state.motion_prev_gray = gray
        elapsed_ms = (time.perf_counter() - start) * 1000
        annotated = add_header(
            annotated,
            "OpenCV Motion",
            f"initialized | {elapsed_ms:.1f} ms"
        )
        event = {
            "task": "opencv_motion",
            "event_type": "MOTION_INITIALIZED",
            "num_records": 0,
            "severity": "NORMAL",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return annotated, records, event

    frame_delta = cv2.absdiff(state.motion_prev_gray, gray)
    thresh = cv2.threshold(
        frame_delta,
        motion_threshold,
        255,
        cv2.THRESH_BINARY
    )[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
        put_label(annotated, f"motion {area:.0f}", (x, max(25, y - 8)), (0, 0, 255))

        records.append({
            "task": "opencv_motion",
            "motion_area": float(area),
            "motion_bbox": [x, y, x + w, y + h],
            "engine": "opencv_frame_difference"
        })

    state.motion_prev_gray = gray

    elapsed_ms = (time.perf_counter() - start) * 1000
    annotated = add_header(
        annotated,
        "OpenCV Motion",
        f"{len(records)} motion regions | {elapsed_ms:.1f} ms"
    )
    event = event_from_records(
        "opencv_motion",
        records,
        "WARNING" if len(records) > 0 else "NORMAL"
    )
    return annotated, records, event


# =============================
# Task registry
# =============================

TASKS = {
    "detection": run_yolo_detection,
    "tracking_counting": run_tracking_counting,
    "pose_landmark": run_pose_landmark,
    "hand_gesture": run_hand_gesture,
    "face_landmark": run_face_landmark,
    "ocr": run_ocr,
    "segmentation": run_segmentation,
    "opencv_motion": run_opencv_motion,
}


def run_task(
    task: str,
    frame: np.ndarray,
    state: Optional[ZooState] = None,
    **params
):
    if state is None:
        state = ZooState()

    if task == "detection":
        return run_yolo_detection(
            frame,
            conf=float(params.get("conf", 0.35)),
            classes=str(params.get("classes", "")),
            model_path=str(params.get("model_path", "yolov8n.pt"))
        )

    if task == "tracking_counting":
        return run_tracking_counting(
            frame,
            state,
            line_ratio=float(params.get("line_ratio", 0.55))
        )

    if task == "pose_landmark":
        return run_pose_landmark(
            frame,
            min_conf=float(params.get("min_conf", 0.5))
        )

    if task == "hand_gesture":
        return run_hand_gesture(
            frame,
            min_conf=float(params.get("min_conf", 0.5))
        )

    if task == "face_landmark":
        return run_face_landmark(
            frame,
            min_conf=float(params.get("min_conf", 0.5))
        )

    if task == "ocr":
        return run_ocr(
            frame,
            text_conf=float(params.get("text_conf", 0.5))
        )

    if task == "segmentation":
        return run_segmentation(
            frame,
            alpha=float(params.get("alpha", 0.35))
        )

    if task == "opencv_motion":
        return run_opencv_motion(
            frame,
            state,
            motion_threshold=int(params.get("motion_threshold", 25)),
            min_area=int(params.get("min_area", 800))
        )

    annotated = resize_keep_width(frame, 640)
    records = [{
        "task": task,
        "error": "unknown task"
    }]
    event = event_from_records(task, records, "WARNING")
    annotated = add_header(annotated, "Unknown Task", task)
    return annotated, records, event
