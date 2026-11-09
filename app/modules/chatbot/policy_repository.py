import chromadb
from typing import List, Dict, Any
from app.core.config import settings

# Khởi tạo client dùng chung ở cấp module
_chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
_policy_collection = _chroma_client.get_or_create_collection(name="hr_policies")

def search_policy_chunks(query_vector: List[float], top_k: int = 3) -> Dict[str, Any]:
    """Tìm kiếm vector tương đồng trong ChromaDB."""
    count = _policy_collection.count()
    if count == 0:
        return {"documents": [], "metadatas": []}

    actual_k = min(top_k, count)
    results = _policy_collection.query(
        query_embeddings=[query_vector],
        n_results=actual_k
    )
    return {
        "documents": results["documents"][0] if results.get("documents") and results["documents"] else [],
        "metadatas": results["metadatas"][0] if results.get("metadatas") and results["metadatas"] else []
    }
