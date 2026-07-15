import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.init_db import init_db
from app.db.session import engine
from app.routers.ai import router as ai_router
from app.routers.ai_history import router as ai_history_router
from app.routers.auth import router as auth_router
from app.routers.financial_profiles import router as financial_profiles_router
from app.routers.health import router as health_router
from app.routers.loans import router as loans_router
from app.routers.settlement_records import router as settlement_records_router
from app.routers.users import router as users_router

app = FastAPI(
    title="FinRelief AI",
    description=(
        "AI-powered debt relief and loan negotiation platform. "
        "Integrates Google Gemini to generate personalised negotiation strategies, "
        "settlement analyses, repayment plans, and professional lender letters."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins in development; restrict in production via env var
# ---------------------------------------------------------------------------
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = (
    ["*"]
    if _allowed_origins_env == "*"
    else [o.strip() for o in _allowed_origins_env.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(auth_router)           # JWT: /auth/register, /auth/login, /auth/me ...
app.include_router(users_router)
app.include_router(loans_router)
app.include_router(financial_profiles_router)
app.include_router(settlement_records_router)
app.include_router(ai_history_router)
app.include_router(ai_router)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    gemini_key = os.getenv("GOOGLE_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    jwt_minutes = os.getenv("JWT_EXPIRE_MINUTES", "1440")
    status_ai = f"[OK] Gemini ({model})" if gemini_key else "[FALLBACK] Rule-based (no GOOGLE_API_KEY set)"
    print(f"[FinRelief AI] AI engine  : {status_ai}")
    print(f"[FinRelief AI] JWT auth   : HS256, expires in {jwt_minutes} min")
    print(f"[FinRelief AI] Database   : {os.getenv('DATABASE_URL', 'sqlite:///./finrelief.db')}")


# ---------------------------------------------------------------------------
# Root endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "FinRelief AI backend is running",
        "version": "2.0.0",
        "docs": "/docs",
        "ai_health": "/ai/health",
    }


@app.get("/test-db", tags=["Root"])
def test_db():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database_status": "Connected ✅"}

