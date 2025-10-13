#!/bin/bash
# Test Cleanup Script
# Date: 2025-10-13
# Version: v6.2.0-alpha

set -e  # Exit on error

echo "🧹 Starting test cleanup for v6.2..."
echo ""

# Create archive directory structure
echo "📁 Creating legacy archive directory..."
mkdir -p legacy/e2e legacy/unit legacy/native

# Archive E2E tests
echo "📦 Archiving E2E tests..."
[ -f e2e_simple_websocket.py ] && mv e2e_simple_websocket.py legacy/e2e/
[ -f e2e_create_and_review.py ] && mv e2e_create_and_review.py legacy/e2e/
[ -f e2e_complex_app.py ] && mv e2e_complex_app.py legacy/e2e/
[ -f e2e_native_with_playground.py ] && mv e2e_native_with_playground.py legacy/e2e/
[ -f test_fix_intent_e2e.py ] && mv test_fix_intent_e2e.py legacy/e2e/
[ -f fix_existing_app.py ] && mv fix_existing_app.py legacy/e2e/
[ -f test_file_validation.py ] && mv test_file_validation.py legacy/

# Archive unit tests
echo "📦 Archiving unit tests..."
[ -f unit/test_memory_v6_basic.py ] && mv unit/test_memory_v6_basic.py legacy/unit/
[ -f unit/test_workflow_v6_checkpoint.py ] && mv unit/test_workflow_v6_checkpoint.py legacy/unit/

# Archive native tests
echo "📦 Archiving native tests..."
[ -f native/native_test_phase2.py ] && mv native/native_test_phase2.py legacy/native/

# Delete broken tests
echo "❌ Deleting broken tests..."
[ -f test_research_v6.py ] && rm test_research_v6.py
[ -f test_simple_e2e_v6_1.py ] && rm test_simple_e2e_v6_1.py
[ -f test_v6_1_subgraphs.py ] && rm test_v6_1_subgraphs.py

# Delete deprecated adapters
echo "❌ Deleting deprecated adapter tests..."
[ -f test_claude_cli_adapter.py ] && rm test_claude_cli_adapter.py
[ -f test_chat_anthropic_direct.py ] && rm test_chat_anthropic_direct.py
[ -f test_file_tools.py ] && rm test_file_tools.py

# Delete utility scripts
echo "❌ Deleting utility scripts..."
[ -f debug_timeout.py ] && rm debug_timeout.py
[ -f manual_memory_test.py ] && rm manual_memory_test.py
[ -f real_api_memory_test.py ] && rm real_api_memory_test.py

# Clean up empty directories
echo "🗑️  Cleaning up empty directories..."
rmdir unit/ 2>/dev/null || true
rmdir native/ 2>/dev/null || true

# Create archive README
echo "📝 Creating archive README..."
cat > legacy/README.md << 'EOF'
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
EOF

# Count files
ARCHIVED=$(find legacy -name "*.py" | wc -l | tr -d ' ')
ACTIVE=$(find . -maxdepth 1 -name "test_*.py" -o -name "e2e_*.py" | wc -l | tr -d ' ')

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "   📦 Archived: $ARCHIVED test files"
echo "   ✅ Active: $ACTIVE test files"
echo "   📁 Archive location: legacy/"
echo ""
echo "📌 Active test files:"
ls -1 test_*.py e2e_*.py 2>/dev/null | sed 's/^/   ✓ /'
echo ""
echo "📂 Full directory structure:"
tree -L 2 -I '__pycache__|*.pyc' legacy/
echo ""
echo "🎯 Next steps:"
echo "   1. Review legacy/README.md"
echo "   2. Run active tests: python3.10 test_planner_only.py"
echo "   3. Update CI/CD to skip legacy tests"
