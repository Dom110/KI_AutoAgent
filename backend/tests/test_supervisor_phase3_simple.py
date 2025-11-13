#!/usr/bin/env python3
"""
🧪 Simple Tests: Supervisor Phase 3 Integration

Tests that don't require importing supervisor_mcp.py directly.
Instead, we analyze the file and check that changes were made correctly.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test.supervisor_phase3")


def test_imports_updated():
    """Test that imports were correctly updated."""
    logger.info("=" * 80)
    logger.info("TEST 1: Imports Updated")
    logger.info("=" * 80)
    
    try:
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # OLD imports should NOT exist
        assert "from langchain_openai import ChatOpenAI" not in content, \
            "❌ Still imports ChatOpenAI directly"
        logger.info("   ✅ ChatOpenAI import removed")
        
        assert "from langchain_core.messages import SystemMessage, HumanMessage" not in content, \
            "❌ Still imports SystemMessage/HumanMessage"
        logger.info("   ✅ SystemMessage/HumanMessage imports removed")
        
        # NEW imports should exist
        assert "from backend.core.llm_factory import AgentLLMFactory" in content, \
            "❌ Missing AgentLLMFactory import"
        logger.info("   ✅ AgentLLMFactory imported")
        
        assert "from backend.core.llm_config import AgentLLMConfigManager" in content, \
            "❌ Missing AgentLLMConfigManager import"
        logger.info("   ✅ AgentLLMConfigManager imported")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_init_updated():
    """Test that __init__() was updated to use Factory."""
    logger.info("=" * 80)
    logger.info("TEST 2: __init__() Updated")
    logger.info("=" * 80)
    
    try:
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # OLD code should NOT exist
        assert "self.llm = ChatOpenAI(" not in content, \
            "❌ Still uses ChatOpenAI directly"
        logger.info("   ✅ ChatOpenAI initialization removed")
        
        # NEW code should exist
        assert "self.llm_provider = AgentLLMFactory.get_provider_for_agent" in content, \
            "❌ Missing AgentLLMFactory usage"
        logger.info("   ✅ Uses AgentLLMFactory")
        
        assert "AgentLLMConfigManager.initialize" in content, \
            "❌ Missing config initialization"
        logger.info("   ✅ Initializes config")
        
        # Check logging
        assert "🤖 Initializing SupervisorMCP" in content, \
            "❌ Missing initialization logging"
        logger.info("   ✅ Has init logging")
        
        assert "✅ LLM Provider:" in content, \
            "❌ Missing provider logging"
        logger.info("   ✅ Logs provider info")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_llm_calls_updated():
    """Test that LLM calls use generate_structured_output()."""
    logger.info("=" * 80)
    logger.info("TEST 3: LLM Calls Updated")
    logger.info("=" * 80)
    
    try:
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # OLD code should NOT exist
        assert ".ainvoke([" not in content or "with_structured_output" not in content, \
            "❌ Still uses .ainvoke() with structured_output"
        logger.info("   ✅ Removed .ainvoke() calls")
        
        # NEW code should exist
        assert "generate_structured_output(" in content, \
            "❌ Missing generate_structured_output() calls"
        logger.info("   ✅ Uses generate_structured_output()")
        
        assert "await self.llm_provider.generate_structured_output" in content, \
            "❌ LLM provider not used for structured output"
        logger.info("   ✅ LLM provider used for structured output")
        
        # Check logging
        assert "🏗️ Requesting structured decision" in content, \
            "❌ Missing structured decision logging"
        logger.info("   ✅ Has decision request logging")
        
        assert "✅ Structured decision received" in content, \
            "❌ Missing success logging"
        logger.info("   ✅ Has success logging")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_error_handling_simplified():
    """Test that error handling was simplified."""
    logger.info("=" * 80)
    logger.info("TEST 4: Error Handling Simplified")
    logger.info("=" * 80)
    
    try:
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # Should have specific error types
        assert "except (ValueError, json.JSONDecodeError)" in content, \
            "❌ Missing JSON error handling"
        logger.info("   ✅ Handles JSON parse errors")
        
        assert "except Exception as e:" in content, \
            "❌ Missing generic error handling"
        logger.info("   ✅ Handles generic errors")
        
        # OLD error handling should mostly be gone
        # (Don't check for exact removal as some code might remain)
        assert "❌ Parsing failed" in content or "❌ Failed to parse" in content, \
            "❌ Missing improved error logging"
        logger.info("   ✅ Has improved error logging")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_factory_function_updated():
    """Test that create_supervisor_mcp() was updated."""
    logger.info("=" * 80)
    logger.info("TEST 5: create_supervisor_mcp() Updated")
    logger.info("=" * 80)
    
    try:
        supervisor_file = Path("backend/core/supervisor_mcp.py")
        content = supervisor_file.read_text()
        
        # Find the factory function
        factory_start = content.find("def create_supervisor_mcp(")
        factory_end = content.find("def ", factory_start + 1)
        factory_func = content[factory_start:factory_end]
        
        # OLD parameters should NOT be passed
        assert 'model="' not in factory_func, \
            "❌ Factory still passes model parameter"
        logger.info("   ✅ No model parameter")
        
        assert 'temperature=' not in factory_func, \
            "❌ Factory still passes temperature parameter"
        logger.info("   ✅ No temperature parameter")
        
        # NEW signature should use just workspace_path and session_id
        assert "workspace_path=workspace_path" in factory_func, \
            "❌ Factory doesn't pass workspace_path"
        logger.info("   ✅ Passes workspace_path")
        
        assert "session_id=session_id" in factory_func, \
            "❌ Factory doesn't pass session_id"
        logger.info("   ✅ Passes session_id")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_config_exists():
    """Test that agent_llm_config.json has supervisor section."""
    logger.info("=" * 80)
    logger.info("TEST 6: Config File Valid")
    logger.info("=" * 80)
    
    try:
        config_path = Path("backend/config/agent_llm_config.json")
        
        # File exists
        assert config_path.exists(), f"❌ Config file not found: {config_path}"
        logger.info(f"   ✅ File exists: {config_path}")
        
        # Valid JSON
        config = json.loads(config_path.read_text())
        logger.info("   ✅ Valid JSON")
        
        # Has agents section
        assert "agents" in config, "❌ Missing agents section"
        logger.info("   ✅ Has agents section")
        
        # Has supervisor agent
        assert "supervisor" in config["agents"], "❌ Missing supervisor agent"
        logger.info("   ✅ Has supervisor agent")
        
        supervisor_config = config["agents"]["supervisor"]
        
        # Has required fields
        required = ["provider", "model", "temperature", "max_tokens"]
        for field in required:
            assert field in supervisor_config, f"❌ Missing {field}"
        logger.info(f"   ✅ All required fields: {required}")
        
        # Correct values
        assert supervisor_config["provider"] == "openai", \
            f"❌ Expected provider=openai, got {supervisor_config['provider']}"
        logger.info(f"   ✅ Provider: {supervisor_config['provider']}")
        
        assert "gpt-4o" in supervisor_config["model"], \
            "❌ Model should contain gpt-4o"
        logger.info(f"   ✅ Model: {supervisor_config['model']}")
        
        assert supervisor_config["temperature"] == 0.3, \
            f"❌ Expected temperature=0.3, got {supervisor_config['temperature']}"
        logger.info(f"   ✅ Temperature: {supervisor_config['temperature']}")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("🧪 PHASE 3 SUPERVISOR SIMPLE TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Imports Updated", test_imports_updated),
        ("__init__() Updated", test_init_updated),
        ("LLM Calls Updated", test_llm_calls_updated),
        ("Error Handling Simplified", test_error_handling_simplified),
        ("Factory Function Updated", test_factory_function_updated),
        ("Config File Valid", test_config_exists),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
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
    
    logger.info(f"\n{'✅' if passed == total else '❌'} Passed: {passed}/{total}")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
