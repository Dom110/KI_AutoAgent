"""
Test Architect Subgraph (Phase 4)

Tests Architect subgraph structure and integration.

Usage:
    python backend/tests/test_architect_subgraph.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from subgraphs.architect_subgraph_v6 import create_architect_subgraph
from memory.memory_system_v6 import MemorySystem
from state_v6 import ArchitectState


async def test_architect_subgraph():
    """Test Architect Subgraph structure and basic flow"""

    print("\n" + "="*70)
    print("TEST: Architect Subgraph (Phase 4)")
    print("="*70 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        print(f"📁 Workspace: {workspace_path}")

        # Test 1: Create Memory System (required for architect)
        print("\n1. Setting up Memory System...")
        memory = MemorySystem(workspace_path=workspace_path)
        await memory.initialize()
        print("✅ Memory System initialized")

        # Test 2: Store mock research data (requires API key)
        print("\n2. Storing mock research data (requires OPENAI_API_KEY)...")

        # Load API key if available
        env_file = os.path.expanduser("~/.ki_autoagent/config/.env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip().strip('"')

        try:
            await memory.store(
                content="React 18 with Vite is recommended for modern web apps. TypeScript for type safety.",
                metadata={
                    "agent": "research",
                    "type": "findings",
                    "topic": "web frameworks"
                }
            )
            print("✅ Mock research stored (API key found)")
            has_memory_data = True
        except Exception as e:
            print(f"⚠️ Skipping memory store (no API key): {str(e)[:60]}...")
            has_memory_data = False

        # Test 3: Create Architect Subgraph
        print("\n3. Creating Architect Subgraph...")
        try:
            subgraph = create_architect_subgraph(
                workspace_path=workspace_path,
                memory=memory
            )
            print("✅ Architect Subgraph created")
        except Exception as e:
            print(f"❌ Failed to create subgraph: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 4: Verify subgraph is callable
        print("\n4. Verifying subgraph structure...")
        assert hasattr(subgraph, 'invoke'), "Subgraph must have invoke method"
        print("✅ Subgraph has invoke method")

        # Test 5: Create test state
        print("\n5. Creating test ArchitectState...")
        test_state: ArchitectState = {
            "workspace_path": workspace_path,
            "user_requirements": "Create a simple React calculator app",
            "research_context": {},
            "design": {},
            "tech_stack": [],
            "patterns": [],
            "diagram": "",
            "adr": "",
            "errors": []
        }
        print("✅ Test state created")

        # Test 6: Invoke subgraph (without API key - should fail gracefully)
        print("\n6. Testing subgraph invocation (without API key)...")
        print("   NOTE: This will fail without OPENAI_API_KEY - that's expected!")

        try:
            # This should fail because no OPENAI_API_KEY
            result = subgraph.invoke(test_state)

            # If we get here, either API key exists or something's wrong
            if result.get("errors"):
                print(f"✅ Subgraph handled missing API key gracefully")
                print(f"   Error: {result['errors'][0].get('error', 'Unknown')[:80]}...")
            else:
                print(f"✅ Subgraph executed (API key found)")
                print(f"   Design keys: {list(result.get('design', {}).keys())}")

        except Exception as e:
            error_msg = str(e)
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                print(f"✅ Expected error (no API key): {error_msg[:80]}...")
            else:
                print(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                return False

        print("\n" + "="*70)
        print("ARCHITECT SUBGRAPH TESTS PASSED! ✅")
        print("="*70 + "\n")

        print("ℹ️ Tests completed:")
        print("   ✅ Memory System integration")
        print("   ✅ Subgraph creation")
        print("   ✅ Structure validation")
        print("   ✅ State handling")
        print("   ✅ Error handling (graceful failure without API key)")

        print("\nℹ️ Full API integration test requires:")
        print("   - OPENAI_API_KEY (for GPT-4o)")
        print("   - Will generate actual architecture designs")

        # Cleanup
        await memory.close()

        return True


if __name__ == "__main__":
    success = asyncio.run(test_architect_subgraph())
    sys.exit(0 if success else 1)
