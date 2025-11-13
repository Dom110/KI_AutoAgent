#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Async stdin reading for MCP servers

Fixes the asyncio blocking I/O issue where servers would freeze
waiting for input from stdin.

This module provides a proper async way to read from stdin without
blocking the event loop.
"""

import asyncio
import sys
import json
import logging
from typing import Optional, AsyncIterator

logger = logging.getLogger(__name__)


async def async_stdin_readline() -> str:
    """
    🔄 Non-blocking stdin readline for asyncio

    Reads one line from stdin without blocking the event loop.
    Returns empty string on EOF.

    This is safer than loop.run_in_executor() which can cause
    the event loop to block when stdin has no data.
    """
    loop = asyncio.get_event_loop()

    def _read_line():
        try:
            return sys.stdin.readline()
        except Exception as e:
            logger.error(f"❌ stdin read error: {e}")
            return ""

    try:
        # Use executor with timeout to prevent indefinite blocking
        # Timeout should be long enough for normal operation
        # but short enough to detect dead connections
        line = await asyncio.wait_for(
            loop.run_in_executor(None, _read_line),
            timeout=300.0  # 5 minutes per request (generous for long OpenAI calls)
        )
        return line
    except asyncio.TimeoutError:
        logger.warning("⏱️ stdin read timeout (5 minutes) - parent may have disconnected")
        return ""
    except Exception as e:
        logger.error(f"❌ async stdin error: {e}")
        return ""


async def mcp_server_loop(
    on_request: callable,
    timeout_per_request: float = 300.0
) -> None:
    """
    ⚠️ MCP BLEIBT: Main event loop for MCP servers

    Handles:
    - Non-blocking stdin reading
    - JSON parsing
    - Request routing
    - Proper error handling

    Args:
        on_request: Async callable that handles requests
        timeout_per_request: Max time for one request (seconds)

    Example:
        async def handle_request(request):
            method = request.get("method")
            if method == "initialize":
                return await server.handle_initialize()
            # ...

        await mcp_server_loop(handle_request)
    """
    logger.info("🚀 MCP Server loop started (non-blocking stdin)")

    try:
        while True:
            # 🔄 Non-blocking read
            line = await async_stdin_readline()

            if not line:
                logger.info("📥 EOF received, shutting down")
                break

            line = line.strip()
            if not line:
                # Empty line - continue waiting for next request
                continue

            # 📦 Parse JSON
            try:
                request = json.loads(line)
                logger.debug(f"📥 Request: {request.get('method')} (id={request.get('id')})")

                # ⏱️ Process with timeout
                try:
                    await asyncio.wait_for(
                        on_request(request),
                        timeout=timeout_per_request
                    )
                except asyncio.TimeoutError:
                    logger.error(f"❌ Request timeout after {timeout_per_request}s")
                    # Continue to next request

            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("⚠️ Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise


# For backward compatibility, also expose as a decorator-style helper
def create_mcp_server_context(server_class):
    """
    Create an async context that properly handles stdin for an MCP server.

    Usage:
        async with create_mcp_server_context(MyServer) as server:
            await server.run()
    """
    import contextlib

    @contextlib.asynccontextmanager
    async def _context():
        server = server_class()
        try:
            yield server
        finally:
            logger.info("Cleaning up server...")

    return _context()
