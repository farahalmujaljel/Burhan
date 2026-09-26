from app.core.config import Settings
from app.embeddings.base import Embedder, HashingEmbedder
from app.embeddings.local import FastEmbedEmbedder, Model2VecEmbedder


def create_embedder(settings: Settings) -> Embedder:
    match settings.embedding_backend:
        case "model2vec":
            return Model2VecEmbedder(settings.embedding_model)
        case "fastembed":
            return FastEmbedEmbedder(settings.embedding_model)
        case _:
            return HashingEmbedder(settings.embedding_dim)
