"""FastAPI entry point.

Once running, http://localhost:8000/docs serves interactive OpenAPI documentation —
generated automatically by FastAPI from the type hints.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import llm
from .config import settings
from .database import Base, engine
from .deps import require_api_key
from .routers import mock, problems, review, stats, templates

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create missing tables on startup.

    This does NOT add columns to tables that already exist — run migrate.py for that
    (start.sh does). Alembic replaces both once columns start being renamed or dropped.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LeetCode Tracker API",
    description="Spaced-repetition tracker for the NeetCode 250",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "llm_enabled": llm.is_enabled(),
        "llm_provider": llm.provider_name(),
        "daily_caps": {"review": settings.daily_review_cap, "new": settings.daily_new_cap},
    }


for r in (problems.router, review.router, stats.router, mock.router, templates.router):
    app.include_router(r, dependencies=[Depends(require_api_key)])
