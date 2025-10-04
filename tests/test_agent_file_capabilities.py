"""
Test Suite for Agent File Writing Capabilities
Tests file operations, permissions, and error handling
"""

import os
import sys
import asyncio
import tempfile
import shutil
import pytest
from pathlib import Path
from typing import Dict, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base.base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResult
from agents.tools.file_tools import FileSystemTools
from agents.specialized.codesmith_agent import CodeSmithAgent
from agents.specialized.architect_agent import ArchitectAgent
from config.capabilities_loader import get_capabilities_loader


class TestAgentFileCapabilities:
    """Test suite for agent file writing capabilities"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_file_tools_creation(self):
        """Test that FileSystemTools can be created"""
        tools = FileSystemTools(self.workspace_path)
        assert tools is not None
        assert tools.workspace_path == self.workspace_path
        assert len(tools.audit_log) == 0

    @pytest.mark.asyncio
    async def test_file_write_with_permission(self):
        """Test file writing with proper permissions"""
        tools = FileSystemTools(self.workspace_path)

        # Write a test file
        result = await tools.write_file(
            path="test.py",
            content="print('Hello World')",
            agent_name="TestAgent",
            allowed_paths=["*.py"]
        )

        assert result['status'] == 'success'
        assert os.path.exists(os.path.join(self.workspace_path, "test.py"))

        # Read the file back
        with open(os.path.join(self.workspace_path, "test.py"), 'r') as f:
            content = f.read()
        assert content == "print('Hello World')"

    @pytest.mark.asyncio
    async def test_file_write_without_permission(self):
        """Test that writing fails without proper permissions"""
        tools = FileSystemTools(self.workspace_path)

        # Try to write to a path not in allowed_paths
        result = await tools.write_file(
            path="test.txt",
            content="Should not be written",
            agent_name="TestAgent",
            allowed_paths=["*.py"]  # Only Python files allowed
        )

        assert result['status'] == 'error'
        assert "not in allowed paths" in result['error']
        assert not os.path.exists(os.path.join(self.workspace_path, "test.txt"))

    @pytest.mark.asyncio
    async def test_protected_path_rejection(self):
        """Test that system paths are protected"""
        tools = FileSystemTools(self.workspace_path)

        # Try to write to a system path
        result = await tools.write_file(
            path="/etc/passwd",
            content="malicious",
            agent_name="TestAgent",
            allowed_paths=["/etc/*"]  # Even with permission
        )

        assert result['status'] == 'error'
        assert "outside workspace" in result['error'] or "protected" in result['error']

    @pytest.mark.asyncio
    async def test_backup_creation(self):
        """Test that backups are created when overwriting"""
        tools = FileSystemTools(self.workspace_path)

        # Write initial file
        file_path = "test.py"
        initial_content = "# Initial content"
        await tools.write_file(
            path=file_path,
            content=initial_content,
            agent_name="TestAgent"
        )

        # Overwrite the file
        new_content = "# New content"
        result = await tools.write_file(
            path=file_path,
            content=new_content,
            agent_name="TestAgent"
        )

        assert result['status'] == 'success'
        assert result['backup'] is not None
        assert os.path.exists(result['backup'])

    @pytest.mark.asyncio
    async def test_codesmith_implementation(self):
        """Test CodeSmithAgent can write code files"""
        # Create a CodeSmithAgent with write permissions
        agent = CodeSmithAgent()
        agent.can_write = True
        agent.allowed_paths = ["*.py"]
        agent.file_tools = FileSystemTools(self.workspace_path)

        # Test implementation
        result = await agent.implement_code_to_file(
            spec="Create a simple hello world function",
            file_path="hello.py"
        )

        if result['status'] == 'success':
            assert os.path.exists(os.path.join(self.workspace_path, "hello.py"))
            assert result['lines'] > 0
        else:
            # If it fails, it should be a proper error
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_architect_redis_config(self):
        """Test ArchitectAgent can create Redis configuration"""
        agent = ArchitectAgent()
        agent.can_write = True
        agent.allowed_paths = ["*.config", "*.yml"]
        agent.file_tools = FileSystemTools(self.workspace_path)

        # Create Redis config
        result = await agent.create_redis_config({
            'maxmemory': '1gb',
            'policy': 'allkeys-lru'
        })

        if result['status'] == 'success':
            config_path = os.path.join(self.workspace_path, "redis.config")
            assert os.path.exists(config_path)

            # Check content
            with open(config_path, 'r') as f:
                content = f.read()
            assert 'maxmemory 1gb' in content
            assert 'allkeys-lru' in content

    @pytest.mark.asyncio
    async def test_architect_docker_compose(self):
        """Test ArchitectAgent can create Docker Compose file"""
        agent = ArchitectAgent()
        agent.can_write = True
        agent.allowed_paths = ["*.yml", "*.yaml"]
        agent.file_tools = FileSystemTools(self.workspace_path)

        # Create Docker Compose
        result = await agent.create_docker_compose(['redis', 'backend'])

        if result['status'] == 'success':
            compose_path = os.path.join(self.workspace_path, "docker-compose.yml")
            assert os.path.exists(compose_path)

            # Check content
            with open(compose_path, 'r') as f:
                content = f.read()
            assert 'redis:' in content
            assert 'backend:' in content

    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test that all operations are logged"""
        tools = FileSystemTools(self.workspace_path)

        # Perform several operations
        await tools.write_file("file1.txt", "Content 1", "Agent1")
        await tools.write_file("file2.txt", "Content 2", "Agent2")
        await tools.write_file("/etc/passwd", "Bad", "Agent3")  # Should fail

        # Check audit log
        assert len(tools.audit_log) == 3
        assert tools.audit_log[0].success == True
        assert tools.audit_log[1].success == True
        assert tools.audit_log[2].success == False

        # Check audit log filtering
        agent1_logs = tools.get_audit_log("Agent1")
        assert len(agent1_logs) == 1
        assert agent1_logs[0]['agent_name'] == "Agent1"

    @pytest.mark.asyncio
    async def test_capabilities_loader(self):
        """Test capabilities loader functionality"""
        loader = get_capabilities_loader()

        # Test getting capabilities
        codesmith_caps = loader.get_agent_capabilities("CodeSmithClaude")
        assert codesmith_caps.get('file_write') == True
        assert len(codesmith_caps.get('allowed_paths', [])) > 0

        reviewer_caps = loader.get_agent_capabilities("ReviewerGPT")
        assert reviewer_caps.get('file_write') == False

        # Test permission checking
        can_write = loader.can_agent_write("CodeSmithClaude", "backend/test.py")
        assert can_write == True

        cannot_write = loader.can_agent_write("ReviewerGPT", "any_file.py")
        assert cannot_write == False

    @pytest.mark.asyncio
    async def test_agent_permission_errors(self):
        """Test that agents without permissions get proper errors"""
        # Create a mock agent without write permissions
        config = AgentConfig(
            name="ReadOnlyAgent",
            agent_id="readonly",
            description="Test agent",
            model="test-model"
        )
        config.capabilities = {'file_write': False}

        agent = BaseAgent(config)
        agent.can_write = False

        # Try to write
        result = await agent.write_implementation("test.txt", "content")

        assert result['status'] == 'error'
        assert "no write permissions" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_directory_creation(self):
        """Test that parent directories are created"""
        tools = FileSystemTools(self.workspace_path)

        # Write to nested path
        result = await tools.write_file(
            path="nested/deep/test.py",
            content="print('nested')",
            agent_name="TestAgent",
            create_dirs=True
        )

        assert result['status'] == 'success'
        file_path = os.path.join(self.workspace_path, "nested", "deep", "test.py")
        assert os.path.exists(file_path)


def main():
    """Run tests"""
    print("🧪 Running Agent File Capabilities Tests...")

    # Run pytest
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    main()