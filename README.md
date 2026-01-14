# Cartographer - Claude Code Plugin

Enhanced codebase mapping plugin for Claude Code that generates comprehensive documentation about your codebase.

## Features

- **CODEBASE_MAP.md** - Full architecture documentation with file purposes, dependencies, and navigation
- **DEPENDENCY_GRAPH.md** - Visual dependency graph in Mermaid format
- **SECURITY_SCAN.md** - Flags potential security concerns (hardcoded secrets, API keys, etc.)
- **TODO_INDEX.md** - Aggregates all TODOs, FIXMEs, and HACKs found in the codebase
- **METRICS.md** - Lines of code, file counts, and language breakdown

## Installation

```bash
# Clone the repository
git clone https://github.com/kmaynardrpp/cartographer.git

# Or install via Claude Code
/plugin install cartographer@kmaynardrpp
```

## Usage

Run the cartographer command in Claude Code:

```
/cartographer
```

This will analyze your codebase and generate documentation in the `docs/` directory.

## Output Files

All output files are generated in your project's `docs/` directory:

| File | Description |
|------|-------------|
| `CODEBASE_MAP.md` | Main architecture documentation |
| `DEPENDENCY_GRAPH.md` | Mermaid dependency visualization |
| `SECURITY_SCAN.md` | Security concern flags |
| `TODO_INDEX.md` | Aggregated TODO/FIXME/HACK comments |
| `METRICS.md` | Code statistics and metrics |

## Requirements

- Python 3.8+
- tiktoken (for token counting)

```bash
pip install tiktoken
```

## License

MIT License - See LICENSE for details.

## Author

kmaynardrpp
