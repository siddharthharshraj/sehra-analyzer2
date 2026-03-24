"""FastAPI app entry point for SEHRA Analyzer API."""

import os
import time
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text as sa_text

from api.config import get_settings
from api.core.db import init_db, engine
from api.core.logging_config import setup_logging, RequestIDMiddleware
from api.core.exceptions import SEHRAError

logger = logging.getLogger("sehra.api")

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    setup_logging()
    init_db()
    _seed_users()
    _start_time = time.time()
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

# Rate limiting (after CORS so preflight OPTIONS requests are not rate-limited)
from api.core.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, default_rpm=60, llm_rpm=20, login_rpm=10)

# Request ID + duration logging middleware
app.add_middleware(RequestIDMiddleware)

from api.routers import auth, sehras, analysis, chat, export, share, codebook, drafts, agent, conversations, audit

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
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(SEHRAError)
async def sehra_error_handler(request: Request, exc: SEHRAError):
    """Handle all SEHRA-specific exceptions with structured error responses."""
    logger.error(
        "[%s] %s: %s", exc.error_id, exc.__class__.__name__, exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions. Returns a structured error
    with a unique ID so the issue can be correlated in logs."""
    from api.core.exceptions import _generate_error_id
    error_id = _generate_error_id()
    logger.exception("[%s] Unhandled exception on %s %s", error_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "detail": "An unexpected error occurred. Reference this error_id when reporting the issue.",
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Enhanced health check with dependency status."""
    # Database connectivity
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    # LLM provider availability (check if API keys are configured)
    llm_providers = {
        "groq": bool(settings.groq_api_key),
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
    }

    uptime = round(time.time() - _start_time, 1) if _start_time else 0

    overall = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "llm_providers": llm_providers,
        "version": "1.0.0",
        "uptime_seconds": uptime,
    }


# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------

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
