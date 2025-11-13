#!/usr/bin/env python3
"""
🧪 SIMULATION: Codesmith Workspace Isolation (Option B)

Test Pattern for Isolated Code Generation Workspaces
=====================================================

Architecture: Client provides workspace_path, Server isolates subdirs
- Client: workspace_path = /home/user/projects/my_app
- Server: Creates isolated subdir → /home/user/projects/my_app/.codesmith/generation_001/
- Generation: Only happens in isolated subdir
- Cleanup: Client responsible (persistent workspaces)
- Execution: Sequential (one at a time)

This simulation tests:
1. ✅ Subdir creation with proper naming
2. ✅ File isolation (files stay in subdir)
3. ✅ Generation ID tracking
4. ✅ Cleanup methods available
5. ✅ Path validation & security
"""

import tempfile
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger("simulation_codesmith_ws")


class CodesmithWorkspaceManager:
    """
    Manages isolated workspaces for code generation (Option B Pattern)
    
    Architecture:
    - Client provides base workspace_path
    - Server creates isolated subdirs: .codesmith/generation_NNN/
    - All generated files stay in isolated subdir
    - Client responsible for cleanup (persistent)
    - Sequential execution (one generation at a time)
    
    Logging: [codesmith_ws] prefix for all workspace operations
    """
    
    def __init__(self, base_workspace_path: str):
        """
        Initialize workspace manager for a project
        
        Args:
            base_workspace_path: Client-provided workspace (e.g. /home/user/projects/app)
            
        Raises:
            ValueError: If path doesn't exist or not accessible
        """
        self.base_path = Path(base_workspace_path)
        self.codesmith_dir = self.base_path / ".codesmith"
        self.current_generation_id: Optional[str] = None
        self.current_generation_path: Optional[Path] = None
        
        logger.info(f"[codesmith_ws] Manager initialized")
        logger.info(f"[codesmith_ws] Base workspace: {self.base_path}")
        logger.info(f"[codesmith_ws] Codesmith dir: {self.codesmith_dir}")
        
        # Validate base path
        if not self.base_path.exists():
            raise ValueError(f"[codesmith_ws] Base path does not exist: {self.base_path}")
        
        if not self.base_path.is_dir():
            raise ValueError(f"[codesmith_ws] Base path is not a directory: {self.base_path}")
        
        logger.info(f"[codesmith_ws] ✅ Base path validated")
    
    async def create_isolated_generation(self) -> str:
        """
        Create isolated subdir for new code generation
        
        Pattern: .codesmith/generation_NNN/
        - NNN is timestamp-based ID (yymmdd_hhmmss)
        - Each generation is completely isolated
        - Files can be reviewed/deleted by client later
        
        Returns:
            generation_id: Unique ID for this generation
            
        Raises:
            OSError: If directory creation fails
        """
        # Create .codesmith directory if not exists
        self.codesmith_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[codesmith_ws] ✅ .codesmith directory ready")
        
        # Generate ID: timestamp-based (compact, sortable)
        now = datetime.now()
        generation_id = now.strftime("%y%m%d_%H%M%S")
        
        # Add UUID suffix for uniqueness (if multiple jobs in same second)
        unique_suffix = str(uuid.uuid4())[:8]
        generation_id = f"{generation_id}_{unique_suffix}"
        
        # Create isolated generation directory
        self.current_generation_path = self.codesmith_dir / generation_id
        self.current_generation_path.mkdir(parents=True, exist_ok=False)
        self.current_generation_id = generation_id
        
        logger.info(f"[codesmith_ws] 🆕 Generation created: {generation_id}")
        logger.info(f"[codesmith_ws] 📁 Path: {self.current_generation_path}")
        logger.info(f"[codesmith_ws] ✅ Isolation ready for code generation")
        
        return generation_id
    
    async def write_generated_file(self, relative_path: str, content: str) -> Path:
        """
        Write generated file to isolated workspace
        
        Security: relative_path cannot escape isolation directory
        
        Args:
            relative_path: Path relative to generation dir (e.g. "src/main.py")
            content: File content
            
        Returns:
            Absolute path to written file
            
        Raises:
            ValueError: If path tries to escape isolation (security check)
            OSError: If write fails
        """
        if not self.current_generation_path:
            raise RuntimeError("[codesmith_ws] No generation context - call create_isolated_generation first")
        
        # Security: Prevent path traversal
        # Note: resolve() on both paths to handle macOS symlink /var/folders -> /private/var/folders
        abs_path = (self.current_generation_path / relative_path).resolve()
        base_resolved = self.current_generation_path.resolve()
        
        if not str(abs_path).startswith(str(base_resolved)):
            raise ValueError(
                f"[codesmith_ws] ❌ SECURITY: Path escape attempt! "
                f"relative_path={relative_path} tries to escape {base_resolved}"
            )
        
        # Create parent directories
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        abs_path.write_text(content, encoding='utf-8')
        
        logger.debug(f"[codesmith_ws] ✍️ File written: {relative_path}")
        logger.debug(f"[codesmith_ws]    Size: {len(content)} bytes")
        
        return abs_path
    
    async def get_generation_info(self) -> Dict[str, Any]:
        """Get info about current generation"""
        if not self.current_generation_path:
            return {"status": "no_generation"}
        
        # Count files in generation
        file_count = sum(1 for _ in self.current_generation_path.rglob('*') if _.is_file())
        dir_count = sum(1 for _ in self.current_generation_path.rglob('*') if _.is_dir())
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in self.current_generation_path.rglob('*') if f.is_file())
        
        return {
            "generation_id": self.current_generation_id,
            "path": str(self.current_generation_path),
            "files": file_count,
            "directories": dir_count,
            "total_size_bytes": total_size,
            "base_workspace": str(self.base_path),
        }
    
    async def list_generations(self) -> list:
        """List all generations in this workspace"""
        if not self.codesmith_dir.exists():
            logger.info(f"[codesmith_ws] No generations yet")
            return []
        
        generations = sorted([
            d.name for d in self.codesmith_dir.iterdir() 
            if d.is_dir()
        ])
        
        logger.info(f"[codesmith_ws] Found {len(generations)} generation(s)")
        for gen_id in generations:
            gen_path = self.codesmith_dir / gen_id
            file_count = sum(1 for _ in gen_path.rglob('*') if _.is_file())
            logger.info(f"[codesmith_ws]   - {gen_id} ({file_count} files)")
        
        return generations
    
    async def cleanup_generation(self, generation_id: str) -> bool:
        """
        Manually cleanup a generation (client calls this)
        
        Args:
            generation_id: ID of generation to delete
            
        Returns:
            True if deleted, False if not found
        """
        gen_path = self.codesmith_dir / generation_id
        
        if not gen_path.exists():
            logger.warning(f"[codesmith_ws] ⚠️ Generation not found for cleanup: {generation_id}")
            return False
        
        # Recursive delete
        import shutil
        shutil.rmtree(gen_path)
        
        logger.info(f"[codesmith_ws] 🗑️ Cleaned up generation: {generation_id}")
        
        return True
    
    async def cleanup_all_generations(self) -> int:
        """Cleanup ALL generations (use with caution!)"""
        if not self.codesmith_dir.exists():
            return 0
        
        import shutil
        shutil.rmtree(self.codesmith_dir)
        
        count = len(self.codesmith_dir.glob('*')) if self.codesmith_dir.exists() else 0
        logger.info(f"[codesmith_ws] 🗑️ Cleaned up .codesmith directory")
        
        return count


async def test_scenario_1_basic_generation():
    """Test 1: Basic generation flow"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Basic Code Generation with Isolation")
    logger.info("="*80)
    
    with tempfile.TemporaryDirectory(prefix="test_codesmith_") as tmpdir:
        manager = CodesmithWorkspaceManager(tmpdir)
        
        # Step 1: Create isolated generation
        logger.info("\n[TEST] Step 1: Creating isolated generation...")
        gen_id = await manager.create_isolated_generation()
        logger.info(f"[TEST] ✅ Generation ID: {gen_id}")
        
        # Step 2: Write some code
        logger.info("\n[TEST] Step 2: Generating code files...")
        await manager.write_generated_file("src/main.py", 'print("Hello")')
        await manager.write_generated_file("src/utils.py", 'def util(): pass')
        await manager.write_generated_file("tests/test_main.py", 'def test(): pass')
        
        # Step 3: Get generation info
        logger.info("\n[TEST] Step 3: Generation info...")
        info = await manager.get_generation_info()
        logger.info(f"[TEST] Generation info: {json.dumps(info, indent=2)}")
        
        # Verify isolation: files exist in subdir, not in base
        assert (manager.current_generation_path / "src/main.py").exists()
        assert not (manager.base_path / "src/main.py").exists()
        logger.info("[TEST] ✅ Files properly isolated in subdir")
        
        logger.info("[TEST] ✅ TEST 1 PASSED\n")
        return True


async def test_scenario_2_security_path_traversal():
    """Test 2: Security - Prevent path traversal attacks"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Security - Path Traversal Prevention")
    logger.info("="*80)
    
    with tempfile.TemporaryDirectory(prefix="test_codesmith_") as tmpdir:
        manager = CodesmithWorkspaceManager(tmpdir)
        gen_id = await manager.create_isolated_generation()
        
        logger.info("\n[TEST] Attempting path traversal attack...")
        try:
            # Try to escape isolation
            await manager.write_generated_file("../../etc/passwd", "HACK")
            logger.error("[TEST] ❌ SECURITY FAILED - path traversal not blocked!")
            return False
        except ValueError as e:
            logger.info(f"[TEST] ✅ Attack blocked: {str(e)[:80]}...")
            logger.info("[TEST] ✅ TEST 2 PASSED\n")
            return True


async def test_scenario_3_multiple_generations():
    """Test 3: Multiple generations in same workspace"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Multiple Generations in Same Workspace")
    logger.info("="*80)
    
    with tempfile.TemporaryDirectory(prefix="test_codesmith_") as tmpdir:
        manager = CodesmithWorkspaceManager(tmpdir)
        
        logger.info("\n[TEST] Creating 3 generations...")
        gen_ids = []
        for i in range(3):
            gen_id = await manager.create_isolated_generation()
            gen_ids.append(gen_id)
            
            # Write different files to each
            await manager.write_generated_file(f"version_{i}.py", f"VERSION = {i}")
            await asyncio.sleep(1.1)  # Ensure different timestamps
        
        logger.info(f"\n[TEST] Listing all generations...")
        generations = await manager.list_generations()
        
        assert len(generations) == 3, f"Expected 3 generations, got {len(generations)}"
        logger.info(f"[TEST] ✅ All 3 generations isolated and listed")
        logger.info("[TEST] ✅ TEST 3 PASSED\n")
        return True


async def test_scenario_4_cleanup():
    """Test 4: Cleanup operations"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Cleanup Operations")
    logger.info("="*80)
    
    with tempfile.TemporaryDirectory(prefix="test_codesmith_") as tmpdir:
        manager = CodesmithWorkspaceManager(tmpdir)
        
        logger.info("\n[TEST] Creating 2 generations...")
        gen1 = await manager.create_isolated_generation()
        await manager.write_generated_file("file1.py", "# gen1")
        
        logger.info("\n[TEST] Creating second generation...")
        gen2 = await manager.create_isolated_generation()
        await manager.write_generated_file("file2.py", "# gen2")
        
        logger.info("\n[TEST] Listing before cleanup...")
        gens_before = await manager.list_generations()
        assert len(gens_before) == 2
        
        logger.info(f"\n[TEST] Cleaning up generation: {gen1}")
        result = await manager.cleanup_generation(gen1)
        assert result == True
        
        logger.info("\n[TEST] Listing after cleanup...")
        gens_after = await manager.list_generations()
        assert len(gens_after) == 1
        assert gen2 in gens_after
        assert gen1 not in gens_after
        
        logger.info("[TEST] ✅ Cleanup works correctly")
        logger.info("[TEST] ✅ TEST 4 PASSED\n")
        return True


async def main():
    """Run all simulation tests"""
    logger.info("\n" + "#"*80)
    logger.info("# 🧪 CODESMITH WORKSPACE ISOLATION SIMULATION (Option B)")
    logger.info("# Architecture: Client provides workspace, Server isolates subdirs")
    logger.info("#"*80)
    
    tests = [
        test_scenario_1_basic_generation,
        test_scenario_2_security_path_traversal,
        test_scenario_3_multiple_generations,
        test_scenario_4_cleanup,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"\n❌ Test failed with exception: {e}", exc_info=True)
            results.append(False)
    
    # Summary
    logger.info("\n" + "#"*80)
    logger.info("# 📊 SIMULATION SUMMARY")
    logger.info("#"*80)
    passed = sum(1 for r in results if r)
    total = len(results)
    logger.info(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED - Ready for production implementation!")
    else:
        logger.error(f"\n❌ FAILURES: {total - passed} tests failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
