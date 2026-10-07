import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import Base, engine
import mqtt_bridge

def get_fastapi(on_reading=None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine)
        if on_reading:
            mqtt_bridge.start(asyncio.get_running_loop(), on_reading)
        yield
        if on_reading:
            mqtt_bridge.stop()

    return FastAPI(title="Api SENTINEL X", lifespan=lifespan)