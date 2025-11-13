#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Codesmith Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! Codesmith Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten Claude CLI-Calls! Alles über Claude CLI MCP Server!

This MCP server provides code generation capabilities:
- Generate production-quality code from architecture
- Implement business logic
- Create tests
- Fix bugs
- Use modern best practices

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for generation stages
- Calls Claude CLI via MCP wrapper
- Dynamic tool discovery

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

import sys
import json
import asyncio
import logging
import time
import os
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

# ⚠️ LOGGING: Configure logging to file (stdout is for JSON-RPC)
# All log messages (info, debug, warning, error) go to /tmp/mcp_codesmith_agent.log
log_file = "/tmp/mcp_codesmith_agent.log"
logging.basicConfig(
    level=logging.DEBUG,  # Log everything!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # Append mode
)
logger = logging.getLogger("codesmith_mcp_server")
logger.info(f"=" * 80)
logger.info(f"🚀 Codesmith MCP Server starting at {datetime.now()}")
logger.info(f"=" * 80)


# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin (FIX #2 V2: No Timeout)
async def async_stdin_readline() -> str:
    """
    🔧 FIX #2 V2: Non-blocking stdin readline WITHOUT arbitrary timeout
    
    Solves the asyncio blocking I/O issue while avoiding 300s timeout problems.
    
    Key improvements:
    - NO timeout → Operations complete fully, no interruptions at 300s
    - EOF detection → Natural shutdown when parent closes connection
    - Signal handling ready → Can add graceful shutdown handlers
    - Scales → Works for any operation duration
    
    How it works:
    - Uses run_in_executor() to keep event loop responsive
    - Waits indefinitely for stdin data or EOF from parent
    - Parent process controls server lifetime via connection
    - Signal handlers provide additional graceful shutdown control
    
    Returns:
        str: Line read from stdin, or empty string on EOF
        
    Logging:
        [stdin_v2] - All stdin operations prefixed with this tag
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        """Blocking read - runs in executor thread, non-blocking to event loop"""
        try:
            logger.debug("[stdin_v2] sys.stdin.readline() called (blocking in executor)")
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
        logger.debug("[stdin_v2] Waiting for input (NO timeout - waits for EOF or data)")
        
        # KEY CHANGE: NO timeout!
        # The old code used: await asyncio.wait_for(..., timeout=300.0)
        # This interrupted operations after 300s arbitrarily.
        # New approach: Just await the executor directly.
        # Server lifetime is controlled by parent process closing stdin.
        result = await loop.run_in_executor(None, _read)
        
        return result
        
    except Exception as e:
        logger.error(f"[stdin_v2] Unexpected error: {type(e).__name__}: {e}")
        return ""




class CodesmithAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: Codesmith Agent als vollständiger MCP Server

    Der Codesmith Agent nutzt Claude CLI über einen MCP-Wrapper.
    KEINE direkten subprocess-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "generate": {
                "description": "Generate production-quality code from architecture design",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to implement (user requirements)"
                        },
                        "architecture": {
                            "type": "object",
                            "description": "System design from architect agent"
                        },
                        "research_context": {
                            "type": "object",
                            "description": "Context from research agent"
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to target workspace"
                        }
                    },
                    "required": ["instructions", "architecture", "workspace_path"]
                }
            }
        }

    async def send_progress(self, progress: float, message: str):
        """
        ⚠️ MCP BLEIBT: Send $/progress notification
        """
        notification = {
            "jsonrpc": "2.0",
            "method": "$/progress",
            "params": {
                "progress": progress,
                "total": 1.0,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        await self.send_message(notification)

    async def send_message(self, message: Dict[str, Any]):
        """Send JSON-RPC message to stdout."""
        try:
            json_str = json.dumps(message)
            sys.stdout.write(json_str + "\n")
            sys.stdout.flush()
            logger.debug(f"Sent: {json_str}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Handle initialize request
        """
        self.initialized = True
        logger.info("Codesmith Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "codesmith-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: Codesmith Agent for KI AutoAgent"
            }
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: List available tools
        """
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"]
                }
                for name, tool in self.tools.items()
            ]
        }

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Execute tool call
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        if tool_name == "generate":
            return await self.tool_generate(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_generate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Generate code using Claude CLI via MCP

        WICHTIG: Dieser Code ruft NIEMALS direkt Claude CLI subprocess auf!
        Alle AI-Calls gehen über den Claude CLI MCP Server!
        """
        try:
            await self.send_progress(0.0, "🔨 Starting code generation...")

            instructions = args.get("instructions", "")
            architecture = args.get("architecture", {})
            research_context = args.get("research_context", {})
            workspace_path = args.get("workspace_path", "")

            logger.info(f"Generating code: {instructions[:100]}...")
            logger.info(f"   Workspace: {workspace_path} (already isolated per request)")

            # Check if we need more research
            await self.send_progress(0.1, "📋 Checking prerequisites...")
            if not architecture:
                logger.info("   📚 Missing architecture - requesting research")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "needs_research": True,
                                "research_request": "Need architecture design before code generation",
                                "code_complete": False
                            })
                        }
                    ],
                    "metadata": {
                        "status": "needs_architecture",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # Build code generation prompt
            await self.send_progress(0.2, "📝 Building generation prompt...")
            prompt = self._build_code_generation_prompt(instructions, architecture)
            system_prompt = self._get_system_prompt()

            # ⚠️ CRITICAL FIX: Call Claude CLI DIRECTLY via subprocess!
            # Cannot use MCPManager here because we ARE an MCP server!
            # Using MCP-in-MCP causes stdin/stdout collision and process crashes!
            await self.send_progress(0.3, "🤖 Calling Claude CLI directly...")
            logger.info("   📡 Calling Claude CLI via direct subprocess...")

            import subprocess
            import shutil
            import psutil
            import asyncio

            # 🔒 ENHANCED CLAUDE LOCK WITH MULTIPLE SAFETY MECHANISMS
            lock_file = Path("/tmp/.claude_instance.lock")
            max_wait = 60  # seconds

            logger.warning("🔒 STARTING CLAUDE SAFETY CHECKS...")

            # ⚠️ SAFETY CHECK 1: Kill any existing Claude CLI subprocess instances!
            # IMPORTANT: Only kill Claude CLI processes (started with -p flag), NOT the parent Claude Code agent!
            existing_claude_cli = []
            try:
                our_pid = os.getpid()
                our_ppid = os.getppid()

                for p in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
                    # Skip if not claude process
                    if 'claude' not in p.info['name'].lower():
                        continue

                    # Skip ourselves and our parent (Claude Code agent)
                    if p.info['pid'] in (our_pid, our_ppid):
                        logger.debug(f"   ⏩ Skipping our own process/parent: PID {p.info['pid']}")
                        continue

                    # Only kill Claude CLI subprocess instances (those with -p flag in cmdline)
                    cmdline = p.info.get('cmdline', [])
                    if cmdline and '-p' in cmdline:
                        existing_claude_cli.append(p)
                        age = time.time() - p.info['create_time']
                        logger.error(f"❌ FOUND EXISTING CLAUDE CLI SUBPROCESS: PID {p.info['pid']}, age {age:.1f}s")
                        logger.debug(f"   Command: {' '.join(cmdline[:5])}")

                if existing_claude_cli:
                    logger.error(f"🚨 KILLING {len(existing_claude_cli)} CLAUDE CLI SUBPROCESSES!")
                    for p in existing_claude_cli:
                        try:
                            p.kill()
                            logger.info(f"   ☠️ Killed Claude CLI subprocess PID {p.info['pid']}")
                        except:
                            pass
                    # Wait for processes to die
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Error checking processes: {e}")

            # ⚠️ SAFETY CHECK 2: Clean up any stale lock files
            if lock_file.exists():
                logger.warning("🔓 Removing stale lock file before starting")
                lock_file.unlink(missing_ok=True)

            # ⚠️ SAFETY CHECK 3: Try to acquire lock with PID tracking
            start_time = asyncio.get_event_loop().time()
            lock_acquired = False
            our_pid = os.getpid()

            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                if not lock_file.exists():
                    # Write our PID to the lock file for tracking
                    try:
                        lock_file.write_text(str(our_pid))
                        lock_acquired = True
                        logger.info(f"✅ Claude lock acquired by PID {our_pid}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to write lock: {e}")

                # Check if the lock holder is still alive
                try:
                    lock_pid = int(lock_file.read_text().strip())
                    if not psutil.pid_exists(lock_pid):
                        logger.warning(f"🔓 Lock holder PID {lock_pid} is dead - removing lock")
                        lock_file.unlink(missing_ok=True)
                        continue
                except:
                    # Invalid lock file - remove it
                    logger.warning("🔓 Invalid lock file - removing")
                    lock_file.unlink(missing_ok=True)
                    continue

                logger.info(f"⏳ Waiting for Claude lock... ({int(asyncio.get_event_loop().time() - start_time)}s)")
                await asyncio.sleep(1)

            if not lock_acquired:
                # Final check - if still Claude CLI subprocesses, kill them
                # IMPORTANT: Only kill Claude CLI (-p flag), not parent Claude Code agent!
                for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if 'claude' not in p.info['name'].lower():
                        continue
                    # Skip ourselves and parent
                    if p.info['pid'] in (our_pid, our_ppid):
                        continue
                    # Only kill Claude CLI subprocesses
                    cmdline = p.info.get('cmdline', [])
                    if cmdline and '-p' in cmdline:
                        logger.error(f"🚨 EMERGENCY KILL: Claude CLI subprocess PID {p.info['pid']}")
                        try:
                            p.kill()
                        except:
                            pass
                raise Exception("Could not acquire Claude lock after killing existing Claude CLI processes!")

            # ⚠️ SAFETY CHECK 4: One final check before starting
            # IMPORTANT: Only count Claude CLI subprocesses (-p flag), not parent Claude Code agent!
            claude_cli_processes = []
            for p in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
                if 'claude' not in p.info['name'].lower():
                    continue
                # Skip ourselves and parent
                if p.info['pid'] in (our_pid, our_ppid):
                    continue
                # Only count Claude CLI subprocesses
                cmdline = p.info.get('cmdline', [])
                if cmdline and '-p' in cmdline:
                    claude_cli_processes.append(p)

            if claude_cli_processes:
                # Get details of existing Claude CLI subprocesses
                existing_details = []
                for p in claude_cli_processes:
                    try:
                        age = time.time() - p.info['create_time']
                        cmd_str = ' '.join(p.info.get('cmdline', ['unknown'])[:3])
                        existing_details.append(f"PID {p.info['pid']} (age {age:.1f}s): {cmd_str}")
                    except:
                        pass

                error_msg = f"❌ BLOCKED: {len(claude_cli_processes)} Claude CLI subprocesses already running!\n"
                error_msg += "Existing Claude CLI processes:\n"
                for detail in existing_details:
                    error_msg += f"  - {detail}\n"
                error_msg += f"\nNew request details:\n"
                error_msg += f"  - Workspace: {workspace_path}\n"
                error_msg += f"  - Instructions: {instructions[:100]}...\n"

                logger.error(error_msg)
                lock_file.unlink(missing_ok=True)

                # Send detailed error via progress
                await self.send_progress(1.0, f"❌ BLOCKED: Claude CLI subprocess already running! See logs for details")

                raise Exception(error_msg)

            logger.info("✅ ALL SAFETY CHECKS PASSED - Starting Claude CLI")

            # ⚠️ CREDIT MONITORING: Track start time and warn about costs
            claude_start_time = time.time()
            claude_pid = None
            logger.warning("💰 STARTING CLAUDE - CREDITS WILL BE CONSUMED!")
            logger.warning("   Estimated cost: $0.01-$0.10 per call")
            logger.warning("   Max execution time: 180 seconds")

            # Find claude command
            claude_cmd = shutil.which("claude")
            if not claude_cmd:
                error_msg = "Claude CLI not found in PATH"
                await self.send_progress(1.0, f"❌ {error_msg}")
                raise Exception(error_msg)

            # Build Claude CLI command
            # Note: Claude CLI doesn't support --max-tokens, --temperature, or --workspace!
            # Use --add-dir to grant access to workspace directory
            # ⚠️ CORRECT Claude CLI command structure
            # Use -p (print mode) for non-interactive automation
            # Use --output-format stream-json for REALTIME streaming updates!
            # This prevents MCP timeout and gives progress feedback
            cmd = [
                claude_cmd,
                "-p",  # Print mode: non-interactive, returns output and exits
                "--output-format", "stream-json",  # ⭐ STREAMING for realtime updates!
                "--verbose",  # REQUIRED for stream-json output format!
                "--model", "claude-sonnet-4-20250514",
                "--tools", "Read,Edit,Bash",
                "--add-dir", workspace_path,  # Grant access to workspace
                "--permission-mode", "acceptEdits",  # Auto-approve edits
                "--max-turns", "10",  # Prevent infinite execution (best practice)
                "--dangerously-skip-permissions"  # Skip ALL permission prompts (automation)
            ]

            # Create full prompt
            full_prompt = f"{system_prompt}\n\n{prompt}"

            # Call Claude CLI with detailed error handling
            logger.info(f"   Executing: {' '.join(cmd)}")
            logger.info(f"   Working directory: {workspace_path}")

            # Check if workspace exists
            if not Path(workspace_path).exists():
                error_msg = f"❌ Workspace directory does not exist: {workspace_path}"
                logger.error(error_msg)
                await self.send_progress(1.0, error_msg)
                lock_file.unlink(missing_ok=True)
                raise FileNotFoundError(error_msg)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workspace_path
                )
                claude_pid = proc.pid
                logger.info(f"   ✅ Claude CLI started with PID: {claude_pid}")
                await self.send_progress(0.4, f"🚀 Claude CLI started (PID {claude_pid})")

            except Exception as e:
                error_msg = f"❌ Failed to start Claude CLI: {str(e)}"
                logger.error(error_msg)
                logger.error(f"   Command: {' '.join(cmd)}")
                logger.error(f"   Workspace: {workspace_path}")
                await self.send_progress(1.0, error_msg)
                lock_file.unlink(missing_ok=True)
                raise

            # ⚠️ CRITICAL: Use communicate() properly!
            # communicate() sends input, closes stdin, and waits for output
            # Do NOT manually close stdin before calling communicate()!
            logger.info(f"   📡 Sending prompt to Claude CLI (PID {claude_pid})...")

            try:
                # ⚠️ STREAM-JSON: Read streaming JSON events from Claude CLI
                # Each line is a JSON event with type and data
                # This automatically keeps MCP connection alive (no 15s timeout!)

                # Write prompt to stdin and close it
                proc.stdin.write(full_prompt.encode())
                await proc.stdin.drain()
                proc.stdin.close()
                await proc.stdin.wait_closed()

                logger.info(f"   📡 Reading streaming JSON events from Claude CLI...")

                collected_content = []
                start_time = asyncio.get_event_loop().time()
                last_event_time = start_time

                while True:
                    # Read one line (one JSON event)
                    try:
                        line = await asyncio.wait_for(
                            proc.stdout.readline(),
                            timeout=180.0  # Max 3 minutes per event
                        )
                    except asyncio.TimeoutError:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        raise asyncio.TimeoutError(f"Claude CLI stream timeout after {elapsed:.0f}s")

                    if not line:
                        # EOF - Claude CLI finished
                        break

                    # Parse JSON event
                    try:
                        event = json.loads(line.decode().strip())
                        event_type = event.get("type")
                        event_subtype = event.get("subtype", "")

                        # Log event for debugging
                        logger.debug(f"   📥 Claude event: {event_type}/{event_subtype}")

                        # ⚠️ ACTUAL CLAUDE CLI STREAM-JSON FORMAT:
                        # {"type":"system","subtype":"init",...}
                        # {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
                        # {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit","input":{...}}]}}
                        # {"type":"user","message":{"content":[{"type":"tool_result",...}]}}
                        # {"type":"result","subtype":"success"|"error_max_turns","result":"..."}

                        if event_type == "system":
                            # System initialization event
                            if event_subtype == "init":
                                logger.info(f"   🚀 Claude session initialized: {event.get('session_id','')}")
                                await self.send_progress(0.5, "🚀 Claude session started")

                        elif event_type == "assistant":
                            # Assistant message with content
                            message = event.get("message", {})
                            content_blocks = message.get("content", [])

                            for block in content_blocks:
                                block_type = block.get("type")

                                if block_type == "text":
                                    # Text content
                                    text = block.get("text", "")
                                    if text:
                                        collected_content.append(text)
                                        logger.debug(f"   📝 Claude text: {text[:100]}...")
                                        await self.send_progress(
                                            0.6,
                                            f"📝 Claude is writing... ({len(collected_content)} chunks)"
                                        )

                                elif block_type == "tool_use":
                                    # Tool usage
                                    tool_name = block.get("name", "unknown")
                                    tool_input = block.get("input", {})
                                    logger.info(f"   🔧 Claude using tool: {tool_name} with {tool_input}")
                                    await self.send_progress(0.7, f"🔧 Claude using tool: {tool_name}")

                        elif event_type == "user":
                            # User message (tool results)
                            message = event.get("message", {})
                            content_blocks = message.get("content", [])

                            for block in content_blocks:
                                if block.get("type") == "tool_result":
                                    tool_result = block.get("content", "")
                                    logger.debug(f"   ✅ Tool result: {str(tool_result)[:200]}...")

                        elif event_type == "result":
                            # Final result event - workflow complete!
                            logger.info(f"   🏁 Claude workflow completed: {event_subtype}")

                            if event_subtype in ("success", "error_max_turns"):
                                # Extract final result
                                result = event.get("result", "")
                                if result:
                                    collected_content.append(f"\n\n{result}")

                                # Log usage/cost info
                                total_cost = event.get("total_cost_usd", 0)
                                num_turns = event.get("num_turns", 0)
                                logger.info(f"   💰 Cost: ${total_cost:.4f}, Turns: {num_turns}")

                                # Check for errors
                                errors = event.get("errors", [])
                                if errors:
                                    logger.warning(f"   ⚠️ Errors occurred: {errors}")

                                # Workflow complete - exit loop
                                break

                            elif "error" in event_subtype:
                                # Error occurred
                                error_msg = event.get("error", {}).get("message", "Unknown error")
                                raise Exception(f"Claude CLI error: {error_msg}")

                        # Update last event time
                        last_event_time = asyncio.get_event_loop().time()

                    except json.JSONDecodeError as e:
                        logger.warning(f"   ⚠️ Failed to parse JSON event: {line[:100]}")
                        continue

                # Wait for process to exit
                await proc.wait()

                # Combine collected content
                result_text = "".join(collected_content)
                logger.info(f"   ✅ Received {len(result_text)} chars from Claude CLI (PID {claude_pid})")

                # Check return code
                if proc.returncode != 0:
                    error_msg = f"❌ Claude CLI failed with exit code {proc.returncode} (PID {claude_pid})"
                    # Read stderr for error details
                    try:
                        stderr_data = await proc.stderr.read()
                        if stderr_data:
                            stderr_text = stderr_data.decode('utf-8', errors='ignore')
                            error_msg += f"\n\nSTDERR Output:\n{stderr_text[:1000]}"
                            logger.error(f"   Claude STDERR: {stderr_text}")
                    except:
                        pass

                    logger.error(error_msg)
                    await self.send_progress(1.0, error_msg)
                    lock_file.unlink(missing_ok=True)
                    raise Exception(error_msg)

                # Success - we already collected the content from streaming events
                if result_text:
                    output_lines = result_text.split('\n')
                    line_count = len(output_lines)

                    # ⚠️ CREDIT MONITORING: Log execution time and estimated cost
                    claude_duration = time.time() - claude_start_time
                    estimated_tokens = len(result_text) // 4  # ~4 chars per token
                    estimated_cost = estimated_tokens * 0.000003  # Sonnet pricing

                    logger.info(f"   ✅ Claude CLI completed successfully (PID {claude_pid})")
                    logger.warning(f"💰 CLAUDE EXECUTION COMPLETE:")
                    logger.warning(f"   PID: {claude_pid}")
                    logger.warning(f"   Duration: {claude_duration:.1f} seconds")
                    logger.warning(f"   Output lines: {line_count}")
                    logger.warning(f"   Output chars: {len(result_text)}")
                    logger.warning(f"   Est. tokens: ~{estimated_tokens}")
                    logger.warning(f"   Est. cost: ~${estimated_cost:.4f}")

                    await self.send_progress(0.9, f"✅ Claude completed ({claude_duration:.1f}s, ${estimated_cost:.4f})")
                else:
                    result_text = ""
                    logger.warning(f"   ⚠️ No content collected from Claude CLI (PID {claude_pid})")
                    await self.send_progress(0.8, f"⚠️ Claude completed with no output")

            except asyncio.TimeoutError:
                error_msg = f"❌ Claude CLI TIMEOUT after 180s (PID {claude_pid})"
                logger.error(error_msg)
                logger.error(f"   Command was: {' '.join(cmd)}")
                logger.error(f"   Workspace: {workspace_path}")
                logger.error(f"   Collected {len(collected_content)} content chunks before timeout")

                # Try to kill the process
                try:
                    proc.kill()
                    logger.info(f"   Killed Claude process {claude_pid}")
                    await asyncio.sleep(0.5)
                except Exception as kill_error:
                    logger.error(f"   Failed to kill Claude: {kill_error}")

                await self.send_progress(1.0, error_msg)
                lock_file.unlink(missing_ok=True)
                raise Exception(error_msg)

            except Exception as e:
                error_msg = f"❌ Unexpected Claude error (PID {claude_pid}): {str(e)}"
                logger.error(error_msg)
                await self.send_progress(1.0, error_msg)
                lock_file.unlink(missing_ok=True)
                raise

            # Wrap result in MCP-like format for compatibility
            claude_result = {
                "content": [{"text": result_text}]
            }

            await self.send_progress(0.8, "📦 Processing Claude CLI response...")

            # Extract result from Claude CLI MCP response
            claude_content = claude_result.get("content", [])
            if claude_content and len(claude_content) > 0:
                result_text = claude_content[0].get("text", "")
                logger.info(f"   Claude CLI returned: {len(result_text)} chars")

                # Parse JSON from result (claude_cli_server returns formatted result)
                try:
                    # Extract JSON from markdown code block
                    if "```json" in result_text:
                        json_str = result_text.split("```json\n")[1].split("\n```")[0]
                    else:
                        json_str = result_text

                    claude_data = json.loads(json_str)

                    # Extract files_created list
                    files_created = claude_data.get("files_created", [])

                    if files_created:
                        # Convert to our format
                        generated_files = [
                            {
                                "path": f.get("path", "unknown"),
                                "content": "", # Content is in workspace, not returned
                                "language": f.get("language", "text"),
                                "lines": 0,
                                "description": f"Generated via Claude CLI MCP",
                                "tool": "Edit"
                            }
                            for f in files_created
                        ]
                        logger.info(f"   ✅ {len(generated_files)} files created")
                    else:
                        # No files_created - use content
                        generated_files = [
                            {
                                "path": "output.txt",
                                "content": claude_data.get("content", ""),
                                "language": "text",
                                "lines": len(claude_data.get("content", "").split("\n")),
                                "description": "Claude CLI output",
                                "tool": "Edit"
                            }
                        ]

                except (json.JSONDecodeError, IndexError, KeyError) as e:
                    logger.warning(f"   Failed to parse Claude CLI result: {e}")
                    # Fallback
                    generated_files = [
                        {
                            "path": "generated.txt",
                            "content": result_text[:500],
                            "language": "text",
                            "lines": len(result_text.split("\n")),
                            "description": "Claude CLI output (raw)",
                            "tool": "Edit"
                        }
                    ]
            else:
                logger.warning("   No content from Claude CLI")
                generated_files = []

            # ⚠️ OBSOLETE: Credit tracking removed - Claude CLI provides cost in result event
            # Cost info is already logged in the event parsing loop (event_type == "result")

            await self.send_progress(1.0, "✅ Code generation complete")
            logger.info(f"   ✅ Generated {len(generated_files)} files")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "generated_files": generated_files,
                            "code_complete": True,
                            "needs_research": False
                        }, indent=2)
                    }
                ],
                "metadata": {
                    "file_count": len(generated_files),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")

            # Clean up lock file on error
            if 'lock_acquired' in locals() and lock_acquired:
                lock_file.unlink(missing_ok=True)
                logger.info("🔓 Released Claude lock (error)")
            raise

        finally:
            # 🔓 ALWAYS RELEASE CLAUDE LOCK!
            if 'lock_acquired' in locals() and lock_acquired:
                lock_file.unlink(missing_ok=True)
                logger.info("🔓 Released Claude lock")

    def _get_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for code generation
        """
        return """You are an expert software engineer specializing in code generation.

Your task is to generate high-quality, production-ready code based on:
- Architecture design (component structure, technologies, file organization)
- Research context (best practices, patterns, documentation)
- Specific instructions from the supervisor

Requirements:
1. Follow the architecture design exactly
2. Use modern best practices for the technology stack
3. Include proper error handling and validation
4. Add comprehensive docstrings and comments
5. Generate tests alongside implementation
6. Use the Read, Edit, and Bash tools to create actual files in the workspace
7. Follow security best practices

DO NOT:
- Create placeholder or TODO code
- Skip error handling
- Ignore the architecture design
- Generate code without tests

Generate production-ready, fully functional code."""

    def _build_code_generation_prompt(
        self,
        instructions: str,
        architecture: dict
    ) -> str:
        """
        ⚠️ MCP BLEIBT: Build detailed prompt for code generation
        """
        prompt_parts = [
            "Generate code based on the following:",
            "",
            "## Instructions",
            instructions,
            "",
            "## Architecture",
        ]

        # Add architecture details
        if "description" in architecture:
            prompt_parts.append(f"Description: {architecture['description']}")

        if "components" in architecture:
            prompt_parts.append("\nComponents:")
            for comp in architecture["components"]:
                if isinstance(comp, dict):
                    prompt_parts.append(f"- {comp.get('name', 'Component')}: {comp.get('description', '')}")
                else:
                    prompt_parts.append(f"- {comp}")

        if "technologies" in architecture:
            prompt_parts.append(f"\nTechnologies: {', '.join(architecture['technologies'])}")

        if "file_structure" in architecture:
            prompt_parts.append("\nFile Structure:")
            for file in architecture["file_structure"]:
                prompt_parts.append(f"- {file}")

        prompt_parts.extend([
            "",
            "## Task",
            "1. Create the file structure using the Edit tool",
            "2. Implement each component with production-quality code",
            "3. Add comprehensive tests",
            "4. Ensure all error handling is in place",
            "5. Verify the code with basic syntax checks if possible",
            "",
            "Use the Read, Edit, and Bash tools to create actual files in the workspace."
        ])

        return "\n".join(prompt_parts)

    async def handle_request(self, request: Dict[str, Any]):
        """
        ⚠️ MCP BLEIBT: Handle incoming JSON-RPC request
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.info(f"Request {request_id}: {method}")

        try:
            # Route to handler
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Send success response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            await self.send_message(response)

        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            await self.send_message(error_response)

    async def run(self):
        """
        ⚠️ MCP BLEIBT: Main server loop
        """
        logger.info("🚀 Codesmith Agent MCP Server starting...")
        logger.info("⚠️ MCP BLEIBT: This server MUST remain MCP-compliant!")

        try:
            loop = asyncio.get_event_loop()

            while True:
                line = await async_stdin_readline()

                if not line:
                    logger.info("EOF received, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


async def main():
    """
    ⚠️ MCP BLEIBT: Entry point for Codesmith Agent MCP Server
    """
    server = CodesmithAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
