import os
import threading
import time

import cv2
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from ultralytics import YOLO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CAMERA_INDEX = 1
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 25
FRAME_INTERVAL = 1 / CAMERA_FPS
RECONNECT_INTERVAL = 2

YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.5
YOLO_INTERVAL = 0.2

API_URL = os.getenv(
    "SENTINEL_API_URL",
    "http://localhost:8000",
)
API_TOKEN = os.getenv("SENTINEL_API_TOKEN")

EVENT_COOLDOWN = 5

camera_active = False
model_loaded = False

latest_frame: bytes | None = None
latest_raw_frame = None
latest_annotated_frame: bytes | None = None

frame_lock = threading.Lock()
annotated_frame_lock = threading.Lock()

last_event_time: dict[str, float] = {}


def open_camera():
    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW,
    )

    if not camera.isOpened():
        camera.release()
        return None

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH,
    )
    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT,
    )
    camera.set(
        cv2.CAP_PROP_FPS,
        CAMERA_FPS,
    )

    return camera


def send_detection_event(
    detection_type: str,
    confidence: float,
    details: dict,
):
    current_time = time.time()
    previous_time = last_event_time.get(detection_type, 0)

    if current_time - previous_time < EVENT_COOLDOWN:
        return

    last_event_time[detection_type] = current_time

    payload = {
        "type": detection_type,
        "source": "vision",
        "confidence": confidence,
        "details": details,
    }

    headers = {
        "Content-Type": "application/json",
    }

    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    try:
        response = requests.post(
            f"{API_URL}/api/events",
            json=payload,
            headers=headers,
            timeout=2,
        )

        if not response.ok:
            print(
                f"[YOLO] Événement rejeté par l'API : "
                f"HTTP {response.status_code}"
            )

    except requests.RequestException as error:
        print(
            f"[YOLO] Impossible d'envoyer l'événement : {error}"
        )


def capture_frames():
    global camera_active
    global latest_frame
    global latest_raw_frame

    while True:
        camera = open_camera()

        if camera is None:
            camera_active = False

            with frame_lock:
                latest_frame = None
                latest_raw_frame = None

            time.sleep(RECONNECT_INTERVAL)
            continue

        print("Caméra ouverte avec succès.")

        while True:
            success, frame = camera.read()

            if not success:
                print("Caméra déconnectée.")

                camera_active = False

                with frame_lock:
                    latest_frame = None
                    latest_raw_frame = None

                camera.release()
                break

            camera_active = True

            with frame_lock:
                latest_raw_frame = frame.copy()

            success, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80],
            )

            if success:
                with frame_lock:
                    latest_frame = buffer.tobytes()

            time.sleep(FRAME_INTERVAL)


def run_yolo():
    global model_loaded
    global latest_annotated_frame

    print(f"[YOLO] Chargement du modèle {YOLO_MODEL}...")

    try:
        model = YOLO(YOLO_MODEL)
        model_loaded = True

        print("[YOLO] Modèle chargé avec succès.")

    except Exception as error:
        model_loaded = False

        print(
            f"[YOLO] Impossible de charger le modèle : {error}"
        )

        return

    while True:
        with frame_lock:
            frame = (
                latest_raw_frame.copy()
                if latest_raw_frame is not None
                else None
            )

        if frame is None:
            time.sleep(0.1)
            continue

        try:
            results = model(
                frame,
                conf=YOLO_CONFIDENCE,
                classes=[0],
                verbose=False,
            )

            result = results[0]
            annotated_frame = result.plot()

            detected_objects = []

            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(
                        box.cls[0].item()
                    )

                    confidence = float(
                        box.conf[0].item()
                    )

                    class_name = model.names[class_id]

                    detected_objects.append(
                        {
                            "class": class_name,
                            "confidence": round(
                                confidence,
                                3,
                            ),
                        }
                    )

                    if class_name == "person":
                        send_detection_event(
                            detection_type="person_detected",
                            confidence=confidence,
                            details={
                                "class": class_name,
                                "objects": detected_objects,
                            },
                        )

            success, buffer = cv2.imencode(
                ".jpg",
                annotated_frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80],
            )

            if success:
                with annotated_frame_lock:
                    latest_annotated_frame = (
                        buffer.tobytes()
                    )

        except Exception as error:
            print(
                f"[YOLO] Erreur pendant l'inférence : {error}"
            )

        time.sleep(YOLO_INTERVAL)


def generate_frames():
    while True:
        with annotated_frame_lock:
            frame = latest_annotated_frame

        if frame is None:
            with frame_lock:
                frame = latest_frame

        if frame is None:
            time.sleep(0.1)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: "
            + str(len(frame)).encode()
            + b"\r\n\r\n"
            + frame
            + b"\r\n"
        )

        time.sleep(FRAME_INTERVAL)


@app.get("/camera/stream")
def camera_stream():
    return StreamingResponse(
        generate_frames(),
        media_type=(
            "multipart/x-mixed-replace; boundary=frame"
        ),
    )


@app.get("/camera/snapshot")
def camera_snapshot():
    with annotated_frame_lock:
        frame = latest_annotated_frame

    if frame is None:
        with frame_lock:
            frame = latest_frame

    if frame is None:
        return Response(
            content=b"Camera indisponible.",
            status_code=503,
        )

    return Response(
        content=frame,
        media_type="image/jpeg",
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "camera": CAMERA_INDEX,
        "camera_open": camera_active,
        "yolo_loaded": model_loaded,
    }


capture_thread = threading.Thread(
    target=capture_frames,
    daemon=True,
)

yolo_thread = threading.Thread(
    target=run_yolo,
    daemon=True,
)

capture_thread.start()
yolo_thread.start()