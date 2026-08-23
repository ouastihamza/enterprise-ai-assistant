import os
from functools import lru_cache
from pathlib import Path

# bge-m3 is a large first-run download. Use the regular resumable Hub transport
# and give unreliable local networks enough time to fetch it.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")

from sentence_transformers import SentenceTransformer


# Multilingual by default: deployments may serve users in the Gulf region
# (Arabic), France (French), and North America (English). The old
# default, all-MiniLM-L6-v2, is trained mostly on English and will
# rank Arabic/French documents poorly against Arabic/French questions.
#
# BAAI/bge-m3 covers 100+ languages, including Arabic and French, and
# is a current standard for production multilingual retrieval.
# Trade-off: ~2.2GB download, noticeably slower to encode on CPU than
# MiniLM. If you need to stay lightweight/CPU-only, swap this for
# "intfloat/multilingual-e5-small" instead.
DEFAULT_MODEL_NAME = "BAAI/bge-m3"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# `storage/` is bind-mounted by Docker Compose, so this cache survives API
# container rebuilds/restarts and is shared with host-run pytest.
MODEL_CACHE_DIR = os.getenv(
    "HF_HOME",
    str(_PROJECT_ROOT / "storage" / "huggingface"),
)


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str):
    return SentenceTransformer(
        model_name,
        cache_folder=MODEL_CACHE_DIR,
    )


class EmbeddingService:
    """
    Shared embedding service for the AI Solutions Platform.

    The embedding model is cached globally so it is not reloaded
    every time a service instance is created.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
    ):
        self.model_name = model_name
        self.model = get_embedding_model(model_name)

    def create_embedding(
        self,
        text: str,
    ) -> list[float]:
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def create_embeddings(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()
