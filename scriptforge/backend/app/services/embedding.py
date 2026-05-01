"""Embedding service with pluggable providers.

Supported providers:
- jieba:  Legacy jieba+SHA256 hash-based pseudo-embedding (384-dim, no semantics)
- bge:    BAAI/bge-small-zh-v1.5 via sentence-transformers (512-dim, Chinese-optimized)

Configure via EMBEDDING_PROVIDER in settings/env.
"""
import hashlib
import logging
from abc import ABC, abstractmethod

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

BGE_DIM = 512
JIABA_DIM = 384


# ── Abstract provider ────────────────────────────────────────────

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    @property
    @abstractmethod
    def dim(self) -> int:
        ...


# ── Jieba + SHA256 hash provider (legacy) ────────────────────────

class JiebaHashProvider(BaseEmbeddingProvider):
    def __init__(self, dim: int = JIABA_DIM):
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        vector = np.zeros(self._dim, dtype=np.float32)
        for token in tokens:
            stripped = token.strip()
            if not stripped:
                continue
            h = int(hashlib.sha256(stripped.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1 if (h >> 16) % 2 == 0 else -1
            vector[idx] += sign / max(len(stripped), 1)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


def _tokenize(text: str) -> list[str]:
    import jieba
    words = list(jieba.cut(text))
    bigrams = [text[i : i + 2] for i in range(len(text) - 1)]
    return words + bigrams


# ── BGE sentence-transformer provider ────────────────────────────

class BgeProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self._model_name = model_name
        self._model = None

    @property
    def dim(self) -> int:
        return BGE_DIM

    def _load(self):
        if self._model is not None:
            return
        logger.info("Loading embedding model %s ...", self._model_name)
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded (dim=%d)", self._model.get_sentence_embedding_dimension())
        except Exception:
            logger.exception("Failed to load sentence-transformers model")
            raise

    def embed(self, text: str) -> list[float]:
        self._load()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load()
        vecs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vecs.tolist()


# ── Provider registry ────────────────────────────────────────────

_providers = {
    "jieba": JiebaHashProvider,
    "local_jieba": JiebaHashProvider,
    "bge": BgeProvider,
}

_provider_instance: BaseEmbeddingProvider | None = None


def _get_provider() -> BaseEmbeddingProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance
    key = settings.EMBEDDING_PROVIDER
    cls = _providers.get(key)

    # Try configured provider first; fall back to jieba on failure
    if cls is not None:
        try:
            instance = cls()
            # Force eager init to detect import errors early
            test_vec = instance.embed("test")
            if not test_vec or len(test_vec) < 2:
                raise RuntimeError("Provider returned invalid embedding")
            _provider_instance = instance
            logger.info("Embedding provider: %s (dim=%d)", type(instance).__name__, instance.dim)
            return _provider_instance
        except Exception as e:
            logger.warning("Provider '%s' failed to initialize: %s. Falling back to jieba.", key, e)

    if cls is None:
        logger.warning("Unknown EMBEDDING_PROVIDER '%s', falling back to jieba", key)

    _provider_instance = JiebaHashProvider()
    logger.info("Embedding provider: JiebaHashProvider (dim=%d)", _provider_instance.dim)
    return _provider_instance


# ── Module-level API (used by all consumers) ─────────────────────

def embed(text: str) -> list[float]:
    return _get_provider().embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    return _get_provider().embed_batch(texts)


def get_embedding_dim() -> int:
    return _get_provider().dim
