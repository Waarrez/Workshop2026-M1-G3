import threading
import time

import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CAMERA_INDEX = 1
FRAME_INTERVAL = 0.04

camera = cv2.VideoCapture(CAMERA_INDEX)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
camera.set(cv2.CAP_PROP_FPS, 25)

camera_active = camera.isOpened()
latest_frame = None
frame_lock = threading.Lock()

print(f"Ouverture de la caméra {CAMERA_INDEX}...")

if not camera_active:
    raise RuntimeError(f"Impossible d'ouvrir la webcam avec l'index {CAMERA_INDEX}.")

print("Caméra ouverte avec succès.")


def capture_frames():
    global camera_active
    global latest_frame

    while True:
        success, frame = camera.read()

        if not success:
            camera_active = False
            time.sleep(1)
            continue

        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

        if not success:
            camera_active = False
            continue

        with frame_lock:
            latest_frame = buffer.tobytes()

        camera_active = True

        time.sleep(FRAME_INTERVAL)


capture_thread = threading.Thread(target=capture_frames, daemon=True)
capture_thread.start()


def generate_frames():
    while True:
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
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/camera/snapshot")
def camera_snapshot():
    with frame_lock:
        frame = latest_frame

    if frame is None:
        return Response(content=b"Impossible de capturer une image.", status_code=503)

    return Response(content=frame, media_type="image/jpeg")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "camera": CAMERA_INDEX,
        "camera_open": camera_active,
    }