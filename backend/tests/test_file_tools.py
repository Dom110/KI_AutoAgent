"""
Test File Tools

Unit tests for read_file, write_file, edit_file.

Usage:
    python backend/tests/test_file_tools.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.file_tools import read_file, write_file, edit_file


async def test_file_tools():
    """Test file tools (read, write, edit)"""

    print("\n" + "="*70)
    print("TEST: File Tools (read_file, write_file, edit_file)")
    print("="*70 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        print(f"📁 Workspace: {workspace_path}")

        # Test 1: Write file
        print("\n1. Testing write_file...")
        result = await write_file.ainvoke({
            "file_path": "test.txt",
            "content": "Hello World",
            "workspace_path": workspace_path
        })
        print(f"   Result: {result}")
        assert result["success"], "Write failed"
        assert result["bytes_written"] == 11, f"Expected 11 bytes, got {result['bytes_written']}"
        print("✅ write_file works")

        # Test 2: Read file
        print("\n2. Testing read_file...")
        result = await read_file.ainvoke({
            "file_path": "test.txt",
            "workspace_path": workspace_path
        })
        print(f"   Result: {result}")
        assert result["success"], "Read failed"
        assert result["content"] == "Hello World", f"Expected 'Hello World', got '{result['content']}'"
        print("✅ read_file works")

        # Test 3: Edit file
        print("\n3. Testing edit_file...")
        result = await edit_file.ainvoke({
            "file_path": "test.txt",
            "old_content": "Hello",
            "new_content": "Hi",
            "workspace_path": workspace_path
        })
        print(f"   Result: {result}")
        assert result["success"], "Edit failed"
        assert result["replacements"] == 1, f"Expected 1 replacement, got {result['replacements']}"
        print("✅ edit_file works")

        # Test 4: Verify edit
        print("\n4. Verifying edit...")
        result = await read_file.ainvoke({
            "file_path": "test.txt",
            "workspace_path": workspace_path
        })
        assert result["content"] == "Hi World", f"Expected 'Hi World', got '{result['content']}'"
        print("✅ Edit verified")

        # Test 5: Security - path outside workspace
        print("\n5. Testing security (path outside workspace)...")
        result = await write_file.ainvoke({
            "file_path": "../outside.txt",
            "content": "Should fail",
            "workspace_path": workspace_path
        })
        assert not result["success"], "Should reject path outside workspace"
        assert "outside workspace" in result["error"], "Should have security error"
        print("✅ Security check works")

        # Test 6: Write file with subdirectory
        print("\n6. Testing write with subdirectory creation...")
        result = await write_file.ainvoke({
            "file_path": "src/app/main.py",
            "content": "# Main file",
            "workspace_path": workspace_path
        })
        assert result["success"], "Write with subdirs failed"
        assert os.path.exists(os.path.join(workspace_path, "src/app/main.py")), "File not created"
        print("✅ Subdirectory creation works")

        print("\n" + "="*70)
        print("ALL FILE TOOLS TESTS PASSED! ✅")
        print("="*70 + "\n")

        return True


if __name__ == "__main__":
    success = asyncio.run(test_file_tools())
    sys.exit(0 if success else 1)
