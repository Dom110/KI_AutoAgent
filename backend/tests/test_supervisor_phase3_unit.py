#!/usr/bin/env python3
"""
🧪 Unit Tests: Supervisor Phase 3 Integration

Tests that supervisor_mcp.py correctly uses AgentLLMFactory
instead of hardcoded ChatOpenAI.
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.llm_config import AgentLLMConfigManager
from backend.core.llm_factory import AgentLLMFactory
from backend.core.supervisor_mcp import SupervisorMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test.supervisor_phase3")


async def test_supervisor_init_with_factory():
    """Test that SupervisorMCP.__init__() uses AgentLLMFactory."""
    logger.info("=" * 80)
    logger.info("TEST 1: SupervisorMCP.__init__() uses AgentLLMFactory")
    logger.info("=" * 80)
    
    try:
        # Initialize config
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        logger.info("✅ Config initialized")
        
        # Create supervisor (without mocking MCPManager)
        workspace_path = "/tmp/test_workspace"
        
        # We'll mock only the MCPManager to avoid needing MCP servers running
        with patch("backend.core.supervisor_mcp.get_mcp_manager") as mock_mcp:
            mock_mcp.return_value = MagicMock()
            
            supervisor = SupervisorMCP(workspace_path=workspace_path)
            
            logger.info("✅ Supervisor created")
            
            # Verify it has llm_provider attribute (not self.llm)
            assert hasattr(supervisor, "llm_provider"), "Missing llm_provider attribute"
            logger.info("   ✅ Has llm_provider attribute")
            
            assert not hasattr(supervisor, "llm") or supervisor.__dict__.get("llm") is None, \
                "Still has old llm attribute!"
            logger.info("   ✅ No old llm attribute")
            
            # Verify provider is correct
            provider = supervisor.llm_provider
            assert provider.get_provider_name() == "openai", \
                f"Expected openai, got {provider.get_provider_name()}"
            logger.info(f"   ✅ Provider: {provider.get_provider_name()}")
            
            assert provider.model == "gpt-4o-2024-11-20", \
                f"Expected gpt-4o-2024-11-20, got {provider.model}"
            logger.info(f"   ✅ Model: {provider.model}")
            
            # Verify temperature from config
            assert provider.temperature == 0.3, \
                f"Expected 0.3, got {provider.temperature}"
            logger.info(f"   ✅ Temperature: {provider.temperature}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supervisor_has_generate_structured_output():
    """Test that supervisor's provider has generate_structured_output method."""
    logger.info("=" * 80)
    logger.info("TEST 2: Provider has generate_structured_output() method")
    logger.info("=" * 80)
    
    try:
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        with patch("backend.core.supervisor_mcp.get_mcp_manager"):
            supervisor = SupervisorMCP(workspace_path="/tmp/test")
            provider = supervisor.llm_provider
            
            # Check method exists
            assert hasattr(provider, "generate_structured_output"), \
                "Provider missing generate_structured_output method"
            logger.info("   ✅ generate_structured_output() exists")
            
            # Check it's callable
            assert callable(getattr(provider, "generate_structured_output")), \
                "generate_structured_output is not callable"
            logger.info("   ✅ generate_structured_output() is callable")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supervisor_logging_shows_provider_info():
    """Test that supervisor initialization logs provider info."""
    logger.info("=" * 80)
    logger.info("TEST 3: Logging shows provider/model/temperature")
    logger.info("=" * 80)
    
    try:
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        # Capture logs
        log_records = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_records.append(self.format(record))
        
        handler = TestHandler()
        handler.setLevel(logging.INFO)
        supervisor_logger = logging.getLogger("backend.core.supervisor_mcp")
        supervisor_logger.addHandler(handler)
        
        with patch("backend.core.supervisor_mcp.get_mcp_manager"):
            supervisor = SupervisorMCP(workspace_path="/tmp/test")
        
        supervisor_logger.removeHandler(handler)
        
        # Check logs
        log_text = "\n".join(log_records)
        
        assert "openai" in log_text, "Logging missing provider name"
        logger.info("   ✅ Logs show provider: openai")
        
        assert "gpt-4o" in log_text, "Logging missing model name"
        logger.info("   ✅ Logs show model: gpt-4o")
        
        assert "0.3" in log_text, "Logging missing temperature"
        logger.info("   ✅ Logs show temperature: 0.3")
        
        assert "🤖" in log_text, "Missing 🤖 emoji marker"
        logger.info("   ✅ Logs use emoji markers (🤖)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supervisor_no_chatOpenAI_import():
    """Test that supervisor_mcp doesn't import ChatOpenAI directly."""
    logger.info("=" * 80)
    logger.info("TEST 4: No direct ChatOpenAI import in supervisor_mcp")
    logger.info("=" * 80)
    
    try:
        # Read the supervisor_mcp.py file
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # Check that ChatOpenAI is NOT imported
        assert "from langchain_openai import ChatOpenAI" not in content, \
            "Found ChatOpenAI import - Phase 3 not complete!"
        logger.info("   ✅ No ChatOpenAI import")
        
        # Check that AgentLLMFactory IS imported
        assert "from backend.core.llm_factory import AgentLLMFactory" in content, \
            "Missing AgentLLMFactory import"
        logger.info("   ✅ Has AgentLLMFactory import")
        
        # Check that self.llm_provider is used (not self.llm)
        assert "self.llm_provider" in content, \
            "Code doesn't use self.llm_provider"
        logger.info("   ✅ Uses self.llm_provider")
        
        # Check that generate_structured_output is used
        assert "generate_structured_output" in content, \
            "LLM calls don't use generate_structured_output"
        logger.info("   ✅ Uses generate_structured_output()")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_has_supervisor_section():
    """Test that agent_llm_config.json has supervisor section."""
    logger.info("=" * 80)
    logger.info("TEST 5: Config has supervisor section")
    logger.info("=" * 80)
    
    try:
        import json
        
        config_path = Path("backend/config/agent_llm_config.json")
        config = json.loads(config_path.read_text())
        
        # Check structure
        assert "agents" in config, "Config missing 'agents' section"
        logger.info("   ✅ Config has 'agents' section")
        
        assert "supervisor" in config["agents"], "Config missing 'supervisor' agent"
        logger.info("   ✅ Config has 'supervisor' agent")
        
        supervisor_config = config["agents"]["supervisor"]
        
        # Check required fields
        required_fields = ["provider", "model", "temperature", "max_tokens"]
        for field in required_fields:
            assert field in supervisor_config, f"Missing field: {field}"
        logger.info(f"   ✅ All required fields present: {required_fields}")
        
        # Check values
        assert supervisor_config["provider"] == "openai", \
            f"Expected provider=openai, got {supervisor_config['provider']}"
        logger.info(f"   ✅ Provider: {supervisor_config['provider']}")
        
        assert "gpt-4o" in supervisor_config["model"], \
            f"Expected gpt-4o in model name"
        logger.info(f"   ✅ Model: {supervisor_config['model']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("🧪 PHASE 3 SUPERVISOR UNIT TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Init uses AgentLLMFactory", test_supervisor_init_with_factory),
        ("Provider has generate_structured_output", test_supervisor_has_generate_structured_output),
        ("Logging shows provider info", test_supervisor_logging_shows_provider_info),
        ("No ChatOpenAI import", test_supervisor_no_chatOpenAI_import),
        ("Config has supervisor section", test_config_has_supervisor_section),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n✅ Passed: {passed}/{total}")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
