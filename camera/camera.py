
"""Serveur caméra et traitement IA SENTINEL-X.

Regroupe la capture vidéo, la détection humaine YOLO, la zone interdite,
le suivi de présence, les alertes API et la commande du buzzer.
"""

import logging
import os
import threading
import time
from pathlib import Path

import cv2
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from ultralytics import YOLO

log = logging.getLogger("sentinel.vision")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(
    os.getenv(
        "SENTINEL_YOLO_MODEL",
        str(Path(__file__).resolve().parent / "yolov8n.pt"),
    )
)

# Paramètres de la caméra et de l'IA.
CAMERA_SOURCE = os.getenv("SENTINEL_CAMERA_SOURCE", "1")
CAMERA_WIDTH = int(os.getenv("SENTINEL_CAMERA_WIDTH", "640"))
CAMERA_HEIGHT = int(os.getenv("SENTINEL_CAMERA_HEIGHT", "480"))
CAMERA_FPS = 25
CAMERA_INTERVAL = 1 / CAMERA_FPS
RECONNECT_INTERVAL = 2

YOLO_CONFIDENCE = 0.45
YOLO_IMAGE_SIZE = 320
YOLO_PROCESS_EVERY_N = 1

# Polygone normalisé fourni par le développeur IA.
# Coordonnées comprises entre 0 et 1.
ZONE_POLYGON = [
    (0.25, 0.35),
    (0.95, 0.35),
    (0.95, 1.0),
    (0.25, 1.0),
]

PRESENCE_MIN_DURATION = 3.0
PRESENCE_GRACE = 1.0
ALERT_COOLDOWN = 20.0

API_URL = os.getenv(
    "SENTINEL_API_URL",
    "http://localhost:8000",
).rstrip("/")
API_TOKEN = os.getenv("SENTINEL_API_TOKEN", "")
DEVICE_ID = os.getenv("SENTINEL_DEVICE_ID", "sentinel-01")

JPEG_QUALITY = 70
HTTP_TIMEOUT = 3

app = FastAPI(title="SENTINEL-X Camera IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# État partagé entre les routes HTTP et le traitement IA.
running = True
worker_started = False
camera_active = False
model_loaded = False

latest_frame: bytes | None = None
latest_annotated_frame: bytes | None = None

frame_lock = threading.Lock()
annotated_frame_lock = threading.Lock()
status_lock = threading.Lock()

vision_status = {
    "persons": 0,
    "in_zone": 0,
    "suspect": False,
    "fps": 0.0,
    "latency_ms": 0.0,
    "buzzer": "desactive",
    "last_error": None,
}


def update_status(**values):
    """Met à jour l'état partagé de la supervision."""
    with status_lock:
        vision_status.update(values)


def get_status():
    """Retourne une copie de l'état de la vision."""
    with status_lock:
        return vision_status.copy()


def encode_frame(frame) -> bytes | None:
    """Encode une image au format JPEG."""
    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY],
    )
    return buffer.tobytes() if success else None


def api_headers() -> dict[str, str]:
    """Construit les en-têtes utilisés par l'API existante."""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


def post_event(
    event_type: str,
    confidence: float,
    details: dict,
):
    """Envoie un événement à POST /api/events sans bloquer l'IA."""
    payload = {
        "type": event_type,
        "source": "vision",
        "confidence": confidence,
        "details": details,
    }

    try:
        response = requests.post(
            f"{API_URL}/api/events",
            json=payload,
            headers=api_headers(),
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        log.info("Événement API envoyé : %s", event_type)
    except requests.RequestException:
        log.exception("Impossible d'envoyer l'événement à l'API.")


def send_event_async(
    event_type: str,
    confidence: float,
    details: dict,
):
    """Exécute l'envoi d'événement dans un thread séparé."""
    threading.Thread(
        target=post_event,
        args=(event_type, confidence, details),
        daemon=True,
    ).start()


def send_buzzer_command(state: bool):
    """Commande le buzzer via POST /api/commands et MQTT."""
    payload = {
        "device_id": DEVICE_ID,
        "target": "buzzer",
        "state": state,
        "duration_ms": 4000 if state else None,
    }

    try:
        response = requests.post(
            f"{API_URL}/api/commands",
            json=payload,
            headers=api_headers(),
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()

        status = "envoye" if state else "desactive"
        update_status(buzzer=status)
        log.info("Commande buzzer envoyée : %s", status)
        return True

    except requests.RequestException:
        update_status(buzzer="echec")
        log.exception("Impossible de commander le buzzer via l'API.")
        return False


def send_buzzer_async(state: bool):
    """Envoie une commande buzzer sans bloquer le traitement vidéo."""
    threading.Thread(
        target=send_buzzer_command,
        args=(state,),
        daemon=True,
    ).start()


def point_in_zone(x: float, y: float, width: int, height: int) -> bool:
    """Vérifie si un point image se trouve dans la zone interdite."""
    polygon = [
        (int(px * width), int(py * height))
        for px, py in ZONE_POLYGON
    ]
    return cv2.pointPolygonTest(
        __import__("numpy").array(polygon, dtype="int32"),
        (float(x), float(y)),
        False,
    ) >= 0


def draw_zone(frame, alert: bool):
    """Dessine le polygone de la zone interdite."""
    import numpy as np

    height, width = frame.shape[:2]
    polygon = np.array(
        [
            (int(x * width), int(y * height))
            for x, y in ZONE_POLYGON
        ],
        dtype=np.int32,
    )

    color = (0, 0, 255) if alert else (0, 165, 255)

    overlay = frame.copy()
    cv2.fillPoly(overlay, [polygon], color)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
    cv2.polylines(frame, [polygon], True, color, 2)

    cv2.putText(
        frame,
        "ZONE INTERDITE",
        (polygon[0][0] + 5, max(20, polygon[0][1] - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
    )


def open_camera():
    """Ouvre la caméra et configure sa résolution."""
    source = CAMERA_SOURCE
    if source.isdigit():
        source = int(source)

    if os.name == "nt" and isinstance(source, int):
        camera = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    else:
        camera = cv2.VideoCapture(source)

    if not camera.isOpened():
        camera.release()
        return None

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    return camera


def capture_frames():
    """Capture continuellement les images de la caméra."""
    global camera_active, latest_frame

    while running:
        camera = open_camera()

        if camera is None:
            camera_active = False
            update_status(last_error="Caméra indisponible")
            time.sleep(RECONNECT_INTERVAL)
            continue

        log.info("Caméra ouverte : source=%s", CAMERA_SOURCE)
        update_status(last_error=None)

        try:
            while running:
                success, frame = camera.read()

                if not success:
                    log.warning("Caméra déconnectée.")
                    break

                camera_active = True
                encoded = encode_frame(frame)

                if encoded is not None:
                    with frame_lock:
                        latest_frame = encoded

                time.sleep(CAMERA_INTERVAL)

        finally:
            camera.release()
            camera_active = False

            with frame_lock:
                latest_frame = None

        if running:
            time.sleep(RECONNECT_INTERVAL)


def process_vision():
    """Détecte les personnes, suit leur présence et gère les alertes."""
    global model_loaded, latest_annotated_frame

    model = None
    alarm_active = False
    last_alert = 0.0
    presence_since = None
    last_presence = None
    last_sequence_frame = None
    frame_count = 0
    fps_times = []

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Modèle YOLO introuvable : {MODEL_PATH}"
            )

        log.info("Chargement du modèle YOLO : %s", MODEL_PATH)
        model = YOLO(str(MODEL_PATH), task="detect")
        model_loaded = True
        update_status(last_error=None)
        log.info("Modèle YOLO chargé.")

        while running:
            with frame_lock:
                encoded = latest_frame

            if encoded is None or encoded is last_sequence_frame:
                time.sleep(0.02)
                continue

            last_sequence_frame = encoded
            frame = cv2.imdecode(
                __import__("numpy").frombuffer(encoded, dtype="uint8"),
                cv2.IMREAD_COLOR,
            )

            if frame is None:
                continue

            start = time.perf_counter()
            now = time.monotonic()
            frame_count += 1

            height, width = frame.shape[:2]
            detections = []

            if frame_count % YOLO_PROCESS_EVERY_N == 0:
                results = model.predict(
                    frame,
                    conf=YOLO_CONFIDENCE,
                    imgsz=YOLO_IMAGE_SIZE,
                    classes=[0],
                    verbose=False,
                )

                result = results[0]
                if result.boxes is not None:
                    for box in result.boxes:
                        coords = box.xyxy[0].cpu().tolist()
                        confidence = float(box.conf[0].item())

                        x1, y1, x2, y2 = (
                            int(value) for value in coords
                        )

                        detections.append(
                            (x1, y1, x2, y2, confidence)
                        )

            in_zone = [
                detection
                for detection in detections
                if point_in_zone(
                    (detection[0] + detection[2]) / 2,
                    detection[3],
                    width,
                    height,
                )
            ]

            if in_zone:
                if presence_since is None:
                    presence_since = now
                last_presence = now
            elif (
                last_presence is not None
                and now - last_presence > PRESENCE_GRACE
            ):
                presence_since = None
                last_presence = None

            duration = (
                now - presence_since
                if presence_since is not None
                else 0.0
            )

            suspect = (
                presence_since is not None
                and duration >= PRESENCE_MIN_DURATION
            )

            # Activation et arrêt du buzzer sur changement d'état.
            if suspect and in_zone and not alarm_active:
                alarm_active = True
                send_buzzer_async(True)

            elif not suspect and alarm_active:
                alarm_active = False
                send_buzzer_async(False)

            # Une alerte API au maximum toutes les 20 secondes.
            if (
                suspect
                and in_zone
                and now - last_alert >= ALERT_COOLDOWN
            ):
                last_alert = now
                best = max(in_zone, key=lambda item: item[4])

                severity = "medium"
                details = {
                    "severity": severity,
                    "message": (
                        "Présence humaine en zone interdite "
                        f"depuis {duration:.1f} secondes."
                    ),
                    "duration_s": round(duration, 1),
                    "bbox": list(best[:4]),
                    "confidence": round(best[4], 3),
                    "pir_confirmed": False,
                }

                snapshot = encode_frame(frame)
                if snapshot is not None:
                    snapshot_dir = PROJECT_ROOT / "camera" / "snapshots"
                    snapshot_dir.mkdir(parents=True, exist_ok=True)
                    snapshot_path = snapshot_dir / (
                        time.strftime("intrusion_%Y%m%d_%H%M%S.jpg")
                    )
                    try:
                        snapshot_path.write_bytes(snapshot)
                        details["snapshot"] = str(snapshot_path)
                    except OSError:
                        log.exception("Impossible d'enregistrer le snapshot.")

                send_event_async(
                    "intrusion",
                    best[4],
                    details,
                )

            # Annotation de la zone et des personnes détectées.
            draw_zone(frame, suspect)

            for detection in detections:
                x1, y1, x2, y2, confidence = detection
                hit = detection in in_zone
                color = (0, 0, 255) if hit else (0, 220, 0)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2,
                )
                cv2.putText(
                    frame,
                    f"person {confidence:.2f}",
                    (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

            latency = (time.perf_counter() - start) * 1000
            fps_times.append(time.monotonic())
            fps_times = fps_times[-30:]

            fps = (
                (len(fps_times) - 1)
                / (fps_times[-1] - fps_times[0])
                if len(fps_times) > 1
                and fps_times[-1] > fps_times[0]
                else 0.0
            )

            status = (
                "INTRUSION"
                if suspect
                else "PRESENCE EN ZONE"
                if in_zone
                else "RAS"
            )

            cv2.putText(
                frame,
                f"{status} | {fps:.1f} FPS | {latency:.0f} ms",
                (8, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255) if suspect else (255, 255, 255),
                2,
            )

            annotated = encode_frame(frame)
            if annotated is not None:
                with annotated_frame_lock:
                    latest_annotated_frame = annotated

            update_status(
                persons=len(detections),
                in_zone=len(in_zone),
                suspect=bool(suspect),
                fps=round(fps, 1),
                latency_ms=round(latency, 1),
                last_error=None,
            )

    except Exception as error:
        model_loaded = False
        update_status(last_error=str(error))
        log.exception("Erreur du traitement IA.")

    finally:
        model_loaded = False

        if alarm_active:
            send_buzzer_async(False)

        log.info("Traitement IA arrêté.")


def generate_frames():
    """Diffuse les images en MJPEG."""
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

        time.sleep(0.01)


@app.on_event("startup")
def startup():
    """Démarre la capture et le traitement IA."""
    global worker_started

    if worker_started:
        return

    worker_started = True

    threading.Thread(
        target=capture_frames,
        name="sentinel-camera",
        daemon=True,
    ).start()

    threading.Thread(
        target=process_vision,
        name="sentinel-vision",
        daemon=True,
    ).start()


@app.get("/camera/stream")
def camera_stream():
    """Retourne le flux vidéo annoté."""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/camera/snapshot")
def camera_snapshot():
    """Retourne la dernière image disponible."""
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
    """Retourne l'état du serveur caméra et du traitement IA."""
    return {
        "status": "ok",
        "camera_open": camera_active,
        "yolo_loaded": model_loaded,
        "vision": get_status(),
    }