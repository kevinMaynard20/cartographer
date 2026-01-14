#!/usr/bin/env python3
"""
TODO Index module for Cartographer.
Finds and aggregates all TODO, FIXME, HACK, XXX, and BUG comments in a codebase.
"""

import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class TodoItem:
    """Represents a TODO/FIXME/etc item found in code."""
    type: str  # 'TODO', 'FIXME', 'HACK', 'XXX', 'BUG'
    file: Path
    line: int
    text: str
    priority: str  # 'high', 'normal', 'low'


# Priority mapping
PRIORITY_MAP = {
    'FIXME': 'high',
    'BUG': 'high',
    'XXX': 'high',
    'TODO': 'normal',
    'HACK': 'low',
    'NOTE': 'low',
}

# Pattern to match TODO-style comments
TODO_PATTERN = re.compile(
    r'(?:^|\s|[#/*]+\s*)(TODO|FIXME|HACK|XXX|BUG|NOTE)[\s:]+(.+?)(?:\*/|$)',
    re.IGNORECASE | re.MULTILINE
)


def extract_todos(file_path: Path) -> List[TodoItem]:
    """Extract TODO items from a file."""
    items = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return []

    for line_num, line in enumerate(lines, 1):
        for match in TODO_PATTERN.finditer(line):
            todo_type = match.group(1).upper()
            text = match.group(2).strip()

            # Clean up the text
            text = re.sub(r'\s*\*/$', '', text)  # Remove closing comment
            text = re.sub(r'\s*-->$', '', text)  # Remove HTML comment close
            text = text.strip()

            if text:  # Only add if there's actual text
                items.append(TodoItem(
                    type=todo_type,
                    file=file_path,
                    line=line_num,
                    text=text[:200],  # Limit text length
                    priority=PRIORITY_MAP.get(todo_type, 'normal')
                ))

    return items


def scan_todos(files: List[Path]) -> List[TodoItem]:
    """Scan all files for TODO items."""
    all_items = []
    for file_path in files:
        items = extract_todos(file_path)
        all_items.extend(items)
    return all_items


def generate_todo_report(items: List[TodoItem], root: Path) -> str:
    """Generate markdown report for TODO items."""
    # Count by type
    by_type = {}
    for item in items:
        by_type[item.type] = by_type.get(item.type, 0) + 1

    lines = [
        "# TODO Index",
        "",
        "## Summary",
        "",
    ]

    for todo_type in ['TODO', 'FIXME', 'BUG', 'HACK', 'XXX', 'NOTE']:
        count = by_type.get(todo_type, 0)
        if count > 0:
            lines.append(f"- **{todo_type}s**: {count}")

    lines.append(f"- **Total**: {len(items)}")
    lines.append("")

    if not items:
        lines.append("No TODO items found in the codebase.")
        lines.append("")
        return '\n'.join(lines)

    # Group by priority
    high_priority = [i for i in items if i.priority == 'high']
    normal_priority = [i for i in items if i.priority == 'normal']
    low_priority = [i for i in items if i.priority == 'low']

    # High priority
    if high_priority:
        lines.append("## High Priority (FIXME/BUG/XXX)")
        lines.append("")
        lines.append("These items should be addressed soon:")
        lines.append("")
        for item in high_priority:
            rel_path = item.file.relative_to(root) if item.file.is_relative_to(root) else item.file
            lines.append(f"- **[{item.type}]** `{rel_path}:{item.line}`")
            lines.append(f"  - {item.text}")
        lines.append("")

    # Normal priority
    if normal_priority:
        lines.append("## Normal Priority (TODO)")
        lines.append("")
        for item in normal_priority:
            rel_path = item.file.relative_to(root) if item.file.is_relative_to(root) else item.file
            lines.append(f"- `{rel_path}:{item.line}`: {item.text}")
        lines.append("")

    # Low priority
    if low_priority:
        lines.append("## Low Priority (HACK/NOTE)")
        lines.append("")
        for item in low_priority:
            rel_path = item.file.relative_to(root) if item.file.is_relative_to(root) else item.file
            lines.append(f"- `{rel_path}:{item.line}`: {item.text}")
        lines.append("")

    # By file
    lines.append("## By File")
    lines.append("")

    by_file = {}
    for item in items:
        key = str(item.file)
        if key not in by_file:
            by_file[key] = []
        by_file[key].append(item)

    for file_path, file_items in sorted(by_file.items()):
        try:
            rel_path = Path(file_path).relative_to(root)
        except ValueError:
            rel_path = Path(file_path)
        lines.append(f"### `{rel_path}` ({len(file_items)} items)")
        lines.append("")
        for item in file_items:
            lines.append(f"- **Line {item.line}** [{item.type}]: {item.text}")
        lines.append("")

    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    from scanner import scan_codebase

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    root = Path(path).resolve()
    scan_results = scan_codebase(path)

    files = [r[0] for r in scan_results]
    items = scan_todos(files)

    print(generate_todo_report(items, root))
