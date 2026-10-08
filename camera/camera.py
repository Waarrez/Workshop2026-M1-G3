import cv2
from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse

app = FastAPI()

CAMERA_INDEX = 1

camera = cv2.VideoCapture(CAMERA_INDEX)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
camera.set(cv2.CAP_PROP_FPS, 25)

print(f"Ouverture de la caméra {CAMERA_INDEX}...")

if not camera.isOpened():
    raise RuntimeError(f"Impossible d'ouvrir la webcam avec l'index {CAMERA_INDEX}.")

print("Caméra ouverte avec succès.")


def generate_frames():
    while True:
        success, frame = camera.read()

        if not success:
            continue

        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: "
            + str(len(buffer)).encode()
            + b"\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


@app.get("/camera/stream")
def camera_stream():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/camera/snapshot")
def camera_snapshot():
    success, frame = camera.read()

    if not success:
        return Response(content=b"Impossible de capturer une image.", status_code=500)

    success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        return Response(content=b"Impossible d'encoder l'image.", status_code=500)

    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "camera": CAMERA_INDEX,
        "camera_open": camera.isOpened(),
    }