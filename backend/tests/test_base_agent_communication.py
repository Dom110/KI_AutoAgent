"""
Test Base Agent Multi-Agent Communication Helper Methods

Tests the 4 helper methods implemented in Phase 5:
1. _wait_for_response() - Async response waiting with queues
2. _can_help_with() - Capability matching
3. _provide_help() - Contextual help generation
4. request_help() response collection
"""

import asyncio
import pytest
from datetime import datetime
from agents.base.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentMessage,
    TaskRequest,
    TaskResult,
)


class TestAgent(BaseAgent):
    """Test agent implementation"""

    async def execute(self, request: TaskRequest) -> TaskResult:
        return TaskResult(
            status="success",
            content="Test result",
            agent=self.name,
        )


@pytest.fixture
def architect_agent():
    """Create test architect agent"""
    config = AgentConfig(
        agent_id="architect",
        name="Architect",
        full_name="Architect Agent",
        description="System architect",
        model="gpt-4",
        capabilities=[
            AgentCapability.ARCHITECTURE_DESIGN,
            AgentCapability.CODE_REVIEW,
        ],
    )
    return TestAgent(config)


@pytest.fixture
def codesmith_agent():
    """Create test codesmith agent"""
    config = AgentConfig(
        agent_id="codesmith",
        name="Codesmith",
        full_name="Codesmith Agent",
        description="Code generator",
        model="gpt-4",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.BUG_FIXING,
        ],
    )
    return TestAgent(config)


@pytest.mark.asyncio
async def test_can_help_with_keyword_matching(architect_agent):
    """Test capability matching with keywords"""
    # Should match ARCHITECTURE_DESIGN capability
    task1 = {"task": "Design system architecture for web app"}
    assert await architect_agent._can_help_with(task1) is True

    # Should match CODE_REVIEW capability
    task2 = {"task": "Review code for best practices"}
    assert await architect_agent._can_help_with(task2) is True

    # Should NOT match (no code generation capability)
    task3 = {"task": "Implement user authentication"}
    assert await architect_agent._can_help_with(task3) is False


@pytest.mark.asyncio
async def test_can_help_with_explicit_capabilities(codesmith_agent):
    """Test capability matching with explicit required capabilities"""
    # Codesmith has CODE_GENERATION
    task1 = {
        "task": "Build API",
        "capabilities_needed": ["code_generation"]
    }
    assert await codesmith_agent._can_help_with(task1) is True

    # Codesmith does NOT have ARCHITECTURE_DESIGN
    task2 = {
        "task": "Design system",
        "capabilities_needed": ["architecture_design"]
    }
    assert await codesmith_agent._can_help_with(task2) is False


@pytest.mark.asyncio
async def test_provide_help_suggestions(architect_agent):
    """Test help provision with suggestions"""
    task = {"task": "Need help designing a microservices architecture"}

    help_response = await architect_agent._provide_help(task)

    assert help_response["agent"] == "Architect"
    assert help_response["agent_id"] == "architect"
    assert "architecture_design" in help_response["capabilities"]
    assert "code_review" in help_response["capabilities"]
    assert len(help_response["suggestions"]) > 0
    assert any("architecture" in s.lower() for s in help_response["suggestions"])


@pytest.mark.asyncio
async def test_provide_help_recommendations(codesmith_agent):
    """Test help provision with recommendations"""
    task = {"task": "Can you suggest best practices for API design?"}

    help_response = await codesmith_agent._provide_help(task)

    assert help_response["help_type"] == "recommendations"
    assert "recommendations" in help_response
    assert len(help_response["recommendations"]) > 0


@pytest.mark.asyncio
async def test_wait_for_response_success(architect_agent):
    """Test successful response waiting"""
    correlation_id = "test_123"

    # Simulate response arrival
    async def send_response():
        await asyncio.sleep(0.1)
        message = AgentMessage(
            from_agent="other_agent",
            to_agent="architect",
            message_type="response",
            content={"result": "success"},
            correlation_id=correlation_id,
        )
        await architect_agent._process_agent_response(message)

    # Start response sender
    asyncio.create_task(send_response())

    # Wait for response
    response = await architect_agent._wait_for_response(correlation_id, timeout=2.0)

    assert response == {"result": "success"}


@pytest.mark.asyncio
async def test_wait_for_response_timeout(architect_agent):
    """Test response waiting timeout"""
    correlation_id = "test_timeout"

    # Should timeout (no response sent)
    with pytest.raises(asyncio.TimeoutError):
        await architect_agent._wait_for_response(correlation_id, timeout=0.5)


@pytest.mark.asyncio
async def test_request_help_no_communication_bus(architect_agent):
    """Test help request without communication bus"""
    responses = await architect_agent.request_help("Need help with task")

    # Should return empty list (no communication bus)
    assert responses == []


def test_response_queue_initialization(architect_agent):
    """Test response queue dictionary exists"""
    assert hasattr(architect_agent, "_response_queues")
    assert isinstance(architect_agent._response_queues, dict)
    assert len(architect_agent._response_queues) == 0


def test_agent_capabilities(architect_agent, codesmith_agent):
    """Test agent capabilities are correctly set"""
    assert AgentCapability.ARCHITECTURE_DESIGN in architect_agent.config.capabilities
    assert AgentCapability.CODE_REVIEW in architect_agent.config.capabilities

    assert AgentCapability.CODE_GENERATION in codesmith_agent.config.capabilities
    assert AgentCapability.BUG_FIXING in codesmith_agent.config.capabilities


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
