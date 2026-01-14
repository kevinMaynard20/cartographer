#!/usr/bin/env python3
"""
Dependency Graph module for Cartographer.
Builds and visualizes module dependencies in Mermaid format.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Represents the dependency graph of a codebase."""
    nodes: Set[str] = field(default_factory=set)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    circular: List[Tuple[str, str]] = field(default_factory=list)


def normalize_module_name(path: Path, root: Path) -> str:
    """Convert file path to module name."""
    rel_path = path.relative_to(root)
    # Remove extension and convert to module notation
    parts = list(rel_path.parts)
    if parts[-1].endswith('.py') or parts[-1].endswith('.rs'):
        parts[-1] = parts[-1].rsplit('.', 1)[0]
    if parts[-1] in ('mod', 'index', '__init__', 'main'):
        parts = parts[:-1]
    return '/'.join(parts) if parts else 'root'


def extract_imports_python(content: str) -> List[str]:
    """Extract import statements from Python code."""
    imports = []
    for match in re.finditer(r'^from\s+(\S+)\s+import', content, re.MULTILINE):
        imports.append(match.group(1))
    for match in re.finditer(r'^import\s+(\S+)', content, re.MULTILINE):
        mod = match.group(1).split(',')[0].split(' ')[0]
        imports.append(mod)
    return imports


def extract_imports_rust(content: str) -> List[str]:
    """Extract use statements from Rust code."""
    imports = []
    for match in re.finditer(r'^use\s+(?:crate::)?(\w+)', content, re.MULTILINE):
        imports.append(match.group(1))
    for match in re.finditer(r'^mod\s+(\w+);', content, re.MULTILINE):
        imports.append(match.group(1))
    return imports


def extract_imports_js(content: str) -> List[str]:
    """Extract import statements from JavaScript/TypeScript code."""
    imports = []
    for match in re.finditer(r"from\s+['\"]\.?\.?/?([^'\"]+)['\"]", content):
        path = match.group(1)
        if not path.startswith('@') and not path.startswith('node_modules'):
            imports.append(path)
    for match in re.finditer(r"require\(['\"]\.?\.?/?([^'\"]+)['\"]\)", content):
        path = match.group(1)
        if not path.startswith('@'):
            imports.append(path)
    return imports


def build_dependency_graph(files: List[Path], root: Path) -> DependencyGraph:
    """Build a dependency graph from source files."""
    graph = DependencyGraph()

    # Map module names to their file paths
    module_map = {}
    for file_path in files:
        module_name = normalize_module_name(file_path, root)
        module_map[module_name] = file_path
        graph.nodes.add(module_name)

    # Extract dependencies for each file
    for file_path in files:
        module_name = normalize_module_name(file_path, root)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        ext = file_path.suffix.lower()
        if ext == '.py':
            imports = extract_imports_python(content)
        elif ext == '.rs':
            imports = extract_imports_rust(content)
        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
            imports = extract_imports_js(content)
        else:
            imports = []

        # Match imports to known modules
        for imp in imports:
            # Normalize the import
            imp_parts = imp.replace('.', '/').split('/')
            imp_normalized = '/'.join(imp_parts)

            # Check if this is an internal module
            for known_module in graph.nodes:
                if known_module.endswith(imp_normalized) or imp_normalized.endswith(known_module.split('/')[-1]):
                    if module_name != known_module:
                        graph.edges.append((module_name, known_module))
                    break

    # Detect circular dependencies
    graph.circular = detect_circular_dependencies(graph)

    return graph


def detect_circular_dependencies(graph: DependencyGraph) -> List[Tuple[str, str]]:
    """Detect circular dependencies in the graph."""
    circular = []

    # Build adjacency list
    adj = {node: set() for node in graph.nodes}
    for src, dst in graph.edges:
        if src in adj:
            adj[src].add(dst)

    # Check for direct circular references
    for src, dst in graph.edges:
        if (dst, src) in graph.edges and (dst, src) not in circular:
            circular.append((src, dst))

    return circular


def generate_mermaid(graph: DependencyGraph, max_nodes: int = 50) -> str:
    """Generate Mermaid diagram from dependency graph."""
    lines = ["```mermaid", "graph TD"]

    # Limit nodes for readability
    nodes = list(graph.nodes)[:max_nodes]
    node_ids = {node: f"N{i}" for i, node in enumerate(nodes)}

    # Add node definitions
    for node, node_id in node_ids.items():
        # Escape special characters
        label = node.replace('"', "'")
        lines.append(f'    {node_id}["{label}"]')

    # Add edges
    added_edges = set()
    for src, dst in graph.edges:
        if src in node_ids and dst in node_ids:
            edge_key = (src, dst)
            if edge_key not in added_edges:
                lines.append(f"    {node_ids[src]} --> {node_ids[dst]}")
                added_edges.add(edge_key)

    # Style circular dependencies
    for src, dst in graph.circular:
        if src in node_ids and dst in node_ids:
            lines.append(f"    linkStyle default stroke:#333")

    lines.append("```")
    return '\n'.join(lines)


def generate_dependency_report(graph: DependencyGraph, root: Path) -> str:
    """Generate markdown report for dependencies."""
    lines = [
        "# Dependency Graph",
        "",
        "## Overview",
        "",
        f"- **Total Modules**: {len(graph.nodes)}",
        f"- **Total Dependencies**: {len(graph.edges)}",
        f"- **Circular Dependencies**: {len(graph.circular)}",
        "",
    ]

    # Mermaid diagram
    lines.append("## Module Dependencies")
    lines.append("")
    lines.append(generate_mermaid(graph))
    lines.append("")

    # Circular dependencies warning
    if graph.circular:
        lines.append("## Circular Dependencies")
        lines.append("")
        lines.append("The following circular dependencies were detected:")
        lines.append("")
        for src, dst in graph.circular:
            lines.append(f"- `{src}` <-> `{dst}`")
        lines.append("")

    # Most connected modules
    incoming = {node: 0 for node in graph.nodes}
    outgoing = {node: 0 for node in graph.nodes}
    for src, dst in graph.edges:
        outgoing[src] = outgoing.get(src, 0) + 1
        incoming[dst] = incoming.get(dst, 0) + 1

    lines.append("## Most Connected Modules")
    lines.append("")
    lines.append("### Most Imported (Hub Modules)")
    lines.append("")
    for node, count in sorted(incoming.items(), key=lambda x: -x[1])[:10]:
        if count > 0:
            lines.append(f"- `{node}`: {count} imports")
    lines.append("")

    lines.append("### Most Importing")
    lines.append("")
    for node, count in sorted(outgoing.items(), key=lambda x: -x[1])[:10]:
        if count > 0:
            lines.append(f"- `{node}`: {count} dependencies")
    lines.append("")

    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    from scanner import scan_codebase

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    root = Path(path).resolve()
    scan_results = scan_codebase(path)

    files = [r[0] for r in scan_results]
    graph = build_dependency_graph(files, root)

    print(generate_dependency_report(graph, root))
