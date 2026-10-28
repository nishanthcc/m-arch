import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("m-arch")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing M-ARCH Database and Storage...")
    await init_db()
    logger.info("M-ARCH Backend Ready.")
    yield
    logger.info("M-ARCH Backend Shutting Down.")

app = FastAPI(
    title="M-ARCH API",
    description="Multi-Agent Retrieval-Augmented Generation Framework Using A2A and MCP",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration restricted to local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "app": "M-ARCH",
        "description": "Multi-Agent Retrieval-Augmented Generation Framework Using A2A and MCP",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }
