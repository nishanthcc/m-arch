from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas import SecurityKnowledgeSourceCreate, SecurityKnowledgeSourceResponse
from app.services.knowledge.manager import knowledge_manager

router = APIRouter()

class ToggleRequest(BaseModel):
    is_enabled: bool

@router.get("/collections", response_model=List[SecurityKnowledgeSourceResponse])
async def list_knowledge_collections(
    db: AsyncSession = Depends(get_db)
):
    """List all bundled baseline and user-imported security knowledge collections."""
    return await knowledge_manager.list_collections(db)

@router.get("/collections/{collection_id}", response_model=SecurityKnowledgeSourceResponse)
async def get_knowledge_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed metadata and records for a specific knowledge collection."""
    coll = await knowledge_manager.get_collection(db, collection_id)
    if not coll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security knowledge collection '{collection_id}' not found."
        )
    return coll

@router.post("/collections", response_model=SecurityKnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_collection(
    payload: SecurityKnowledgeSourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Import a custom security standard or compliance collection."""
    existing = await knowledge_manager.get_collection(db, payload.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Collection '{payload.id}' already exists."
        )
    return await knowledge_manager.create_collection(db, payload.model_dump())

@router.patch("/collections/{collection_id}", response_model=SecurityKnowledgeSourceResponse)
async def toggle_knowledge_collection(
    collection_id: str,
    payload: ToggleRequest,
    db: AsyncSession = Depends(get_db)
):
    """Enable or disable a knowledge collection from being used during reviews."""
    updated = await knowledge_manager.toggle_collection(db, collection_id, payload.is_enabled)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found."
        )
    return updated
