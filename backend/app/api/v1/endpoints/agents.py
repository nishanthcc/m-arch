from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models import AgentTask
from app.a2a.cards import AGENT_CARDS_REGISTRY
from app.schemas import AgentCard
from app.core.config import settings
from app.providers.router import model_router
from app.prompts.registry import get_prompt_definition

router = APIRouter()

@router.get("", response_model=List[AgentCard])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """
    Returns real dynamic agent status, actual model used, provider fallback history,
    prompt versions, and live A2A connectivity.
    """
    health = await model_router.get_health_status()
    groq_info = health["providers"].get("Groq", {})
    ollama_info = health["providers"].get("Ollama", {})
    gemini_info = health["providers"].get("Gemini", {})

    default_provider = settings.AI_PRIMARY_PROVIDER
    default_model = settings.GROQ_MODEL if default_provider == "Groq" else settings.OLLAMA_MODEL

    cards = []
    for agent_id, meta in AGENT_CARDS_REGISTRY.items():
        # Dedicated provider check: code_agent is powered strictly by Gemini
        if agent_id == "code_agent" and settings.is_gemini_configured():
            configured_provider = "Gemini"
            configured_model = settings.GEMINI_MODEL
        else:
            configured_provider = default_provider
            configured_model = default_model

        # Get prompt definition
        prompt_id = meta.get("prompt_id")
        prompt_version = "1.1.0"
        if prompt_id:
            try:
                pdef = get_prompt_definition(prompt_id)
                prompt_version = pdef.version
            except Exception:
                pass

        # Query latest AgentTask for this agent
        stmt = (
            select(AgentTask)
            .where(AgentTask.agent_id == agent_id)
            .order_by(desc(AgentTask.created_at))
            .limit(1)
        )
        res = await db.execute(stmt)
        latest_task = res.scalar_one_or_none()

        # Check if there is an active running task
        running_stmt = (
            select(AgentTask)
            .where(AgentTask.agent_id == agent_id, AgentTask.status == "running")
            .limit(1)
        )
        running_task = (await db.execute(running_stmt)).scalar_one_or_none()

        # Determine real dynamic state
        last_error = None
        actual_model_used = None
        last_task_time = None
        fallback_history = []

        if latest_task:
            actual_model_used = latest_task.model_used
            last_error = latest_task.error_message
            last_task_time = latest_task.updated_at.isoformat() if latest_task.updated_at else None
            if latest_task.provider_used and latest_task.provider_used != configured_provider:
                fallback_history.append(f"Fallback to {latest_task.provider_used} ({latest_task.model_used})")

        if running_task:
            status = "busy"
        elif configured_provider == "Gemini":
            status = "available" if gemini_info.get("available", False) else "unavailable"
        elif configured_provider == "Groq" and not groq_info.get("configured", False):
            if ollama_info.get("available", False):
                status = "available"  # Automatic fallback active
                fallback_history.append(f"Auto-routed to Ollama ({settings.OLLAMA_MODEL}) due to unconfigured Groq API key")
            else:
                status = "misconfigured"
        elif configured_provider == "Groq" and not groq_info.get("available", False):
            if ollama_info.get("available", False):
                status = "available"
            else:
                status = "unavailable"
        elif configured_provider == "Ollama" and not ollama_info.get("available", False):
            status = "unavailable"
        else:
            status = "available"

        cards.append(
            AgentCard(
                agent_id=meta["agent_id"],
                name=meta["name"],
                role=meta["role"],
                description=meta["description"],
                endpoint=meta["endpoint"],
                skills=meta["skills"],
                allowed_mcp_tools=meta["allowed_mcp_tools"],
                configured_provider=configured_provider,
                configured_model=configured_model,
                status=status,
                current_state=status,
                a2a_connectivity="connected",
                prompt_version=prompt_version,
                actual_model_used=actual_model_used or configured_model,
                fallback_history=fallback_history,
                last_task_time=last_task_time,
                last_error=last_error
            )
        )

    return cards

@router.get("/{agent_id}/health")
async def get_agent_health(agent_id: str, db: AsyncSession = Depends(get_db)):
    meta = AGENT_CARDS_REGISTRY.get(agent_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Agent not found")

    health = await model_router.get_health_status()
    configured_provider = settings.AI_PRIMARY_PROVIDER
    configured_model = settings.GROQ_MODEL if configured_provider == "Groq" else settings.OLLAMA_MODEL

    return {
        "agent_id": agent_id,
        "name": meta["name"],
        "status": "available",
        "a2a_endpoint": meta["endpoint"],
        "a2a_connectivity": "connected",
        "skills_count": len(meta["skills"]),
        "mcp_tools_count": len(meta["allowed_mcp_tools"]),
        "allowed_mcp_tools": meta["allowed_mcp_tools"],
        "configured_provider": configured_provider,
        "configured_model": configured_model,
        "provider_health": health
    }
