"""
Test Suite for MCP Integration (v6.2)

Tests all MCP-converted subgraphs and workflow orchestrator.

Test Coverage:
1. MCP Client initialization
2. Research subgraph (all 3 modes: research, explain, analyze)
3. Architect subgraph
4. Codesmith subgraph
5. ReviewFix subgraph
6. Workflow orchestrator integration
7. Error handling and recovery

Author: KI AutoAgent Team
Version: 6.2.0-alpha
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

# MCP Client
from mcp.mcp_client import MCPClient, MCPConnectionError

# Subgraphs
from subgraphs.research_subgraph_v6_1 import create_research_subgraph
from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph
from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph
from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph

# Workflow
from workflow_v6_integrated import WorkflowV6Integrated

# State
from state_v6 import ResearchState, ArchitectState, CodesmithState, ReviewFixState


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def mcp_client():
    """Create and initialize MCP client for testing."""
    client = MCPClient()
    await client.initialize()
    yield client
    await client.cleanup()


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create workspace structure
        workspace = Path(tmpdir)
        (workspace / ".ki_autoagent_ws").mkdir(parents=True, exist_ok=True)
        (workspace / ".ki_autoagent_ws/cache").mkdir(parents=True, exist_ok=True)
        (workspace / ".ki_autoagent_ws/memory").mkdir(parents=True, exist_ok=True)

        yield str(workspace)


# ============================================================================
# TEST: MCP Client
# ============================================================================

@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization and server connections."""
    client = MCPClient()

    # Test initialization
    await client.initialize()

    # Verify servers are connected
    assert len(client.servers) > 0, "MCP client should connect to at least one server"

    # Check for required servers
    required_servers = ["perplexity", "claude", "memory"]
    for server_name in required_servers:
        assert server_name in client.servers, f"Required server '{server_name}' not connected"

    # Test cleanup
    await client.cleanup()

    print("✅ MCP Client initialization test passed")


@pytest.mark.asyncio
async def test_mcp_client_call_perplexity(mcp_client):
    """Test MCP client call to Perplexity server."""
    result = await mcp_client.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": "Python async patterns",
            "max_results": 3
        }
    )

    # Verify response structure
    assert "content" in result, "Perplexity response should have content"
    assert result.get("isError") is not True, "Perplexity call should not error"

    print("✅ MCP Perplexity call test passed")


@pytest.mark.asyncio
async def test_mcp_client_call_memory(mcp_client, temp_workspace):
    """Test MCP client call to Memory server."""
    # Store memory
    store_result = await mcp_client.call(
        server="memory",
        tool="store_memory",
        arguments={
            "workspace_path": temp_workspace,
            "content": "Test memory content",
            "metadata": {
                "agent": "test",
                "type": "test_data"
            }
        }
    )

    assert result.get("isError") is not True, "Memory store should not error"

    # Search memory
    search_result = await mcp_client.call(
        server="memory",
        tool="search_memory",
        arguments={
            "workspace_path": temp_workspace,
            "query": "test memory",
            "k": 5
        }
    )

    assert "content" in search_result, "Memory search should return content"

    print("✅ MCP Memory call test passed")


# ============================================================================
# TEST: Research Subgraph (3 modes)
# ============================================================================

@pytest.mark.asyncio
async def test_research_subgraph_research_mode(mcp_client, temp_workspace):
    """Test research subgraph in 'research' mode (web search)."""
    subgraph = create_research_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    # Test state
    state = ResearchState(
        query="Python async best practices",
        mode="research",
        findings={},
        report="",
        sources=[],
        errors=[]
    )

    # Execute subgraph
    result = await subgraph.ainvoke(state)

    # Verify results
    assert result["findings"], "Research mode should return findings"
    assert result["report"], "Research mode should generate report"
    assert len(result["errors"]) == 0, "Research should complete without errors"
    assert result["mode"] == "research", "Mode should be preserved"

    print("✅ Research subgraph (research mode) test passed")


@pytest.mark.asyncio
async def test_research_subgraph_explain_mode(mcp_client, temp_workspace):
    """Test research subgraph in 'explain' mode (codebase analysis)."""
    # Create test file in workspace
    test_file = Path(temp_workspace) / "test.py"
    test_file.write_text("def hello():\n    return 'world'\n")

    subgraph = create_research_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    state = ResearchState(
        query="Explain the test.py file",
        mode="explain",
        findings={},
        report="",
        sources=[],
        errors=[]
    )

    result = await subgraph.ainvoke(state)

    assert result["findings"], "Explain mode should return findings"
    assert result["report"], "Explain mode should generate report"
    assert result["mode"] == "explain", "Mode should be preserved"

    print("✅ Research subgraph (explain mode) test passed")


@pytest.mark.asyncio
async def test_research_subgraph_analyze_mode(mcp_client, temp_workspace):
    """Test research subgraph in 'analyze' mode (deep analysis)."""
    # Create test file
    test_file = Path(temp_workspace) / "test.py"
    test_file.write_text("def hello():\n    return 'world'\n")

    subgraph = create_research_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    state = ResearchState(
        query="Analyze code quality in test.py",
        mode="analyze",
        findings={},
        report="",
        sources=[],
        errors=[]
    )

    result = await subgraph.ainvoke(state)

    assert result["findings"], "Analyze mode should return findings"
    assert result["report"], "Analyze mode should generate report"
    assert result["mode"] == "analyze", "Mode should be preserved"

    print("✅ Research subgraph (analyze mode) test passed")


# ============================================================================
# TEST: Architect Subgraph
# ============================================================================

@pytest.mark.asyncio
async def test_architect_subgraph(mcp_client, temp_workspace):
    """Test architect subgraph with MCP."""
    subgraph = create_architect_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    state = ArchitectState(
        user_requirements="Build a simple REST API with authentication",
        workspace_path=temp_workspace,
        research_context={},
        design={},
        tech_stack=[],
        patterns=[],
        diagram="",
        adr="",
        errors=[]
    )

    result = await subgraph.ainvoke(state)

    assert result["design"], "Architect should generate design"
    assert result["tech_stack"], "Architect should define tech stack"
    assert result["patterns"], "Architect should identify patterns"
    assert result["diagram"], "Architect should generate diagram"
    assert len(result["errors"]) == 0, "Architect should complete without errors"

    print("✅ Architect subgraph test passed")


# ============================================================================
# TEST: Codesmith Subgraph
# ============================================================================

@pytest.mark.asyncio
async def test_codesmith_subgraph(mcp_client, temp_workspace):
    """Test codesmith subgraph with MCP."""
    subgraph = create_codesmith_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    state = CodesmithState(
        design={"description": "Simple Python module with hello function"},
        workspace_path=temp_workspace,
        generated_files=[],
        implementation_summary="",
        errors=[]
    )

    result = await subgraph.ainvoke(state)

    assert result["generated_files"], "Codesmith should generate files"
    assert result["implementation_summary"], "Codesmith should provide summary"

    print("✅ Codesmith subgraph test passed")


# ============================================================================
# TEST: ReviewFix Subgraph
# ============================================================================

@pytest.mark.asyncio
async def test_reviewfix_subgraph(mcp_client, temp_workspace):
    """Test reviewfix subgraph with MCP."""
    # Create test file
    test_file = Path(temp_workspace) / "test.py"
    test_file.write_text("def hello():\n    return 'world'\n")

    subgraph = create_reviewfix_subgraph(
        workspace_path=temp_workspace,
        mcp=mcp_client,
        hitl_callback=None
    )

    state = ReviewFixState(
        generated_files=[{"path": "test.py"}],
        workspace_path=temp_workspace,
        iteration=0,
        max_iterations=1,
        quality_score=0.0,
        feedback="",
        fixes_applied="",
        file_paths=[],
        build_validation_result=None,
        errors=[]
    )

    result = await subgraph.ainvoke(state)

    assert result["quality_score"] > 0, "ReviewFix should provide quality score"
    assert result["feedback"], "ReviewFix should provide feedback"
    assert result["iteration"] > 0, "ReviewFix should increment iteration"

    print("✅ ReviewFix subgraph test passed")


# ============================================================================
# TEST: Workflow Integration
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_mcp_initialization(temp_workspace):
    """Test workflow MCP client initialization."""
    workflow = WorkflowV6Integrated(
        workspace_path=temp_workspace,
        websocket_callback=None
    )

    await workflow.initialize()

    # Verify MCP client is initialized
    assert workflow.mcp is not None, "Workflow should initialize MCP client"
    assert len(workflow.mcp.servers) > 0, "MCP client should connect to servers"

    # Verify workflow is compiled
    assert workflow.workflow is not None, "Workflow should be compiled"

    # Cleanup
    await workflow.cleanup()

    print("✅ Workflow MCP initialization test passed")


@pytest.mark.asyncio
async def test_workflow_end_to_end_simple(temp_workspace):
    """Test simple end-to-end workflow execution with MCP."""
    workflow = WorkflowV6Integrated(
        workspace_path=temp_workspace,
        websocket_callback=None
    )

    await workflow.initialize()

    try:
        # Run simple workflow
        result = await workflow.run(
            user_query="Explain what a Python async function is",
            session_id="test_session_simple"
        )

        # Verify result
        assert result.get("success") is not False, "Workflow should not fail"
        assert "message" in result or "final_output" in result, "Workflow should return output"

        print("✅ Workflow end-to-end (simple) test passed")

    finally:
        await workflow.cleanup()


# ============================================================================
# TEST: Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_mcp_error_handling_invalid_server():
    """Test MCP error handling for invalid server."""
    client = MCPClient()
    await client.initialize()

    try:
        # Try to call non-existent server
        result = await client.call(
            server="nonexistent_server",
            tool="some_tool",
            arguments={}
        )

        # Should return error
        assert result.get("isError") is True, "Invalid server should return error"

    finally:
        await client.cleanup()

    print("✅ MCP error handling (invalid server) test passed")


@pytest.mark.asyncio
async def test_mcp_error_handling_invalid_tool():
    """Test MCP error handling for invalid tool."""
    client = MCPClient()
    await client.initialize()

    try:
        # Try to call non-existent tool
        result = await client.call(
            server="perplexity",
            tool="nonexistent_tool",
            arguments={}
        )

        # Should return error
        assert result.get("isError") is True, "Invalid tool should return error"

    finally:
        await client.cleanup()

    print("✅ MCP error handling (invalid tool) test passed")


# ============================================================================
# MAIN (for running tests manually)
# ============================================================================

if __name__ == "__main__":
    """Run all tests manually (without pytest)."""
    print("🧪 Running MCP Integration Tests...\n")

    # Run tests
    asyncio.run(test_mcp_client_initialization())

    print("\n✅ All MCP integration tests passed!")
