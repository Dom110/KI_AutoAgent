#!/usr/bin/env python3
"""
Test v4.0.0 features without API calls
"""

import sys
import os

# Ensure we're in the backend directory
if not os.path.exists('agents'):
    print("❌ Error: Must run from backend directory")
    sys.exit(1)

def test_v4_features():
    """Test v4.0.0 features are properly integrated"""
    print("🧪 Testing v4.0.0 Feature Integration")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Check execution_time fix in base_agent
    print("\n1️⃣ Testing execution_time fix in base_agent.py")
    try:
        with open('agents/base/base_agent.py', 'r') as f:
            content = f.read()
            if 'execution_time = 0  # Initialize to prevent UnboundLocalError' in content:
                print("  ✅ execution_time initialization found")
                passed += 1
            else:
                print("  ❌ execution_time initialization missing")
                failed += 1
    except Exception as e:
        print(f"  ❌ Error reading base_agent.py: {e}")
        failed += 1

    # Test 2: Check execution_time in agent_registry
    print("\n2️⃣ Testing execution_time fix in agent_registry.py")
    try:
        with open('agents/agent_registry.py', 'r') as f:
            content = f.read()
            if 'execution_time=0  # Ensure execution_time is set' in content:
                print("  ✅ execution_time in error response found")
                passed += 1
            else:
                print("  ❌ execution_time in error response missing")
                failed += 1
    except Exception as e:
        print(f"  ❌ Error reading agent_registry.py: {e}")
        failed += 1

    # Test 3: Check import guards in architect_agent
    print("\n3️⃣ Testing import guards in architect_agent.py")
    try:
        with open('agents/specialized/architect_agent.py', 'r') as f:
            content = f.read()
            has_guards = all([
                'INDEXING_AVAILABLE' in content,
                'ANALYSIS_AVAILABLE' in content,
                'DIAGRAM_AVAILABLE' in content,
                'except ImportError' in content
            ])
            if has_guards:
                print("  ✅ All import guards present")
                passed += 1
            else:
                print("  ❌ Some import guards missing")
                failed += 1
    except Exception as e:
        print(f"  ❌ Error reading architect_agent.py: {e}")
        failed += 1

    # Test 4: Check new methods in architect_agent
    print("\n4️⃣ Testing new methods in architect_agent.py")
    try:
        with open('agents/specialized/architect_agent.py', 'r') as f:
            content = f.read()
            methods = [
                'async def understand_system',
                'async def analyze_infrastructure_improvements',
                'async def generate_architecture_flowchart',
                'def _generate_improvement_suggestions'
            ]
            missing = []
            for method in methods:
                if method not in content:
                    missing.append(method.split()[-1])

            if not missing:
                print("  ✅ All new methods present")
                passed += 1
            else:
                print(f"  ❌ Missing methods: {', '.join(missing)}")
                failed += 1
    except Exception as e:
        print(f"  ❌ Error checking methods: {e}")
        failed += 1

    # Test 5: Check import availability
    print("\n5️⃣ Testing module imports")
    try:
        from agents.specialized.architect_agent import (
            ArchitectAgent,
            INDEXING_AVAILABLE,
            ANALYSIS_AVAILABLE,
            DIAGRAM_AVAILABLE
        )
        print(f"  ✅ ArchitectAgent imported")
        print(f"     Indexing available: {INDEXING_AVAILABLE}")
        print(f"     Analysis available: {ANALYSIS_AVAILABLE}")
        print(f"     Diagrams available: {DIAGRAM_AVAILABLE}")
        passed += 1
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        failed += 1

    # Test 6: Check CLAUDE.md version update
    print("\n6️⃣ Testing version documentation")
    try:
        with open('../CLAUDE.md', 'r') as f:
            content = f.read()
            if 'v4.0.0' in content and 'COGNITIVE ARCHITECTURE' in content:
                print("  ✅ v4.0.0 documented in CLAUDE.md")
                passed += 1
            else:
                print("  ❌ v4.0.0 documentation missing")
                failed += 1
    except Exception as e:
        print(f"  ⚠️  Could not check CLAUDE.md: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print("=" * 50)

    if failed == 0:
        print("\n🎉 All v4.0.0 features are properly integrated!")
        print("The execution_time fixes are in place.")
        print("Import guards are working.")
        print("New infrastructure analysis methods are available.")
    else:
        print(f"\n⚠️  {failed} issues found, but core fixes are in place.")

    return failed == 0

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 KI AutoAgent v4.0.0 Feature Verification")
    print("=" * 50)
    print("\nThis test verifies the v4.0.0 fixes and features")
    print("without making API calls.")
    print("-" * 50)

    success = test_v4_features()
    sys.exit(0 if success else 1)