#!/usr/bin/env python3
"""
Multi-Agent Claude Web Demo
Demonstrates how multiple KI_AutoAgent agents can use Claude Web simultaneously
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import time
import signal

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from claude_web_proxy.crewai_integration import create_claude_web_llm
from orchestration.master_dispatcher import MasterDispatcher


class MultiAgentClaudeWebDemo:
    """Demonstration of multiple agents using Claude Web simultaneously"""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.server_process = None
        self.dispatcher = None
        
    def start_claude_web_server(self):
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
            print("✅ Claude Web Proxy server started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_claude_web_server(self):
        """Stop the Claude Web Proxy server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                print("🛑 Claude Web Proxy server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            finally:
                self.server_process = None
    
    async def demonstrate_agent_coordination(self):
        """Demonstrate how agents coordinate using Claude Web"""
        print("\n" + "="*80)
        print("🎭 MULTI-AGENT CLAUDE WEB COORDINATION DEMO")
        print("="*80)
        
        # Create Claude Web LLM instances for different agents
        claude_agents = {
            "CodeSmithClaude": create_claude_web_llm(
                server_url=self.server_url,
                new_conversation_per_agent=True
            ),
            "FixerBot": create_claude_web_llm(
                server_url=self.server_url, 
                new_conversation_per_agent=True
            ),
            "TradeStrat": create_claude_web_llm(
                server_url=self.server_url,
                new_conversation_per_agent=True
            )
        }
        
        # Simulate a complex development task
        print("\n📋 Task: Create a simple trading strategy with error handling")
        
        tasks = [
            {
                "agent": "CodeSmithClaude",
                "task": "Write a simple moving average crossover trading strategy in Python",
                "context": "Development Phase"
            },
            {
                "agent": "FixerBot", 
                "task": "Review the trading strategy code for potential bugs and edge cases",
                "context": "Quality Assurance Phase"
            },
            {
                "agent": "TradeStrat",
                "task": "Analyze the strategy logic and suggest risk management improvements",
                "context": "Strategy Analysis Phase"
            }
        ]
        
        results = {}
        
        for task_info in tasks:
            agent_name = task_info["agent"]
            task_prompt = task_info["task"]
            context = task_info["context"]
            
            print(f"\n🤖 {agent_name} - {context}")
            print(f"📝 Task: {task_prompt}")
            
            try:
                # Use agent-specific conversation
                response = claude_agents[agent_name].generate(
                    task_prompt,
                    agent_id=agent_name
                )
                
                results[agent_name] = response
                print(f"✅ Response received ({len(response)} chars)")
                print(f"📄 Preview: {response[:200]}...")
                
                # Small delay between agents to avoid overwhelming
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error for {agent_name}: {e}")
                results[agent_name] = f"Error: {str(e)}"
        
        return results
    
    async def demonstrate_conversation_continuity(self):
        """Demonstrate conversation continuity per agent"""
        print("\n" + "="*80)
        print("💬 CONVERSATION CONTINUITY DEMO")
        print("="*80)
        
        claude_llm = create_claude_web_llm(
            server_url=self.server_url,
            new_conversation_per_agent=True
        )
        
        # Simulate a multi-turn conversation with an agent
        conversation_turns = [
            {
                "agent": "CodeSmithClaude",
                "message": "Hello! I'm CodeSmithClaude. I need help with a Python function."
            },
            {
                "agent": "CodeSmithClaude", 
                "message": "Can you write a function to calculate fibonacci numbers?"
            },
            {
                "agent": "CodeSmithClaude",
                "message": "Now can you optimize that function using memoization?"
            },
            {
                "agent": "FixerBot",
                "message": "Hi, I'm FixerBot. What's the most common bug in Python?"
            },
            {
                "agent": "CodeSmithClaude",
                "message": "Thanks for the fibonacci help earlier. Can you add error handling?"
            }
        ]
        
        for i, turn in enumerate(conversation_turns, 1):
            agent = turn["agent"]
            message = turn["message"]
            
            print(f"\n🔄 Turn {i} - {agent}")
            print(f"💭 Message: {message}")
            
            try:
                response = claude_llm.generate(message, agent_id=agent)
                print(f"🤖 Response: {response[:150]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(1.5)
    
    async def demonstrate_parallel_agent_execution(self):
        """Demonstrate parallel execution with multiple agents"""
        print("\n" + "="*80)
        print("⚡ PARALLEL AGENT EXECUTION DEMO")  
        print("="*80)
        
        claude_llm = create_claude_web_llm(server_url=self.server_url)
        
        # Create multiple concurrent tasks for different agents
        parallel_tasks = [
            ("ArchitectGPT", "Design a microservices architecture for a trading platform"),
            ("CodeSmithClaude", "Write a Python REST API endpoint for user authentication"),
            ("DocuBot", "Create documentation for a trading bot API"),
            ("ReviewerGPT", "Review security considerations for financial APIs"),
            ("TradeStrat", "Explain the momentum trading strategy in simple terms")
        ]
        
        print(f"🚀 Starting {len(parallel_tasks)} parallel agent tasks...")
        
        async def agent_task(agent_name: str, task: str) -> Dict[str, str]:
            """Execute a single agent task"""
            try:
                start_time = time.time()
                response = await claude_llm.agenerate(task, agent_id=agent_name)
                duration = time.time() - start_time
                
                return {
                    "agent": agent_name,
                    "task": task,
                    "response": response,
                    "duration": duration,
                    "status": "success"
                }
                
            except Exception as e:
                return {
                    "agent": agent_name, 
                    "task": task,
                    "error": str(e),
                    "status": "error"
                }
        
        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[agent_task(agent, task) for agent, task in parallel_tasks],
            return_exceptions=True
        )
        
        # Display results
        print(f"\n📊 Results from {len(results)} parallel executions:")
        
        for result in results:
            if isinstance(result, dict):
                agent = result.get("agent", "Unknown")
                status = result.get("status", "unknown")
                
                if status == "success":
                    duration = result.get("duration", 0)
                    response_len = len(result.get("response", ""))
                    print(f"✅ {agent}: {response_len} chars in {duration:.2f}s")
                else:
                    error = result.get("error", "Unknown error")
                    print(f"❌ {agent}: {error}")
            else:
                print(f"⚠️  Exception: {result}")
    
    async def run_comprehensive_demo(self):
        """Run the complete multi-agent demo"""
        print("🎯 MULTI-AGENT CLAUDE WEB INTEGRATION DEMO")
        print("This demo shows advanced Claude Web usage with multiple agents")
        print()
        
        # Start the server
        if not self.start_claude_web_server():
            print("❌ Cannot continue without Claude Web Proxy server")
            return
        
        try:
            print("⏳ Warming up system...")
            await asyncio.sleep(3)
            
            # Run all demonstrations
            await self.demonstrate_agent_coordination()
            await self.demonstrate_conversation_continuity()
            await self.demonstrate_parallel_agent_execution()
            
            print("\n" + "="*80)
            print("🎉 MULTI-AGENT DEMO COMPLETE!")
            print("="*80)
            
            print("\n🚀 What you've seen:")
            print("✅ Multiple agents using Claude Web simultaneously")
            print("✅ Per-agent conversation tracking and continuity")
            print("✅ Parallel execution with proper resource management")
            print("✅ Error handling and graceful degradation")
            
            print("\n💡 Key Benefits:")
            print("• No Claude API costs - uses your existing Max Plan")
            print("• Full Claude capabilities through browser automation")
            print("• Separate conversations per agent maintain context")
            print("• Robust error handling and recovery mechanisms")
            
            print("\n🔧 Integration with KI_AutoAgent:")
            print("• Replace direct Claude API calls with Claude Web LLM")
            print("• Maintains full CrewAI compatibility") 
            print("• Transparent to existing agent implementations")
            print("• Scales to handle multiple concurrent agents")
            
        finally:
            self.stop_claude_web_server()


async def main():
    """Main function with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent Claude Web Demo")
    parser.add_argument("--demo", action="store_true", help="Run full demo")
    parser.add_argument("--coordination", action="store_true", help="Agent coordination demo")
    parser.add_argument("--continuity", action="store_true", help="Conversation continuity demo")
    parser.add_argument("--parallel", action="store_true", help="Parallel execution demo")
    
    args = parser.parse_args()
    
    demo = MultiAgentClaudeWebDemo()
    
    if args.coordination:
        if demo.start_claude_web_server():
            try:
                await demo.demonstrate_agent_coordination()
            finally:
                demo.stop_claude_web_server()
    
    elif args.continuity:
        if demo.start_claude_web_server():
            try:
                await demo.demonstrate_conversation_continuity()
            finally:
                demo.stop_claude_web_server()
    
    elif args.parallel:
        if demo.start_claude_web_server():
            try:
                await demo.demonstrate_parallel_agent_execution()
            finally:
                demo.stop_claude_web_server()
    
    elif args.demo:
        await demo.run_comprehensive_demo()
    
    else:
        print("Multi-Agent Claude Web Integration Demo")
        print("=====================================")
        print()
        print("Usage:")
        print("  python multi_agent_claude_web_demo.py --demo         # Full demo")
        print("  python multi_agent_claude_web_demo.py --coordination # Agent coordination")
        print("  python multi_agent_claude_web_demo.py --continuity   # Conversation continuity")
        print("  python multi_agent_claude_web_demo.py --parallel     # Parallel execution")
        print()
        print("Prerequisites:")
        print("1. 🌐 Be logged into Claude.ai in your browser")
        print("2. 📦 Install dependencies: pip install -r requirements.txt")
        print("3. 🎭 Install Playwright: python -m playwright install chromium")
        print()
        print("This demo shows how the KI_AutoAgent system can use Claude Web")
        print("instead of direct API access, saving costs while maintaining")
        print("full functionality for all Claude-based agents.")


if __name__ == "__main__":
    asyncio.run(main())