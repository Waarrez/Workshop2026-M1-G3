from factory import get_fastapi
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
from itertools import count
from datetime import datetime, timezone
from models.models import ReadingIn, CommandIn, EventIn
from hub import Hub
from fastapi import Query, WebSocket, WebSocketDisconnect,Depends
from typing import Optional
from pydantic import ValidationError
from fastapi import HTTPException
import mqtt_bridge
from models.db_models import ReadingDB, EventDB, CommandDB
from database import SessionLocal
import os
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends

hub = Hub()

security = HTTPBearer()
API_TOKEN = os.getenv("SENTINEL_API_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    if not API_TOKEN or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token invalide")

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

    db = SessionLocal()
    try:
        db_row = ReadingDB(
            device_id=row["id"],
            v=row.get("v", 1),
            seq=row.get("seq"),
            uptime_s=row.get("uptime_s"),
            valid=row.get("valid", True),
            temp_c=row.get("temp_c"),
            humidity_pct=row.get("humidity_pct"),
            gas_raw=row.get("gas_raw"),
            motion=row.get("motion"),
        )
        db.add(db_row)
        db.commit()
    finally:
        db.close()

    await hub.broadcast({"type": "reading", "payload": row})

app = get_fastapi(on_reading=ingest)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

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

@app.post("/api/commands", status_code=201, dependencies=[Depends(verify_token)])
async def send_command(cmd: CommandIn):
    ok = mqtt_bridge.publish_command(cmd.device_id, {
        "target": cmd.target, "state": cmd.state, "duration_ms": cmd.duration_ms})
    if not ok:
        raise HTTPException(503, "Broker MQTT indisponible")
    entry = {"cmd_id": next(CMD_IDS), "created_at": now_iso(), **cmd.model_dump()}

    db = SessionLocal()
    try:
        db_row = CommandDB(
            device_id=cmd.device_id,
            target=cmd.target,
            state=cmd.state,
            duration_ms=cmd.duration_ms,
        )
        db.add(db_row)
        db.commit()
    finally:
        db.close()

    await hub.broadcast({"type": "command", "payload": entry})
    return entry

@app.get("/api/readings")
async def list_readings(device_id: Optional[str] = None,
                        limit: int = Query(100, ge=1, le=1000),
                        dependencies=[Depends(verify_token)]):
    rows = [r for r in READINGS if device_id is None or r["id"] == device_id]
    return rows[-limit:]

@app.get("/api/readings/latest", dependencies=[Depends(verify_token)])
async def latest_readings():
    latest = {}
    for r in READINGS:
        latest[r["id"]] = r
    return list(latest.values())

@app.get("/api/devices", dependencies=[Depends(verify_token)])
async def list_devices():
    now = datetime.now(timezone.utc)
    out = []
    for dev_id, last in DEVICES.items():
        age = (now - datetime.fromisoformat(last)).total_seconds()
        out.append({"id": dev_id, "last_seen": last, "online": age < ONLINE_TIMEOUT_S})
    return out

@app.post("/api/events", status_code=201, dependencies=[Depends(verify_token)])
async def post_event(event: EventIn):
    row = {"received_at": now_iso(), **event.model_dump()}
    EVENTS.append(row)

    db = SessionLocal()
    try:
        db_row = EventDB(
            type=row["type"],
            source=row.get("source", "vision"),
            confidence=row.get("confidence"),
            details=row.get("details"),
        )
        db.add(db_row)
        db.commit()
    finally:
        db.close()

    await hub.broadcast({"type": "event", "payload": row})
    return {"status": "ok"}

@app.get("/api/events", dependencies=[Depends(verify_token)])
async def list_events(limit: int = Query(100, ge=1, le=1000)):
    return list(EVENTS)[-limit:]

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # garde la connexion ouverte
    except WebSocketDisconnect:
        hub.disconnect(ws)
