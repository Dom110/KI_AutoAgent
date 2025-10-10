#!/usr/bin/env python3
"""
Test different Claude CLI parameter combinations to find what works with long prompts
"""

import asyncio
import json
import time

# Test data
SHORT_PROMPT = "Say hello in exactly 3 words."

LONG_PROMPT = """Analyze the following research results:

**Query:** Python async best practices

**Search Results:**
The best practices for Python asynchronous programming focus on using **async-native libraries**, understanding when to apply async code, avoiding blocking synchronous calls in async contexts, and leveraging modern Python features like `async`/`await` and `asyncio`. Key points are:

1. **Use async-native libraries** such as `aiohttp` or `httpx` for network I/O instead of synchronous libraries to fully benefit from async concurrency and avoid blocking the event loop.

2. **Apply async only for I/O-bound tasks** where concurrency improves performance, like HTTP requests, database queries, or file operations. Avoid async for CPU-bound tasks, which require multiprocessing or threading instead.

3. **Avoid mixing synchronous blocking calls inside async functions**, such as `time.sleep()` or synchronous file I/O (`open()`), which block the event loop and reduce concurrency. Use async equivalents like `asyncio.sleep()` and async file libraries.

4. **Use Python 3.7 or above** to leverage improvements like `asyncio.run()` and context variables that help manage task-local data cleanly.

5. **Structure async code clearly using `async`/`await` syntax**, which simplifies writing and reading asynchronous code by making it look more like synchronous code while maintaining concurrency.

6. **Use proper logging instead of print statements** in async applications to avoid blocking and support structured, parseable logs.

7. **Design applications to run multiple processes or containers** if concurrency beyond async I/O is needed, using tools like Gunicorn or the `multiprocessing` module, since async concurrency is single-threaded.

8. **Understand the event loop** as the core of async concurrency; it schedules tasks and switches between them efficiently without preemptive threading.

### Latest trends and updates (2025):

- Python async ecosystem is rapidly evolving with more async-native libraries and frameworks, especially in web servers, real-time apps, and microservices.
- Async programming is becoming the default choice for I/O-bound concurrency in Python projects, supported by improvements in language syntax and runtime.
- Emphasis on combining async with modern Python tooling and infrastructure as code for scalable applications.

### Summary table of best practices:

| Practice                        | Description                                                                                  |
|--------------------------------|----------------------------------------------------------------------------------------------|
| Use async-native libraries      | Prefer `aiohttp`, `httpx` over synchronous libraries for I/O                                |
| Async for I/O-bound only       | Use async for network, DB, file I/O; avoid for CPU-bound tasks                              |
| Avoid blocking sync calls       | Replace `time.sleep()` with `asyncio.sleep()`, avoid sync file I/O in async functions       |
| Use Python 3.7+ features        | Use `asyncio.run()`, context variables for better async code management                      |
| Use `async`/`await` syntax      | Write clear, readable async code that resembles synchronous flow                            |
| Use logging over print          | Avoid blocking print calls; use structured logging                                          |
| Multi-process for CPU-bound     | Use multiprocessing or containers for parallelism beyond async I/O                          |
| Understand event loop           | Event loop schedules and switches async tasks cooperatively                                |

These points synthesize the most relevant and recent insights about Python async best practices from the latest 2025 sources.

Provide a structured summary of the key findings."""


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


async def test_scenario(name, cmd, timeout=15):
    """Test a single scenario."""
    print(f"\n{'='*80}")
    print(f"🧪 {name}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(cmd[:4])}... ({len(cmd)} args)")

    start = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            elapsed = time.time() - start

            if process.returncode == 0:
                output = stdout.decode()
                print(f"✅ SUCCESS in {elapsed:.1f}s")
                print(f"   Output length: {len(output)} chars")
                # Show first 100 chars
                preview = output[:100].replace('\n', ' ')
                print(f"   Preview: {preview}...")
                return {"status": "success", "time": elapsed, "output_len": len(output)}
            else:
                error = stderr.decode() if stderr else "Unknown error"
                print(f"❌ FAILED in {elapsed:.1f}s")
                print(f"   Error: {error[:200]}")
                return {"status": "error", "time": elapsed, "error": error[:200]}

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            print(f"⏱️  TIMEOUT after {timeout}s")
            return {"status": "timeout", "time": timeout}

    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return {"status": "exception", "error": str(e)}


async def main():
    print("="*80)
    print("🔬 CLAUDE CLI PARAMETER TEST SUITE")
    print("="*80)

    results = {}

    # ========================================================================
    # TEST 1: Short prompt, -p flag, no agents
    # ========================================================================
    results["test1"] = await test_scenario(
        "TEST 1: Short prompt with -p (baseline)",
        ["claude", "-p", SHORT_PROMPT]
    )

    # ========================================================================
    # TEST 2: Short prompt, --prompt flag, no agents
    # ========================================================================
    results["test2"] = await test_scenario(
        "TEST 2: Short prompt with --prompt",
        ["claude", "--prompt", SHORT_PROMPT]
    )

    # ========================================================================
    # TEST 3: Long prompt, -p flag, no agents
    # ========================================================================
    results["test3"] = await test_scenario(
        "TEST 3: Long prompt (4300 chars) with -p",
        ["claude", "-p", LONG_PROMPT],
        timeout=20
    )

    # ========================================================================
    # TEST 4: Long prompt, --prompt flag, no agents
    # ========================================================================
    results["test4"] = await test_scenario(
        "TEST 4: Long prompt (4300 chars) with --prompt",
        ["claude", "--prompt", LONG_PROMPT],
        timeout=20
    )

    # ========================================================================
    # TEST 5: Short prompt with --agents
    # ========================================================================
    agent_def = {
        "research": {
            "description": "Research analyst",
            "prompt": SYSTEM_PROMPT,
            "tools": ["Read", "Bash"]
        }
    }

    results["test5"] = await test_scenario(
        "TEST 5: Short prompt with --agents",
        [
            "claude",
            "--agents", json.dumps(agent_def),
            "-p", SHORT_PROMPT
        ],
        timeout=20
    )

    # ========================================================================
    # TEST 6: Long prompt with --agents
    # ========================================================================
    results["test6"] = await test_scenario(
        "TEST 6: Long prompt with --agents",
        [
            "claude",
            "--agents", json.dumps(agent_def),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # TEST 7: Long prompt with --agents + --verbose
    # ========================================================================
    results["test7"] = await test_scenario(
        "TEST 7: Long prompt with --agents + --verbose",
        [
            "claude",
            "--agents", json.dumps(agent_def),
            "--verbose",
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # TEST 8: Long prompt with --agents + stream-json + --verbose
    # ========================================================================
    results["test8"] = await test_scenario(
        "TEST 8: Long prompt with --agents + stream-json + --verbose",
        [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--agents", json.dumps(agent_def),
            "--output-format", "stream-json",
            "--verbose",
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # TEST 9: Long prompt WITHOUT --agents, just model + output-format
    # ========================================================================
    results["test9"] = await test_scenario(
        "TEST 9: Long prompt WITHOUT --agents (simple mode)",
        [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--output-format", "stream-json",
            "--verbose",
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # TEST 10: Long prompt with stdin instead of -p
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"🧪 TEST 10: Long prompt via STDIN")
    print(f"{'='*80}")
    start = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            "claude",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=LONG_PROMPT.encode()),
                timeout=20
            )
            elapsed = time.time() - start

            if process.returncode == 0:
                print(f"✅ SUCCESS in {elapsed:.1f}s")
                results["test10"] = {"status": "success", "time": elapsed}
            else:
                print(f"❌ FAILED in {elapsed:.1f}s")
                results["test10"] = {"status": "error", "time": elapsed}
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            print(f"⏱️  TIMEOUT after 20s")
            results["test10"] = {"status": "timeout", "time": 20}
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        results["test10"] = {"status": "exception", "error": str(e)}

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("📊 RESULTS SUMMARY")
    print("="*80)

    for test_name, result in results.items():
        status = result["status"]
        time_str = f"{result.get('time', 0):.1f}s" if "time" in result else "N/A"

        emoji = {
            "success": "✅",
            "timeout": "⏱️ ",
            "error": "❌",
            "exception": "💥"
        }.get(status, "❓")

        print(f"{emoji} {test_name}: {status.upper():12s} ({time_str})")

    # Find working solutions
    working = [name for name, res in results.items() if res["status"] == "success"]

    print("\n" + "="*80)
    if working:
        print(f"✅ WORKING SOLUTIONS: {', '.join(working)}")
    else:
        print("❌ NO WORKING SOLUTION FOUND!")
    print("="*80)

    # Save detailed results
    with open("/tmp/claude_cli_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📝 Detailed results saved to: /tmp/claude_cli_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
