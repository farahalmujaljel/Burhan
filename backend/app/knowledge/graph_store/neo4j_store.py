"""Neo4j implementation of the graph store.

Graph layout:
  (:Entity:<Type> {id, type, name, aliases, description, paper_ids, evidence_ids, ...props})
  (:Entity)-[:<RELATION_TYPE> {id, paper_ids, evidence_ids, confidence, ...props}]->(:Entity)
  (:Evidence {id, paper_id, quote, section, chunk_id, page, char_start, char_end, confidence,
              verification_status, verification_note, extracted_by, model})

Labels and relationship types cannot be Cypher parameters; they are interpolated only from
the EntityType / RelationType enums, never from user input.
"""

import json
import logging

from app.core.errors import ProviderError
from app.knowledge.graph_store.base import GraphStore
from app.schemas.entities import EntityType
from app.schemas.evidence import Evidence, SourceSpan
from app.schemas.graph import GraphEdge, GraphNode
from app.schemas.relations import RelationType

logger = logging.getLogger(__name__)

_NODE_FIELDS = {"id", "type", "name", "aliases", "description", "paper_ids", "evidence_ids"}
_EDGE_FIELDS = {"id", "paper_ids", "evidence_ids", "confidence"}
_PROPS_KEY = "props_json"  # arbitrary properties kept as JSON to preserve types exactly


def _label(entity_type: EntityType | str) -> str:
    return EntityType(entity_type).value  # raises for anything outside the enum


def _rel_type(rel_type: RelationType | str) -> str:
    return RelationType(rel_type).value


class Neo4jGraphStore(GraphStore):
    backend = "neo4j"

    def __init__(self, uri: str, user: str, password: str, database: str | None = None) -> None:
        import neo4j

        self._driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self._database = database
        self._ready = False

    def _run(self, query: str, **params) -> list[dict]:
        import neo4j

        try:
            if not self._ready:
                self._ensure_schema()
            records, _, _ = self._driver.execute_query(
                query, parameters_=params, database_=self._database
            )
            return [r.data() for r in records]
        except neo4j.exceptions.Neo4jError as exc:
            raise ProviderError(f"Neo4j query failed: {exc}") from exc
        except (neo4j.exceptions.ServiceUnavailable, OSError) as exc:
            raise ProviderError(f"Neo4j is unreachable: {exc}") from exc

    def _ensure_schema(self) -> None:
        self._ready = True
        for q in (
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX evidence_paper IF NOT EXISTS FOR (e:Evidence) ON (e.paper_id)",
        ):
            self._run(q)

    # --- conversion ---
    @staticmethod
    def _node_row(n: GraphNode) -> dict:
        row = n.model_dump(mode="json", exclude={"properties"})
        row[_PROPS_KEY] = json.dumps(n.properties)
        return row

    @staticmethod
    def _to_node(data: dict) -> GraphNode:
        props = json.loads(data.get(_PROPS_KEY) or "{}")
        return GraphNode(**{k: data[k] for k in _NODE_FIELDS if k in data}, properties=props)

    @staticmethod
    def _to_edge(rel: dict, rtype: str, src: dict, tgt: dict) -> GraphEdge:
        return GraphEdge(
            **{k: rel[k] for k in _EDGE_FIELDS if k in rel},
            type=rtype,
            source_id=src["id"],
            source_type=src["type"],
            target_id=tgt["id"],
            target_type=tgt["type"],
            properties=json.loads(rel.get(_PROPS_KEY) or "{}"),
        )

    # --- nodes ---
    def get_nodes(self, ids):
        rows = self._run("MATCH (n:Entity) WHERE n.id IN $ids RETURN properties(n) AS n", ids=ids)
        return {r["n"]["id"]: self._to_node(r["n"]) for r in rows}

    def find_nodes(self, *, types=None, paper_id=None, limit=None):
        rows = self._run(
            "MATCH (n:Entity) "
            "WHERE ($types IS NULL OR n.type IN $types) "
            "AND ($paper_id IS NULL OR $paper_id IN n.paper_ids) "
            "RETURN properties(n) AS n ORDER BY n.type, n.name "
            + ("LIMIT $limit" if limit else ""),
            types=[_label(t) for t in types] if types else None,
            paper_id=paper_id,
            limit=limit,
        )
        return [self._to_node(r["n"]) for r in rows]

    def upsert_nodes(self, nodes):
        by_type: dict[str, list[dict]] = {}
        for n in nodes:
            by_type.setdefault(_label(n.type), []).append(self._node_row(n))
        for label, rows in by_type.items():
            # SET n = row replaces all properties, so removed aliases/ids do not linger.
            self._run(
                f"UNWIND $rows AS row MERGE (n:Entity {{id: row.id}}) SET n = row, n:`{label}`",
                rows=rows,
            )

    def delete_nodes(self, ids):
        self._run("MATCH (n:Entity) WHERE n.id IN $ids DETACH DELETE n", ids=list(ids))

    # --- edges ---
    def find_edges(self, *, paper_id=None, node_ids=None, limit=None):
        rows = self._run(
            "MATCH (a:Entity)-[r]->(b:Entity) "
            "WHERE ($paper_id IS NULL OR $paper_id IN r.paper_ids) "
            "AND ($node_ids IS NULL OR a.id IN $node_ids OR b.id IN $node_ids) "
            "RETURN properties(r) AS r, type(r) AS t, properties(a) AS a, properties(b) AS b "
            "ORDER BY t, a.id, b.id " + ("LIMIT $limit" if limit else ""),
            paper_id=paper_id,
            node_ids=list(node_ids) if node_ids is not None else None,
            limit=limit,
        )
        return [self._to_edge(r["r"], r["t"], r["a"], r["b"]) for r in rows]

    def upsert_edges(self, edges):
        by_type: dict[str, list[dict]] = {}
        for e in edges:
            row = e.model_dump(mode="json", include=_EDGE_FIELDS)
            row[_PROPS_KEY] = json.dumps(e.properties)
            by_type.setdefault(_rel_type(e.type), []).append(
                {"source": e.source_id, "target": e.target_id, "props": row}
            )
        for rtype, rows in by_type.items():
            result = self._run(
                "UNWIND $rows AS row "
                "MATCH (a:Entity {id: row.source}), (b:Entity {id: row.target}) "
                f"MERGE (a)-[r:`{rtype}` {{id: row.props.id}}]->(b) SET r = row.props "
                "RETURN count(r) AS n",
                rows=rows,
            )
            if result and result[0]["n"] != len(rows):
                raise ProviderError(f"Some {rtype} edges reference unknown nodes")

    def delete_edges(self, ids):
        self._run("MATCH ()-[r]->() WHERE r.id IN $ids DELETE r", ids=list(ids))

    # --- evidence ---
    @staticmethod
    def _evidence_row(e: Evidence) -> dict:
        span = e.span or SourceSpan()
        row = e.model_dump(mode="json", exclude={"span"})
        row.update(page=span.page, char_start=span.char_start, char_end=span.char_end)
        return row

    @staticmethod
    def _to_evidence(d: dict) -> Evidence:
        # Neo4j drops null properties, so every optional field may be absent.
        span = SourceSpan(
            page=d.pop("page", None),
            char_start=d.pop("char_start", None),
            char_end=d.pop("char_end", None),
        )
        return Evidence(**{k: v for k, v in d.items() if v is not None}, span=span)

    def get_evidence(self, ids):
        rows = self._run("MATCH (e:Evidence) WHERE e.id IN $ids RETURN properties(e) AS e", ids=ids)
        found = {r["e"]["id"]: self._to_evidence(dict(r["e"])) for r in rows}
        return [found[i] for i in ids if i in found]

    def upsert_evidence(self, evidence):
        self._run(
            "UNWIND $rows AS row MERGE (e:Evidence {id: row.id}) SET e = row",
            rows=[self._evidence_row(e) for e in evidence],
        )

    def delete_evidence_for_paper(self, paper_id):
        self._run("MATCH (e:Evidence {paper_id: $pid}) DELETE e", pid=paper_id)

    def evidence_ids_for_paper(self, paper_id):
        rows = self._run("MATCH (e:Evidence {paper_id: $pid}) RETURN e.id AS id", pid=paper_id)
        return {r["id"] for r in rows}

    def counts(self):
        row = self._run(
            "CALL { MATCH (n:Entity) RETURN count(n) AS nodes } "
            "CALL { MATCH (:Entity)-[r]->(:Entity) RETURN count(r) AS edges } "
            "CALL { MATCH (e:Evidence) RETURN count(e) AS evidence } "
            "RETURN nodes, edges, evidence"
        )[0]
        return {"nodes": row["nodes"], "edges": row["edges"], "evidence": row["evidence"]}

    def all_evidence(self):
        rows = self._run("MATCH (e:Evidence) RETURN properties(e) AS e")
        return [self._to_evidence(dict(r["e"])) for r in rows]

    def close(self):
        self._driver.close()
