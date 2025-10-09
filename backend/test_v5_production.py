#!/usr/bin/env python3
"""
Test v5.8.0 Production System - Proper WebSocket Protocol
Tests actual running backend with desktop app creation task
Monitors progress every 30 seconds
"""
import asyncio
import aiohttp
import json
import time
from pathlib import Path
from typing import Any
import os

WORKSPACE = Path.home() / "TestApps" / "FocusTimerApp"
BACKEND_URL = "ws://localhost:8001/ws/chat"
LOG_FILE = Path.home() / "TestApps" / "test_v5_production.log"

# Desktop App Task
TASK = """Create a Focus Timer desktop application in Python:

**App Name:** Focus Timer Pro

**Core Features:**
1. Pomodoro timer (25min work, 5min break, 15min long break)
2. Task list with priorities (High/Medium/Low)
3. Session tracking (completed tasks + timestamps)
4. Statistics dashboard (focus time, completion rate, streak)
5. Settings (timer duration, break duration, notifications)
6. Data persistence (JSON file)
7. System tray integration (macOS)

**Technical Requirements:**
- GUI: tkinter with modern styling (ttk)
- Architecture: MVC pattern
- Type hints everywhere
- Docstrings for all classes/functions
- Error handling and logging
- Configuration file
- Unit tests for core logic

**Files to Create:**
- main.py (entry point)
- timer_gui.py (GUI components - views)
- timer_controller.py (business logic - controller)
- task_model.py (data models)
- session_tracker.py (history tracking)
- stats_calculator.py (statistics logic)
- data_persistence.py (JSON save/load)
- config_manager.py (settings)
- notifications.py (system notifications)
- README.md (comprehensive documentation)
- requirements.txt
- tests/test_timer.py
- tests/test_tasks.py
- tests/test_stats.py

**Code Quality:**
- Clean code principles
- SOLID principles where applicable
- Comprehensive error handling
- Logging throughout
- Performance optimization

Please create a complete, production-ready application.
"""


class ConversationLogger:
    """Logs all messages to file and console"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.messages: list[dict[str, Any]] = []
        self.start_time = time.time()

    def log(self, msg_type: str, content: str, raw_msg: dict | None = None):
        """Log message to file and console"""
        elapsed = time.time() - self.start_time
        timestamp = time.strftime("%H:%M:%S")

        # Console output with emoji
        emoji_map = {
            "connected": "🔌",
            "initialized": "✅",
            "agent_message": "🤖",
            "agent_thinking": "💭",
            "tool_use": "🔧",
            "status": "📊",
            "result": "✅",
            "error": "❌",
            "progress": "⏱️ ",
        }
        emoji = emoji_map.get(msg_type, "📝")

        print(f"{emoji} [{timestamp}] {msg_type}: {content[:200]}")

        # File output (full)
        log_entry = {
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed, 2),
            "type": msg_type,
            "content": content,
            "raw": raw_msg
        }
        self.messages.append(log_entry)

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def save_summary(self):
        """Save conversation summary"""
        summary_file = self.log_file.parent / "test_v5_summary.json"

        # Count files created
        files_created = []
        if WORKSPACE.exists():
            files_created = [
                str(f.relative_to(WORKSPACE))
                for f in WORKSPACE.rglob("*")
                if f.is_file()
            ]

        summary = {
            "test_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            "test_duration_seconds": round(time.time() - self.start_time, 2),
            "total_messages": len(self.messages),
            "message_types": {
                msg_type: sum(1 for m in self.messages if m["type"] == msg_type)
                for msg_type in set(m["type"] for m in self.messages)
            },
            "files_created": len(files_created),
            "file_list": files_created,
            "workspace": str(WORKSPACE),
            "features_observed": self._analyze_features(),
            "conversation": self.messages
        }

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n📄 Summary saved to: {summary_file}")
        return summary

    def _analyze_features(self) -> dict[str, bool]:
        """Analyze which features were observed in conversation"""
        conversation_text = " ".join(
            m.get("content", "") for m in self.messages
        ).lower()

        return {
            "thinking_visible": any(m["type"] == "agent_thinking" for m in self.messages),
            "tool_calls_visible": any(m["type"] == "tool_use" for m in self.messages),
            "status_updates": any(m["type"] == "status" for m in self.messages),
            "memory_mentioned": "memory" in conversation_text,
            "predictive_mentioned": "predict" in conversation_text,
            "curiosity_mentioned": "curiosity" in conversation_text or "novelty" in conversation_text,
            "architecture_mentioned": "architecture" in conversation_text,
            "playground_mentioned": "playground" in conversation_text or "sandbox" in conversation_text,
        }


async def monitor_progress(logger: ConversationLogger, stop_event: asyncio.Event):
    """Monitor progress every 30 seconds"""
    while not stop_event.is_set():
        await asyncio.sleep(30)

        if stop_event.is_set():
            break

        # Count files
        file_count = 0
        if WORKSPACE.exists():
            file_count = sum(1 for _ in WORKSPACE.rglob("*") if _.is_file())

        elapsed = time.time() - logger.start_time
        logger.log(
            "progress",
            f"Still running... {int(elapsed)}s elapsed, {file_count} files created, "
            f"{len(logger.messages)} messages received",
            None
        )


async def test_production_v5():
    """Test v5.8.0 production system"""
    # Clean workspace
    if WORKSPACE.exists():
        import shutil
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    logger = ConversationLogger(LOG_FILE)
    logger.log("progress", f"Starting test - workspace: {WORKSPACE}", None)

    # Progress monitor
    stop_event = asyncio.Event()
    monitor_task = asyncio.create_task(monitor_progress(logger, stop_event))

    try:
        async with aiohttp.ClientSession() as session:
            # Connect to WebSocket
            logger.log("progress", f"Connecting to {BACKEND_URL}", None)
            async with session.ws_connect(BACKEND_URL) as ws:

                # 1. Wait for connected
                msg = await ws.receive_json()
                logger.log(msg["type"], json.dumps(msg), msg)

                if msg["type"] != "connected":
                    raise ValueError(f"Expected 'connected', got {msg['type']}")

                # 2. Send init
                init_msg = {
                    "type": "init",
                    "workspace_path": str(WORKSPACE)
                }
                logger.log("progress", f"Sending init: {init_msg}", None)
                await ws.send_json(init_msg)

                # 3. Wait for initialized
                msg = await ws.receive_json()
                logger.log(msg["type"], json.dumps(msg), msg)

                if msg["type"] != "initialized":
                    raise ValueError(f"Expected 'initialized', got {msg['type']}")

                # 4. Send chat message
                chat_msg = {
                    "type": "chat",
                    "content": TASK
                }
                logger.log("progress", "Sending desktop app task...", None)
                await ws.send_json(chat_msg)

                # 5. Collect all messages
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.receive_json(), timeout=60)

                        msg_type = msg.get("type", "unknown")

                        # Log based on type
                        if msg_type == "agent_message":
                            content = msg.get("content", "")
                            agent = msg.get("agent", "unknown")
                            logger.log(msg_type, f"[{agent}] {content}", msg)

                        elif msg_type == "agent_thinking":
                            thinking = msg.get("thinking", "")
                            agent = msg.get("agent", "unknown")
                            logger.log(msg_type, f"[{agent}] {thinking}", msg)

                        elif msg_type == "tool_use":
                            tool = msg.get("tool", "")
                            args = msg.get("arguments", {})
                            logger.log(msg_type, f"{tool}({list(args.keys())})", msg)

                        elif msg_type == "status":
                            status = msg.get("status", "")
                            logger.log(msg_type, status, msg)

                        elif msg_type == "result":
                            result = msg.get("result", "")
                            logger.log(msg_type, f"DONE: {result}", msg)
                            break

                        elif msg_type == "error":
                            error = msg.get("error", "")
                            logger.log(msg_type, f"ERROR: {error}", msg)
                            break

                        else:
                            logger.log(msg_type, json.dumps(msg), msg)

                    except asyncio.TimeoutError:
                        logger.log("progress", "No message for 60s, still waiting...", None)
                        continue

    except Exception as e:
        logger.log("error", f"Test failed: {e}", None)
        import traceback
        traceback.print_exc()

    finally:
        # Stop progress monitor
        stop_event.set()
        await monitor_task

        # Save summary
        summary = logger.save_summary()

        # Print summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"Duration: {summary['test_duration_seconds']}s")
        print(f"Messages: {summary['total_messages']}")
        print(f"Files Created: {summary['files_created']}")
        print(f"\nMessage Types:")
        for msg_type, count in summary['message_types'].items():
            print(f"  {msg_type}: {count}")
        print(f"\nFeatures Observed:")
        for feature, observed in summary['features_observed'].items():
            icon = "✅" if observed else "❌"
            print(f"  {icon} {feature}")
        print(f"\nFiles Created:")
        for file in summary['file_list'][:20]:  # First 20
            print(f"  - {file}")
        if len(summary['file_list']) > 20:
            print(f"  ... and {len(summary['file_list']) - 20} more")
        print("="*80)


if __name__ == "__main__":
    print("🚀 Testing v5.8.0 Production System")
    print(f"📁 Workspace: {WORKSPACE}")
    print(f"📝 Log file: {LOG_FILE}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print()

    asyncio.run(test_production_v5())
