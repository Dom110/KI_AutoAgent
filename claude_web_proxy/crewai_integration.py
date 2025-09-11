"""
CrewAI Integration for Claude Web Proxy
Custom LLM implementation that uses Claude Web via REST API
"""
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List, Union
import structlog

# Try to import CrewAI components - graceful fallback if not installed
try:
    from crewai.llm import BaseLLM
    from crewai.agent import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    # Create dummy base class if CrewAI not available
    class BaseLLM:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate(self, prompt: str) -> str:
            raise NotImplementedError("CrewAI not installed")
    
    CREWAI_AVAILABLE = False

logger = structlog.get_logger()

class ClaudeWebLLM(BaseLLM):
    """
    Custom LLM implementation that uses Claude Web via REST API
    Compatible with CrewAI Agent system
    """
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 timeout: int = 120,
                 new_conversation_per_agent: bool = True,
                 **kwargs):
        """
        Initialize Claude Web LLM
        
        Args:
            server_url: URL of the Claude Web Proxy server
            timeout: Timeout for API calls in seconds
            new_conversation_per_agent: Start new conversation for each agent
            **kwargs: Additional arguments passed to BaseLLM
        """
        super().__init__(**kwargs)
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.new_conversation_per_agent = new_conversation_per_agent
        self._session: Optional[aiohttp.ClientSession] = None
        self._agent_conversations: Dict[str, str] = {}  # Track conversations per agent
        
        logger.info("Initialized Claude Web LLM", 
                   server_url=self.server_url, 
                   timeout=self.timeout)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self._session
    
    async def _check_server_status(self) -> bool:
        """Check if Claude Web Proxy server is running and ready"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.server_url}/claude/status") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('logged_in', False)
                return False
        except Exception as e:
            logger.error("Failed to check server status", error=str(e))
            return False
    
    async def _ensure_setup(self) -> bool:
        """Ensure Claude Web Proxy is set up and ready"""
        try:
            if await self._check_server_status():
                return True
            
            logger.info("Claude Web Proxy not ready, attempting setup...")
            session = await self._get_session()
            
            # Attempt setup (this will require manual login if not already logged in)
            setup_data = {
                "headless": False,  # Always use visible browser for setup
                "timeout": 300
            }
            
            async with session.post(f"{self.server_url}/claude/setup", json=setup_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Setup completed", status=result.get('status'))
                    return result.get('status') == 'success'
                else:
                    error_text = await response.text()
                    logger.error("Setup failed", status=response.status, error=error_text)
                    return False
                    
        except Exception as e:
            logger.error("Error during setup", error=str(e))
            return False
    
    async def _send_message_async(self, 
                                 prompt: str, 
                                 agent_id: Optional[str] = None,
                                 **kwargs) -> str:
        """
        Send message to Claude Web asynchronously
        
        Args:
            prompt: The prompt/message to send
            agent_id: Optional agent identifier for conversation tracking
            **kwargs: Additional arguments
            
        Returns:
            Claude's response
        """
        try:
            # Ensure server is ready
            if not await self._ensure_setup():
                raise Exception("Claude Web Proxy is not ready. Please run setup first.")
            
            session = await self._get_session()
            
            # Prepare request data
            request_data = {
                "message": prompt,
                "new_conversation": False
            }
            
            # Handle new conversation logic
            if self.new_conversation_per_agent and agent_id:
                # Check if this is the first message from this agent
                if agent_id not in self._agent_conversations:
                    request_data["new_conversation"] = True
                    self._agent_conversations[agent_id] = "active"
                    logger.info("Starting new conversation for agent", agent_id=agent_id)
            
            # Send message to Claude
            async with session.post(f"{self.server_url}/claude/chat", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get('response', '')
                    
                    logger.info("Received response from Claude Web", 
                               prompt_length=len(prompt),
                               response_length=len(response_text))
                    
                    return response_text
                else:
                    error_text = await response.text()
                    logger.error("Chat request failed", 
                               status=response.status, 
                               error=error_text)
                    raise Exception(f"Chat request failed: {error_text}")
                    
        except Exception as e:
            logger.error("Error sending message to Claude Web", error=str(e))
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response from Claude (synchronous interface for CrewAI)
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments
            
        Returns:
            Generated response
        """
        try:
            # Extract agent context if available
            agent_id = kwargs.get('agent_id') or kwargs.get('agent_name')
            
            # Run async method in event loop
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(self._send_message_async(prompt, agent_id, **kwargs))
            
            # If we're in an async context, we need to handle this carefully
            if loop.is_running():
                # Create a new event loop in a thread (this is a fallback)
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self._send_message_async(prompt, agent_id, **kwargs)
                        )
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=self.timeout)
            else:
                return loop.run_until_complete(self._send_message_async(prompt, agent_id, **kwargs))
                
        except Exception as e:
            logger.error("Error in generate method", error=str(e))
            return f"Error generating response: {str(e)}"
    
    async def agenerate(self, prompt: str, **kwargs) -> str:
        """
        Async version of generate (for async CrewAI usage)
        """
        agent_id = kwargs.get('agent_id') or kwargs.get('agent_name')
        return await self._send_message_async(prompt, agent_id, **kwargs)
    
    def stream_generate(self, prompt: str, **kwargs):
        """
        Streaming generation (yields chunks of response)
        Note: Claude Web doesn't support streaming via our proxy,
        so this just yields the complete response
        """
        response = self.generate(prompt, **kwargs)
        yield response
    
    async def astream_generate(self, prompt: str, **kwargs):
        """Async streaming generation"""
        response = await self.agenerate(prompt, **kwargs)
        yield response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model_name": "Claude Web",
            "provider": "Anthropic (via Web Interface)",
            "type": "conversational",
            "capabilities": ["text_generation", "conversation", "analysis"],
            "proxy_server": self.server_url
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP session closed")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # Try to close session, but don't fail if we can't
            try:
                # Check if we're in an async context and event loop is running
                try:
                    loop = asyncio.get_running_loop()
                    if not loop.is_closed():
                        # Schedule cleanup task
                        loop.create_task(self._session.close())
                except RuntimeError:
                    # No event loop running, try to close synchronously
                    # This may show a warning, but it's better than leaving it open
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", ResourceWarning)
                        try:
                            # Close the session directly - this may generate warnings
                            # but it's the safest approach when no event loop is available
                            pass  # Let it be handled by the session's own cleanup
                        except:
                            pass
            except Exception:
                # Completely silent fallback
                pass


# Convenience functions for CrewAI integration
def create_claude_web_agent(role: str,
                           goal: str,
                           backstory: str,
                           server_url: str = "http://localhost:8000",
                           **kwargs) -> 'Agent':
    """
    Create a CrewAI Agent that uses Claude Web
    
    Args:
        role: Agent role
        goal: Agent goal
        backstory: Agent backstory
        server_url: Claude Web Proxy server URL
        **kwargs: Additional Agent arguments
        
    Returns:
        CrewAI Agent configured with Claude Web LLM
    """
    if not CREWAI_AVAILABLE:
        raise ImportError("CrewAI is not installed. Install with: pip install crewai")
    
    # Create Claude Web LLM
    claude_llm = ClaudeWebLLM(server_url=server_url)
    
    # Create and return Agent
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=claude_llm,
        **kwargs
    )


def create_claude_web_llm(server_url: str = "http://localhost:8000", **kwargs) -> ClaudeWebLLM:
    """
    Create a Claude Web LLM instance
    
    Args:
        server_url: Claude Web Proxy server URL
        **kwargs: Additional arguments
        
    Returns:
        Configured ClaudeWebLLM instance
    """
    return ClaudeWebLLM(server_url=server_url, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    async def test_claude_web_llm():
        """Test the Claude Web LLM"""
        llm = ClaudeWebLLM()
        
        try:
            # Test basic generation
            response = await llm.agenerate("Hello! What's 2 + 2?")
            print(f"Claude's response: {response}")
            
            # Test with agent context
            response2 = await llm.agenerate(
                "Can you help me with Python coding?", 
                agent_id="test_agent"
            )
            print(f"Claude's response 2: {response2}")
            
        except Exception as e:
            print(f"Error testing Claude Web LLM: {e}")
        finally:
            await llm.cleanup()
    
    # Run test if CrewAI is available
    if CREWAI_AVAILABLE:
        print("Testing Claude Web LLM...")
        asyncio.run(test_claude_web_llm())
    else:
        print("CrewAI not available. Install with: pip install crewai")
        print("You can still use ClaudeWebLLM directly for basic functionality.")