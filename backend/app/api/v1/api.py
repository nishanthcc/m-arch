from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, projects, sources, index, reviews, agents, settings, evaluations, knowledge
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(sources.router, tags=["Sources"])
api_router.include_router(index.router, tags=["Indexing"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Security Knowledge"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])

