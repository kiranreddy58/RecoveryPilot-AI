import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import RequestLoggingMiddleware, setup_logging
from app.core.database import init_db
from app.api.routes import health, events, cases

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RecoveryPilot AI",
    description="Explainable Autonomous Revenue Recovery Control Tower",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware — allow localhost dev servers and Vercel production/preview domains
origins = [
    settings.FRONTEND_URL,
    "https://recovery-pilot-ai.vercel.app",
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^(http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

# Import all routes
from app.api.routes import health, events, cases, metrics, batch, demo, razorpay, guardian, stream

# Include Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Recovery Cases"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(batch.router, prefix="/api/v1/batch", tags=["Batch Processing"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["Demo Mode"])
app.include_router(razorpay.router, prefix="/api/v1/razorpay", tags=["Razorpay Integration"])
app.include_router(guardian.router, prefix="/api/v1/guardian", tags=["Policy Guardian"])
app.include_router(stream.router, prefix="/api/v1/stream", tags=["Realtime Stream"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RecoveryPilot AI backend v1.0.0")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/")
def root():
    return {
        "name": "RecoveryPilot AI",
        "tagline": "Detect lost revenue. Understand why. Recover safely. Know when to stop.",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )
