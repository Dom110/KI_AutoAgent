#!/usr/bin/env python3
"""
Claude Web Integration Example
Demonstrates how to use the Claude Web Proxy with the KI_AutoAgent system
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from claude_web_proxy.crewai_integration import ClaudeWebLLM, create_claude_web_llm
from claude_web_proxy.fastapi_server import run_server
import subprocess
import time
import signal

class ClaudeWebIntegrationDemo:
    """Demonstration of Claude Web integration with KI_AutoAgent"""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.server_process = None
        
    def start_proxy_server(self):
        """Start the Claude Web Proxy server"""
        print("🚀 Starting Claude Web Proxy server...")
        
        try:
            self.server_process = subprocess.Popen([
                "python", "-m", "uvicorn",
                "claude_web_proxy.fastapi_server:app",
                "--host", "0.0.0.0",
                "--port", "8000"
            ], cwd=Path(__file__).parent.parent)
            
            # Wait for server to start
            time.sleep(5)
            print("✅ Server started at http://localhost:8000")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_proxy_server(self):
        """Stop the Claude Web Proxy server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                print("🛑 Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            finally:
                self.server_process = None
    
    async def demo_direct_llm_usage(self):
        """Demonstrate direct LLM usage with Claude Web"""
        print("\n" + "="*60)
        print("📝 Demo 1: Direct Claude Web LLM Usage")
        print("="*60)
        
        # Create Claude Web LLM instance
        claude_llm = create_claude_web_llm(server_url=self.server_url)
        
        # Display model info
        model_info = claude_llm.get_model_info()
        print(f"🤖 Model Info:")
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        # Test basic generation
        test_prompt = "Hello! Can you explain what you are and how you work in 2-3 sentences?"
        
        print(f"\n💬 Sending prompt: {test_prompt}")
        
        try:
            response = claude_llm.generate(test_prompt)
            print(f"✅ Response received:")
            print(f"   {response}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Note: Make sure you're logged into Claude.ai in your browser")
    
    async def demo_async_usage(self):
        """Demonstrate async usage with Claude Web"""
        print("\n" + "="*60)
        print("📝 Demo 2: Async Claude Web LLM Usage")
        print("="*60)
        
        claude_llm = create_claude_web_llm(server_url=self.server_url)
        
        test_prompt = "What are the key benefits of using async/await in Python?"
        
        print(f"💬 Sending async prompt: {test_prompt}")
        
        try:
            response = await claude_llm.agenerate(test_prompt)
            print(f"✅ Async response received:")
            print(f"   {response}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Note: Make sure the Claude Web Proxy server is running")
    
    async def demo_agent_conversation_tracking(self):
        """Demonstrate agent conversation tracking"""
        print("\n" + "="*60)
        print("📝 Demo 3: Agent Conversation Tracking")
        print("="*60)
        
        claude_llm = create_claude_web_llm(
            server_url=self.server_url,
            new_conversation_per_agent=True
        )
        
        # Simulate different agents having conversations
        agents = ["ArchitectGPT", "CodeSmithClaude", "DocuBot"]
        
        for agent in agents:
            print(f"\n🤖 Agent: {agent}")
            prompt = f"Hi, I'm {agent}. What's 2+2?"
            
            try:
                response = claude_llm.generate(prompt, agent_id=agent)
                print(f"✅ Response: {response[:100]}...")
                
            except Exception as e:
                print(f"❌ Error for {agent}: {e}")
    
    async def demo_crewai_integration(self):
        """Demonstrate potential CrewAI integration"""
        print("\n" + "="*60)
        print("📝 Demo 4: CrewAI Integration Concept")
        print("="*60)
        
        print("🔧 This demonstrates how Claude Web could be integrated with CrewAI:")
        print()
        
        # Show how to create an agent with Claude Web LLM
        code_example = '''
from crewai import Agent
from claude_web_proxy.crewai_integration import create_claude_web_llm

# Create Claude Web LLM
claude_llm = create_claude_web_llm(server_url="http://localhost:8000")

# Create CrewAI Agent using Claude Web
agent = Agent(
    role="Senior Software Developer",
    goal="Write high-quality Python code",
    backstory="You are an expert Python developer with years of experience",
    llm=claude_llm,
    verbose=True
)

# The agent would now use Claude Web for responses
'''
        
        print("💻 Example Code:")
        print(code_example)
        print("⚠️  Note: This requires CrewAI to be installed and configured")
    
    async def demo_streaming_concept(self):
        """Demonstrate streaming concept"""
        print("\n" + "="*60)
        print("📝 Demo 5: Streaming Concept")
        print("="*60)
        
        claude_llm = create_claude_web_llm(server_url=self.server_url)
        
        print("💫 Streaming simulation (Claude Web doesn't support true streaming):")
        
        try:
            prompt = "Explain Python decorators in simple terms"
            
            # Use the streaming generator
            async for chunk in claude_llm.astream_generate(prompt):
                print(f"📤 Received chunk: {chunk[:50]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def run_full_demo(self):
        """Run the complete demonstration"""
        print("🎯 Claude Web Integration Demo")
        print("This demo shows how to integrate Claude Web with KI_AutoAgent")
        print()
        
        # Start server
        if not self.start_proxy_server():
            print("❌ Cannot continue without proxy server")
            return
        
        try:
            # Run all demos
            await self.demo_direct_llm_usage()
            await self.demo_async_usage()
            await self.demo_agent_conversation_tracking()
            await self.demo_crewai_integration()
            await self.demo_streaming_concept()
            
            print("\n" + "="*60)
            print("🎉 Demo Complete!")
            print()
            print("Next Steps:")
            print("1. 🌐 Open browser and log into Claude.ai")
            print("2. 🔧 Call /claude/setup endpoint to initialize")
            print("3. 💬 Start sending messages via the API")
            print("4. 🚀 Integrate with your KI_AutoAgent workflows")
            
        finally:
            # Clean shutdown
            self.stop_proxy_server()
    
    def interactive_mode(self):
        """Interactive mode for testing"""
        print("\n🎮 Interactive Mode")
        print("Commands:")
        print("  'q' or 'quit' - Exit")
        print("  'help' - Show this help")
        print("  'status' - Check server status")
        print("  anything else - Send to Claude Web")
        
        claude_llm = create_claude_web_llm(server_url=self.server_url)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['q', 'quit']:
                    break
                elif user_input.lower() == 'help':
                    print("Available commands: q, quit, help, status, or any message")
                elif user_input.lower() == 'status':
                    print("🔍 Checking server status...")
                    # This would check server health
                    print("Server should be running at http://localhost:8000")
                elif user_input:
                    print(f"💬 Sending: {user_input}")
                    try:
                        response = claude_llm.generate(user_input)
                        print(f"🤖 Claude: {response}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        
            except KeyboardInterrupt:
                break
        
        print("👋 Goodbye!")


async def main():
    """Main function with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Web Integration Demo")
    parser.add_argument("--demo", action="store_true", help="Run full demo")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--server-only", action="store_true", help="Only start server")
    
    args = parser.parse_args()
    
    demo = ClaudeWebIntegrationDemo()
    
    if args.server_only:
        print("🖥️  Starting Claude Web Proxy server only...")
        if demo.start_proxy_server():
            try:
                print("✅ Server running. Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                demo.stop_proxy_server()
    
    elif args.interactive:
        if demo.start_proxy_server():
            try:
                demo.interactive_mode()
            finally:
                demo.stop_proxy_server()
        else:
            print("❌ Cannot start interactive mode without server")
    
    elif args.demo:
        await demo.run_full_demo()
    
    else:
        print("Claude Web Integration Example")
        print("Usage:")
        print("  python claude_web_integration_example.py --demo")
        print("  python claude_web_integration_example.py --interactive")
        print("  python claude_web_integration_example.py --server-only")
        print()
        print("Make sure to:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Playwright browsers: playwright install chromium")
        print("3. Log into Claude.ai in your browser")


if __name__ == "__main__":
    asyncio.run(main())