# LangChain Version Pinning Documentation

**Date:** 2025-10-13
**Status:** CRITICAL - DO NOT MODIFY WITHOUT TESTING

---

## Overview

This document explains why LangChain/LangGraph package versions are strictly pinned in `backend/requirements.txt` and what issues can occur if versions are changed.

---

## Pinned Versions (v6.2-alpha)

```txt
# CRITICAL: Exact versions required - DO NOT use >= or ~ operators
langgraph==0.6.10
langchain==0.3.9
langchain-core==0.3.79
langchain-community==0.3.31
langchain-openai==0.2.10
langchain-anthropic==0.3.22
langgraph-checkpoint==2.0.7
langgraph-checkpoint-sqlite==2.0.11
anthropic==0.69.0
pydantic==2.11.9
```

---

## Why Strict Version Pinning?

### 1. Pydantic v2 Compatibility Issues

**Problem:** LangChain packages have complex dependencies on Pydantic v2 internal types that are not always forward-compatible.

**Specific Errors Encountered:**
- `ChatOpenAI is not fully defined; you should define 'BaseCache', then call 'ChatOpenAI.model_rebuild()'`
- `ChatOpenAI is not fully defined; you should define 'Callbacks', then call 'ChatOpenAI.model_rebuild()'`

**Why It Happens:**
- LangChain imports Pydantic models before all type annotations are available
- Pydantic v2 validates models more strictly than v1
- Circular dependency issues between langchain-core, langchain-openai, and pydantic

**Solution Applied:**
```python
# In workflow_planner_v6.py
# Import required type annotations BEFORE ChatOpenAI
from langchain_core.caches import BaseCache
from langchain_core.callbacks.manager import Callbacks

# Now ChatOpenAI can be imported safely
from langchain_openai import ChatOpenAI
```

### 2. LangGraph API Changes

**Problem:** LangGraph 0.2.x → 0.6.x had breaking changes in graph validation.

**Specific Error:**
- `ValueError: Node 'supervisor' is not reachable`

**Why It Happened:**
- LangGraph 0.6.x validates that all nodes must be reachable from entry point
- v6.2 architecture changed entry point from 'supervisor' to 'workflow_planning'
- Old supervisor node became unreachable

**Solution Applied:**
- Removed obsolete supervisor node from graph
- Updated to v6.2 architecture with workflow_planning as entry point

### 3. Anthropic SDK Updates

**Problem:** anthropic package updates must match langchain-anthropic version.

**Compatibility Matrix:**
```
langchain-anthropic==0.3.22 → requires anthropic>=0.69.0
langchain-anthropic==0.3.0  → works with anthropic==0.68.0
```

---

## Tested Configuration

### Environment
- **OS:** macOS (Darwin 25.0.0)
- **Python:** 3.13.8
- **Package Manager:** pip 24.0+

### Test Results
```
✅ Backend server starts successfully
✅ All v6 systems initialize without errors
✅ LangGraph workflow compiles successfully
✅ ChatOpenAI instantiates without Pydantic errors
✅ No "BaseCache not defined" errors
✅ No "Callbacks not defined" errors
✅ No "supervisor node not reachable" errors
```

---

## What NOT To Do

### ❌ DO NOT use version ranges:
```python
# WRONG - Will break compatibility
langchain-core>=0.3.21
langgraph~=0.6.0
langchain-anthropic>=0.3.0,<0.4.0
```

### ❌ DO NOT upgrade individually:
```bash
# WRONG - Can create version mismatches
pip install --upgrade langchain-core
pip install --upgrade langgraph
```

### ❌ DO NOT downgrade without testing:
```python
# WRONG - Old versions have Pydantic v1 dependencies
langgraph==0.2.45  # Incompatible with our Pydantic v2 setup
```

---

## How To Update Safely

### Step 1: Research Compatibility

Before updating, check:
1. LangChain changelog for breaking changes
2. Pydantic compatibility notes
3. Python version requirements

### Step 2: Test in Isolated Environment

```bash
# Create test venv
python3.13 -m venv test_venv
source test_venv/bin/activate

# Install new versions
pip install langchain-core==X.Y.Z langgraph==A.B.C

# Run compatibility tests
python -c "from langchain_openai import ChatOpenAI; ChatOpenAI()"
```

### Step 3: Update All Related Packages Together

```bash
# Update all langchain packages atomically
pip install --upgrade \
  langgraph==X.Y.Z \
  langchain-core==A.B.C \
  langchain-community==D.E.F \
  langchain-anthropic==G.H.I \
  anthropic==J.K.L
```

### Step 4: Run Full Test Suite

```bash
cd backend
source venv/bin/activate

# Start backend
python api/server_v6_integrated.py &

# Run tests
python tests/test_simple_websocket.py
python tests/e2e_comprehensive_v6_2.py
```

### Step 5: Update requirements.txt

Only after ALL tests pass:

```bash
# Freeze exact versions
pip freeze | grep -E "langchain|langgraph|anthropic|pydantic" > versions.txt

# Update requirements.txt with exact versions
# Add comments explaining why each version is pinned
```

---

## Troubleshooting

### Error: "BaseCache not fully defined"

**Cause:** langchain-core version mismatch or import order issue

**Fix:**
1. Verify langchain-core==0.3.79
2. Check import order in workflow_planner_v6.py
3. Ensure BaseCache is imported before ChatOpenAI

### Error: "Callbacks not defined"

**Cause:** Missing langchain_core.callbacks.manager import

**Fix:**
```python
from langchain_core.callbacks.manager import Callbacks
# Import BEFORE ChatOpenAI
```

### Error: "Node not reachable"

**Cause:** LangGraph graph structure issue or obsolete nodes

**Fix:**
1. Verify all nodes have incoming edges
2. Remove obsolete nodes (like old supervisor node)
3. Check entry point is correct

### Error: "anthropic version incompatible"

**Cause:** anthropic SDK version mismatch with langchain-anthropic

**Fix:**
```bash
# Check compatibility
pip show langchain-anthropic anthropic

# Update both together
pip install anthropic==0.69.0 langchain-anthropic==0.3.22
```

---

## Version History

### 2025-10-13: v6.2-alpha Update
- **Reason:** Pydantic v2 compatibility issues
- **Changes:**
  - langgraph: 0.2.45 → 0.6.10
  - langchain-core: 0.3.21 → 0.3.79
  - langchain-community: 0.3.8 → 0.3.31
  - langchain-anthropic: 0.3.0 → 0.3.22
  - langgraph-checkpoint-sqlite: 2.0.1 → 2.0.11
  - anthropic: 0.68.0 → 0.69.0
- **Commits:** 6700883, d8668c7

---

## Contact

If you need to update LangChain versions:
1. Read this document completely
2. Test in isolated environment first
3. Run full test suite
4. Document changes in commit message
5. Update this file with new version history

**NEVER** update LangChain versions without thorough testing!

---

## References

- LangChain Docs: https://python.langchain.com/docs/get_started/introduction
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- Pydantic v2 Migration: https://docs.pydantic.dev/latest/migration/
- Related Issues:
  - Commit 6700883: Pydantic v2 compatibility fix
  - Commit d8668c7: Requirements.txt version pinning
