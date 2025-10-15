"""
Integration Tests: Agent Orchestrator

Tests agent-to-agent communication and workflow integration.

Run with:
    python -m pytest backend/tests/test_orchestrator_integration.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from core.agent_orchestrator import (
    AgentOrchestrator,
    AgentInvocationError,
    CircularInvocationError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_mcp():
    """Create mock MCP client."""
    mcp = Mock()
    mcp.call = AsyncMock(return_value={
        "content": [{
            "type": "text",
            "text": "Research result"
        }]
    })
    return mcp


@pytest.fixture
def orchestrator(mock_mcp):
    """Create orchestrator instance."""
    return AgentOrchestrator(
        mcp_client=mock_mcp,
        workspace_path="/tmp/test",
        approval_manager=None,
        hitl_manager=None
    )


# ============================================================================
# TEST: invoke_research()
# ============================================================================

@pytest.mark.asyncio
async def test_invoke_research_success(orchestrator, mock_mcp):
    """Test successful research invocation."""
    # Configure mock to return research result
    mock_mcp.call.return_value = {
        "content": [{
            "type": "text",
            "text": '{"findings": {"analysis": "Test result"}, "report": "Test report"}'
        }]
    }

    # Invoke research
    result = await orchestrator.invoke_research(
        query="Test query",
        mode="research",
        caller="test"
    )

    # Verify result
    assert result["success"] is True
    assert "result" in result
    assert result["mode"] == "research"

    # Verify metrics
    assert orchestrator.invocation_count["research"] == 1
    assert len(orchestrator.execution_stack) == 0  # Should be popped after completion


@pytest.mark.asyncio
async def test_invoke_research_modes(orchestrator):
    """Test different research modes."""
    modes = ["research", "explain", "analyze", "index"]

    for mode in modes:
        result = await orchestrator.invoke_research(
            query=f"Test {mode}",
            mode=mode,
            caller="test"
        )

        assert result["success"] is True
        assert result["mode"] == mode


@pytest.mark.asyncio
async def test_invoke_research_invalid_mode(orchestrator):
    """Test invalid research mode."""
    with pytest.raises(AgentInvocationError) as exc_info:
        await orchestrator.invoke_research(
            query="Test",
            mode="invalid_mode",
            caller="test"
        )

    assert "Invalid research mode" in str(exc_info.value)


# ============================================================================
# TEST: Circular Invocation Detection
# ============================================================================

@pytest.mark.asyncio
async def test_circular_invocation_prevention(orchestrator):
    """Test that circular invocations are prevented."""
    # Simulate: architect calls research, which tries to call architect again
    orchestrator._push_execution("architect", "supervisor", {})

    # This should raise CircularInvocationError
    with pytest.raises(CircularInvocationError):
        orchestrator._check_circular_invocation("architect", "research")


@pytest.mark.asyncio
async def test_max_stack_depth(orchestrator):
    """Test maximum stack depth limit."""
    # Push 5 levels (max allowed)
    for i in range(5):
        orchestrator._push_execution(f"agent_{i}", f"caller_{i}", {})

    # 6th level should fail
    with pytest.raises(AgentInvocationError) as exc_info:
        orchestrator._check_circular_invocation("agent_6", "agent_5")

    assert "Maximum invocation depth exceeded" in str(exc_info.value)


# ============================================================================
# TEST: Shared Context
# ============================================================================

def test_shared_context_management(orchestrator):
    """Test shared context between agents."""
    # Update context
    orchestrator.update_shared_context("key1", "value1")
    orchestrator.update_shared_context("key2", {"nested": "data"})

    # Retrieve context
    assert orchestrator.get_shared_context("key1") == "value1"
    assert orchestrator.get_shared_context("key2") == {"nested": "data"}
    assert orchestrator.get_shared_context("missing", "default") == "default"

    # Check metrics
    metrics = orchestrator.get_metrics()
    assert "key1" in metrics["shared_context_keys"]
    assert "key2" in metrics["shared_context_keys"]


# ============================================================================
# TEST: Execution History
# ============================================================================

@pytest.mark.asyncio
async def test_execution_history_tracking(orchestrator):
    """Test execution history tracking."""
    # Invoke research
    await orchestrator.invoke_research(
        query="Test",
        mode="research",
        caller="architect"
    )

    # Check results
    assert len(orchestrator.agent_results) > 0

    # Get history (should be empty after pop)
    history = orchestrator.get_execution_history()
    assert len(history) == 0  # Stack is empty after completion


# ============================================================================
# TEST: Metrics
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_metrics(orchestrator):
    """Test orchestrator metrics tracking."""
    # Initial state
    metrics = orchestrator.get_metrics()
    assert metrics["invocation_count"]["research"] == 0
    assert metrics["current_stack_depth"] == 0

    # Invoke research
    await orchestrator.invoke_research(
        query="Test",
        mode="research",
        caller="test"
    )

    # Check metrics updated
    metrics = orchestrator.get_metrics()
    assert metrics["invocation_count"]["research"] == 1
    assert metrics["current_stack_depth"] == 0  # Stack cleared after execution


# ============================================================================
# TEST: Reset
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_reset(orchestrator):
    """Test orchestrator reset."""
    # Create some state
    await orchestrator.invoke_research("Test", "research", "test")
    orchestrator.update_shared_context("key", "value")

    # Reset
    orchestrator.reset()

    # Verify state cleared
    metrics = orchestrator.get_metrics()
    assert metrics["invocation_count"]["research"] == 0
    assert metrics["agent_results_count"] == 0
    assert len(metrics["shared_context_keys"]) == 0


# ============================================================================
# TEST: Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_research_invocation_error_handling(orchestrator, mock_mcp):
    """Test error handling in research invocation."""
    # Configure mock to raise error
    mock_mcp.call.side_effect = Exception("MCP error")

    # Invoke research should raise AgentInvocationError
    with pytest.raises(AgentInvocationError) as exc_info:
        await orchestrator.invoke_research(
            query="Test",
            mode="research",
            caller="test"
        )

    assert "Research invocation failed" in str(exc_info.value)


# ============================================================================
# MAIN (for direct execution)
# ============================================================================

if __name__ == "__main__":
    print("🧪 Running Agent Orchestrator Integration Tests\n")
    pytest.main([__file__, "-v", "--tb=short"])
