from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.lobby_router import router as lobby_router
from app.routers.game_session_router import router as game_session_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="StaffordChess API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(lobby_router)
app.include_router(game_session_router)
@app.get("/health")
async def health():
    return {"status": "ok"}