# 🚀 Migration Guide: v3.x → v4.0

## 📋 Overview

Version 4.0 represents a **MAJOR** architectural shift in the KI AutoAgent system. This guide will help you migrate from v3.x to the new cognitive architecture.

## 🔴 Breaking Changes

### 1. Agent API Changes

#### Extended Agent Methods

All agents now require new analysis methods:

**ArchitectAgent**
```python
# NEW REQUIRED METHODS:
async def understand_system(self, root_path: str) -> Dict[str, Any]
async def analyze_infrastructure_improvements(self) -> str
async def generate_architecture_flowchart(self) -> str
```

**CodeSmithAgent**
```python
# NEW REQUIRED METHODS:
async def analyze_codebase(self, root_path: str) -> Dict[str, Any]
async def implement_with_patterns(self, spec: str) -> str
async def refactor_complex_code(self, file_path: str = None) -> List[Dict]
async def optimize_performance_hotspots(self) -> List[Dict]
async def cleanup_dead_code(self) -> str
```

### 2. Initialization Changes

Agents now require analysis tools during initialization:

```python
# OLD (v3.x)
architect = ArchitectAgent()

# NEW (v4.0)
architect = ArchitectAgent()  # Automatically initializes:
# - TreeSitterIndexer
# - CodeIndexer
# - SemgrepAnalyzer
# - VultureAnalyzer
# - RadonMetrics
# - DiagramService
```

### 3. System Knowledge Cache

Agents now maintain a system knowledge cache:

```python
# The system knowledge is automatically built on first use
architect.system_knowledge = await architect.understand_system()

# Cache includes:
# - code_index: Complete AST analysis
# - security: Vulnerability analysis
# - metrics: Code quality metrics
# - diagrams: Generated visualizations
```

### 4. Enhanced TaskResult

TaskResult now includes additional metadata:

```python
TaskResult(
    status="success",
    content=response,
    agent=agent_id,
    metadata={
        "metrics": {...},        # NEW: Code metrics
        "security_score": 85,    # NEW: Security assessment
        "patterns_used": [...],  # NEW: Applied patterns
        "diagrams": {...}        # NEW: Generated diagrams
    }
)
```

## 🟢 New Features

### 1. Infrastructure Analysis

Ask the system about improvements:
```python
response = await architect.analyze_infrastructure_improvements()
# Returns detailed analysis with concrete improvements
```

### 2. Pattern-Based Code Generation

Generate code that matches existing patterns:
```python
code = await codesmith.implement_with_patterns(spec)
# Uses learned patterns from codebase
```

### 3. Automatic Visualization

Generate architecture diagrams:
```python
diagram = await architect.generate_architecture_flowchart()
# Returns Mermaid diagram code
```

### 4. Security Scanning

Automatic security analysis:
```python
# Happens automatically during understand_system()
security_issues = architect.system_knowledge['security']
```

## 📦 New Dependencies

Install new requirements:
```bash
cd backend
pip install -r requirements.txt
```

New major dependencies:
- `tree-sitter` (>=0.21.0) - AST parsing
- `semgrep` (>=1.52.0) - Security analysis
- `radon` (>=6.0.1) - Code metrics
- `vulture` (>=2.11) - Dead code detection
- `mermaid-py` (>=0.5.0) - Diagram generation

## 🔧 Migration Steps

### Step 1: Update Dependencies

```bash
# Update all dependencies
cd backend
pip install --upgrade -r requirements.txt
```

### Step 2: Test New Capabilities

```bash
# Run test script
python test_system_understanding.py
```

### Step 3: Update Your Code

If you have custom agent implementations:

```python
# Add new required methods to your agents
class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        # Initialize new analysis tools
        self.tree_sitter = TreeSitterIndexer()
        self.code_indexer = CodeIndexer()

    async def understand_system(self, root_path='.'):
        # Implement system understanding
        return await self.code_indexer.build_full_index(root_path)
```

### Step 4: Update API Calls

If you're calling agents directly:

```python
# OLD WAY (v3.x)
result = await architect.execute(TaskRequest(prompt="Design system"))

# NEW WAY (v4.0) - with system understanding
await architect.understand_system()  # Build understanding first
result = await architect.execute(TaskRequest(prompt="Design system"))
```

## 🎯 Quick Start Example

```python
from agents.specialized.architect_agent import ArchitectAgent

# Initialize agent
architect = ArchitectAgent()

# Build system understanding (one-time)
system_knowledge = await architect.understand_system('.')
print(f"Analyzed {len(system_knowledge['code_index']['ast']['files'])} files")

# Now ask about improvements
improvements = await architect.analyze_infrastructure_improvements()
print(improvements)  # Detailed report with suggestions

# Generate architecture diagram
diagram = await architect.generate_architecture_flowchart()
print(diagram)  # Mermaid diagram code
```

## ⚠️ Common Issues

### Issue 1: Missing Dependencies
```
ImportError: No module named 'tree_sitter'
```
**Solution**: Install all requirements: `pip install -r backend/requirements.txt`

### Issue 2: System Knowledge Not Built
```
AttributeError: 'NoneType' object has no attribute 'get'
```
**Solution**: Call `understand_system()` before using analysis features

### Issue 3: Performance on Large Codebases
```
Indexing taking too long...
```
**Solution**: Use path filtering:
```python
await architect.understand_system('./src')  # Index only src directory
```

## 📚 Additional Resources

- [System Understanding Documentation](backend/SYSTEM_UNDERSTANDING_IMPLEMENTATION.md)
- [Test Script](backend/test_system_understanding.py)
- [CLAUDE.md](CLAUDE.md) - Version history and rules

## 🆘 Getting Help

If you encounter issues during migration:

1. Check the test script: `python backend/test_system_understanding.py`
2. Review generated reports in:
   - `infrastructure_report.md`
   - `architecture_flowchart.md`
   - `dead_code_cleanup.md`
3. Check agent logs for detailed error messages

## ✅ Migration Checklist

- [ ] Update to v4.0.0 in package.json
- [ ] Install new dependencies
- [ ] Run test script successfully
- [ ] Update custom agent implementations (if any)
- [ ] Test infrastructure analysis feature
- [ ] Review breaking changes
- [ ] Update API calls to use new methods

---

## 🎉 Welcome to KI AutoAgent v4.0!

The system now understands code like a senior developer. Enjoy the new cognitive capabilities!