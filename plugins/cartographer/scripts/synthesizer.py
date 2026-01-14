#!/usr/bin/env python3
"""
Synthesizer module for Cartographer.
Combines all analysis results into comprehensive documentation.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

from scanner import scan_codebase, print_scan_summary
from analyzer import analyze_codebase, FileAnalysis
from dependency_graph import build_dependency_graph, generate_dependency_report
from security_scan import scan_codebase_security, generate_security_report
from todo_index import scan_todos, generate_todo_report


def generate_metrics_report(scan_results: List[Tuple[Path, int, int]], root: Path) -> str:
    """Generate code metrics report."""
    total_files = len(scan_results)
    total_lines = sum(r[1] for r in scan_results)
    total_tokens = sum(r[2] for r in scan_results)

    # Group by extension
    by_ext = {}
    for path, lines, tokens in scan_results:
        ext = path.suffix.lower() or 'no extension'
        if ext not in by_ext:
            by_ext[ext] = {'files': 0, 'lines': 0, 'tokens': 0}
        by_ext[ext]['files'] += 1
        by_ext[ext]['lines'] += lines
        by_ext[ext]['tokens'] += tokens

    # Group by directory
    by_dir = {}
    for path, lines, tokens in scan_results:
        try:
            rel_path = path.relative_to(root)
            dir_name = str(rel_path.parts[0]) if len(rel_path.parts) > 1 else '.'
        except ValueError:
            dir_name = '.'
        if dir_name not in by_dir:
            by_dir[dir_name] = {'files': 0, 'lines': 0}
        by_dir[dir_name]['files'] += 1
        by_dir[dir_name]['lines'] += lines

    lines = [
        "# Code Metrics",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Summary",
        "",
        f"- **Total Files**: {total_files:,}",
        f"- **Total Lines**: {total_lines:,}",
        f"- **Total Tokens**: {total_tokens:,}",
        f"- **Languages**: {len(by_ext)}",
        "",
        "## By Language/Extension",
        "",
        "| Extension | Files | Lines | Tokens | % of Code |",
        "|-----------|-------|-------|--------|-----------|",
    ]

    for ext, stats in sorted(by_ext.items(), key=lambda x: -x[1]['lines']):
        pct = (stats['lines'] / total_lines * 100) if total_lines > 0 else 0
        lines.append(f"| {ext} | {stats['files']:,} | {stats['lines']:,} | {stats['tokens']:,} | {pct:.1f}% |")

    lines.extend([
        "",
        "## By Directory",
        "",
        "| Directory | Files | Lines |",
        "|-----------|-------|-------|",
    ])

    for dir_name, stats in sorted(by_dir.items(), key=lambda x: -x[1]['lines']):
        lines.append(f"| {dir_name}/ | {stats['files']:,} | {stats['lines']:,} |")

    lines.extend([
        "",
        "## Size Distribution",
        "",
    ])

    # File size distribution
    small = sum(1 for _, l, _ in scan_results if l < 100)
    medium = sum(1 for _, l, _ in scan_results if 100 <= l < 500)
    large = sum(1 for _, l, _ in scan_results if 500 <= l < 1000)
    xlarge = sum(1 for _, l, _ in scan_results if l >= 1000)

    lines.extend([
        f"- **Small (<100 lines)**: {small} files",
        f"- **Medium (100-500 lines)**: {medium} files",
        f"- **Large (500-1000 lines)**: {large} files",
        f"- **Extra Large (>1000 lines)**: {xlarge} files",
        "",
    ])

    # Largest files
    lines.extend([
        "## Largest Files",
        "",
    ])

    for path, line_count, tokens in sorted(scan_results, key=lambda x: -x[1])[:10]:
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            rel_path = path
        lines.append(f"- `{rel_path}`: {line_count:,} lines, {tokens:,} tokens")

    lines.append("")
    return '\n'.join(lines)


def generate_codebase_map(
    scan_results: List[Tuple[Path, int, int]],
    analyses: List[FileAnalysis],
    root: Path
) -> str:
    """Generate the main codebase map."""
    lines = [
        "# Codebase Map",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Overview",
        "",
    ]

    # Try to find README for project description
    readme_path = root / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            # Extract first paragraph after title
            readme_lines = readme_content.split('\n')
            for i, line in enumerate(readme_lines):
                if line.startswith('# '):
                    lines.append(f"**Project**: {line[2:].strip()}")
                    # Find next non-empty, non-heading line
                    for j in range(i + 1, min(i + 10, len(readme_lines))):
                        if readme_lines[j].strip() and not readme_lines[j].startswith('#'):
                            lines.append("")
                            lines.append(readme_lines[j].strip())
                            break
                    break
        except Exception:
            pass

    lines.extend([
        "",
        f"- **Total Files**: {len(scan_results):,}",
        f"- **Root Directory**: `{root}`",
        "",
        "## Directory Structure",
        "",
        "```",
    ])

    # Build directory tree
    dirs_seen = set()
    for path, _, _ in scan_results:
        try:
            rel_path = path.relative_to(root)
            for i in range(len(rel_path.parts) - 1):
                dir_path = '/'.join(rel_path.parts[:i + 1])
                if dir_path not in dirs_seen:
                    dirs_seen.add(dir_path)
                    indent = "  " * i
                    lines.append(f"{indent}{rel_path.parts[i]}/")
        except ValueError:
            pass

    lines.extend([
        "```",
        "",
        "## Key Modules",
        "",
    ])

    # Group analyses by directory
    by_dir = {}
    for analysis in analyses:
        try:
            rel_path = analysis.path.relative_to(root)
            dir_name = str(rel_path.parts[0]) if len(rel_path.parts) > 1 else '.'
        except ValueError:
            dir_name = '.'
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(analysis)

    for dir_name, dir_analyses in sorted(by_dir.items()):
        lines.append(f"### `{dir_name}/`")
        lines.append("")

        # Show top files in each directory
        for analysis in dir_analyses[:5]:
            try:
                rel_path = analysis.path.relative_to(root)
            except ValueError:
                rel_path = analysis.path

            lines.append(f"- **`{rel_path.name}`**")
            if analysis.purpose:
                lines.append(f"  - {analysis.purpose}")
            if analysis.classes:
                lines.append(f"  - Classes: {', '.join(analysis.classes[:3])}")
            if analysis.functions:
                lines.append(f"  - Functions: {', '.join(analysis.functions[:5])}")

        if len(dir_analyses) > 5:
            lines.append(f"  - *...and {len(dir_analyses) - 5} more files*")
        lines.append("")

    lines.extend([
        "## Entry Points",
        "",
    ])

    # Find main entry points
    entry_points = []
    for analysis in analyses:
        if analysis.path.name in ('main.py', 'main.rs', 'index.js', 'index.ts', 'app.py', 'server.py'):
            entry_points.append(analysis)
        elif 'main' in analysis.functions:
            entry_points.append(analysis)

    if entry_points:
        for analysis in entry_points:
            try:
                rel_path = analysis.path.relative_to(root)
            except ValueError:
                rel_path = analysis.path
            lines.append(f"- `{rel_path}` ({analysis.language})")
    else:
        lines.append("- No obvious entry points detected")

    lines.extend([
        "",
        "## Navigation Guide",
        "",
        "| Task | Look In |",
        "|------|---------|",
    ])

    # Try to provide navigation hints based on common patterns
    nav_hints = [
        ("Add a new feature", "src/"),
        ("Fix a bug", "src/, tests/"),
        ("Update configuration", "config/, *.toml, *.json"),
        ("Add tests", "tests/, *_test.*, *_spec.*"),
        ("Update documentation", "docs/, *.md"),
    ]

    for task, location in nav_hints:
        lines.append(f"| {task} | `{location}` |")

    lines.append("")
    return '\n'.join(lines)


def run_cartographer(root_path: str, output_dir: str = None):
    """Run the full cartographer analysis and generate all reports."""
    root = Path(root_path).resolve()

    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = root / "docs"

    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Cartographer: Analyzing {root}")
    print("=" * 60)

    # Phase 1: Scanning
    print("\n[1/6] Scanning codebase...")
    scan_results = scan_codebase(root_path)
    files = [r[0] for r in scan_results]
    print(f"  Found {len(files)} source files")

    # Phase 2: Analysis
    print("\n[2/6] Analyzing file structure...")
    analyses = analyze_codebase(files)
    print(f"  Analyzed {len(analyses)} files")

    # Phase 3: Dependency Graph
    print("\n[3/6] Building dependency graph...")
    graph = build_dependency_graph(files, root)
    dep_report = generate_dependency_report(graph, root)
    print(f"  Found {len(graph.nodes)} modules, {len(graph.edges)} dependencies")

    # Phase 4: Security Scan
    print("\n[4/6] Running security scan...")
    findings = scan_codebase_security(files)
    security_report = generate_security_report(findings, root)
    critical = sum(1 for f in findings if f.severity == 'critical')
    print(f"  Found {len(findings)} issues ({critical} critical)")

    # Phase 5: TODO Index
    print("\n[5/6] Indexing TODOs...")
    todos = scan_todos(files)
    todo_report = generate_todo_report(todos, root)
    print(f"  Found {len(todos)} TODO items")

    # Phase 6: Generate Reports
    print("\n[6/6] Generating reports...")

    # Metrics
    metrics_report = generate_metrics_report(scan_results, root)
    (out_path / "METRICS.md").write_text(metrics_report, encoding='utf-8')
    print(f"  Wrote METRICS.md")

    # Dependency Graph
    (out_path / "DEPENDENCY_GRAPH.md").write_text(dep_report, encoding='utf-8')
    print(f"  Wrote DEPENDENCY_GRAPH.md")

    # Security Scan
    (out_path / "SECURITY_SCAN.md").write_text(security_report, encoding='utf-8')
    print(f"  Wrote SECURITY_SCAN.md")

    # TODO Index
    (out_path / "TODO_INDEX.md").write_text(todo_report, encoding='utf-8')
    print(f"  Wrote TODO_INDEX.md")

    # Codebase Map
    codebase_map = generate_codebase_map(scan_results, analyses, root)
    (out_path / "CODEBASE_MAP.md").write_text(codebase_map, encoding='utf-8')
    print(f"  Wrote CODEBASE_MAP.md")

    print("\n" + "=" * 60)
    print(f"Cartographer complete! Reports saved to {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    output = sys.argv[2] if len(sys.argv) > 2 else None
    run_cartographer(path, output)
