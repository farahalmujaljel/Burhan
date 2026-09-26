"""Research Twin Builder: merges one paper's PaperKnowledge into the Scientific Knowledge Graph.

Idempotency: applying a paper first *detaches* that paper's previous contribution (in memory),
then merges the new one, diffs against the stored graph, and writes only what changed. Node and
edge IDs are deterministic, so applying the same knowledge twice produces an empty update.

Nodes/edges owned only by the paper are rebuilt from scratch; shared canonical nodes (methods,
datasets, metrics used by several papers) keep other papers' support and gain this paper's.
"""

import hashlib
from dataclasses import dataclass, field

from app.knowledge.entity_resolution import EntityResolver
from app.knowledge.graph_store.base import GraphStore
from app.schemas.entities import EntityType
from app.schemas.evidence import Evidence
from app.schemas.extraction import PaperKnowledge
from app.schemas.graph import RESOLVABLE_TYPES, GraphEdge, GraphNode
from app.schemas.relations import RelationType
from app.schemas.twin import TwinUpdate
from app.services.extraction import normalize_key

_CLAIM_PREFIX = {
    EntityType.FINDING: "finding",
    EntityType.LIMITATION: "limitation",
    EntityType.FUTURE_WORK: "future",
}
_ROLE_PRIORITY = {"proposed": 3, "baseline": 2, "other": 1}
# REPORTS edges are distinguished by what was measured, not just paper -> metric.
_EDGE_KEY_PROPS = {RelationType.REPORTS: ("value", "method_id", "dataset_id")}


def _hash(*parts: object) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _union(*lists: list[str]) -> list[str]:
    return sorted({x for lst in lists for x in lst})


@dataclass(frozen=True)
class EvidenceLink:
    """What a piece of evidence supports (used to label vector-index records)."""

    subject_id: str
    subject_type: str
    claim: str


@dataclass
class BuildResult:
    update: TwinUpdate
    evidence: list[Evidence] = field(default_factory=list)
    links: dict[str, EvidenceLink] = field(default_factory=dict)


def merge_nodes(base: GraphNode | None, new: GraphNode) -> GraphNode:
    if base is None:
        return new
    aliases = list(base.aliases)
    for name in [new.name, *new.aliases]:
        if name != base.name and name not in aliases:
            aliases.append(name)
    props = {**new.properties, **{k: v for k, v in base.properties.items() if v is not None}}
    return base.model_copy(
        update={
            "aliases": aliases,
            "description": base.description or new.description,
            "paper_ids": _union(base.paper_ids, new.paper_ids),
            "evidence_ids": _union(base.evidence_ids, new.evidence_ids),
            "properties": props,
        }
    )


def merge_edges(base: GraphEdge | None, new: GraphEdge) -> GraphEdge:
    if base is None:
        return new
    props = {**base.properties, **{k: v for k, v in new.properties.items() if v is not None}}
    roles = [r for r in (base.properties.get("role"), new.properties.get("role")) if r]
    if roles:
        props["role"] = max(roles, key=lambda r: _ROLE_PRIORITY.get(r, 0))
    return base.model_copy(
        update={
            "paper_ids": _union(base.paper_ids, new.paper_ids),
            "evidence_ids": _union(base.evidence_ids, new.evidence_ids),
            "confidence": max(base.confidence, new.confidence),
            "properties": props,
        }
    )


def _detach_node(node: GraphNode, paper_id: str, paper_evidence: set[str]) -> GraphNode | None:
    """Remove a paper's support from a node; None if nothing else supports it."""
    remaining = [p for p in node.paper_ids if p != paper_id]
    if not remaining:
        return None
    return node.model_copy(
        update={
            "paper_ids": remaining,
            "evidence_ids": [e for e in node.evidence_ids if e not in paper_evidence],
        }
    )


def _detach_edge(edge: GraphEdge, paper_id: str, paper_evidence: set[str]) -> GraphEdge | None:
    remaining = [p for p in edge.paper_ids if p != paper_id]
    if not remaining:
        return None
    return edge.model_copy(
        update={
            "paper_ids": remaining,
            "evidence_ids": [e for e in edge.evidence_ids if e not in paper_evidence],
        }
    )


class TwinBuilder:
    def __init__(self, graph: GraphStore) -> None:
        self.graph = graph

    def apply(self, knowledge: PaperKnowledge) -> BuildResult:
        return self._sync(knowledge.paper.id, knowledge)

    def remove(self, paper_id: str) -> BuildResult:
        return self._sync(paper_id, None)

    def _sync(self, pid: str, knowledge: PaperKnowledge | None) -> BuildResult:
        g = self.graph
        # 1. What the graph holds for this paper right now.
        before_nodes = {n.id: n for n in g.find_nodes(paper_id=pid)}
        before_edges = {e.id: e for e in g.find_edges(paper_id=pid)}
        old_evidence = g.evidence_ids_for_paper(pid)

        # 2. Working set with this paper's previous contribution detached.
        nodes: dict[str, GraphNode] = {}
        for n in before_nodes.values():
            if detached := _detach_node(n, pid, old_evidence):
                nodes[n.id] = detached
        edges: dict[str, GraphEdge] = {}
        for e in before_edges.values():
            if detached := _detach_edge(e, pid, old_evidence):
                edges[e.id] = detached

        result = BuildResult(update=TwinUpdate(operation="remove", paper_ids=[pid]))
        if knowledge is not None:
            result = self._merge_paper(knowledge, nodes, edges, before_nodes, before_edges)

        # 3. Diff and write.
        self._write(pid, result, before_nodes, before_edges, nodes, edges, old_evidence)
        return result

    # ------------------------------------------------------------------------

    def _merge_paper(self, k, nodes, edges, before_nodes, before_edges) -> BuildResult:
        pid = k.paper.id
        update = TwinUpdate(operation="apply", paper_ids=[pid])
        result = BuildResult(update=update)
        g = self.graph

        existing = g.find_nodes(types=list(RESOLVABLE_TYPES))
        resolver = EntityResolver(existing)
        known = {n.id: n for n in existing}
        local_to_canonical: dict[str, str] = {}

        def put_node(node: GraphNode) -> None:
            if node.id not in nodes and node.id not in before_nodes and node.id in known:
                # Shared canonical node supported by other papers only: merge onto it.
                before_nodes[node.id] = known[node.id]
                nodes[node.id] = known[node.id]
            nodes[node.id] = merge_nodes(nodes.get(node.id), node)

        def link(evidence: list[Evidence], subject_id, subject_type, claim) -> list[str]:
            for ev in evidence:
                result.links.setdefault(ev.id, EvidenceLink(subject_id, str(subject_type), claim))
            return [ev.id for ev in evidence]

        # Paper node
        statements = [s for s in [k.research_problem, *k.research_questions] if s]
        paper_ev = [ev for s in statements for ev in s.evidence]
        put_node(
            GraphNode(
                id=pid,
                type=EntityType.PAPER,
                name=k.paper.name,
                paper_ids=[pid],
                evidence_ids=link(paper_ev, pid, "ResearchStatement", k.paper.name),
                properties={
                    "year": k.paper.year,
                    "venue": k.paper.venue,
                    "doi": k.paper.doi,
                    "file_name": k.paper.file_name,
                    "abstract": k.paper.abstract,
                    "research_problem": k.research_problem.text if k.research_problem else None,
                    "research_questions": [q.text for q in k.research_questions],
                },
            )
        )

        # Shared concepts, resolved against the whole graph.
        for entity in [*k.methods, *k.datasets, *k.metrics]:
            res = resolver.resolve(entity.type, entity.name)
            local_to_canonical[entity.id] = res.canonical_id
            if res.decision.method != "new":
                update.resolutions.append(res.decision)
            props = {}
            if entity.type == EntityType.METRIC:
                props["higher_is_better"] = entity.higher_is_better
            put_node(
                GraphNode(
                    id=res.canonical_id,
                    type=entity.type,
                    name=res.canonical_name,
                    aliases=[entity.name] if entity.name != res.canonical_name else [],
                    description=entity.description,
                    paper_ids=[pid],
                    evidence_ids=link(entity.evidence, res.canonical_id, entity.type, entity.name),
                    properties=props,
                )
            )
        update.possible_duplicates = resolver.possible_duplicates

        # Paper-bound claims: deterministic IDs from paper + normalized statement.
        for claim in [*k.findings, *k.limitations, *k.future_work]:
            node_id = (
                f"{_CLAIM_PREFIX[claim.type]}_{_hash(pid, claim.type, normalize_key(claim.name))}"
            )
            local_to_canonical[claim.id] = node_id
            put_node(
                GraphNode(
                    id=node_id,
                    type=claim.type,
                    name=claim.name,
                    paper_ids=[pid],
                    evidence_ids=link(claim.evidence, node_id, claim.type, claim.name),
                )
            )

        # Relations, remapped onto canonical node IDs (including IDs inside properties).
        local_to_canonical[pid] = pid
        for rel in k.relations:
            src = local_to_canonical.get(rel.source_id)
            tgt = local_to_canonical.get(rel.target_id)
            if not src or not tgt or src == tgt:
                continue
            props = dict(rel.properties)
            for key in ("method_id", "dataset_id"):
                if props.get(key):
                    props[key] = local_to_canonical.get(props[key], props[key])
            key_parts = [props.get(p) for p in _EDGE_KEY_PROPS.get(rel.type, ())]
            edge = GraphEdge(
                id=f"rel_{_hash(rel.type, src, tgt, *key_parts)}",
                type=rel.type,
                source_id=src,
                source_type=rel.source_type,
                target_id=tgt,
                target_type=rel.target_type,
                paper_ids=[pid],
                evidence_ids=link(rel.evidence, tgt, rel.type, self._relation_claim(rel)),
                confidence=rel.confidence,
                properties=props,
            )
            edges[edge.id] = merge_edges(edges.get(edge.id), edge)

        result.evidence = list({ev.id: ev for ev in k.all_evidence()}.values())
        return result

    @staticmethod
    def _relation_claim(rel) -> str:
        p = rel.properties
        if rel.type == RelationType.REPORTS:
            parts = [p.get("method"), p.get("value"), p.get("dataset") and f"on {p['dataset']}"]
            return " ".join(str(x) for x in parts if x)
        return str(rel.type)

    def _write(self, pid, result, before_nodes, before_edges, nodes, edges, old_evidence) -> None:
        g, update = self.graph, result.update
        # No edge can point at a removed node: a node is removed only when no paper supports
        # it, and an edge's supporting papers always support both of its endpoints.

        def classify(before: dict, after: dict, added, strengthened, changed, removed) -> list:
            to_write = []
            for i, item in after.items():
                old = before.get(i)
                if old is None:
                    added.append(i)
                    to_write.append(item)
                elif item != old:
                    to_write.append(item)
                    grew = set(item.paper_ids) - set(old.paper_ids) or len(item.evidence_ids) > len(
                        old.evidence_ids
                    )
                    (strengthened if grew else changed).append(i)
            removed.extend(i for i in before if i not in after)
            return to_write

        node_writes = classify(
            before_nodes,
            nodes,
            update.added_entity_ids,
            update.strengthened_entity_ids,
            update.changed_entity_ids,
            update.removed_entity_ids,
        )
        edge_writes = classify(
            before_edges,
            edges,
            update.added_relation_ids,
            update.strengthened_relation_ids,
            update.changed_relation_ids,
            update.removed_relation_ids,
        )
        for ids in (
            update.added_entity_ids,
            update.strengthened_entity_ids,
            update.changed_entity_ids,
            update.removed_entity_ids,
            update.added_relation_ids,
            update.strengthened_relation_ids,
            update.changed_relation_ids,
            update.removed_relation_ids,
        ):
            ids.sort()

        if update.removed_relation_ids:
            g.delete_edges(update.removed_relation_ids)
        if update.removed_entity_ids:
            g.delete_nodes(update.removed_entity_ids)
        if old_evidence - {e.id for e in result.evidence}:
            g.delete_evidence_for_paper(pid)
        if result.evidence:
            g.upsert_evidence(result.evidence)
        if node_writes:
            g.upsert_nodes(node_writes)
        if edge_writes:
            g.upsert_edges(edge_writes)
