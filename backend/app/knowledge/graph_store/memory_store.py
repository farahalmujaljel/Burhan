"""In-memory graph store with optional JSON persistence (the demo-safe default backend)."""

import json
import os
import tempfile
import threading
from pathlib import Path

from app.knowledge.graph_store.base import GraphStore
from app.schemas.evidence import Evidence
from app.schemas.graph import GraphEdge, GraphNode


class MemoryGraphStore(GraphStore):
    backend = "memory"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._evidence: dict[str, Evidence] = {}
        self._lock = threading.RLock()
        if path and path.exists():
            data = json.loads(path.read_text("utf-8"))
            self._nodes = {n["id"]: GraphNode.model_validate(n) for n in data["nodes"]}
            self._edges = {e["id"]: GraphEdge.model_validate(e) for e in data["edges"]}
            self._evidence = {e["id"]: Evidence.model_validate(e) for e in data["evidence"]}

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [n.model_dump(mode="json") for n in self._nodes.values()],
            "edges": [e.model_dump(mode="json") for e in self._edges.values()],
            "evidence": [e.model_dump(mode="json") for e in self._evidence.values()],
        }
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".graph.")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, self.path)

    # --- nodes ---
    def get_nodes(self, ids):
        with self._lock:
            return {i: self._nodes[i] for i in ids if i in self._nodes}

    def find_nodes(self, *, types=None, paper_id=None, limit=None):
        with self._lock:
            wanted = set(types) if types else None
            out = [
                n
                for n in self._nodes.values()
                if (wanted is None or n.type in wanted)
                and (paper_id is None or paper_id in n.paper_ids)
            ]
        out.sort(key=lambda n: (n.type, n.name))
        return out[:limit] if limit else out

    def upsert_nodes(self, nodes):
        with self._lock:
            self._nodes.update({n.id: n for n in nodes})
            self._persist()

    def delete_nodes(self, ids):
        with self._lock:
            ids = set(ids)
            for i in ids:
                self._nodes.pop(i, None)
            for edge_id in [
                e.id for e in self._edges.values() if e.source_id in ids or e.target_id in ids
            ]:
                del self._edges[edge_id]
            self._persist()

    # --- edges ---
    def find_edges(self, *, paper_id=None, node_ids=None, limit=None):
        with self._lock:
            touching = set(node_ids) if node_ids is not None else None
            out = [
                e
                for e in self._edges.values()
                if (paper_id is None or paper_id in e.paper_ids)
                and (touching is None or e.source_id in touching or e.target_id in touching)
            ]
        out.sort(key=lambda e: (e.type, e.source_id, e.target_id))
        return out[:limit] if limit else out

    def upsert_edges(self, edges):
        with self._lock:
            missing = {i for e in edges for i in (e.source_id, e.target_id)} - self._nodes.keys()
            if missing:
                raise ValueError(f"edges reference unknown nodes: {sorted(missing)[:5]}")
            self._edges.update({e.id: e for e in edges})
            self._persist()

    def delete_edges(self, ids):
        with self._lock:
            for i in ids:
                self._edges.pop(i, None)
            self._persist()

    # --- evidence ---
    def get_evidence(self, ids):
        with self._lock:
            return [self._evidence[i] for i in ids if i in self._evidence]

    def upsert_evidence(self, evidence):
        with self._lock:
            self._evidence.update({e.id: e for e in evidence})
            self._persist()

    def delete_evidence_for_paper(self, paper_id):
        with self._lock:
            for i in self.evidence_ids_for_paper(paper_id):
                del self._evidence[i]
            self._persist()

    def evidence_ids_for_paper(self, paper_id):
        with self._lock:
            return {e.id for e in self._evidence.values() if e.paper_id == paper_id}

    def counts(self):
        with self._lock:
            return {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                "evidence": len(self._evidence),
            }

    def all_evidence(self):
        with self._lock:
            return list(self._evidence.values())
