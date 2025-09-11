#!/usr/bin/env python3
"""
Claude Web Proxy - Quick Test Script
Fast validation and testing for Claude Web Proxy functionality
"""
import asyncio
import aiohttp
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from claude_web_proxy.crewai_integration import create_claude_web_llm


async def quick_health_check(server_url: str = "http://localhost:8000") -> bool:
    """Quick health check of the server"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{server_url}/", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server healthy: {data.get('message', 'OK')}")
                    return True
                else:
                    print(f"❌ Server unhealthy: Status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot reach server: {e}")
        return False


async def quick_status_check(server_url: str = "http://localhost:8000") -> dict:
    """Quick status check"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{server_url}/claude/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    browser_running = data.get("browser_running", False)
                    logged_in = data.get("logged_in", False)
                    uptime = data.get("uptime_seconds", 0)
                    
                    print(f"🤖 Browser running: {'✅' if browser_running else '❌'}")
                    print(f"🔐 Logged in: {'✅' if logged_in else '❌'}")
                    print(f"⏰ Uptime: {uptime:.1f}s")
                    
                    return data
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return {}
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return {}


async def quick_message_test(server_url: str = "http://localhost:8000") -> bool:
    """Quick message test"""
    test_message = "Hello! Please respond with just 'Hello back!' to confirm you're working."
    
    try:
        claude_llm = create_claude_web_llm(server_url=server_url)
        
        print(f"💬 Sending test message: {test_message}")
        start_time = time.time()
        
        response = claude_llm.generate(test_message)
        
        duration = time.time() - start_time
        print(f"🤖 Response received in {duration:.2f}s:")
        print(f"📄 {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Message test failed: {e}")
        return False


async def quick_agent_test(server_url: str = "http://localhost:8000") -> bool:
    """Quick agent-specific conversation test"""
    try:
        claude_llm = create_claude_web_llm(
            server_url=server_url,
            new_conversation_per_agent=True
        )
        
        agents = ["TestAgent1", "TestAgent2"]
        
        for agent in agents:
            print(f"🤖 Testing {agent}...")
            
            response = claude_llm.generate(
                f"Hi, I'm {agent}. What's 1+1?",
                agent_id=agent
            )
            
            print(f"✅ {agent} response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False


async def run_quick_tests():
    """Run all quick tests"""
    print("🚀 CLAUDE WEB PROXY - QUICK TEST")
    print("=" * 40)
    
    server_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n1️⃣ Health Check...")
    healthy = await quick_health_check(server_url)
    
    if not healthy:
        print("\n❌ Server not healthy. Make sure it's running:")
        print("   python setup_and_test.py --server-only")
        return
    
    # Test 2: Status check
    print("\n2️⃣ Status Check...")
    status = await quick_status_check(server_url)
    
    if not status.get("browser_running", False):
        print("\n⚠️  Browser not running. Try setup:")
        print("   curl -X POST http://localhost:8000/claude/setup")
        
    if not status.get("logged_in", False):
        print("\n⚠️  Not logged in. Manual login required:")
        print("   1. Browser will open automatically during setup")
        print("   2. Log into Claude.ai manually")
        
    # Test 3: Simple message test (if logged in)
    if status.get("logged_in", False):
        print("\n3️⃣ Message Test...")
        await quick_message_test(server_url)
        
        print("\n4️⃣ Agent Conversation Test...")
        await quick_agent_test(server_url)
        
        print("\n🎉 ALL TESTS PASSED!")
        print("Claude Web Proxy is fully functional!")
        
    else:
        print("\n⏭️  Skipping message tests (not logged in)")
        print("Complete the login process first:")
        print("1. Run: python setup_and_test.py")
        print("2. Log into Claude.ai when browser opens")
        print("3. Run this test again")
    
    print("\n" + "=" * 40)


def print_instructions():
    """Print usage instructions"""
    print("Claude Web Proxy - Quick Test")
    print("============================")
    print()
    print("This script quickly validates your Claude Web Proxy setup.")
    print()
    print("Prerequisites:")
    print("1. 🖥️  Server running: python setup_and_test.py --server-only")
    print("2. 🌐 Logged into Claude.ai (manual login required)")
    print()
    print("Usage:")
    print("  python quick_test.py          # Run all tests")
    print("  python quick_test.py --help   # Show this help")
    print()
    print("What this tests:")
    print("• ✅ Server health and connectivity")
    print("• ✅ Browser automation status") 
    print("• ✅ Claude.ai login status")
    print("• ✅ Basic message sending/receiving")
    print("• ✅ Agent-specific conversations")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_instructions()
    else:
        asyncio.run(run_quick_tests())