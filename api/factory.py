from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

def get_fastapi():
    return FastAPI(title="Api SENTINEL X", lifespan=lifespan)
