"""FastAPI app entry point for SEHRA Analyzer API."""

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.config import get_settings
from api.core.db import init_db
from api.core.logging_config import setup_logging

logger = logging.getLogger("sehra.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_db()
    _seed_users()
    logger.info("SEHRA API started")
    yield
    logger.info("SEHRA API shutting down")


app = FastAPI(
    title="SEHRA Analyzer API",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

# GZip responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routers import auth, sehras, analysis, chat, export, share, codebook, drafts, agent, conversations

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sehras.router, prefix="/api/v1", tags=["sehras"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(share.router, prefix="/api/v1", tags=["share"])
app.include_router(codebook.router, prefix="/api/v1", tags=["codebook"])
app.include_router(drafts.router, prefix="/api/v1", tags=["drafts"])
app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])


@app.get("/health")
def health():
    return {"status": "ok"}


def _seed_users():
    """Seed users table from auth_config.yaml on first startup."""
    import yaml
    from api.core.db import get_session, User

    config_path = os.path.join(os.path.dirname(__file__), "..", "auth_config.yaml")
    if not os.path.exists(config_path):
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    credentials = config.get("credentials", {}).get("usernames", {})

    with get_session() as session:
        for username, info in credentials.items():
            role = info.get("role", "admin" if username == "admin" else "analyst")
            existing = session.query(User).filter(User.username == username).first()
            if not existing:
                user = User(
                    username=username,
                    name=info.get("name", username),
                    password_hash=info.get("password", ""),
                    role=role,
                )
                session.add(user)
                logger.info("Seeded user: %s (%s)", username, role)
