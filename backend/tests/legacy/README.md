# Legacy Tests Archive

**Date Archived:** 2025-10-13
**Reason:** Tests from v6.0/v6.1, superseded by v6.2 architecture

These tests are kept for reference but are not actively maintained or run in CI/CD.

## E2E Tests
- Old E2E workflows from v6.0/v6.1
- Superseded by `test_workflow_planner_e2e.py` (v6.2)
- Still functional but use deprecated architecture

## Unit Tests
- Old memory and checkpoint tests from v6.0
- Superseded by v6.2 memory manager tests
- May still be useful for debugging

## Native Tests
- Manual review workflows with playground
- Archived due to manual intervention requirements
- 953 lines of comprehensive 4-phase testing

## Migration Notes

If you need to run these tests:
1. They may require old imports (e.g., `workflow_v6.py` instead of `workflow_v6_integrated.py`)
2. Update imports to current v6.2 architecture
3. Some tests require manual intervention (native tests)
4. Check API key requirements
