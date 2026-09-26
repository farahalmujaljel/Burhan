"""Local embedding models.

- model2vec (default): static embeddings, numpy only, no torch/onnxruntime, works on Intel
  Macs. Default model: minishlab/potion-retrieval-32M (tuned for retrieval).
- fastembed: ONNX models such as BAAI/bge-small-en-v1.5. Requires `pip install fastembed`,
  which needs onnxruntime (not available for Intel macOS / Python 3.12).

Models are loaded lazily on first use; the first load downloads weights from Hugging Face
into the local cache, after which everything runs offline.
"""

import logging
import threading
from pathlib import Path

from app.core.errors import ProviderError
from app.embeddings.base import Embedder

logger = logging.getLogger(__name__)

MODEL2VEC_FILES = ["*.json", "*.safetensors", "*.txt"]  # weights, tokenizer, config, vocab


class Model2VecEmbedder(Embedder):
    name = "model2vec"

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                try:
                    from model2vec import StaticModel

                    logger.info("Loading embedding model %s", self.model_name)
                    # force_download defaults to True in model2vec; reuse the local cache.
                    self._model = StaticModel.from_pretrained(
                        self._local_path(), force_download=False
                    )
                except Exception as exc:
                    raise ProviderError(
                        f"Could not load embedding model '{self.model_name}': {exc}"
                    ) from exc
        return self._model

    def _local_path(self) -> str:
        """Download only the files model2vec needs (repos may also ship a large ONNX copy)."""
        if Path(self.model_name).is_dir():
            return self.model_name
        from huggingface_hub import snapshot_download

        return snapshot_download(self.model_name, allow_patterns=MODEL2VEC_FILES)

    @property
    def dim(self) -> int:
        return int(self._load().dim)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._load().encode(texts).astype(float).tolist()


class FastEmbedEmbedder(Embedder):
    name = "fastembed"

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._dim: int | None = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                try:
                    from fastembed import TextEmbedding
                except ImportError as exc:
                    raise ProviderError(
                        "EMBEDDING_BACKEND=fastembed requires `pip install fastembed`"
                    ) from exc
                self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed_query("dimension probe"))
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._load().passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._load().query_embed([text]))).tolist()
