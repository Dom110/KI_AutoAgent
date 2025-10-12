# Tree-Sitter Setup Guide (v6.2)

Tree-Sitter provides fast, incremental parsing for code analysis. This enables the Architect Agent to understand existing codebases and generate contextually appropriate architectures.

## Quick Install

```bash
# 1. Install tree-sitter core library
pip install tree-sitter

# 2. Install language parsers
pip install tree-sitter-python tree-sitter-javascript tree-sitter-typescript

# Optional: Additional languages
pip install tree-sitter-go tree-sitter-rust tree-sitter-java tree-sitter-c tree-sitter-cpp
```

## Verification

```bash
# Test if tree-sitter is available
python3 -c "import tree_sitter; print('tree-sitter version:', tree_sitter.__version__)"

# Test tree-sitter analyzer
python3 -c "from backend.utils.tree_sitter_analyzer import TREE_SITTER_AVAILABLE; print('Available:', TREE_SITTER_AVAILABLE)"
```

## Language Support

The Tree-Sitter analyzer currently supports:

| Language      | Extension          | Parser Package              |
|---------------|--------------------|-----------------------------|
| Python        | `.py`              | tree-sitter-python          |
| JavaScript    | `.js`, `.jsx`      | tree-sitter-javascript      |
| TypeScript    | `.ts`, `.tsx`      | tree-sitter-typescript      |
| Go            | `.go`              | tree-sitter-go              |
| Rust          | `.rs`              | tree-sitter-rust            |
| Java          | `.java`            | tree-sitter-java            |
| C             | `.c`, `.h`         | tree-sitter-c               |
| C++           | `.cpp`, `.hpp`     | tree-sitter-cpp             |

## Usage

### Architect Agent (Automatic)

The Architect subgraph automatically uses Tree-Sitter when available:

```python
# When tree-sitter is installed:
# - Analyzes workspace code structure
# - Extracts classes, functions, imports
# - Calculates complexity metrics
# - Provides detailed codebase summary to LLM

# When tree-sitter is NOT installed:
# - Falls back to basic file analysis
# - Continues workflow without errors
# - Logs warning with installation instructions
```

### Manual Analysis

```python
from backend.utils.tree_sitter_analyzer import TreeSitterAnalyzer

# Analyze workspace
analyzer = TreeSitterAnalyzer("/path/to/workspace")
result = analyzer.analyze_workspace(
    max_files=100,
    exclude_dirs=["node_modules", "venv", ".git"]
)

print(f"Analyzed {result.analyzed_files} files")
print(f"Languages: {result.languages}")
print(f"Total classes: {result.total_classes}")
print(f"Total functions: {result.total_functions}")
print(f"Average complexity: {result.avg_complexity:.1f}")

# Get markdown summary
summary = analyzer.get_codebase_summary(result)
print(summary)
```

### Analyze Single File

```python
# Analyze individual file
structure = analyzer.analyze_file("/path/to/file.py")

print(f"Classes: {len(structure.classes)}")
print(f"Functions: {len(structure.functions)}")
print(f"Imports: {len(structure.imports)}")
print(f"Complexity: {structure.complexity_score:.1f}")
```

## Features

### Code Structure Extraction

Tree-Sitter extracts:

- **Classes**: Class definitions with names and line numbers
- **Functions**: Function/method definitions
- **Imports**: Import statements and dependencies
- **Exports**: Export statements (JavaScript/TypeScript)

### Complexity Analysis

Simple heuristic based on:
- Nesting depth (penalizes deep nesting)
- Control flow branches (if/else)
- Loops (for/while)
- Exception handling (try/except)

Score: 0-100 (higher = more complex)

### Performance

- **Incremental parsing**: Fast re-parsing on edits
- **Max files limit**: Default 50 for Architect Agent (configurable)
- **Exclude patterns**: Skips common directories (node_modules, venv, etc.)

## Troubleshooting

### "tree-sitter not installed"

```bash
pip install tree-sitter
```

### "Language library not found"

Tree-Sitter requires compiled language grammars. Install language packages:

```bash
# Python
pip install tree-sitter-python

# JavaScript/TypeScript
pip install tree-sitter-javascript tree-sitter-typescript
```

### Language parser not loading

Check library locations:

```bash
# Common locations:
ls ~/.tree-sitter/lib/
ls /usr/local/lib/tree-sitter-*.so
ls /usr/lib/tree-sitter-*.so
```

If libraries are missing, reinstall language packages.

### Module import errors

Ensure backend is importable:

```bash
cd /path/to/KI_AutoAgent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 -c "from backend.utils.tree_sitter_analyzer import TreeSitterAnalyzer"
```

## Integration Points

### Architect Subgraph

File: `backend/subgraphs/architect_subgraph_v6_1.py`

Step 2: Codebase Analysis
- Initializes TreeSitterAnalyzer
- Analyzes workspace (max 50 files)
- Generates markdown summary
- Passes to Claude for architecture design

### Benefits

With Tree-Sitter:
- **Context-aware designs**: Architecture matches existing code style
- **Technology detection**: Automatically identifies tech stack
- **Complexity insights**: Suggests refactoring if needed
- **Dependency analysis**: Understands import relationships

Without Tree-Sitter:
- Still works (graceful degradation)
- Uses basic file analysis
- Less detailed architecture suggestions

## Example Output

```
# Codebase Analysis Summary

## Overview
**Workspace:** `/Users/.../MyProject`
**Files Analyzed:** 42 / 156
**Total Lines:** 8,432

## Languages
- **python**: 28 files
- **javascript**: 12 files
- **typescript**: 2 files

## Code Structure
- **Classes:** 45
- **Functions:** 234
- **Average Complexity:** 18.3/100

## Top Files
- `app.py` (python): 12 classes, 45 functions, complexity 42
- `server.js` (javascript): 3 classes, 28 functions, complexity 35
- `utils.py` (python): 0 classes, 67 functions, complexity 28
```

This summary is provided to Claude for architecture design, resulting in more accurate and contextually appropriate recommendations.

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Semantic code search
- [ ] Refactoring suggestions
- [ ] Dependency graph visualization
- [ ] Code smell detection
- [ ] Test coverage analysis
- [ ] Security vulnerability scanning

## References

- Tree-Sitter Documentation: https://tree-sitter.github.io/tree-sitter/
- Tree-Sitter Python: https://github.com/tree-sitter/py-tree-sitter
- Language Grammars: https://github.com/tree-sitter

## Version

**Tree-Sitter Integration:** v6.2.0
**Added:** 2025-10-12
**Status:** Production Ready (with graceful degradation)
