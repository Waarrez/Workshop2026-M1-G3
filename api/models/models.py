from pydantic import BaseModel
from typing import Literal, Optional

class ReadingIn(BaseModel):
    id: str
    v: int = 1
    seq: Optional[int] = None
    uptime_s: Optional[int] = None
    valid: bool = True
    temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    gas_raw: Optional[int] = None
    motion: Optional[bool] = None
    data: Optional[dict] = None


class CommandIn(BaseModel):
    device_id: str
    target: Literal["buzzer", "led"]
    state: bool  # true = ON, false = OFF
    duration_ms: Optional[int] = None


class EventIn(BaseModel):
    type: str  # ex. "person_detected"
    source: str = "vision"
    confidence: Optional[float] = None
    details: Optional[dict] = None