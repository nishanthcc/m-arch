from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.schemas import SettingsUpdate, ProvidersHealthResponse
from app.providers import model_router

router = APIRouter()

@router.get("")
async def get_settings():
    return {
        "ai_mode": settings.AI_MODE,
        "primary_provider": settings.AI_PRIMARY_PROVIDER,
        "fallback_provider": settings.AI_FALLBACK_PROVIDER,
        "groq_configured": settings.is_groq_configured(),
        "groq_model": settings.GROQ_MODEL,
        "gemini_configured": settings.is_gemini_configured(),
        "gemini_model": settings.GEMINI_MODEL,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "upload_max_mb": settings.UPLOAD_MAX_MB,
        "rerank_enabled": settings.RERANK_ENABLED,
        "hybrid_policy": {
            "orchestrator": settings.HYBRID_ORCHESTRATOR_PROVIDER,
            "code_agent": settings.HYBRID_CODE_PROVIDER,
            "security_agent": settings.HYBRID_SECURITY_PROVIDER,
            "documentation_agent": settings.HYBRID_DOCS_PROVIDER
        }
    }

@router.patch("")
async def update_settings(payload: SettingsUpdate):
    if payload.ai_mode is not None:
        settings.AI_MODE = payload.ai_mode
    if payload.primary_provider is not None:
        settings.AI_PRIMARY_PROVIDER = payload.primary_provider
    if payload.fallback_provider is not None:
        settings.AI_FALLBACK_PROVIDER = payload.fallback_provider
    if payload.groq_model is not None:
        settings.GROQ_MODEL = payload.groq_model
    if payload.ollama_model is not None:
        settings.OLLAMA_MODEL = payload.ollama_model
    if payload.rerank_enabled is not None:
        settings.RERANK_ENABLED = payload.rerank_enabled

    return {"message": "Settings updated successfully"}

@router.get("/providers", response_model=ProvidersHealthResponse)
async def check_providers_health():
    """Performs live health checks on Groq and Ollama without revealing secrets."""
    health = await model_router.get_health_status()
    return health
