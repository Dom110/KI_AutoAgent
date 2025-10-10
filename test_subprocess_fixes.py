#!/usr/bin/env python3
"""
Test different subprocess configurations to fix timeout issue
"""

import asyncio
import json
import os
import sys
import time

# Prepare test data
SYSTEM_PROMPT = """You are a research analyst specializing in software development.

Your responsibilities:
1. Analyze search results and extract key insights
2. Identify relevant technologies, patterns, and best practices
3. Summarize findings concisely
4. Provide actionable recommendations

Output format:
- Key Findings: Main insights from the research
- Technologies: Relevant tools/frameworks mentioned
- Best Practices: Recommended approaches
- Sources: Where the information came from"""

with open("/tmp/claude_user_prompt.txt") as f:
    USER_PROMPT = f.read()

COMBINED_PROMPT = f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}"

AGENT_DEF = {
    "research": {
        "description": "Research analyst specializing in software development and technology",
        "prompt": "You are a helpful assistant.",
        "tools": ["Read", "Bash"]
    }
}

BASE_CMD = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Read Edit Bash",
    "--agents", json.dumps(AGENT_DEF),
    "--output-format", "stream-json",
    "--verbose",
    "-p", COMBINED_PROMPT
]


async def test_config(name, cmd, stdin_config=None, env_config=None, timeout=20):
    """Test a specific subprocess configuration."""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    print(f"stdin: {stdin_config}")
    print(f"env: {'custom' if env_config else 'inherit'}")
    print(f"timeout: {timeout}s")

    start = time.time()

    try:
        # Build subprocess kwargs
        kwargs = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
        }

        if stdin_config == "DEVNULL":
            kwargs["stdin"] = asyncio.subprocess.DEVNULL
        elif stdin_config == "PIPE":
            kwargs["stdin"] = asyncio.subprocess.PIPE

        if env_config:
            kwargs["env"] = env_config

        # Start process
        print("⏳ Starting subprocess...")
        process = await asyncio.create_subprocess_exec(*cmd, **kwargs)
        print(f"✅ PID: {process.pid}")

        # Close stdin if PIPE
        if stdin_config == "PIPE" and process.stdin:
            process.stdin.close()
            await process.stdin.wait_closed()
            print("✅ stdin closed")

        # Wait for completion
        print("⏳ Waiting for response...")
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            elapsed = time.time() - start

            print(f"✅ SUCCESS in {elapsed:.1f}s")
            print(f"   stdout: {len(stdout)} bytes")
            print(f"   stderr: {len(stderr)} bytes")
            print(f"   returncode: {process.returncode}")

            # Parse events
            output = stdout.decode()
            events = [json.loads(line) for line in output.split('\n') if line.strip()]
            print(f"   events: {len(events)}")

            return {"status": "success", "time": elapsed, "events": len(events)}

        except asyncio.TimeoutError:
            elapsed = time.time() - start
            print(f"⏱️  TIMEOUT after {timeout}s")
            process.kill()
            await process.wait()
            return {"status": "timeout", "time": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        print(f"💥 EXCEPTION: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


async def test_real_time_reading(name, cmd, timeout=20):
    """Test with real-time stdout reading instead of communicate()."""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*80}")
    print(f"Reading stdout in real-time")

    start = time.time()

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL
        )
        print(f"✅ PID: {process.pid}")

        output_lines = []

        async def read_stdout():
            """Read stdout line by line."""
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.decode())
                print(f"  📥 Line {len(output_lines)}: {len(line)} bytes")

        # Race between reading and timeout
        print("⏳ Reading output in real-time...")
        try:
            await asyncio.wait_for(read_stdout(), timeout=timeout)
            await process.wait()
            elapsed = time.time() - start

            print(f"✅ SUCCESS in {elapsed:.1f}s")
            print(f"   Total lines: {len(output_lines)}")
            print(f"   returncode: {process.returncode}")

            return {"status": "success", "time": elapsed, "lines": len(output_lines)}

        except asyncio.TimeoutError:
            elapsed = time.time() - start
            print(f"⏱️  TIMEOUT after {timeout}s")
            print(f"   Lines received: {len(output_lines)}")
            process.kill()
            await process.wait()
            return {"status": "timeout", "time": elapsed, "lines": len(output_lines)}

    except Exception as e:
        elapsed = time.time() - start
        print(f"💥 EXCEPTION: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


async def main():
    print("="*80)
    print("🔬 SUBPROCESS CONFIGURATION TESTING")
    print("="*80)

    results = {}

    # ========================================================================
    # TEST 1: Current config (baseline - should timeout)
    # ========================================================================
    results["baseline"] = await test_config(
        "BASELINE: No stdin config",
        BASE_CMD,
        stdin_config=None,
        timeout=20
    )

    # ========================================================================
    # TEST 2: stdin=DEVNULL
    # ========================================================================
    results["stdin_devnull"] = await test_config(
        "stdin=DEVNULL",
        BASE_CMD,
        stdin_config="DEVNULL",
        timeout=20
    )

    # ========================================================================
    # TEST 3: stdin=PIPE then close
    # ========================================================================
    results["stdin_pipe_close"] = await test_config(
        "stdin=PIPE + close immediately",
        BASE_CMD,
        stdin_config="PIPE",
        timeout=20
    )

    # ========================================================================
    # TEST 4: Explicit environment
    # ========================================================================
    env = os.environ.copy()
    # Add any missing vars
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    env.setdefault("HOME", os.path.expanduser("~"))

    results["explicit_env"] = await test_config(
        "Explicit environment vars",
        BASE_CMD,
        stdin_config="DEVNULL",
        env_config=env,
        timeout=20
    )

    # ========================================================================
    # TEST 5: Real-time reading
    # ========================================================================
    results["realtime_reading"] = await test_real_time_reading(
        "Real-time stdout reading",
        BASE_CMD,
        timeout=20
    )

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("📊 RESULTS SUMMARY")
    print("="*80)

    for name, result in results.items():
        status = result["status"]
        time_str = f"{result.get('time', 0):.1f}s"

        emoji = {"success": "✅", "timeout": "⏱️ ", "exception": "💥"}.get(status, "❓")

        extra = ""
        if "events" in result:
            extra = f" ({result['events']} events)"
        elif "lines" in result:
            extra = f" ({result['lines']} lines)"

        print(f"{emoji} {name:25s}: {status:12s} ({time_str}){extra}")

    # Find working solutions
    working = [name for name, res in results.items() if res["status"] == "success"]

    print("\n" + "="*80)
    if working:
        print(f"✅ WORKING SOLUTIONS:")
        for name in working:
            print(f"   - {name}: {results[name]['time']:.1f}s")
    else:
        print("❌ NO WORKING SOLUTION FOUND!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
