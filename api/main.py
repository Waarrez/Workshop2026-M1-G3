from factory import get_fastapi
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
from itertools import count
from datetime import datetime, timezone
from models.models import ReadingIn, CommandIn, EventIn
from hub import Hub
from fastapi import Query, WebSocket, WebSocketDisconnect
from typing import Optional
from pydantic import ValidationError
from fastapi import HTTPException
import mqtt_bridge

async def ingest(data: dict):
    print(f"[MQTT] message reçu : {data}")
    try:
        reading = ReadingIn(**data)
    except ValidationError as e:
        print(f"[MQTT] message rejeté : {e}")
        return
    row = normalize(reading)
    READINGS.append(row)
    DEVICES[row["id"]] = row["received_at"]
    await hub.broadcast({"type": "reading", "payload": row})

app = get_fastapi(on_reading=ingest)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

hub = Hub()

READINGS: deque = deque(maxlen=5000)
EVENTS: deque = deque(maxlen=1000)
DEVICES: dict = {}                       # id -> dernière activité
PENDING_CMDS: dict = defaultdict(deque)  # id -> commandes en attente
CMD_IDS = count(1)
ONLINE_TIMEOUT_S = 30

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@app.get("/health")
def health():
    return {"status": "ok"}

def normalize(r: ReadingIn) -> dict:
    row = r.model_dump(exclude={"data"})
    if r.data:
        row.update({k: v for k, v in r.data.items() if k in row})
    row["received_at"] = now_iso()
    return row

@app.post("/data", status_code=201)  # route utilisée par l'ESP8266
@app.post("/api/readings", status_code=201)
async def post_reading(reading: ReadingIn):
    await ingest(reading.model_dump())
    return {"status": "ok"}

@app.post("/api/commands", status_code=201)
async def send_command(cmd: CommandIn):
    ok = mqtt_bridge.publish_command(cmd.device_id, {
        "target": cmd.target, "state": cmd.state, "duration_ms": cmd.duration_ms})
    if not ok:
        raise HTTPException(503, "Broker MQTT indisponible")
    entry = {"cmd_id": next(CMD_IDS), "created_at": now_iso(), **cmd.model_dump()}
    await hub.broadcast({"type": "command", "payload": entry})
    return entry


@app.get("/api/readings")
async def list_readings(device_id: Optional[str] = None,
                        limit: int = Query(100, ge=1, le=1000)):
    rows = [r for r in READINGS if device_id is None or r["id"] == device_id]
    return rows[-limit:]


@app.get("/api/readings/latest")
async def latest_readings():
    latest = {}
    for r in READINGS:
        latest[r["id"]] = r
    return list(latest.values())


# ---------- Appareils ----------
@app.get("/api/devices")
async def list_devices():
    now = datetime.now(timezone.utc)
    out = []
    for dev_id, last in DEVICES.items():
        age = (now - datetime.fromisoformat(last)).total_seconds()
        out.append({"id": dev_id, "last_seen": last, "online": age < ONLINE_TIMEOUT_S})
    return out

@app.get("/api/commands/{device_id}/pending")  # pour un ESP qui interroge en HTTP
async def pop_pending(device_id: str):
    queue = PENDING_CMDS[device_id]
    out = list(queue)
    queue.clear()
    return out

# ---------- Événements (vision, alertes) ----------
@app.post("/api/events", status_code=201)
async def post_event(event: EventIn):
    row = {"received_at": now_iso(), **event.model_dump()}
    EVENTS.append(row)
    await hub.broadcast({"type": "event", "payload": row})
    return {"status": "ok"}


@app.get("/api/events")
async def list_events(limit: int = Query(100, ge=1, le=1000)):
    return list(EVENTS)[-limit:]


# ---------- WebSocket ----------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # garde la connexion ouverte
    except WebSocketDisconnect:
        hub.disconnect(ws)
