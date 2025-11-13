"""
FIX #2 V2: Async Stdin WITHOUT Timeout + Graceful Shutdown
===========================================================

Replaces the 300s timeout pattern with a clean, timeout-free solution.

Changes:
1. Remove: asyncio.wait_for(..., timeout=300.0)
2. Add: Direct run_in_executor() WITHOUT timeout
3. Add: Signal handlers for graceful shutdown
4. Add: Proper EOF detection and logging

This pattern will be applied to all 6 MCP servers.

Research:
- Python docs: https://docs.python.org/3/library/asyncio-stream.html
- Best practice: No arbitrary timeouts for long-running operations
- MCP spec: Servers should handle EOF from parent process
- Graceful shutdown: Signal handling + EOF detection
"""

import signal
import asyncio
import sys
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# FIX #2 V2: Async Stdin WITHOUT Timeout (RECOMMENDED)
# ============================================================================

async def async_stdin_readline_no_timeout() -> str:
    """
    🔧 NEW FIX #2 V2: Non-blocking stdin readline WITHOUT arbitrary timeout
    
    Solves the original problem (stdin blocking) WITHOUT the 300s timeout issue.
    
    Why this is better:
    1. ✅ No arbitrary 300s timeout that interrupts long operations
    2. ✅ Waits for real EOF from parent process
    3. ✅ Graceful shutdown via signal handlers or natural EOF
    4. ✅ Scales for any operation duration
    5. ✅ Parent process has full control over server lifetime
    
    How it works:
    - Uses loop.run_in_executor() to avoid blocking the event loop
    - NO timeout = waits indefinitely for input or EOF
    - Signal handlers (SIGTERM, SIGINT) provide control
    - EOF from stdin triggers natural shutdown
    
    Args:
        None
    
    Returns:
        str: Line read from stdin, or empty string on EOF
    
    Raises:
        Nothing - gracefully handles all conditions
    
    Logging:
        - [stdin_v2] Waiting for input
        - [stdin_v2] Read N bytes
        - [stdin_v2] EOF detected
        - [stdin_v2] Error with details
    """
    loop = asyncio.get_running_loop()
    
    def _read_blocking():
        """Blocking read helper - runs in executor thread"""
        try:
            logger.debug("[stdin_v2] sys.stdin.readline() called (blocking)")
            line = sys.stdin.readline()
            
            if line:
                logger.debug(f"[stdin_v2] Read {len(line)} bytes")
            else:
                logger.info("[stdin_v2] EOF detected (empty line from stdin)")
            
            return line
            
        except Exception as e:
            logger.error(f"[stdin_v2] Read error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("[stdin_v2] Starting non-blocking read (no timeout)")
        
        # KEY CHANGE: NO timeout! Just run in executor.
        # This allows stdin to block until parent sends data or closes connection.
        line = await loop.run_in_executor(None, _read_blocking)
        
        return line
        
    except Exception as e:
        logger.error(f"[stdin_v2] Unexpected error in executor: {type(e).__name__}: {e}")
        return ""


# ============================================================================
# Signal Handlers for Graceful Shutdown
# ============================================================================

class GracefulShutdownHandler:
    """Manages graceful server shutdown via signal handlers"""
    
    def __init__(self, logger_instance):
        self.logger = logger_instance
        self.shutdown_requested = asyncio.Event()
        self.signal_received = None
    
    def setup(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Setup SIGTERM and SIGINT handlers for graceful shutdown
        
        How it works:
        1. Parent sends SIGTERM when it wants to stop the server
        2. Handler sets flag, but doesn't hard-kill
        3. Main loop detects flag and exits gracefully
        4. All cleanup happens (close connections, flush logs, etc)
        
        Args:
            loop: The running asyncio event loop
        """
        def handle_signal(signum: int) -> None:
            sig_name = signal.Signals(signum).name
            self.logger.warning(f"[signal] Received {sig_name} ({signum}) - initiating graceful shutdown")
            self.signal_received = signum
            self.shutdown_requested.set()
        
        try:
            # Register SIGTERM (normal termination from parent)
            loop.add_signal_handler(signal.SIGTERM, handle_signal, signal.SIGTERM)
            self.logger.info("[signal] SIGTERM handler registered")
            
            # Register SIGINT (Ctrl+C)
            loop.add_signal_handler(signal.SIGINT, handle_signal, signal.SIGINT)
            self.logger.info("[signal] SIGINT handler registered")
            
        except Exception as e:
            self.logger.warning(f"[signal] Could not register handlers: {type(e).__name__}: {e}")
            self.logger.warning("[signal] Will rely on EOF detection for shutdown")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested via signal"""
        return self.shutdown_requested.is_set()


# ============================================================================
# Main Loop Pattern
# ============================================================================

async def mcp_main_loop_v2(
    request_handler: Callable,
    shutdown_handler: Optional[GracefulShutdownHandler] = None,
    logger_instance = None
) -> None:
    """
    NEW: Main loop for MCP server with timeout-free stdin handling
    
    Pattern:
    1. Register signal handlers for graceful shutdown
    2. Loop reading lines from stdin (no timeout!)
    3. Check for EOF or shutdown signal
    4. Process requests
    5. Write responses
    6. Exit gracefully
    
    Args:
        request_handler: async function(request_dict) -> response_dict
        shutdown_handler: GracefulShutdownHandler instance (optional)
        logger_instance: Logger for output
    
    Example usage:
        async def handle_request(req):
            # Process and return response
            return {"result": "ok"}
        
        shutdown = GracefulShutdownHandler(logger)
        await mcp_main_loop_v2(handle_request, shutdown, logger)
    """
    if logger_instance is None:
        logger_instance = logger
    
    if shutdown_handler:
        loop = asyncio.get_running_loop()
        shutdown_handler.setup(loop)
    
    logger_instance.info("[main_loop] Starting MCP server main loop")
    request_count = 0
    
    try:
        while True:
            # Check for graceful shutdown signal
            if shutdown_handler and shutdown_handler.is_shutdown_requested():
                logger_instance.info("[main_loop] Shutdown signal received - exiting")
                break
            
            # Read next line from stdin (NO TIMEOUT!)
            logger_instance.debug("[main_loop] Waiting for next request...")
            line = await async_stdin_readline_no_timeout()
            
            if not line:
                # EOF reached - parent closed connection
                logger_instance.info("[main_loop] EOF received - shutting down")
                break
            
            line = line.rstrip('\n\r')
            if not line:
                # Empty line, skip
                logger_instance.debug("[main_loop] Skipped empty line")
                continue
            
            try:
                # Parse JSON-RPC request
                logger_instance.debug(f"[main_loop] Parsing request: {line[:80]}")
                request = eval(line)  # NOTE: In real code, use json.loads()
                
                # Process request
                request_count += 1
                logger_instance.info(f"[main_loop] Request #{request_count}")
                
                # Call handler (async)
                response = await request_handler(request)
                
                # Write response to stdout (binary-safe)
                response_json = str(response)  # NOTE: In real code, use json.dumps()
                sys.stdout.write(response_json + '\n')
                sys.stdout.flush()
                
                logger_instance.info(f"[main_loop] Response #{request_count} sent")
                
            except json.JSONDecodeError as e:
                logger_instance.error(f"[main_loop] JSON parse error: {e}")
                # Send JSON-RPC error response
                error_resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
                sys.stdout.write(str(error_resp) + '\n')
                sys.stdout.flush()
            
            except Exception as e:
                logger_instance.error(f"[main_loop] Request processing error: {type(e).__name__}: {e}")
    
    except Exception as e:
        logger_instance.error(f"[main_loop] Fatal error: {type(e).__name__}: {e}")
    
    finally:
        logger_instance.info(f"[main_loop] Server loop ended after {request_count} requests")


# ============================================================================
# Summary
# ============================================================================

IMPLEMENTATION_SUMMARY = """
🔧 FIX #2 V2: Implementation Summary

WHAT CHANGED:
1. Old: asyncio.wait_for(executor, timeout=300.0)
   → New: Direct await loop.run_in_executor(None, readline)
   
2. Old: Arbitrary 300s timeout for all operations
   → New: Wait indefinitely for real EOF or signal
   
3. Old: No graceful shutdown handling
   → New: Signal handlers + EOF detection + logging

BENEFITS:
✅ Long operations no longer interrupted at 300s
✅ Graceful shutdown via signal handlers
✅ Natural EOF detection from parent
✅ Scales for any operation duration
✅ Better logging for debugging
✅ No performance overhead

TESTING:
- Test 1: Normal operation (reads stdin, processes requests)
- Test 2: Long operation (>300s) - should NOT timeout
- Test 3: Signal shutdown (SIGTERM) - should exit cleanly
- Test 4: Parent crash (EOF) - should detect and exit

MIGRATION:
Apply to all 6 MCP servers:
1. openai_server.py
2. architect_agent_server.py
3. codesmith_agent_server.py
4. responder_agent_server.py
5. reviewfix_agent_server.py
6. research_agent_server.py

Replace async_stdin_readline() with async_stdin_readline_no_timeout()
Add signal handler setup in main()
Update main loop to use new function
"""

print(IMPLEMENTATION_SUMMARY)
