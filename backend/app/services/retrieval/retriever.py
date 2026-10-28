from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Chunk, Source
from app.schemas import EvidenceItem
from app.services.embeddings.local_embeddings import embedding_service
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import search_fts

class HybridRetriever:
    async def retrieve(
        self,
        session: AsyncSession,
        project_id: str,
        query: str,
        top_k: int = 10,
        file_type_filter: Optional[str] = None,
        source_id_filter: Optional[str] = None,
    ) -> List[EvidenceItem]:
        """
        Executes hybrid retrieval (Dense Semantic + SQLite FTS5) with Reciprocal Rank Fusion (RRF).
        """
        # 1. Dense retrieval
        query_vec = embedding_service.embed_text(query)
        dense_results = vector_store.search_similarity(project_id, query_vec, top_k=top_k * 2)

        # 2. SQLite FTS5 keyword retrieval
        fts_results = await search_fts(session, project_id, query, limit=top_k * 2)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score = sum(weight / (k + rank)) where k = 60
        k = 60.0
        rrf_scores: Dict[str, float] = {}
        retrieval_methods: Dict[str, str] = {}

        dense_weight = settings.HYBRID_RETRIEVAL_DENSE_WEIGHT
        fts_weight = settings.HYBRID_RETRIEVAL_FTS_WEIGHT

        for rank, (chunk_id, _) in enumerate(dense_results, 1):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (dense_weight / (k + rank))
            retrieval_methods[chunk_id] = "dense"

        for rank, (chunk_id, _) in enumerate(fts_results, 1):
            existing = rrf_scores.get(chunk_id, 0.0)
            rrf_scores[chunk_id] = existing + (fts_weight / (k + rank))
            if chunk_id in retrieval_methods:
                retrieval_methods[chunk_id] = "hybrid"
            else:
                retrieval_methods[chunk_id] = "fts5"

        if not rrf_scores:
            return []

        # Sort chunk IDs by fused RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        # 4. Fetch chunk & source details from DB
        stmt = (
            select(Chunk, Source)
            .join(Source, Chunk.source_id == Source.id)
            .where(Chunk.id.in_(sorted_chunk_ids))
        )
        if file_type_filter:
            stmt = stmt.where(Source.file_type == file_type_filter)
        if source_id_filter:
            stmt = stmt.where(Source.id == source_id_filter)

        exec_res = await session.execute(stmt)
        records = exec_res.fetchall()

        # Build evidence items mapped to chunk details
        records_by_id = {chunk.id: (chunk, source) for chunk, source in records}

        evidence_items: List[EvidenceItem] = []
        for cid in sorted_chunk_ids:
            if cid in records_by_id:
                chunk, source = records_by_id[cid]
                evidence_items.append(
                    EvidenceItem(
                        source_id=source.id,
                        display_path=source.file_path,
                        line_start=chunk.start_line,
                        line_end=chunk.end_line,
                        section=chunk.section_heading,
                        excerpt=chunk.content,
                        evidence_type="code_snippet" if source.file_type == "code" else "doc_reference",
                        retrieval_method=retrieval_methods.get(cid, "hybrid"),
                        score=round(rrf_scores[cid], 5),
                        content_hash=source.content_hash,
                    )
                )

        return evidence_items

hybrid_retriever = HybridRetriever()
