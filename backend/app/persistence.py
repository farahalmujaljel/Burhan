from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import psycopg
from psycopg.types.json import Jsonb
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from .schemas import GraphEdge, GraphNode, PaperRecord, TwinState
from .settings import settings


class Persistence:
    def __init__(self) -> None:
        self.storage_root = Path(settings.storage_dir)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        (self.storage_root / "runs").mkdir(parents=True, exist_ok=True)

    def save_run_artifact(self, twin: TwinState) -> None:
        path = self.storage_root / "runs" / f"{twin.run_id}.json"
        path.write_text(twin.model_dump_json(indent=2), encoding="utf-8")

    def save_metadata_postgres(self, run_id: str, papers: list[PaperRecord]) -> None:
        if not settings.database_url:
            return
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    create table if not exists papers (
                        id text primary key,
                        run_id text not null,
                        filename text not null,
                        title text not null,
                        authors jsonb not null,
                        year integer,
                        abstract text,
                        extraction jsonb not null
                    )
                    """
                )
                for paper in papers:
                    cur.execute(
                        """
                        insert into papers (id, run_id, filename, title, authors, year, abstract, extraction)
                        values (%s, %s, %s, %s, %s, %s, %s, %s)
                        on conflict (id) do update set
                            title = excluded.title,
                            authors = excluded.authors,
                            year = excluded.year,
                            abstract = excluded.abstract,
                            extraction = excluded.extraction
                        """,
                        (
                            paper.id,
                            run_id,
                            paper.filename,
                            paper.metadata.title,
                            Jsonb(paper.metadata.authors),
                            paper.metadata.year,
                            paper.metadata.abstract,
                            Jsonb(paper.extraction.model_dump()),
                        ),
                    )

    def save_embeddings_qdrant(self, run_id: str, points: Iterable[tuple[str, list[float], dict]]) -> None:
        if not settings.qdrant_url:
            return
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        collection = f"burhan_{run_id}"
        prepared = [PointStruct(id=index + 1, vector=vector, payload=payload | {"source_id": source_id}) for index, (source_id, vector, payload) in enumerate(points)]
        if not prepared:
            return
        client.recreate_collection(collection_name=collection, vectors_config=VectorParams(size=len(prepared[0].vector), distance=Distance.COSINE))
        client.upsert(collection_name=collection, points=prepared)

    def save_graph_neo4j(self, run_id: str, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        if not settings.neo4j_uri or not settings.neo4j_user or not settings.neo4j_password:
            return
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            session.run("merge (:TwinRun {id: $run_id})", run_id=run_id)
            for node in nodes:
                session.run(
                    """
                    merge (n:BurhanNode {id: $id})
                    set n.type = $type, n.label = $label, n.metadata = $metadata
                    with n
                    match (r:TwinRun {id: $run_id})
                    merge (r)-[:CONTAINS]->(n)
                    """,
                    id=node.id,
                    type=node.type,
                    label=node.label,
                    metadata=json.dumps(node.metadata),
                    run_id=run_id,
                )
            for edge in edges:
                session.run(
                    """
                    match (a:BurhanNode {id: $source}), (b:BurhanNode {id: $target})
                    merge (a)-[rel:RELATED {id: $id}]->(b)
                    set rel.type = $type
                    """,
                    source=edge.source,
                    target=edge.target,
                    id=edge.id,
                    type=edge.type,
                )
        driver.close()
