#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: ReviewFix Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! ReviewFix Agent läuft NUR als MCP-Server!
⚠️ Architecture: Agent MCP Servers call Claude CLI DIRECTLY!
(Not via MCPManager - that would cause stdin/stdout collision)

This MCP server provides code review and fixing capabilities:
- Review generated code for quality
- Validate code with tests
- Fix errors and issues
- Improve code quality
- Iterate until tests pass

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for review/fix stages
- Calls Claude CLI via subprocess (direct, like CodeSmith Agent)
- Dynamic tool discovery

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

import sys
import json
import asyncio
import logging
import shutil
import time
import os
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.utils.api_validator import validate_openai_key

# ⚠️ Load environment variables
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)

# ⚠️ LOGGING: Configure logging to file (stdout is for JSON-RPC)
# All log messages (info, debug, warning, error) go to /tmp/mcp_reviewfix_agent.log
log_file = "/tmp/mcp_reviewfix_agent.log"
logging.basicConfig(
    level=logging.DEBUG,  # Log everything!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # Append mode
)
logger = logging.getLogger("reviewfix_mcp_server")
logger.info(f"=" * 80)
logger.info(f"🚀 ReviewFix MCP Server starting at {datetime.now()}")
logger.info(f"=" * 80)


# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin (FIXES FIX #2: Async Blocking I/O)
async def async_stdin_readline() -> str:
    """
    🔄 Non-blocking stdin readline for asyncio
    
    Fixes the asyncio blocking I/O issue where servers would freeze
    waiting for input from stdin. Uses run_in_executor with 300s timeout.
    
    Returns:
        str: Line read from stdin, or empty string on timeout/EOF
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        try:
            line = sys.stdin.readline()
            if line:
                logger.debug(f"🔍 [stdin] Read {len(line)} bytes")
            return line
        except Exception as e:
            logger.error(f"❌ [stdin] readline() error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("⏳ [stdin] Waiting for input (300s timeout)...")
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _read),
            timeout=300.0
        )
        if result:
            logger.debug(f"✅ [stdin] Got line: {result[:60].strip()}...")
        else:
            logger.debug("ℹ️ [stdin] EOF (empty line)")
        return result
    except asyncio.TimeoutError:
        logger.warning("⏱️ [stdin] Timeout (300s) - parent process may have disconnected")
        return ""
    except Exception as e:
        logger.error(f"❌ [stdin] Unexpected error: {type(e).__name__}: {e}")
        return ""




class ReviewFixAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: ReviewFix Agent als vollständiger MCP Server

    Der ReviewFix Agent nutzt Claude CLI über einen MCP-Wrapper für
    Code Review und Fixes. KEINE direkten subprocess-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "review_and_fix": {
                "description": "Review code and fix any issues until tests pass",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to review and fix"
                        },
                        "generated_files": {
                            "type": "array",
                            "description": "List of generated files to review",
                            "items": {"type": "object"}
                        },
                        "validation_errors": {
                            "type": "array",
                            "description": "List of errors from previous validation",
                            "items": {"type": "string"}
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to workspace"
                        },
                        "iteration": {
                            "type": "integer",
                            "description": "Current iteration number",
                            "default": 1
                        }
                    },
                    "required": ["instructions", "workspace_path"]
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
        logger.info("ReviewFix Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "reviewfix-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: ReviewFix Agent for KI AutoAgent"
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

        if tool_name == "review_and_fix":
            return await self.tool_review_and_fix(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_review_and_fix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Review and fix code using Claude CLI via MCP

        WICHTIG: Dieser Code ruft Claude CLI ÜBER den Claude CLI MCP Server auf!
        Alle Claude-Calls gehen über das MCP Protocol!
        """
        try:
            await self.send_progress(0.0, "🔍 Starting code review...")

            instructions = args.get("instructions", "")
            generated_files = args.get("generated_files", [])
            validation_errors = args.get("validation_errors", [])
            workspace_path = args.get("workspace_path", "")
            iteration = args.get("iteration", 1)

            logger.info(f"Reviewing code (iteration {iteration}): {instructions[:100]}...")
            logger.info(f"   Workspace: {workspace_path}")
            logger.info(f"   Files: {len(generated_files)}")
            logger.info(f"   Errors: {len(validation_errors)}")

            # Build review prompt
            await self.send_progress(0.1, "📝 Building review prompt...")
            prompt = self._build_review_prompt(
                instructions,
                generated_files,
                validation_errors,
                iteration
            )
            system_prompt = self._get_system_prompt()

            # ⚠️ MCP BLEIBT: Call Claude CLI DIRECTLY via subprocess!
            # Cannot use MCPManager here because we ARE an MCP server!
            # Using MCP-in-MCP causes stdin/stdout collision and process crashes!
            await self.send_progress(0.3, "🤖 Calling Claude CLI directly...")
            logger.info("   📡 Calling Claude CLI via direct subprocess...")

            import subprocess
            import psutil

            # 🔒 SUBPROCESS LOCK WITH SAFETY MECHANISMS
            lock_file = Path("/tmp/.claude_instance.lock")
            max_wait = 60  # seconds

            logger.warning("🔒 STARTING CLAUDE SAFETY CHECKS...")

            # ⚠️ SAFETY CHECK 1: Kill any existing Claude CLI subprocess instances!
            existing_claude_cli = []
            try:
                our_pid = os.getpid()
                our_ppid = os.getppid()

                for p in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
                    if 'claude' not in p.info['name'].lower():
                        continue

                    if p.info['pid'] in (our_pid, our_ppid):
                        logger.debug(f"   ⏩ Skipping our own process/parent: PID {p.info['pid']}")
                        continue

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
                    logger.warning("🔓 Invalid lock file - removing")
                    lock_file.unlink(missing_ok=True)
                    continue

                logger.info(f"⏳ Waiting for Claude lock... ({int(asyncio.get_event_loop().time() - start_time)}s)")
                await asyncio.sleep(1)

            if not lock_acquired:
                error_msg = "Could not acquire Claude lock after 60 seconds!"
                logger.error(error_msg)
                await self.send_progress(1.0, f"❌ {error_msg}")
                lock_file.unlink(missing_ok=True)
                raise Exception(error_msg)

            logger.info("✅ ALL SAFETY CHECKS PASSED - Starting Claude CLI")

            # ⚠️ CREDIT MONITORING: Track start time
            claude_start_time = time.time()
            claude_pid = None
            logger.warning("💰 STARTING CLAUDE - CREDITS WILL BE CONSUMED!")
            logger.warning("   Estimated cost: $0.01-$0.10 per call")
            logger.warning("   Max execution time: 300 seconds")

            # Find claude command
            claude_cmd = shutil.which("claude")
            if not claude_cmd:
                error_msg = "Claude CLI not found in PATH"
                await self.send_progress(1.0, f"❌ {error_msg}")
                lock_file.unlink(missing_ok=True)
                raise Exception(error_msg)

            # Build Claude CLI command
            cmd = [
                claude_cmd,
                "-p",  # Print mode: non-interactive
                "--output-format", "stream-json",  # ⭐ STREAMING for realtime updates!
                "--verbose",  # REQUIRED for stream-json output format!
                "--model", "claude-sonnet-4-20250514",
                "--tools", "Read,Edit,Bash",
                "--add-dir", workspace_path,
                "--permission-mode", "acceptEdits",
                "--max-turns", "15",  # Code review/fix may need more turns
                "--dangerously-skip-permissions"
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
                await self.send_progress(1.0, error_msg)
                lock_file.unlink(missing_ok=True)
                raise Exception(error_msg)

            # Send prompt to stdin
            try:
                proc.stdin.write(full_prompt.encode())
                proc.stdin.close()
                await proc.stdin.wait_closed()

                logger.info(f"   📡 Reading streaming JSON events from Claude CLI...")

                collected_content = []
                start_time = asyncio.get_event_loop().time()

                while True:
                    # Read one line (one JSON event)
                    try:
                        line = await asyncio.wait_for(
                            proc.stdout.readline(),
                            timeout=300.0  # Max 5 minutes per event
                        )
                    except asyncio.TimeoutError:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        raise asyncio.TimeoutError(f"Claude CLI stream timeout after {elapsed:.0f}s")

                    if not line:
                        break

                    # Parse JSON event
                    try:
                        event = json.loads(line.decode().strip())
                        event_type = event.get("type")
                        event_subtype = event.get("subtype", "")

                        logger.debug(f"   📥 Claude event: {event_type}/{event_subtype}")

                        if event_type == "system":
                            if event_subtype == "init":
                                logger.info(f"   🚀 Claude session initialized: {event.get('session_id','')}")
                                await self.send_progress(0.5, "🚀 Claude session started")

                        elif event_type == "assistant":
                            message = event.get("message", {})
                            content_blocks = message.get("content", [])

                            for block in content_blocks:
                                block_type = block.get("type")

                                if block_type == "text":
                                    text = block.get("text", "")
                                    if text:
                                        collected_content.append(text)
                                        logger.debug(f"   📝 Claude text: {text[:100]}...")
                                        await self.send_progress(
                                            0.6,
                                            f"📝 Claude is reviewing... ({len(collected_content)} chunks)"
                                        )

                                elif block_type == "tool_use":
                                    tool_name = block.get("name", "unknown")
                                    logger.info(f"   🔧 Claude using tool: {tool_name}")
                                    await self.send_progress(0.7, f"🔧 Claude using tool: {tool_name}")

                        elif event_type == "user":
                            message = event.get("message", {})
                            content_blocks = message.get("content", [])

                            for block in content_blocks:
                                if block.get("type") == "tool_result":
                                    tool_result = block.get("content", "")
                                    logger.debug(f"   ✅ Tool result: {str(tool_result)[:200]}...")

                        elif event_type == "result":
                            logger.info(f"   🏁 Claude workflow completed: {event_subtype}")

                            if event_subtype in ("success", "error_max_turns"):
                                result = event.get("result", "")
                                if result:
                                    collected_content.append(f"\n\n{result}")

                                total_cost = event.get("total_cost_usd", 0)
                                num_turns = event.get("num_turns", 0)
                                logger.info(f"   💰 Cost: ${total_cost:.4f}, Turns: {num_turns}")

                                errors = event.get("errors", [])
                                if errors:
                                    logger.warning(f"   ⚠️ Errors occurred: {errors}")

                                break

                            elif "error" in event_subtype:
                                error_msg = event.get("error", {}).get("message", "Unknown error")
                                raise Exception(f"Claude CLI error: {error_msg}")

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

                    # ⚠️ CREDIT MONITORING: Log execution time
                    claude_duration = time.time() - claude_start_time
                    estimated_tokens = len(result_text) // 4
                    estimated_cost = estimated_tokens * 0.000003

                    logger.info(f"   ⏱️ Duration: {claude_duration:.1f}s")
                    logger.info(f"   📊 Estimated: {estimated_tokens} tokens, ${estimated_cost:.4f} cost")
                    logger.info(f"   📄 Output: {line_count} lines")

                    # Parse JSON from result
                    try:
                        logger.debug(f"   Checking for markdown JSON block...")
                        if "```json" in result_text:
                            json_str = result_text.split("```json\n")[1].split("\n```")[0]
                            logger.debug(f"   Extracted JSON from markdown block: {len(json_str)} chars")
                        else:
                            json_str = result_text

                        claude_data = json.loads(json_str)
                        logger.info(f"   ✅ Successfully parsed JSON")
                        logger.info(f"   JSON keys: {list(claude_data.keys())}")

                        # Extract validation result from Claude
                        validation_passed = claude_data.get("validation_passed", False)
                        fixed_files = claude_data.get("fixed_files", [])
                        remaining_errors = claude_data.get("remaining_errors", [])
                        tests_passing = claude_data.get("tests_passing", [])
                        fix_summary = claude_data.get("fix_summary", "")

                        logger.info(f"   ✅ Validation: {validation_passed}")
                        logger.info(f"   ✅ Fixed files: {len(fixed_files)}")
                        logger.info(f"   ✅ Remaining errors: {len(remaining_errors)}")
                        logger.info(f"   ✅ Tests passing: {tests_passing}")

                        result = {
                            "fixed_files": fixed_files if fixed_files else generated_files,
                            "validation_passed": validation_passed,
                            "remaining_errors": remaining_errors,
                            "iteration": iteration,
                            "fix_complete": True,
                            "tests_passing": tests_passing,
                            "fix_summary": fix_summary,
                            "note": "✅ Code reviewed and fixed via Claude CLI"
                        }

                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        logger.error(f"   ❌ Failed to parse Claude CLI result: {e}")
                        logger.error(f"   Full raw response: {result_text}")
                        result = {
                            "fixed_files": generated_files,
                            "validation_passed": False,
                            "remaining_errors": ["Failed to parse review result from Claude"],
                            "iteration": iteration,
                            "fix_complete": False,
                            "note": f"⚠️ Error parsing Claude result: {str(e)[:100]}"
                        }
                else:
                    logger.error("❌ No content in Claude CLI response!")
                    logger.error(f"   Claude return code: {proc.returncode}")
                    result = {
                        "fixed_files": generated_files,
                        "validation_passed": False,
                        "remaining_errors": ["No response from Claude CLI"],
                        "iteration": iteration,
                        "fix_complete": False,
                        "note": "⚠️ No content returned from Claude CLI"
                    }

            except Exception as e:
                logger.error(f"❌ Claude CLI execution failed: {e}")
                await self.send_progress(1.0, f"❌ Claude CLI error: {str(e)[:100]}")
                lock_file.unlink(missing_ok=True)
                raise

            finally:
                # Always cleanup lock file
                lock_file.unlink(missing_ok=True)
                # Log final cost
                if claude_pid:
                    claude_total_time = time.time() - claude_start_time
                    logger.info(f"   🏁 Claude CLI (PID {claude_pid}) finished in {claude_total_time:.1f}s")


            await self.send_progress(0.7, "🔧 Processing fixes...")

            await self.send_progress(1.0, "✅ Review and fix complete")
            logger.info(f"   ✅ Review complete: validation_passed={result['validation_passed']}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                "metadata": {
                    "validation_passed": result["validation_passed"],
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Review and fix failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            # Return conservative failure result
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "fixed_files": args.get("generated_files", []),
                            "validation_passed": False,
                            "remaining_errors": [f"ReviewFix failed: {str(e)}"],
                            "iteration": args.get("iteration", 1),
                            "fix_complete": False,
                            "note": f"❌ ReviewFix error: {str(e)[:100]}"
                        }, indent=2)
                    }
                ],
                "metadata": {
                    "validation_passed": False,
                    "iteration": args.get("iteration", 1),
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            }

    def _get_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for code review and fixing
        """
        return """You are an expert code reviewer and debugger specializing in quality assurance.

Your task is to:
1. Review generated code for correctness, quality, and best practices
2. Run tests to validate functionality
3. Fix any errors or issues found
4. Improve code quality (error handling, documentation, edge cases)
5. Ensure all tests pass before completing

Requirements:
- Use Read tool to examine existing code
- Use Edit tool to fix issues
- Use Bash tool to run tests and validation
- Fix ALL errors - do not leave TODO comments
- Ensure proper error handling
- Verify all edge cases
- Add missing tests if needed

DO NOT:
- Skip test execution
- Leave errors unfixed
- Ignore validation failures
- Create placeholder fixes

CRITICAL: After completing all fixes, return a JSON response with this structure:
```json
{
  "validation_passed": true/false,
  "fixed_files": ["list of fixed file paths"],
  "remaining_errors": ["list of any remaining errors or empty array"],
  "tests_passing": ["list of passing tests or empty array"],
  "fix_summary": "brief summary of what was fixed"
}
```

Fix ALL issues until tests pass completely, then return the JSON response."""

    def _build_review_prompt(
        self,
        instructions: str,
        generated_files: list,
        validation_errors: list,
        iteration: int
    ) -> str:
        """
        ⚠️ MCP BLEIBT: Build detailed prompt for code review
        """
        prompt_parts = [
            f"Review and fix code (Iteration {iteration}):",
            "",
            "## Original Instructions",
            instructions,
            "",
        ]

        # Add file information
        if generated_files:
            prompt_parts.append("## Generated Files")
            for file in generated_files[:5]:  # Limit to 5 files in prompt
                if isinstance(file, dict):
                    prompt_parts.append(f"- {file.get('path', 'unknown')}: {file.get('description', '')}")
            prompt_parts.append("")

        # Add validation errors if present
        if validation_errors:
            prompt_parts.append(f"## Validation Errors ({len(validation_errors)} errors)")
            for i, error in enumerate(validation_errors[:10], 1):  # Limit to 10 errors
                prompt_parts.append(f"{i}. {error}")
            prompt_parts.append("")

        # Add tasks
        prompt_parts.extend([
            "## Task",
            "1. Read the generated files using the Read tool",
            "2. Run tests using the Bash tool",
        ])

        if validation_errors:
            prompt_parts.append("3. Fix ALL validation errors using the Edit tool")
            prompt_parts.append("4. Re-run tests to verify fixes")
        else:
            prompt_parts.append("3. Review code quality and improve if needed")
            prompt_parts.append("4. Ensure all tests pass")

        prompt_parts.extend([
            "5. Verify all edge cases are handled",
            "",
            "Fix ALL issues. Do not complete until ALL tests pass."
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
        logger.info("🚀 ReviewFix Agent MCP Server starting...")
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
    ⚠️ MCP BLEIBT: Entry point for ReviewFix Agent MCP Server
    """
    server = ReviewFixAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
