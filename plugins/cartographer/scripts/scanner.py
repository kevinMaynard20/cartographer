#!/usr/bin/env python3
"""
Scanner module for Cartographer.
Discovers all source files in a codebase while respecting .gitignore.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Set, Tuple

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def load_gitignore(root_path: Path) -> List[str]:
    """Load .gitignore patterns from the root directory."""
    gitignore_path = root_path / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)

    # Add common ignore patterns
    patterns.extend([
        '.git',
        'node_modules',
        '__pycache__',
        '.pytest_cache',
        'venv',
        '.venv',
        'dist',
        'build',
        '*.pyc',
        '*.pyo',
        '.DS_Store',
        'Thumbs.db',
    ])

    return patterns


def should_ignore(path: Path, patterns: List[str], root: Path) -> bool:
    """Check if a path should be ignored based on gitignore patterns."""
    rel_path = str(path.relative_to(root))
    name = path.name

    for pattern in patterns:
        # Match against filename
        if fnmatch.fnmatch(name, pattern):
            return True
        # Match against relative path
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(rel_path, f"**/{pattern}"):
            return True
        # Match directory patterns
        if pattern.endswith('/') and path.is_dir():
            if fnmatch.fnmatch(name, pattern.rstrip('/')):
                return True

    return False


def get_source_extensions() -> Set[str]:
    """Return a set of common source file extensions."""
    return {
        # Programming languages
        '.py', '.pyw',  # Python
        '.js', '.jsx', '.mjs', '.cjs',  # JavaScript
        '.ts', '.tsx',  # TypeScript
        '.rs',  # Rust
        '.go',  # Go
        '.java',  # Java
        '.c', '.h',  # C
        '.cpp', '.hpp', '.cc', '.cxx',  # C++
        '.cs',  # C#
        '.rb',  # Ruby
        '.php',  # PHP
        '.swift',  # Swift
        '.kt', '.kts',  # Kotlin
        '.scala',  # Scala
        '.r', '.R',  # R
        '.lua',  # Lua
        '.pl', '.pm',  # Perl
        '.sh', '.bash', '.zsh',  # Shell
        '.ps1', '.psm1',  # PowerShell

        # Web
        '.html', '.htm',
        '.css', '.scss', '.sass', '.less',
        '.vue', '.svelte',

        # Config/Data
        '.json', '.yaml', '.yml', '.toml',
        '.xml', '.md', '.rst',

        # Other
        '.sql', '.graphql',
        '.dockerfile', '.Dockerfile',
    }


def count_tokens(content: str) -> int:
    """Count tokens in content using tiktoken if available."""
    if TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(content))
        except Exception:
            pass
    # Fallback: rough estimate (1 token ≈ 4 characters)
    return len(content) // 4


def scan_codebase(root_path: str) -> List[Tuple[Path, int, int]]:
    """
    Scan a codebase and return list of (file_path, line_count, token_count).

    Args:
        root_path: Root directory to scan

    Returns:
        List of tuples containing (path, lines, tokens)
    """
    root = Path(root_path).resolve()
    patterns = load_gitignore(root)
    source_extensions = get_source_extensions()

    results = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        # Filter out ignored directories
        dirnames[:] = [
            d for d in dirnames
            if not should_ignore(current_dir / d, patterns, root)
        ]

        for filename in filenames:
            file_path = current_dir / filename

            # Skip ignored files
            if should_ignore(file_path, patterns, root):
                continue

            # Check if it's a source file
            ext = file_path.suffix.lower()
            if ext not in source_extensions and filename not in {'Dockerfile', 'Makefile', 'Cargo.toml', 'package.json'}:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.count('\n') + 1
                tokens = count_tokens(content)

                results.append((file_path, lines, tokens))
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")

    return results


def print_scan_summary(results: List[Tuple[Path, int, int]], root: Path):
    """Print a summary of the scan results."""
    total_files = len(results)
    total_lines = sum(r[1] for r in results)
    total_tokens = sum(r[2] for r in results)

    print(f"\n{'='*60}")
    print(f"Scan Summary")
    print(f"{'='*60}")
    print(f"Root: {root}")
    print(f"Total files: {total_files}")
    print(f"Total lines: {total_lines:,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"{'='*60}\n")

    # Group by extension
    by_ext = {}
    for path, lines, tokens in results:
        ext = path.suffix.lower() or 'no extension'
        if ext not in by_ext:
            by_ext[ext] = {'files': 0, 'lines': 0, 'tokens': 0}
        by_ext[ext]['files'] += 1
        by_ext[ext]['lines'] += lines
        by_ext[ext]['tokens'] += tokens

    print("By Extension:")
    print(f"{'Extension':<15} {'Files':>8} {'Lines':>12} {'Tokens':>12}")
    print("-" * 50)
    for ext, stats in sorted(by_ext.items(), key=lambda x: -x[1]['tokens']):
        print(f"{ext:<15} {stats['files']:>8} {stats['lines']:>12,} {stats['tokens']:>12,}")


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_codebase(path)
    print_scan_summary(results, Path(path).resolve())
