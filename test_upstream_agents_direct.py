#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC TEST: Check if upstream agents return data via MCP

Tests:
1. Research Agent - does it return research_context?
2. Architect Agent - does it return architecture?
3. Codesmith Agent - does it return generated_files?

We'll test each agent independently and check MCP response structure.
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

# Setup logging to see all details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_upstream_agents")

sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.mcp_manager import get_mcp_manager


async def test_research_agent():
    """Test if Research Agent returns data via MCP"""
    print("\n" + "="*60)
    print("🔍 TEST 1: RESEARCH AGENT (MCP)")
    print("="*60)
    
    try:
        # Get MCP manager
        mcp = get_mcp_manager(workspace_path="/tmp")
        await mcp.initialize()
        
        # Call research agent
        logger.info("📡 Calling Research Agent via MCP...")
        result = await mcp.call(
            server="research_agent",
            tool="research",
            arguments={
                "instructions": "analyze test workspace",
                "workspace_path": "/tmp",
                "error_info": []
            }
        )
        
        logger.info(f"✅ RESEARCH RESPONSE RECEIVED")
        logger.info(f"   Response type: {type(result)}")
        logger.info(f"   Response keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            content = result.get("content", [])
            logger.info(f"   Content type: {type(content)}")
            logger.info(f"   Content length: {len(content) if isinstance(content, list) else 'N/A'}")
            
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                logger.info(f"   Text content (first 200 chars): {text_content[:200]}")
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(text_content)
                    logger.info(f"   ✅ Parsed JSON keys: {list(parsed.keys())}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"   ❌ Failed to parse JSON: {e}")
                    return None
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Research test failed: {e}", exc_info=True)
        return None


async def test_architect_agent():
    """Test if Architect Agent returns data via MCP"""
    print("\n" + "="*60)
    print("🔍 TEST 2: ARCHITECT AGENT (MCP)")
    print("="*60)
    
    try:
        # Get MCP manager
        mcp = get_mcp_manager(workspace_path="/tmp")
        await mcp.initialize()
        
        # Sample research context from previous test
        research_context = {
            "workspace_analysis": {
                "project_type": "Python",
                "file_count": 10
            }
        }
        
        # Call architect agent
        logger.info("📡 Calling Architect Agent via MCP...")
        result = await mcp.call(
            server="architect_agent",
            tool="design",
            arguments={
                "instructions": "design test architecture",
                "research_context": research_context,
                "workspace_path": "/tmp"
            }
        )
        
        logger.info(f"✅ ARCHITECT RESPONSE RECEIVED")
        logger.info(f"   Response type: {type(result)}")
        logger.info(f"   Response keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            content = result.get("content", [])
            logger.info(f"   Content type: {type(content)}")
            logger.info(f"   Content length: {len(content) if isinstance(content, list) else 'N/A'}")
            
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                logger.info(f"   Text content (first 200 chars): {text_content[:200]}")
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(text_content)
                    logger.info(f"   ✅ Parsed JSON keys: {list(parsed.keys())}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"   ❌ Failed to parse JSON: {e}")
                    return None
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Architect test failed: {e}", exc_info=True)
        return None


async def test_codesmith_agent():
    """Test if Codesmith Agent returns data via MCP"""
    print("\n" + "="*60)
    print("🔍 TEST 3: CODESMITH AGENT (MCP)")
    print("="*60)
    
    try:
        # Get MCP manager
        mcp = get_mcp_manager(workspace_path="/tmp")
        await mcp.initialize()
        
        # Sample architecture from previous test
        architecture = {
            "layers": ["api", "core", "utils"],
            "components": ["server", "database"]
        }
        
        # Call codesmith agent
        logger.info("📡 Calling Codesmith Agent via MCP...")
        result = await mcp.call(
            server="codesmith_agent",
            tool="generate",
            arguments={
                "instructions": "generate test code",
                "architecture": architecture,
                "workspace_path": "/tmp"
            }
        )
        
        logger.info(f"✅ CODESMITH RESPONSE RECEIVED")
        logger.info(f"   Response type: {type(result)}")
        logger.info(f"   Response keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            content = result.get("content", [])
            logger.info(f"   Content type: {type(content)}")
            logger.info(f"   Content length: {len(content) if isinstance(content, list) else 'N/A'}")
            
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                logger.info(f"   Text content (first 200 chars): {text_content[:200]}")
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(text_content)
                    logger.info(f"   ✅ Parsed JSON keys: {list(parsed.keys())}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"   ❌ Failed to parse JSON: {e}")
                    return None
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Codesmith test failed: {e}", exc_info=True)
        return None


async def main():
    """Run all upstream agent tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "UPSTREAM AGENTS DIAGNOSTIC TEST" + " "*13 + "║")
    print("║" + " "*10 + "Testing if agents return data via MCP calls" + " "*5 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        # Test each agent
        research_data = await test_research_agent()
        architect_data = await test_architect_agent()
        codesmith_data = await test_codesmith_agent()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Research Agent returned data: {research_data is not None}")
        print(f"✅ Architect Agent returned data: {architect_data is not None}")
        print(f"✅ Codesmith Agent returned data: {codesmith_data is not None}")
        
        if research_data:
            print(f"   Research keys: {list(research_data.keys())}")
        if architect_data:
            print(f"   Architect keys: {list(architect_data.keys())}")
        if codesmith_data:
            print(f"   Codesmith keys: {list(codesmith_data.keys())}")
        
        # Check if all agents returned data
        all_good = research_data is not None and architect_data is not None and codesmith_data is not None
        if all_good:
            print("\n✅ ALL AGENTS RETURNING DATA - Data flow is working!")
        else:
            print("\n❌ SOME AGENTS NOT RETURNING DATA - Data flow problem detected!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())