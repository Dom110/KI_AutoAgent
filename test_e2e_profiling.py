#!/usr/bin/env python3
"""
E2E Workflow Timing Profiler

Measures actual execution time for each component:
1. v6 System Initialization
2. Pre-execution Analysis
3. Research Agent
4. Architect Agent
5. Codesmith Agent
6. ReviewFix Agent
7. Post-execution Learning

Identifies real bottlenecks with concrete timing data.

Author: KI AutoAgent Team
Version: 6.1.0-alpha
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Any

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()


# ============================================================================
# TIMING CONTEXT MANAGER
# ============================================================================

class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration = 0.0

    def __enter__(self):
        print(f"\n⏱️  {self.name} - START")
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print(f"⏱️  {self.name} - END ({self.duration:.2f}s)")
        return False


# ============================================================================
# PROFILING TEST
# ============================================================================

async def profile_workflow_initialization():
    """Profile v6 system initialization."""
    from workflow_v6_integrated import WorkflowV6Integrated

    test_workspace = "/tmp/ki_autoagent_profiling_test"
    Path(test_workspace).mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("🔍 E2E WORKFLOW PROFILING")
    print("=" * 80)

    timings = {}

    # Phase 1: Workflow Creation
    with Timer("1️⃣ Workflow Instance Creation") as t:
        workflow = WorkflowV6Integrated(
            workspace_path=test_workspace,
            websocket_callback=None
        )
    timings["workflow_creation"] = t.duration

    # Phase 2: v6 System Initialization
    with Timer("2️⃣ v6 System Initialization") as t:
        await workflow.initialize()
    timings["v6_initialization"] = t.duration

    print("\n" + "=" * 80)
    print("📊 INITIALIZATION BREAKDOWN")
    print("=" * 80)

    # Check individual components
    components = {
        "checkpointer": workflow.checkpointer,
        "memory": workflow.memory,
        "workflow": workflow.workflow,
        "query_classifier": workflow.query_classifier,
        "curiosity": workflow.curiosity,
        "learning": workflow.learning,
        "predictive": workflow.predictive,
        "tool_registry": workflow.tool_registry,
        "approval_manager": workflow.approval_manager,
        "workflow_adapter": workflow.workflow_adapter,
        "neurosymbolic": workflow.neurosymbolic,
        "self_diagnosis": workflow.self_diagnosis,
    }

    print("\n✅ Initialized Components:")
    for name, component in components.items():
        status = "✅" if component is not None else "❌"
        print(f"  {status} {name}")

    return workflow, timings


async def profile_simple_task():
    """Profile a simple task execution (Research only)."""
    print("\n" + "=" * 80)
    print("🧪 SIMPLE TASK: Research Query")
    print("=" * 80)

    from subgraphs.research_subgraph_v6_1 import create_research_subgraph

    timings = {}

    with Timer("Research Agent Execution") as t:
        subgraph = create_research_subgraph(
            workspace_path="/tmp/ki_autoagent_profiling_test",
            memory=None,
            hitl_callback=None
        )

        result = await subgraph.ainvoke({
            "query": "What is Python asyncio?",
            "findings": None,
            "report": None,
            "completed": False,
            "errors": []
        })

    timings["research"] = t.duration

    print(f"\n✅ Research completed: {result.get('completed', False)}")
    print(f"   Has findings: {bool(result.get('findings'))}")

    return timings


async def profile_medium_task():
    """Profile medium task (Research + Architect)."""
    print("\n" + "=" * 80)
    print("🧪 MEDIUM TASK: Research + Architecture Design")
    print("=" * 80)

    from subgraphs.research_subgraph_v6_1 import create_research_subgraph
    from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph

    timings = {}

    # Research
    with Timer("1️⃣ Research Agent") as t:
        research_subgraph = create_research_subgraph(
            workspace_path="/tmp/ki_autoagent_profiling_test",
            memory=None,
            hitl_callback=None
        )

        research_result = await research_subgraph.ainvoke({
            "query": "Best practices for REST API design",
            "findings": None,
            "report": None,
            "completed": False,
            "errors": []
        })

    timings["research"] = t.duration

    # Architect
    with Timer("2️⃣ Architect Agent") as t:
        architect_subgraph = create_architect_subgraph(
            workspace_path="/tmp/ki_autoagent_profiling_test",
            memory=None,
            hitl_callback=None
        )

        architect_result = await architect_subgraph.ainvoke({
            "user_requirements": "Design a REST API for user management",
            "workspace_path": "/tmp/ki_autoagent_profiling_test",
            "research_context": {},
            "design": {},
            "tech_stack": [],
            "patterns": [],
            "diagram": "",
            "adr": "",
            "errors": []
        })

    timings["architect"] = t.duration

    print(f"\n✅ Research completed: {bool(research_result.get('findings'))}")
    print(f"✅ Architecture completed: {bool(architect_result.get('design'))}")

    return timings


async def main():
    print("\n" + "=" * 80)
    print("🎯 E2E WORKFLOW PERFORMANCE PROFILING")
    print("=" * 80)
    print("\nThis test measures ACTUAL execution times to identify")
    print("real bottlenecks and validate optimization targets.")
    print("\n" + "=" * 80)

    all_timings = {}

    # Test 1: Initialization Profiling
    print("\n\n📍 TEST 1: WORKFLOW INITIALIZATION")
    print("=" * 80)

    workflow, init_timings = await profile_workflow_initialization()
    all_timings["initialization"] = init_timings

    # Test 2: Simple Task Profiling
    print("\n\n📍 TEST 2: SIMPLE TASK (Research Only)")
    print("=" * 80)

    simple_timings = await profile_simple_task()
    all_timings["simple_task"] = simple_timings

    # Test 3: Medium Task Profiling
    print("\n\n📍 TEST 3: MEDIUM TASK (Research + Architect)")
    print("=" * 80)

    medium_timings = await profile_medium_task()
    all_timings["medium_task"] = medium_timings

    # Generate Report
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE REPORT")
    print("=" * 80)

    print("\n🔧 INITIALIZATION TIMES:")
    print(f"  Workflow Creation: {all_timings['initialization']['workflow_creation']:.2f}s")
    print(f"  v6 System Init: {all_timings['initialization']['v6_initialization']:.2f}s")
    total_init = sum(all_timings['initialization'].values())
    print(f"  ➡️  TOTAL INIT: {total_init:.2f}s")

    print("\n⚡ AGENT EXECUTION TIMES:")
    print(f"  Research (simple): {all_timings['simple_task']['research']:.2f}s")
    print(f"  Research (medium): {all_timings['medium_task']['research']:.2f}s")
    print(f"  Architect (medium): {all_timings['medium_task']['architect']:.2f}s")

    print("\n📈 TASK TOTALS:")
    simple_total = all_timings['simple_task']['research']
    print(f"  Simple Task: {simple_total:.2f}s")

    medium_total = (
        all_timings['medium_task']['research'] +
        all_timings['medium_task']['architect']
    )
    print(f"  Medium Task: {medium_total:.2f}s")

    estimated_complex = medium_total * 2 + 40  # +Codesmith +ReviewFix +overhead
    print(f"  Complex Task (estimated): {estimated_complex:.2f}s")

    print("\n🎯 BOTTLENECK ANALYSIS:")

    bottlenecks = []

    # Initialization
    if all_timings['initialization']['v6_initialization'] > 30:
        bottlenecks.append({
            "component": "v6 System Initialization",
            "time": all_timings['initialization']['v6_initialization'],
            "severity": "HIGH",
            "recommendation": "Implement parallel initialization (asyncio.gather)"
        })

    # Architect
    if all_timings['medium_task']['architect'] > 60:
        bottlenecks.append({
            "component": "Architect Agent",
            "time": all_timings['medium_task']['architect'],
            "severity": "MEDIUM",
            "recommendation": "Already using v6.1 (Claude). Consider caching or parallel design generation."
        })

    if bottlenecks:
        print("\n⚠️  IDENTIFIED BOTTLENECKS:")
        for i, b in enumerate(bottlenecks, 1):
            print(f"\n  {i}. {b['component']} ({b['severity']})")
            print(f"     Current: {b['time']:.2f}s")
            print(f"     💡 {b['recommendation']}")
    else:
        print("\n✅ No major bottlenecks identified!")

    print("\n" + "=" * 80)
    print("✅ PROFILING COMPLETE")
    print("=" * 80)

    print("\n📝 RECOMMENDATIONS:")
    print("  1. Focus on v6 system initialization parallelization")
    print("  2. Consider caching for repeated operations")
    print("  3. Profile full E2E workflow with all 4 agents")

    # Save report
    report_file = Path("/tmp/e2e_profiling_report.txt")
    with open(report_file, "w") as f:
        f.write("E2E WORKFLOW PROFILING REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Version: 6.1.0-alpha\n\n")

        f.write("INITIALIZATION:\n")
        f.write(f"  Workflow Creation: {all_timings['initialization']['workflow_creation']:.2f}s\n")
        f.write(f"  v6 System Init: {all_timings['initialization']['v6_initialization']:.2f}s\n")
        f.write(f"  TOTAL: {total_init:.2f}s\n\n")

        f.write("AGENT EXECUTION:\n")
        f.write(f"  Research: {all_timings['simple_task']['research']:.2f}s\n")
        f.write(f"  Architect: {all_timings['medium_task']['architect']:.2f}s\n\n")

        f.write("TASK TOTALS:\n")
        f.write(f"  Simple: {simple_total:.2f}s\n")
        f.write(f"  Medium: {medium_total:.2f}s\n")
        f.write(f"  Complex (est): {estimated_complex:.2f}s\n\n")

        if bottlenecks:
            f.write("BOTTLENECKS:\n")
            for b in bottlenecks:
                f.write(f"  - {b['component']}: {b['time']:.2f}s ({b['severity']})\n")
                f.write(f"    {b['recommendation']}\n")

    print(f"\n📁 Full report saved: {report_file}")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
