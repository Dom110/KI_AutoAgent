# 🚨 Deprecation Management System - Quick Start Guide

## 📊 What's New?

The KI AutoAgent now has a **Production-Grade Deprecation Management System** that:

- ✅ **Blocks startup** if CRITICAL deprecated modules are imported
- ✅ **Shows visual warnings** for ERROR-level deprecations
- ✅ **Provides migration guides** for every deprecated feature
- ✅ **Automatically intercepts imports** to prevent old code usage

---

## 🚀 For Developers: Using the System

### 1. Check Deprecation Status

**Show full deprecation report:**
```bash
python -m backend.deprecation report
```

**List all deprecated modules:**
```bash
python -m backend.deprecation list
```

### 2. Get Migration Help

**See all available migration guides:**
```bash
python -m backend.deprecation migrate
```

**Get specific migration guide:**
```bash
python -m backend.deprecation migrate v6_to_v7_workflow
```

### 3. Check Startup Compatibility

**Before starting server, verify deprecation status:**
```bash
python -m backend.deprecation check
python start_server.py --check-only
```

### 4. Programmatic Usage

```python
from backend.deprecation import (
    get_registry,
    DeprecationValidator,
    get_migration_guide,
)

# Check status
registry = get_registry()
summary = registry.get_summary()
print(f"Critical deprecations: {summary['critical']}")

# Validate code
validator = DeprecationValidator()
is_valid, error = validator.check_startup_compatibility()

# Get migration guide
guide = get_migration_guide("v6_to_v7_workflow")
print(guide)
```

---

## 📋 Deprecated Modules Overview

### 🚫 CRITICAL (Blocks Startup)
These will **prevent the server from starting** if imported:

| Module | File | Replacement |
|--------|------|-------------|
| `backend.workflow_v6_integrated` | workflow_v6_integrated.py | workflow_v7_mcp.py |
| `backend.cognitive.query_classifier_v6` | query_classifier_v6.py | SupervisorMCP |
| `backend.cognitive.curiosity_system_v6` | curiosity_system_v6.py | MCP Agents |

**Action:** Update your code immediately if you get startup errors.

### ⚠️ ERROR (Warns Loudly)
These allow startup but log **prominent warnings**:

| Module | Reason |
|--------|--------|
| predictive_system_v6.py | → Use MCP metrics |
| learning_system_v6.py | → Use MCP Memory Server |
| neurosymbolic_reasoner_v6.py | → Use distributed MCP reasoning |
| self_diagnosis_v6.py | → Use MCP error handlers |
| tool_registry_v6.py | → Use MCP server native tools |

**Action:** Update soon to eliminate warnings.

### ℹ️ WARNING (Informational)
These are partially migrated but still supported:

| Module | Status |
|--------|--------|
| approval_manager_v6.py | Partially migrated to v7 |
| hitl_manager_v6.py | Partially migrated to v7 |
| workflow_adapter_v6.py | Replaced by MCP agents |
| asimov_permissions_v6.py | Partially migrated to v7 |

**Action:** Update when convenient.

---

## 🔄 Migration Workflow

### Step-by-Step for Each Deprecated Module:

1. **Identify** where the old code is used:
   ```bash
   grep -r "workflow_v6_integrated" .
   ```

2. **Get migration guide**:
   ```bash
   python -m backend.deprecation migrate v6_to_v7_workflow
   ```

3. **Update imports**:
   ```python
   # OLD
   from backend.workflow_v6_integrated import WorkflowV6Integrated
   
   # NEW
   from backend.workflow_v7_mcp import WorkflowV7MCP
   ```

4. **Update usage**:
   ```python
   # OLD
   workflow = WorkflowV6Integrated(workspace_path="...")
   
   # NEW
   from backend.utils.mcp_manager import MCPManager
   mcp_manager = MCPManager()
   workflow = WorkflowV7MCP(mcp_manager=mcp_manager)
   ```

5. **Test thoroughly**:
   ```bash
   pytest backend/tests/test_v7_complete_workflow.py
   ```

6. **Verify startup**:
   ```bash
   python start_server.py --check-only
   ```

7. **Commit with clear message**:
   ```bash
   git commit -am "chore: migrate from workflow_v6_integrated to workflow_v7_mcp"
   ```

---

## 🛠️ Common Scenarios

### Scenario 1: Server Won't Start - CRITICAL Deprecation

**Error:**
```
🚫 CRITICAL DEPRECATION - STARTUP BLOCKED
Module: backend.workflow_v6_integrated
This module is CRITICAL deprecated as of v7.0.0
Cannot start server while using deprecated critical modules
```

**Fix:**
```bash
# 1. Find the import
grep -r "workflow_v6_integrated" .

# 2. Get migration guide
python -m backend.deprecation migrate v6_to_v7_workflow

# 3. Update the code (see guide)

# 4. Restart server
python start_server.py
```

### Scenario 2: Warnings During Startup

**Message:**
```
⚠️  ERROR-LEVEL DEPRECATIONS (Warn loudly)
   • backend.cognitive.learning_system_v6
     Reason: Learning now handled by MCP Memory Server
```

**Fix:**
```bash
# Not urgent, but should be fixed
python -m backend.deprecation migrate learning_system_migration
# Follow the guide to update your code
```

### Scenario 3: Check Before Development

**Command:**
```bash
python -m backend.deprecation check
```

**Output if clean:**
```
✅ All deprecation checks passed
   Server can start successfully
```

---

## 📚 Migration Guides Available

| Key | Module | Effort | Time |
|-----|--------|--------|------|
| v6_to_v7_workflow | workflow_v6_integrated | HARD | 2-4h |
| query_classifier_migration | query_classifier_v6 | MEDIUM | 1-2h |
| curiosity_system_migration | curiosity_system_v6 | HARD | 2-3h |
| predictive_system_migration | predictive_system_v6 | MEDIUM | 1-2h |
| learning_system_migration | learning_system_v6 | MEDIUM | 1-2h |
| neurosymbolic_reasoner_migration | neurosymbolic_reasoner_v6 | HARD | 2-3h |
| self_diagnosis_migration | self_diagnosis_v6 | MEDIUM | 1-2h |
| tool_registry_migration | tool_registry_v6 | MEDIUM | 1-2h |
| approval_manager_migration | approval_manager_v6 | EASY | <1h |
| hitl_manager_migration | hitl_manager_v6 | EASY | <1h |
| workflow_adapter_migration | workflow_adapter_v6 | MEDIUM | 1-2h |
| asimov_rules_migration | asimov_permissions_v6 | EASY | <1h |

---

## 🔧 Advanced Usage

### Installing Import Hook Programmatically

```python
from backend.deprecation import DeprecationValidator

validator = DeprecationValidator()
validator.install_import_hook()  # Now catches deprecated imports

# This will now be blocked/warned:
# from backend.workflow_v6_integrated import WorkflowV6Integrated
```

### Validating File Access

```python
from backend.deprecation import DeprecationValidator

validator = DeprecationValidator()
can_import = validator.validate_file_access("backend/workflow_v6_integrated.py")
# False - this file is CRITICAL deprecated
```

### Checking Startup Compatibility

```python
from backend.deprecation import DeprecationValidator

validator = DeprecationValidator()
is_valid, error_msg = validator.check_startup_compatibility()

if not is_valid:
    print(f"Cannot start: {error_msg}")
    # Fix the deprecated imports and try again
```

---

## 🧪 Testing with Deprecation System

### Example Test

```python
import pytest
from backend.deprecation import DeprecationValidator

def test_no_critical_deprecations():
    """Ensure server can start without critical deprecations"""
    validator = DeprecationValidator()
    is_valid, error_msg = validator.check_startup_compatibility()
    
    assert is_valid, f"Critical deprecations found: {error_msg}"
```

### Running Tests

```bash
pytest backend/tests/test_deprecation_check.py
```

---

## 📖 Full Documentation

For comprehensive documentation, see:

```bash
cat backend/deprecation/DEPRECATION_SYSTEM.md
```

---

## ❓ FAQ

### Q: Can I ignore CRITICAL deprecations?

**A:** No. They will block the server from starting. You must update your code to use v7 APIs.

### Q: Why is my old code being blocked?

**A:** To ensure code quality and prevent security issues. The new v7 APIs are better maintained and more secure.

### Q: How do I migrate my code?

**A:** Follow the migration guides:
```bash
python -m backend.deprecation migrate <key>
```

### Q: What if I need the old functionality?

**A:** The v7 APIs have equivalent functionality. The migration guides show you how to use the new APIs to achieve the same results.

### Q: Can I disable the deprecation system?

**A:** Not recommended. But if you need to, you can manually remove the import hook (see advanced usage).

---

## 🆘 Getting Help

1. **Check the migration guide**: `python -m backend.deprecation migrate <key>`
2. **Review the documentation**: `cat backend/deprecation/DEPRECATION_SYSTEM.md`
3. **Check test examples**: `grep -r "workflow_v7_mcp" backend/tests/`
4. **Contact team**: team@ki-autoagent.dev

---

## 📊 Current Deprecation Status

```bash
python -m backend.deprecation report
```

**Summary (as of now):**
- Total deprecated: 12 modules
- CRITICAL: 3 (blocks startup)
- ERROR: 5 (warns loudly)
- WARNING: 4 (informational)

---

## ✅ Checklist: Before Starting Server

- [ ] Reviewed deprecated modules list: `python -m backend.deprecation list`
- [ ] Checked startup compatibility: `python -m backend.deprecation check`
- [ ] No CRITICAL deprecations in my code
- [ ] Updated old imports to v7 APIs
- [ ] Tests pass: `pytest backend/tests/`
- [ ] Server starts: `python start_server.py --check-only`
- [ ] Ready to launch: `python start_server.py`

---

**Version:** 1.0.0  
**Last Updated:** 2025  
**Maintained by:** KI AutoAgent Team