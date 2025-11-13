#!/usr/bin/env python3
"""Direct Responder Agent test for debugging"""
import asyncio
import sys
sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent')

from backend.utils.mcp_manager import get_mcp_manager

async def test_responder():
    """Test responder format_response tool directly"""
    mcp = get_mcp_manager(workspace_path="/tmp/test_responder")
    await mcp.initialize()  # ⚠️ IMPORTANT: Initialize MCP manager first
    
    # Simple test result with actual data
    workflow_result = {
        "summary": "Test API created successfully",
        "generated_files": [
            {"path": "main.py", "description": "FastAPI server"},
            {"path": "requirements.txt", "description": "Dependencies"}
        ],
        "architecture": {
            "description": "REST API with FastAPI",
            "components": ["Router", "Database", "Models"],
            "technologies": ["FastAPI", "Pydantic", "SQLite"]
        }
    }
    
    try:
        print("📤 Calling responder_agent.format_response...")
        result = await mcp.call(
            server="responder_agent",
            tool="format_response",
            arguments={
                "workflow_result": workflow_result,
                "status": "success"
            }
        )
        print(f"✅ Result type: {type(result)}")
        print(f"✅ Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            content = result.get("content", [])
            print(f"✅ Content length: {len(content)}")
            if content:
                text = content[0].get("text", "")
                print(f"✅ Response length: {len(text)} chars")
                print(f"✅ First 300 chars:\n{text[:300]}")
                if len(text) > 500:
                    print(f"... (truncated, total {len(text)} chars)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_responder())