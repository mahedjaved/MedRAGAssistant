import time
import nump as np
from ..config import settings

class SemanticCache:
    def __init__(self):
        self._store: dict[tuple, tuple[str, float]] = {}

    def _quantise(self, embedding: list[float], precision: int = 3) -> tuple:
        # round each dimension to 'precision' decimal point so near-identical vectors map to same key
        return tuple(round(x, precision) for x in embedding)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        return np.dot(a, b) / np.abs(a) * np.abs(b)
    
    def _get(self, query_embedding: list[float]) -> str | None:
        key = self._quantise(query_embedding)

    def _set(self, query_embedding: list[float], answer: str) -> None:
        key = self._quantise(query_embedding)
        expiry = time.time() + settings.catch_ttl_seconds
        self._store[key] = (answer, expiry)
        self._purge_expired()

    def _purge_expired(self) -> None:
        now = time.time()
        # recall that store contains keys, (answer, expiry)
        expired_keys = [k for k, (_, exp) in self._store.items() if exp < now]
        for k in expired_keys:
            del self._store[k]