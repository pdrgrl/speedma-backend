import chromadb
from chromadb import Collection
from app.config import settings

_client: chromadb.PersistentClient | None = None
_collection: Collection | None = None

COLLECTION_NAME = "chamusca_corpus"

def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    return _client

def get_collection() -> Collection:
    global _collection
    if _collection is None:
        _collection = _get_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection