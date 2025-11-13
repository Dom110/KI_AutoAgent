# 🚨 KI AutoAgent Deprecation Management System

## Overview

The Deprecation Management System ensures that:
- ✅ **Obsolete modules are clearly marked** during development
- ✅ **Startup is BLOCKED** if critical deprecated code is imported
- ✅ **Developers see VISUAL warnings** when they try to use old APIs
- ✅ **Clear migration guides** are provided for every deprecated feature
- ✅ **Automatic import interception** catches deprecated imports at runtime

## Architecture

```
backend/deprecation/
├── __init__.py                 # Public API
├── registry.py                 # Central registry of deprecated modules
├── validator.py                # Runtime validator and import blocker
├── warnings.py                 # Visual warning system
└── migration_guides.py         # Migration documentation
```

## Severity Levels

### 🚫 CRITICAL
- **What happens:** Startup is **BLOCKED**
- **Use case:** Major architectural changes (v6 → v7 migration)
- **Example:** `workflow_v6_integrated.py`
- **Developer action:** **MUST update code** before server can start

### ⚠️ ERROR
- **What happens:** Server starts but **logs prominent warning**
- **Use case:** Important features removed but partial compatibility exists
- **Example:** `query_classifier_v6.py`
- **Developer action:** Should update code soon, but not required

### ℹ️ WARNING
- **What happens:** Server starts with **informational message**
- **Use case:** Features partially migrated
- **Example:** `approval_manager_v6.py`
- **Developer action:** Update when convenient

## How It Works

### 1. Startup Process (Automatic)

When you run `python start_server.py`:

```
Step 1: Check Python Version       ✅
Step 2: Check Environment          ✅
Step 3: Check Dependencies         ✅
Step 4: Check Port                 ✅
Step 5: Cleanup Port               ✅
Step 6: Full Diagnostics           ✅
Step 7: Deprecation Validation     ✅ ← NEW!
    • 12 deprecated modules registered
    • 4 CRITICAL (blocks if loaded)
    • 5 ERROR (warns loudly)
    • 3 WARNING (informational)
    • ✅ Import deprecation hook installed
```

### 2. Import Interception

The system automatically intercepts imports:

```python
# This will be BLOCKED at startup if it happens
from backend.workflow_v6_integrated import WorkflowV6Integrated

# Error output:
# ============================================================
# 🚫 CRITICAL DEPRECATION - STARTUP BLOCKED
# ============================================================
# 
# Module: backend.workflow_v6_integrated
# File: backend/workflow_v6_integrated.py
# Deprecated Since: v7.0.0
#
# Reason: Replaced by Pure MCP Architecture (workflow_v7_mcp.py)
# Replacement: backend.workflow_v7_mcp
#
# Features NOT in v7:
#   ❌ Query Classification (QueryClassifierV6)
#   ❌ Curiosity System (CuriositySystemV6)
#   ❌ [9 more features]
#
# Migration Effort: HARD
# Contact: team@ki-autoagent.dev
# ============================================================
```

### 3. Migration Guides

Each deprecated module has a specific migration guide:

```python
from backend.deprecation import get_migration_guide

guide = get_migration_guide("v6_to_v7_workflow")
print(guide)

# Output:
# 🔄 MIGRATION: workflow_v6_integrated.py → workflow_v7_mcp.py
# 
# OVERVIEW:
# The v6 workflow has been replaced with Pure MCP Architecture...
#
# MIGRATION STEPS:
# 1. REPLACE WORKFLOW INITIALIZATION
# 2. REPLACE QUERY EXECUTION
# 3. COGNITIVE SYSTEMS MIGRATION
# ... etc
```

## Using the Deprecation System

### For Developers

#### Check deprecation status:

```python
from backend.deprecation import DeprecationRegistry

registry = DeprecationRegistry()
summary = registry.get_summary()

print(f"Total deprecated: {summary['total_deprecated']}")
print(f"Critical: {summary['critical']}")
# Total deprecated: 12
# Critical: 4
```

#### Validate code before starting server:

```python
from backend.deprecation import DeprecationValidator

validator = DeprecationValidator()

# Check if a file can be imported
can_import = validator.validate_file_access("backend/workflow_v6_integrated.py")
# False (will block)

# Get detailed deprecation report
validator.print_deprecation_report()
```

#### Access migration guides programmatically:

```python
from backend.deprecation import get_migration_guide

guide = get_migration_guide("query_classifier_migration")
print(guide)
```

### For Integration Tests

```python
import pytest
from backend.deprecation import DeprecationValidator, DeprecationSeverity

def test_no_critical_deprecations_loaded():
    """Ensure no critical deprecated modules are loaded"""
    validator = DeprecationValidator()
    is_valid, error_msg = validator.check_startup_compatibility()
    
    assert is_valid, f"Critical deprecations found: {error_msg}"
```

### CLI Tool (Planned)

```bash
# Show deprecation report
python -m backend.deprecation report

# Check specific file
python -m backend.deprecation check backend/workflow_v6_integrated.py

# Show migration guide
python -m backend.deprecation migrate query_classifier_migration

# Watch for deprecated imports
python -m backend.deprecation watch
```

## Deprecated Modules

### Workflow
- ❌ **workflow_v6_integrated.py** (CRITICAL)
  - Reason: Replaced by Pure MCP Architecture
  - Migration: backend.workflow_v7_mcp

### Cognitive Systems
- ❌ **query_classifier_v6.py** (ERROR)
  - Reason: Classification now in SupervisorMCP
- ❌ **curiosity_system_v6.py** (CRITICAL)
  - Reason: Replaced by MCP agents
- ❌ **predictive_system_v6.py** (ERROR)
  - Reason: Replaced by MCP metrics
- ❌ **learning_system_v6.py** (ERROR)
  - Reason: Replaced by MCP Memory Server
- ❌ **neurosymbolic_reasoner_v6.py** (ERROR)
  - Reason: Replaced by distributed MCP reasoning
- ❌ **self_diagnosis_v6.py** (ERROR)
  - Reason: Replaced by MCP error handlers

### Tools & Security
- ❌ **tool_registry_v6.py** (ERROR)
  - Reason: Replaced by MCP server native tools
- ❌ **asimov_permissions_v6.py** (WARNING)
  - Reason: Partially migrated to v7

### Workflow Management
- ⚠️ **approval_manager_v6.py** (WARNING)
  - Reason: Partially migrated to v7
- ⚠️ **hitl_manager_v6.py** (WARNING)
  - Reason: Partially migrated to v7
- ⚠️ **workflow_adapter_v6.py** (WARNING)
  - Reason: Replaced by MCP agent adaptation

## Migration Checklist

### For Each Deprecated Module:

- [ ] Identify all imports in codebase
- [ ] Get migration guide: `get_migration_guide(key)`
- [ ] Update imports to v7 API
- [ ] Update test cases
- [ ] Run test suite to verify
- [ ] Remove old import statements
- [ ] Commit with clear message

### Example: Migrating workflow_v6_integrated

```bash
# 1. Find all imports
grep -r "from backend.workflow_v6_integrated import" .
grep -r "import.*workflow_v6_integrated" .

# 2. Get migration guide
python -c "from backend.deprecation import get_migration_guide; print(get_migration_guide('v6_to_v7_workflow'))"

# 3. Update imports in files:
#    OLD: from backend.workflow_v6_integrated import WorkflowV6Integrated
#    NEW: from backend.workflow_v7_mcp import WorkflowV7MCP

# 4. Run tests
pytest backend/tests/test_v7_complete_workflow.py

# 5. Verify server starts
python start_server.py --check-only

# 6. Commit
git commit -am "chore: migrate from workflow_v6_integrated to workflow_v7_mcp"
```

## Best Practices

### 1. When Adding Deprecation

```python
from backend.deprecation import DeprecationRegistry, DeprecationSeverity

# In registry.py:
self.register(DeprecatedModule(
    module_path="backend.my_old_module",
    file_path="backend/my_old_module.py",
    deprecated_since="v8.0.0",
    reason="Replaced by newer system X",
    replacement="backend.my_new_module",
    severity=DeprecationSeverity.ERROR,  # or CRITICAL, WARNING
    migration_effort="MEDIUM",
    migration_guide_key="my_module_migration",
))
```

### 2. When Creating Migration Guide

```python
def _guide_my_module_migration() -> str:
    return """
🔄 MIGRATION: my_old_module → my_new_module

OLD APPROACH (v7):
    [code example]
    
NEW APPROACH (v8):
    [code example]

MIGRATION BENEFITS:
[list benefits]
"""
```

### 3. In Your Code

```python
# ❌ DON'T: Silently use old APIs
from backend.workflow_v6_integrated import WorkflowV6Integrated

# ✅ DO: Migrate to v7 API
from backend.workflow_v7_mcp import WorkflowV7MCP
```

## Common Errors

### Error: "CRITICAL DEPRECATION - STARTUP BLOCKED"

**Solution:** Remove the deprecated import and migrate to v7 API

```python
# Find the problem import
grep -r "workflow_v6_integrated" .

# Get migration guide
python -c "from backend.deprecation import get_migration_guide; print(get_migration_guide('v6_to_v7_workflow'))"

# Update your code
```

### Error: "Import deprecation hook not installed"

**Solution:** Ensure deprecation validator is initialized before imports

```python
# In start_server.py (already done):
from backend.deprecation import DeprecationValidator
validator = DeprecationValidator()
validator.install_import_hook()  # Must be before imports
```

## Troubleshooting

### Q: How do I disable deprecation warnings?

**A:** You can't (by design). Deprecation warnings are critical for maintaining code quality. Instead:
- Follow the migration guides
- Update your code to use v7 APIs
- Contact team@ki-autoagent.dev if you have questions

### Q: Why is my import still blocked?

**A:** Check that:
1. You've updated all import statements
2. You've restarted the server
3. The import hook is installed (check startup logs)
4. The module name is exactly matching the registry

### Q: Can I use deprecated modules in tests?

**A:** Not recommended. Tests should use v7 APIs. If you need to test deprecated behavior:
```python
# Import the deprecated module directly (bypasses the hook)
import sys
sys.meta_path.remove(validator.blocker)
from backend.workflow_v6_integrated import WorkflowV6Integrated
```

## Next Steps

1. **Review** deprecated modules in your codebase
2. **Plan** migration timeline
3. **Execute** migrations using provided guides
4. **Test** thoroughly with v7 APIs
5. **Commit** with clear commit messages
6. **Document** any custom deprecations you add

## Support

For questions about:
- **Deprecation system:** Contact the team at team@ki-autoagent.dev
- **Specific migrations:** See corresponding migration guide in `migration_guides.py`
- **Code issues:** Check backend tests: `backend/tests/test_v7_*.py`

---

**Version:** 1.0.0  
**Last Updated:** 2025  
**Maintained by:** KI AutoAgent Team