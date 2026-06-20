from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.core.config import settings
from contextlib import asynccontextmanager
from app.routers import auth, users, rooms, messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="chatapp-cache")
    yield

app = FastAPI(
    title="ChatApp",
    lifespan=lifespan,
)

app.mount(
    "/uploads", 
    StaticFiles(directory=settings.upload_path), 
    name="uploads"
)

@app.get("/")
async def healthcheck():
    return {"message": "Hello world"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)
