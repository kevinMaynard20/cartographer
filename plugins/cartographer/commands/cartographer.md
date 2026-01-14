# /cartographer

Maps and documents codebases of any size by orchestrating parallel subagents. Creates comprehensive documentation in the `docs/` directory.

## Usage

```
/cartographer
```

## Output Files

The command generates the following files in `docs/`:

1. **CODEBASE_MAP.md** - Main architecture documentation
   - Project overview and purpose
   - Directory structure breakdown
   - Key files and their purposes
   - Module dependencies
   - Navigation guide

2. **DEPENDENCY_GRAPH.md** - Visual dependency graph
   - Mermaid diagram format
   - Module relationships
   - Import/export visualization

3. **SECURITY_SCAN.md** - Security concern flags
   - Hardcoded secrets detection
   - API key exposure warnings
   - Credential patterns
   - Insecure configurations

4. **TODO_INDEX.md** - Aggregated task markers
   - All TODO comments with locations
   - FIXME markers
   - HACK notes
   - Priority classification

5. **METRICS.md** - Code statistics
   - Lines of code per language
   - File counts by type
   - Directory size breakdown
   - Complexity indicators

## Workflow

1. **Scan Phase**: Discover all source files, respect .gitignore
2. **Analyze Phase**: Parse each file for structure and patterns
3. **Graph Phase**: Build dependency relationships
4. **Security Phase**: Scan for potential vulnerabilities
5. **Todo Phase**: Extract all task markers
6. **Metrics Phase**: Calculate statistics
7. **Synthesize Phase**: Generate markdown documentation

## Triggers

This skill activates when users say:
- "map this codebase"
- "analyze architecture"
- "document codebase"
- "create codebase map"
- "understand this codebase"

## Update Mode

If documentation already exists, Cartographer:
- Checks git history for changes since last mapping
- Re-analyzes only modified modules
- Merges updates with existing documentation
