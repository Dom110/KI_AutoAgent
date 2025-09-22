#!/usr/bin/env python3
"""
Test script for infrastructure analysis functionality
Tests the execution_time fixes and import guards
"""

import asyncio
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory for relative imports to work
original_dir = os.getcwd()
os.chdir(backend_path)

try:
    from agents.specialized.architect_agent import ArchitectAgent
    from agents.base.base_agent import TaskRequest
finally:
    os.chdir(original_dir)

async def test_infrastructure_analysis():
    """Test the infrastructure analysis feature"""
    print("🧪 Testing Infrastructure Analysis Feature...")
    print("-" * 60)

    # Initialize ArchitectAgent
    print("📦 Initializing ArchitectAgent...")
    architect = ArchitectAgent()

    # Check if analysis tools are available
    from agents.specialized.architect_agent import INDEXING_AVAILABLE, ANALYSIS_AVAILABLE, DIAGRAM_AVAILABLE

    print(f"✅ Code Indexing Available: {INDEXING_AVAILABLE}")
    print(f"✅ Analysis Tools Available: {ANALYSIS_AVAILABLE}")
    print(f"✅ Diagram Service Available: {DIAGRAM_AVAILABLE}")
    print("-" * 60)

    # Create test request
    request = TaskRequest(
        prompt="Was kann an der Infrastruktur verbessert werden?",
        context={
            "project_root": os.path.dirname(__file__),
            "test_mode": True
        }
    )

    try:
        print("🔍 Analyzing infrastructure improvements...")
        print("(This may take a moment as it analyzes the codebase...)")
        print("-" * 60)

        # Execute the analysis
        result = await architect.execute_with_memory(request)

        # Display results
        print("📊 Analysis Results:")
        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f} seconds")
        print(f"Agent: {result.agent}")

        if result.status == "success":
            print("\n🎯 Infrastructure Improvements Found:")
            print("-" * 60)
            # Show first 2000 chars of the response
            print(result.content[:2000])
            if len(result.content) > 2000:
                print(f"\n... (truncated, total {len(result.content)} characters)")
        else:
            print(f"\n❌ Error: {result.content}")

        # Test execution_time is properly set
        assert hasattr(result, 'execution_time'), "execution_time attribute missing!"
        assert result.execution_time >= 0, "execution_time should be non-negative!"
        print("\n✅ execution_time attribute properly set!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ Infrastructure analysis test completed successfully!")
    return True

async def test_basic_execution():
    """Test basic agent execution without analysis tools"""
    print("\n🧪 Testing Basic Agent Execution...")
    print("-" * 60)

    architect = ArchitectAgent()

    request = TaskRequest(
        prompt="Design a simple REST API architecture",
        context={}
    )

    try:
        result = await architect.execute_with_memory(request)

        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f} seconds")

        # Verify execution_time
        assert result.execution_time >= 0, "execution_time should be set!"
        print("✅ Basic execution works correctly!")

    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

    return True

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 KI AutoAgent v4.0.0 - Infrastructure Analysis Test Suite")
    print("=" * 60)

    # Test basic execution first
    basic_success = await test_basic_execution()

    # Then test infrastructure analysis
    if basic_success:
        analysis_success = await test_infrastructure_analysis()
    else:
        print("\n⚠️  Skipping infrastructure analysis test due to basic test failure")
        analysis_success = False

    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Basic Execution: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"  Infrastructure Analysis: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    print("=" * 60)

    if basic_success and analysis_success:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())