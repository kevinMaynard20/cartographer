#!/usr/bin/env python3
"""
Analyzer module for Cartographer.
Analyzes source files to extract structure, imports, exports, and key components.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    path: Path
    language: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    purpose: str = ""


def detect_language(path: Path) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'Python',
        '.js': 'JavaScript', '.jsx': 'JavaScript', '.mjs': 'JavaScript',
        '.ts': 'TypeScript', '.tsx': 'TypeScript',
        '.rs': 'Rust',
        '.go': 'Go',
        '.java': 'Java',
        '.c': 'C', '.h': 'C',
        '.cpp': 'C++', '.hpp': 'C++', '.cc': 'C++',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell', '.bash': 'Shell',
        '.ps1': 'PowerShell',
        '.html': 'HTML',
        '.css': 'CSS', '.scss': 'SCSS',
        '.json': 'JSON',
        '.yaml': 'YAML', '.yml': 'YAML',
        '.toml': 'TOML',
        '.md': 'Markdown',
        '.sql': 'SQL',
    }
    return ext_map.get(path.suffix.lower(), 'Unknown')


def extract_python_info(content: str) -> Dict:
    """Extract information from Python source code."""
    imports = []
    exports = []
    classes = []
    functions = []

    # Find imports
    for match in re.finditer(r'^(?:from\s+(\S+)\s+)?import\s+(.+)$', content, re.MULTILINE):
        if match.group(1):
            imports.append(f"from {match.group(1)} import {match.group(2).strip()}")
        else:
            imports.append(f"import {match.group(2).strip()}")

    # Find classes
    for match in re.finditer(r'^class\s+(\w+)', content, re.MULTILINE):
        classes.append(match.group(1))

    # Find top-level functions
    for match in re.finditer(r'^def\s+(\w+)', content, re.MULTILINE):
        functions.append(match.group(1))

    # Find __all__ exports
    all_match = re.search(r'__all__\s*=\s*\[([^\]]+)\]', content)
    if all_match:
        exports = [x.strip().strip('"\'') for x in all_match.group(1).split(',')]

    return {'imports': imports, 'exports': exports, 'classes': classes, 'functions': functions}


def extract_rust_info(content: str) -> Dict:
    """Extract information from Rust source code."""
    imports = []
    exports = []
    structs = []
    functions = []

    # Find use statements
    for match in re.finditer(r'^use\s+(.+);', content, re.MULTILINE):
        imports.append(match.group(1).strip())

    # Find pub items (exports)
    for match in re.finditer(r'^pub\s+(?:fn|struct|enum|trait|mod)\s+(\w+)', content, re.MULTILINE):
        exports.append(match.group(1))

    # Find structs
    for match in re.finditer(r'^(?:pub\s+)?struct\s+(\w+)', content, re.MULTILINE):
        structs.append(match.group(1))

    # Find functions
    for match in re.finditer(r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', content, re.MULTILINE):
        functions.append(match.group(1))

    return {'imports': imports, 'exports': exports, 'classes': structs, 'functions': functions}


def extract_js_ts_info(content: str) -> Dict:
    """Extract information from JavaScript/TypeScript source code."""
    imports = []
    exports = []
    classes = []
    functions = []

    # Find imports
    for match in re.finditer(r'^import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content, re.MULTILINE):
        imports.append(match.group(1))
    for match in re.finditer(r'^import\s+[\'"]([^\'"]+)[\'"]', content, re.MULTILINE):
        imports.append(match.group(1))
    for match in re.finditer(r'require\([\'"]([^\'"]+)[\'"]\)', content):
        imports.append(match.group(1))

    # Find exports
    for match in re.finditer(r'^export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', content, re.MULTILINE):
        exports.append(match.group(1))

    # Find classes
    for match in re.finditer(r'^(?:export\s+)?class\s+(\w+)', content, re.MULTILINE):
        classes.append(match.group(1))

    # Find functions
    for match in re.finditer(r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', content, re.MULTILINE):
        functions.append(match.group(1))
    for match in re.finditer(r'^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', content, re.MULTILINE):
        functions.append(match.group(1))

    return {'imports': imports, 'exports': exports, 'classes': classes, 'functions': functions}


def extract_go_info(content: str) -> Dict:
    """Extract information from Go source code."""
    imports = []
    functions = []
    structs = []

    # Find imports
    single_import = re.finditer(r'^import\s+"([^"]+)"', content, re.MULTILINE)
    for match in single_import:
        imports.append(match.group(1))

    multi_import = re.search(r'import\s*\((.*?)\)', content, re.DOTALL)
    if multi_import:
        for line in multi_import.group(1).split('\n'):
            match = re.search(r'"([^"]+)"', line)
            if match:
                imports.append(match.group(1))

    # Find structs
    for match in re.finditer(r'^type\s+(\w+)\s+struct', content, re.MULTILINE):
        structs.append(match.group(1))

    # Find functions
    for match in re.finditer(r'^func\s+(?:\([^)]+\)\s+)?(\w+)', content, re.MULTILINE):
        functions.append(match.group(1))

    return {'imports': imports, 'exports': [], 'classes': structs, 'functions': functions}


def analyze_file(path: Path) -> FileAnalysis:
    """Analyze a source file and extract its structure."""
    language = detect_language(path)

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return FileAnalysis(path=path, language=language)

    # Extract based on language
    if language == 'Python':
        info = extract_python_info(content)
    elif language == 'Rust':
        info = extract_rust_info(content)
    elif language in ('JavaScript', 'TypeScript'):
        info = extract_js_ts_info(content)
    elif language == 'Go':
        info = extract_go_info(content)
    else:
        info = {'imports': [], 'exports': [], 'classes': [], 'functions': []}

    # Try to determine purpose from docstring or first comment
    purpose = ""
    if language == 'Python':
        doc_match = re.search(r'^"""(.+?)"""', content, re.DOTALL)
        if doc_match:
            purpose = doc_match.group(1).strip().split('\n')[0]
    elif language in ('JavaScript', 'TypeScript'):
        doc_match = re.search(r'^/\*\*(.+?)\*/', content, re.DOTALL)
        if doc_match:
            purpose = doc_match.group(1).strip().split('\n')[0].lstrip('* ')
    elif language == 'Rust':
        doc_match = re.search(r'^//!\s*(.+)$', content, re.MULTILINE)
        if doc_match:
            purpose = doc_match.group(1).strip()

    return FileAnalysis(
        path=path,
        language=language,
        imports=info.get('imports', []),
        exports=info.get('exports', []),
        classes=info.get('classes', []),
        functions=info.get('functions', []),
        purpose=purpose
    )


def analyze_codebase(files: List[Path]) -> List[FileAnalysis]:
    """Analyze all files in a codebase."""
    results = []
    for file_path in files:
        analysis = analyze_file(file_path)
        results.append(analysis)
    return results


if __name__ == "__main__":
    import sys
    from scanner import scan_codebase

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_results = scan_codebase(path)

    for file_path, _, _ in scan_results[:10]:  # Analyze first 10 files as demo
        analysis = analyze_file(file_path)
        print(f"\n{analysis.path}")
        print(f"  Language: {analysis.language}")
        print(f"  Purpose: {analysis.purpose or 'N/A'}")
        print(f"  Imports: {len(analysis.imports)}")
        print(f"  Classes: {', '.join(analysis.classes[:5]) or 'None'}")
        print(f"  Functions: {', '.join(analysis.functions[:5]) or 'None'}")
