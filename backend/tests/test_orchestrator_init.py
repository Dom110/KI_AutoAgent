"""
Test: Basic AgentOrchestrator Initialization

Verifies that AgentOrchestrator can be created and initialized properly.

Run with:
    python -m pytest backend/tests/test_orchestrator_init.py -v
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import Mock, AsyncMock
from core.agent_orchestrator import AgentOrchestrator


def test_orchestrator_creation():
    """Test that AgentOrchestrator can be instantiated."""
    # Mock dependencies
    mock_mcp = Mock()
    mock_approval_manager = Mock()
    mock_hitl_manager = Mock()

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp,
        workspace_path="/tmp/test_workspace",
        approval_manager=mock_approval_manager,
        hitl_manager=mock_hitl_manager
    )

    # Verify initialization
    assert orchestrator.mcp == mock_mcp
    assert orchestrator.workspace_path == "/tmp/test_workspace"
    assert orchestrator.approval_manager == mock_approval_manager
    assert orchestrator.hitl_manager == mock_hitl_manager

    # Verify tracking structures initialized
    assert orchestrator.execution_stack == []
    assert orchestrator.agent_results == {}
    assert orchestrator.shared_context == {}

    # Verify metrics initialized
    assert orchestrator.invocation_count["research"] == 0
    assert orchestrator.invocation_count["architect"] == 0
    assert orchestrator.invocation_count["code_indexer"] == 0
    assert orchestrator.invocation_count["hitl_approvals"] == 0

    print("✅ Test passed: AgentOrchestrator initialization successful")


def test_orchestrator_metrics():
    """Test that orchestrator metrics are properly tracked."""
    orchestrator = AgentOrchestrator(
        mcp_client=Mock(),
        workspace_path="/tmp/test_workspace",
        approval_manager=None,
        hitl_manager=None
    )

    # Get initial metrics
    metrics = orchestrator.get_metrics()

    assert metrics["invocation_count"]["research"] == 0
    assert metrics["current_stack_depth"] == 0
    assert metrics["agent_results_count"] == 0
    assert metrics["shared_context_keys"] == []

    print("✅ Test passed: Orchestrator metrics tracking works")


def test_orchestrator_shared_context():
    """Test shared context management."""
    orchestrator = AgentOrchestrator(
        mcp_client=Mock(),
        workspace_path="/tmp/test_workspace",
        approval_manager=None,
        hitl_manager=None
    )

    # Update shared context
    orchestrator.update_shared_context("test_key", "test_value")

    # Retrieve value
    value = orchestrator.get_shared_context("test_key")
    assert value == "test_value"

    # Retrieve non-existent key with default
    value = orchestrator.get_shared_context("missing_key", "default")
    assert value == "default"

    print("✅ Test passed: Shared context management works")


def test_orchestrator_reset():
    """Test orchestrator state reset."""
    orchestrator = AgentOrchestrator(
        mcp_client=Mock(),
        workspace_path="/tmp/test_workspace",
        approval_manager=None,
        hitl_manager=None
    )

    # Add some state
    orchestrator.update_shared_context("key1", "value1")
    orchestrator.agent_results["test"] = {"result": "data"}
    orchestrator.invocation_count["research"] = 5

    # Reset
    orchestrator.reset()

    # Verify state cleared
    assert orchestrator.shared_context == {}
    assert orchestrator.agent_results == {}
    assert orchestrator.execution_stack == []

    # Verify counters reset
    assert orchestrator.invocation_count["research"] == 0

    print("✅ Test passed: Orchestrator reset works")


if __name__ == "__main__":
    print("🧪 Running AgentOrchestrator Initialization Tests\n")

    test_orchestrator_creation()
    test_orchestrator_metrics()
    test_orchestrator_shared_context()
    test_orchestrator_reset()

    print("\n✅ All tests passed!")
