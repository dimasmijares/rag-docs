"""Small repository-owned CLI for validating and querying the KDD graph."""

from __future__ import annotations

import argparse
import collections
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Node:
    id: str
    layer: str
    status: str
    confidence: str
    title: str
    file: Path
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", content, re.DOTALL)
    if not match:
        return {}, content
    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, match.group(2)


def scan(specs: Path) -> tuple[list[Node], list[Edge], list[str]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    errors: list[str] = []
    for path in sorted(specs.rglob("*.md")):
        try:
            metadata, body = parse_frontmatter(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        spec_id = metadata.get("id")
        if not spec_id:
            continue
        heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        node = Node(
            id=str(spec_id),
            layer=str(metadata.get("layer") or "unspecified"),
            status=str(metadata.get("status") or "draft"),
            confidence=str(metadata.get("confidence") or "low"),
            title=heading.group(1).strip() if heading else str(spec_id),
            file=path,
            metadata=metadata,
        )
        nodes.append(node)

        dependencies = metadata.get("dependencies") or []
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if isinstance(dependency, dict) and dependency.get("id"):
                    edges.append(
                        Edge(
                            node.id,
                            str(dependency["id"]),
                            str(dependency.get("relation") or "depends-on"),
                        )
                    )
        activates = metadata.get("activates") or []
        if isinstance(activates, list):
            edges.extend(Edge(node.id, str(target), "activates") for target in activates)
        if metadata.get("parent"):
            edges.append(Edge(node.id, str(metadata["parent"]), "depends-on"))
        if metadata.get("supersedes"):
            edges.append(Edge(node.id, str(metadata["supersedes"]), "supersedes"))
    return nodes, edges, errors


def find_orphans(nodes: list[Node], edges: list[Edge]) -> list[Node]:
    connected = {endpoint for edge in edges for endpoint in (edge.source, edge.target)}
    return [node for node in nodes if node.id not in connected]


def validate(nodes: list[Node], edges: list[Edge], parse_errors: list[str]) -> int:
    counts = collections.Counter(node.id for node in nodes)
    node_ids = set(counts)
    errors = list(parse_errors)
    errors.extend(
        f'duplicate ID "{spec_id}" ({count} occurrences)'
        for spec_id, count in counts.items()
        if count > 1
    )
    errors.extend(
        f'"{edge.source}" references missing "{edge.target}"'
        for edge in edges
        if edge.target not in node_ids
    )
    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  ERROR  {error}")
        return 1
    print("Validation passed. No issues found.")
    print(f"Checked {len(nodes)} specs, {len(edges)} edges.")
    return 0


def print_orphans(nodes: list[Node], edges: list[Edge]) -> int:
    orphans = find_orphans(nodes, edges)
    if not orphans:
        print("No orphan specs found. All specs are connected.")
        return 0
    print(f"{len(orphans)} orphan spec(s) found:")
    for node in orphans:
        print(f"  {node.id} [{node.status}/{node.confidence}] — {node.file}")
    return 1


def print_stats(nodes: list[Node], edges: list[Edge]) -> int:
    print("=== KDD Knowledge Graph — Statistics ===\n")
    print(f"Total specs:  {len(nodes)}")
    print(f"Total edges:  {len(edges)}")
    print(f"Orphans:      {len(find_orphans(nodes, edges))}")
    for label, values in (
        ("layer", (node.layer for node in nodes)),
        ("status", (node.status for node in nodes)),
        ("confidence", (node.confidence for node in nodes)),
        ("relation", (edge.relation for edge in edges)),
    ):
        print(f"\nBy {label}:")
        for value, count in collections.Counter(values).most_common():
            print(f"  {value}: {count}")
    return 0


def adjacency(edges: list[Edge]) -> tuple[dict[str, list[Edge]], dict[str, list[Edge]]]:
    outgoing: dict[str, list[Edge]] = collections.defaultdict(list)
    incoming: dict[str, list[Edge]] = collections.defaultdict(list)
    for edge in edges:
        outgoing[edge.source].append(edge)
        incoming[edge.target].append(edge)
    return outgoing, incoming


def print_impact(spec_id: str, nodes: list[Node], edges: list[Edge]) -> int:
    node_map = {node.id: node for node in nodes}
    if spec_id not in node_map:
        print(f'Error: Spec "{spec_id}" not found.', file=sys.stderr)
        return 1
    _, incoming = adjacency(edges)
    queue = collections.deque([spec_id])
    seen = {spec_id}
    affected: list[tuple[Node, Edge]] = []
    while queue:
        current = queue.popleft()
        for edge in incoming[current]:
            if edge.source in seen:
                continue
            seen.add(edge.source)
            queue.append(edge.source)
            affected.append((node_map[edge.source], edge))
    if not affected:
        print(f'No specs are affected by changes to "{spec_id}".')
        return 0
    print(f'Impact analysis for "{spec_id}": {len(affected)} spec(s) affected.\n')
    for node, edge in affected:
        print(f"  {node.id} [{node.status}/{node.confidence}]")
        print(f"    Relation: inverse({edge.relation}) via {edge.target}")
        print(f"    File: {node.file}")
    return 0


def print_context(spec_id: str, nodes: list[Node], edges: list[Edge]) -> int:
    node_map = {node.id: node for node in nodes}
    if spec_id not in node_map:
        print(f'Error: Spec "{spec_id}" not found.', file=sys.stderr)
        return 1
    outgoing, incoming = adjacency(edges)
    queue = collections.deque([(spec_id, 0)])
    depths = {spec_id: 0}
    while queue:
        current, depth = queue.popleft()
        if depth == 3:
            continue
        neighbors = [edge.target for edge in outgoing[current]] + [
            edge.source for edge in incoming[current]
        ]
        for neighbor in neighbors:
            if neighbor not in depths:
                depths[neighbor] = depth + 1
                queue.append((neighbor, depth + 1))
    print(f"# Activation Context: {spec_id}\n")
    print(f"Depth: 3 | Total specs: {len(depths)}\n")
    for depth in range(4):
        selected = sorted(spec for spec, value in depths.items() if value == depth)
        if not selected:
            continue
        print(f"## Depth {depth} ({len(selected)})\n")
        for selected_id in selected:
            node = node_map[selected_id]
            print(f"### {node.id}")
            print(f"**{node.title}**")
            print(f"- Layer: {node.layer} | Status: {node.status} | Confidence: {node.confidence}")
            print(f"- File: {node.file}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("command", choices=("validate", "orphans", "stats", "context", "impact"))
    parser.add_argument("id", nargs="?")
    args = parser.parse_args()
    nodes, edges, errors = scan(args.specs.resolve())
    if args.command == "validate":
        return validate(nodes, edges, errors)
    if errors:
        print("Cannot query a graph with parse errors.", file=sys.stderr)
        return 1
    if args.command == "orphans":
        return print_orphans(nodes, edges)
    if args.command == "stats":
        return print_stats(nodes, edges)
    if not args.id:
        parser.error(f"{args.command} requires an ID")
    if args.command == "impact":
        return print_impact(args.id, nodes, edges)
    return print_context(args.id, nodes, edges)


if __name__ == "__main__":
    raise SystemExit(main())
