#!/usr/bin/env python3
"""
Deep analysis: WHY does long prompt work with --agents but timeout without?
"""

import asyncio
import json
import time

# Same test data as before
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


async def test_scenario(name, cmd, timeout=20):
    """Test a single scenario."""
    print(f"\n{'='*80}")
    print(f"🧪 {name}")
    print(f"{'='*80}")

    # Show key parameters
    has_agents = "--agents" in cmd
    has_stream = "--output-format" in cmd and "stream-json" in cmd
    has_verbose = "--verbose" in cmd
    print(f"   --agents: {'YES' if has_agents else 'NO'}")
    print(f"   stream-json: {'YES' if has_stream else 'NO'}")
    print(f"   --verbose: {'YES' if has_verbose else 'NO'}")

    start = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            elapsed = time.time() - start

            if process.returncode == 0:
                output = stdout.decode()
                print(f"✅ SUCCESS in {elapsed:.1f}s")
                print(f"   Output: {len(output)} chars")
                return {"status": "success", "time": elapsed, "output_len": len(output)}
            else:
                error = stderr.decode() if stderr else "Unknown error"
                print(f"❌ FAILED in {elapsed:.1f}s")
                print(f"   Error: {error[:150]}")
                return {"status": "error", "time": elapsed}

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            print(f"⏱️  TIMEOUT after {timeout}s")
            return {"status": "timeout", "time": timeout}

    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return {"status": "exception"}


async def main():
    print("="*80)
    print("🔬 DEEP ANALYSIS: Long Prompt with --agents")
    print("="*80)

    results = {}

    # ========================================================================
    # GROUP 1: Reproduce the problem & solution
    # ========================================================================
    print("\n" + "="*80)
    print("📊 GROUP 1: Reproduce Problem & Solution")
    print("="*80)

    # Original timeout (from test3)
    results["baseline_timeout"] = await test_scenario(
        "BASELINE: Long prompt WITHOUT --agents (should timeout)",
        ["claude", "-p", LONG_PROMPT],
        timeout=20
    )

    # Original success (from test6)
    agent_def = {
        "research": {
            "description": "Research analyst",
            "prompt": SYSTEM_PROMPT,
            "tools": []  # NO tools - just text analysis
        }
    }

    results["baseline_success"] = await test_scenario(
        "BASELINE: Long prompt WITH --agents (should work)",
        ["claude", "--agents", json.dumps(agent_def), "-p", LONG_PROMPT],
        timeout=25
    )

    # ========================================================================
    # GROUP 2: Minimal requirements - what's REALLY needed?
    # ========================================================================
    print("\n" + "="*80)
    print("📊 GROUP 2: Find Minimal Working Configuration")
    print("="*80)

    # Test: --agents + --model only
    results["minimal_1"] = await test_scenario(
        "MINIMAL 1: --agents + --model",
        [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--agents", json.dumps(agent_def),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # Test: --agents + --model + stream-json
    results["minimal_2"] = await test_scenario(
        "MINIMAL 2: --agents + --model + stream-json",
        [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--agents", json.dumps(agent_def),
            "--output-format", "stream-json",
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # Test: --agents + --model + verbose (NO stream-json)
    results["minimal_3"] = await test_scenario(
        "MINIMAL 3: --agents + --model + verbose (NO stream-json)",
        [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--agents", json.dumps(agent_def),
            "--verbose",
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # GROUP 3: Where should system prompt go?
    # ========================================================================
    print("\n" + "="*80)
    print("📊 GROUP 3: System Prompt Placement")
    print("="*80)

    # Option A: System prompt in agent.prompt (current approach)
    agent_with_system = {
        "research": {
            "description": "Research analyst",
            "prompt": SYSTEM_PROMPT,
            "tools": []
        }
    }

    results["system_in_agent"] = await test_scenario(
        "SYSTEM PROMPT in agent.prompt",
        [
            "claude",
            "--agents", json.dumps(agent_with_system),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # Option B: System prompt combined in user prompt
    agent_no_system = {
        "research": {
            "description": "Research analyst",
            "prompt": "You are a helpful assistant.",  # Minimal
            "tools": []
        }
    }

    combined_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{LONG_PROMPT}"

    results["system_in_user"] = await test_scenario(
        "SYSTEM PROMPT combined in -p",
        [
            "claude",
            "--agents", json.dumps(agent_no_system),
            "-p", combined_prompt
        ],
        timeout=25
    )

    # Option C: System prompt ONLY in agent.prompt, minimal user prompt
    minimal_user_prompt = "Provide a structured summary of the key findings from the research above."

    results["system_only_agent"] = await test_scenario(
        "SYSTEM PROMPT only in agent (minimal user prompt)",
        [
            "claude",
            "--agents", json.dumps(agent_with_system),
            "-p", minimal_user_prompt
        ],
        timeout=25
    )

    # ========================================================================
    # GROUP 4: Tools matter?
    # ========================================================================
    print("\n" + "="*80)
    print("📊 GROUP 4: Do Tools Affect Long Prompt Handling?")
    print("="*80)

    # With tools
    agent_with_tools = {
        "research": {
            "description": "Research analyst",
            "prompt": SYSTEM_PROMPT,
            "tools": ["Read", "Bash"]  # Tools included
        }
    }

    results["with_tools"] = await test_scenario(
        "WITH tools: [Read, Bash]",
        [
            "claude",
            "--agents", json.dumps(agent_with_tools),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # Without tools (empty list)
    agent_no_tools = {
        "research": {
            "description": "Research analyst",
            "prompt": SYSTEM_PROMPT,
            "tools": []  # Explicitly empty
        }
    }

    results["without_tools"] = await test_scenario(
        "WITHOUT tools: []",
        [
            "claude",
            "--agents", json.dumps(agent_no_tools),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # GROUP 5: Permission mode?
    # ========================================================================
    print("\n" + "="*80)
    print("📊 GROUP 5: Does Permission Mode Help?")
    print("="*80)

    results["with_permission"] = await test_scenario(
        "WITH --permission-mode acceptEdits",
        [
            "claude",
            "--permission-mode", "acceptEdits",
            "--agents", json.dumps(agent_def),
            "-p", LONG_PROMPT
        ],
        timeout=25
    )

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("📊 FINAL ANALYSIS")
    print("="*80)

    success_tests = {k: v for k, v in results.items() if v["status"] == "success"}
    timeout_tests = {k: v for k, v in results.items() if v["status"] == "timeout"}

    print(f"\n✅ SUCCESSFUL: {len(success_tests)}/{len(results)} tests")
    for name, result in success_tests.items():
        print(f"   {name:30s} → {result['time']:.1f}s")

    print(f"\n⏱️  TIMEOUT: {len(timeout_tests)}/{len(results)} tests")
    for name in timeout_tests.keys():
        print(f"   {name}")

    # Key insights
    print("\n" + "="*80)
    print("🎓 KEY INSIGHTS:")
    print("="*80)

    if results["baseline_timeout"]["status"] == "timeout" and results["baseline_success"]["status"] == "success":
        print("\n1. ✅ CONFIRMED: Long prompt NEEDS --agents to work")
        print("   WITHOUT --agents → timeout")
        print("   WITH --agents → success")

    # Compare different configurations
    minimal_configs = ["minimal_1", "minimal_2", "minimal_3"]
    working_minimal = [k for k in minimal_configs if results[k]["status"] == "success"]

    if working_minimal:
        fastest = min(working_minimal, key=lambda k: results[k]["time"])
        print(f"\n2. ⚡ FASTEST minimal config: {fastest}")
        print(f"   Time: {results[fastest]['time']:.1f}s")

    # System prompt placement
    system_tests = ["system_in_agent", "system_in_user", "system_only_agent"]
    system_working = [k for k in system_tests if k in results and results[k]["status"] == "success"]

    if system_working:
        print(f"\n3. 📝 SYSTEM PROMPT placement:")
        for test in system_working:
            print(f"   {test:30s} → {results[test]['time']:.1f}s")

    # Tools impact
    if "with_tools" in results and "without_tools" in results:
        with_t = results["with_tools"]
        without_t = results["without_tools"]

        print(f"\n4. 🛠️  TOOLS impact:")
        print(f"   WITH tools: {with_t['status']} ({with_t.get('time', 0):.1f}s)")
        print(f"   WITHOUT tools: {without_t['status']} ({without_t.get('time', 0):.1f}s)")

    # Save results
    with open("/tmp/claude_deep_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📝 Full results: /tmp/claude_deep_analysis.json")


if __name__ == "__main__":
    asyncio.run(main())
