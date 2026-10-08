from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class ReadingDB(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, index=True, nullable=False)
    v = Column(Integer, default=1)
    seq = Column(Integer, nullable=True)
    uptime_s = Column(Integer, nullable=True)
    valid = Column(Boolean, default=True)
    temp_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    gas_raw = Column(Integer, nullable=True)
    motion = Column(Boolean, nullable=True)
    data = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class CommandDB(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, index=True, nullable=False)
    target = Column(String, nullable=False)
    state = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventDB(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    source = Column(String, default="vision")
    confidence = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)