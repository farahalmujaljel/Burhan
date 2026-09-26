"""Graph-store interface.

Stores are deliberately simple repositories (read, replace-by-id, delete). All merge,
resolution, and diff logic lives in the Twin Builder, so every backend behaves identically.
"""

from abc import ABC, abstractmethod

from app.schemas.entities import EntityType
from app.schemas.evidence import Evidence
from app.schemas.graph import GraphEdge, GraphNode


class GraphStore(ABC):
    backend: str

    # --- nodes ---
    @abstractmethod
    def get_nodes(self, ids: list[str]) -> dict[str, GraphNode]: ...

    @abstractmethod
    def find_nodes(
        self,
        *,
        types: list[EntityType] | None = None,
        paper_id: str | None = None,
        limit: int | None = None,
    ) -> list[GraphNode]: ...

    @abstractmethod
    def upsert_nodes(self, nodes: list[GraphNode]) -> None: ...

    @abstractmethod
    def delete_nodes(self, ids: list[str]) -> None:
        """Delete nodes and any edges attached to them."""

    # --- edges ---
    @abstractmethod
    def find_edges(
        self,
        *,
        paper_id: str | None = None,
        node_ids: list[str] | None = None,
        limit: int | None = None,
    ) -> list[GraphEdge]:
        """Edges supported by `paper_id` and/or touching any of `node_ids`."""

    @abstractmethod
    def upsert_edges(self, edges: list[GraphEdge]) -> None: ...

    @abstractmethod
    def delete_edges(self, ids: list[str]) -> None: ...

    # --- evidence ---
    @abstractmethod
    def get_evidence(self, ids: list[str]) -> list[Evidence]: ...

    @abstractmethod
    def upsert_evidence(self, evidence: list[Evidence]) -> None: ...

    @abstractmethod
    def delete_evidence_for_paper(self, paper_id: str) -> None: ...

    @abstractmethod
    def evidence_ids_for_paper(self, paper_id: str) -> set[str]: ...

    # --- whole graph ---
    @abstractmethod
    def counts(self) -> dict[str, int]:
        """{'nodes': n, 'edges': m, 'evidence': k}"""

    def all_evidence(self) -> list[Evidence]:
        return self.get_evidence(sorted({i for n in self.find_nodes() for i in n.evidence_ids}))

    def close(self) -> None:  # noqa: B027 - optional hook
        pass
