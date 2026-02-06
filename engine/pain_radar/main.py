"""Pain Radar research engine — FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pain_radar.api.routes import init_routes, router
from pain_radar.core.config import get_settings
from pain_radar.db import Database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Ensure data directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Connect database
    db = Database(settings.db_path)
    await db.connect()

    # Create orchestrator (lazy import to avoid circular deps)
    from pain_radar.pipeline.orchestrator import ResearchOrchestrator
    orchestrator = ResearchOrchestrator(db=db, settings=settings)

    # Wire up routes
    init_routes(db, orchestrator)

    yield

    # Shutdown
    await db.close()


app = FastAPI(
    title="Pain Radar Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "pain-radar-engine"}
