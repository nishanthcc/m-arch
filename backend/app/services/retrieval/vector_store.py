import json
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from app.core.config import settings

class LocalVectorStore:
    def __init__(self):
        self.base_dir = settings.VECTOR_STORAGE_PATH

    def _get_project_dir(self, project_id: str) -> Path:
        proj_dir = self.base_dir / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_dir

    def save_vectors(self, project_id: str, chunk_ids: List[str], vectors: np.ndarray):
        proj_dir = self._get_project_dir(project_id)
        vec_file = proj_dir / "vectors.npy"
        meta_file = proj_dir / "chunk_ids.json"

        # If existing vectors exist, merge or overwrite
        np.save(vec_file, vectors)
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(chunk_ids, f)

    def search_similarity(
        self, project_id: str, query_vector: np.ndarray, top_k: int = 15
    ) -> List[Tuple[str, float]]:
        """
        Cosine similarity search across stored project vectors.
        Returns: [(chunk_id, similarity_score)]
        """
        proj_dir = self.base_dir / project_id
        vec_file = proj_dir / "vectors.npy"
        meta_file = proj_dir / "chunk_ids.json"

        if not vec_file.exists() or not meta_file.exists():
            return []

        vectors = np.load(vec_file)
        with open(meta_file, "r", encoding="utf-8") as f:
            chunk_ids = json.load(f)

        if len(chunk_ids) == 0 or len(vectors) == 0:
            return []

        # Cosine similarity (vectors are already L2 normalized)
        scores = np.dot(vectors, query_vector)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append((chunk_ids[idx], round(score, 4)))

        return results

    def delete_project_vectors(self, project_id: str):
        proj_dir = self.base_dir / project_id
        if proj_dir.exists():
            shutil.rmtree(proj_dir, ignore_errors=True)

vector_store = LocalVectorStore()
