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
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 25
FRAME_INTERVAL = 1 / CAMERA_FPS
RECONNECT_INTERVAL = 2

camera_active = False
latest_frame: bytes | None = None
frame_lock = threading.Lock()


def open_camera():
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        return None

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    return camera


def capture_frames():
    global camera_active
    global latest_frame

    while True:
        camera = open_camera()

        if camera is None:
            camera_active = False

            with frame_lock:
                latest_frame = None

            time.sleep(RECONNECT_INTERVAL)
            continue

        print("Caméra ouverte avec succès.")
        camera_active = True

        while True:
            success, frame = camera.read()

            if not success:
                print("Caméra déconnectée.")

                camera_active = False

                with frame_lock:
                    latest_frame = None

                camera.release()
                break

            success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

            if success:
                with frame_lock:
                    latest_frame = buffer.tobytes()

            time.sleep(FRAME_INTERVAL)


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
        return Response(content=b"Camera indisponible.", status_code=503)

    return Response(content=frame, media_type="image/jpeg")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "camera": CAMERA_INDEX,
        "camera_open": camera_active,
    }


capture_thread = threading.Thread(target=capture_frames, daemon=True)

capture_thread.start()