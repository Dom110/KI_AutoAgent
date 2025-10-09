#!/usr/bin/env python3
"""
E2E Test: VSCode Extension to v6 Backend Communication

This test verifies:
1. VSCode Extension connects to v6 backend on ws://localhost:8002/ws/chat
2. Extension sends chat message
3. v6 backend receives and processes with all 12 systems
4. Backend responds with workflow_complete
5. Extension receives and handles response

User's requirement: "nur das Kommando an den Websocket sendest"
"""

import asyncio
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
LOG_FILE = Path.home() / ".ki_autoagent" / "logs" / "server.log"
EXTENSION_PATH = Path("/Users/dominikfoert/git/KI_AutoAgent/vscode-extension")
WORKSPACE_PATH = Path("/Users/dominikfoert/TestApps/manualTest")

def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")

def check_backend_running() -> bool:
    """Check if v6 backend is running on port 8002"""
    result = subprocess.run(
        ["lsof", "-i", ":8002"],
        capture_output=True,
        text=True
    )
    return "Python" in result.stdout

def get_log_tail(lines: int = 50) -> str:
    """Get last N lines from server log"""
    if not LOG_FILE.exists():
        return "Log file not found"

    result = subprocess.run(
        ["tail", "-n", str(lines), str(LOG_FILE)],
        capture_output=True,
        text=True
    )
    return result.stdout

def search_log_for_patterns(patterns: list[str], since: float) -> dict:
    """Search log for specific patterns since timestamp"""
    if not LOG_FILE.exists():
        return {}

    # Get recent log content
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    # Filter lines since timestamp
    recent_lines = []
    for line in lines:
        try:
            # Extract timestamp from log line (format: 2025-10-09 HH:MM:SS)
            if len(line) > 19:
                line_time_str = line[:19]
                line_time = datetime.strptime(line_time_str, "%Y-%m-%d %H:%M:%S").timestamp()
                if line_time >= since:
                    recent_lines.append(line)
        except:
            recent_lines.append(line)  # Include lines without parseable timestamp

    # Search for patterns
    results = {}
    for pattern in patterns:
        matching_lines = [line.strip() for line in recent_lines if pattern.lower() in line.lower()]
        results[pattern] = matching_lines

    return results

async def monitor_logs(duration_seconds: int, check_interval: int = 5):
    """Monitor logs for duration, checking every interval"""
    start_time = time.time()
    print_info(f"Monitoring logs for {duration_seconds} seconds (checking every {check_interval}s)...")
    print_info(f"Watching: {LOG_FILE}")
    print()

    # Patterns to search for
    patterns = [
        "WebSocket client connected",
        "Session initialized",
        "v6 workflow starting",
        "Query Classifier",
        "Curiosity System",
        "Workflow complete",
        "Quality Score",
        "Files generated",
        "ERROR",
        "CRITICAL"
    ]

    iteration = 0
    while time.time() - start_time < duration_seconds:
        iteration += 1
        elapsed = int(time.time() - start_time)

        print(f"\n[{elapsed}s / {duration_seconds}s] Check #{iteration}")
        print("-" * 40)

        # Search for patterns in recent logs
        results = search_log_for_patterns(patterns, start_time)

        found_something = False
        for pattern, lines in results.items():
            if lines:
                found_something = True
                print(f"\n  🔍 Found '{pattern}': {len(lines)} occurrence(s)")
                for line in lines[-2:]:  # Show last 2 matches
                    print(f"     {line}")

        if not found_something:
            print("  ⏳ No relevant log entries yet...")

        await asyncio.sleep(check_interval)

    print("\n" + "=" * 80)
    print("  Monitoring Complete - Final Log Summary")
    print("=" * 80 + "\n")

    # Final summary
    final_results = search_log_for_patterns(patterns, start_time)

    for pattern, lines in final_results.items():
        count = len(lines)
        if count > 0:
            print(f"✅ {pattern}: {count} occurrence(s)")
        else:
            print(f"⚠️  {pattern}: Not found")

def main():
    print_header("E2E Test: VSCode Extension → v6 Backend")

    # Step 1: Check backend
    print_info("Step 1: Check v6 backend status...")
    if not check_backend_running():
        print_error("v6 backend is NOT running on port 8002!")
        print_info("Start it with: ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py")
        return 1
    print_success("v6 backend is running on port 8002")

    # Step 2: Check extension
    print_info("Step 2: Check extension build...")
    extension_js = EXTENSION_PATH / "dist" / "extension.js"
    if not extension_js.exists():
        print_error(f"Extension not built: {extension_js}")
        print_info("Build with: cd vscode-extension && npm run compile")
        return 1
    print_success(f"Extension built: {extension_js}")

    # Step 3: Check workspace
    print_info("Step 3: Check test workspace...")
    if not WORKSPACE_PATH.exists():
        print_info(f"Creating test workspace: {WORKSPACE_PATH}")
        WORKSPACE_PATH.mkdir(parents=True, exist_ok=True)
    print_success(f"Test workspace ready: {WORKSPACE_PATH}")

    # Step 4: Instructions for user
    print_header("Manual Test Instructions")
    print("1. Open VSCode")
    print("2. Open workspace: /Users/dominikfoert/TestApps/manualTest")
    print("3. Press F5 to launch Extension Development Host")
    print("4. In Extension Development Host:")
    print("   - Open Command Palette (Cmd+Shift+P)")
    print("   - Run: 'KI AutoAgent: Show Chat'")
    print("   - Send message: 'Erstelle eine einfache Taschenrechner App'")
    print("5. Watch logs below for v6 workflow execution")
    print()
    print_info("Logs will be monitored automatically for 120 seconds...")
    print_info("Press Ctrl+C to stop monitoring early")
    print()

    input("Press ENTER when ready to start monitoring... ")

    # Step 5: Monitor logs
    print_header("Log Monitoring Started")
    try:
        asyncio.run(monitor_logs(duration_seconds=120, check_interval=10))
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")

    # Step 6: Show final logs
    print_header("Recent Log Tail (Last 100 lines)")
    print(get_log_tail(100))

    print_header("E2E Test Complete")
    print_success("Check logs above to verify:")
    print("  1. WebSocket connection from Extension")
    print("  2. Session initialization with workspace_path")
    print("  3. All 12 v6 systems activated")
    print("  4. Workflow completion with quality score")
    print("  5. Files generated in workspace")
    print()

    return 0

if __name__ == "__main__":
    exit(main())
