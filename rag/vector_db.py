"""ChromaDB persistent vector store. Uses cosine space so distance -> similarity
is simply (1 - distance).
"""
from typing import Dict, List

from core import config
from core.logging import get_logger
from rag import embedding

log = get_logger("vector_db")


class VectorDB:
    def __init__(self, collection_name: str = None):
        import chromadb
        self.client = chromadb.PersistentClient(path=str(config.VECTOR_STORE_DIR))
        self.collection = self.client.get_or_create_collection(
            name=collection_name or config.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        """Drop and recreate the collection (clears all chunks)."""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[dict]) -> int:
        """chunks: [{"id", "source", "text"}]. Embeds locally and upserts."""
        if not chunks:
            return 0
        ids = [c["id"] for c in chunks]
        docs = [c["text"] for c in chunks]
        metadatas = [{"source": c.get("source", "")} for c in chunks]
        vectors = embedding.embed_texts(docs)
        self.collection.upsert(
            ids=ids, documents=docs, metadatas=metadatas, embeddings=vectors
        )
        log.info("Upserted %d chunks into ChromaDB", len(ids))
        return len(ids)

    def query(self, text: str, top_k: int = None) -> List[Dict]:
        """Return [{"text", "source", "distance", "similarity"}] ordered closest-first."""
        top_k = top_k or config.RETRIEVER_TOP_K
        if self.count() == 0:
            return []
        qvec = embedding.embed_query(text)
        res = self.collection.query(
            query_embeddings=[qvec],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({
                "text": doc,
                "source": (meta or {}).get("source", ""),
                "distance": dist,
                "similarity": 1.0 - dist,  # cosine space
            })
        return out

    def count(self) -> int:
        return self.collection.count()
