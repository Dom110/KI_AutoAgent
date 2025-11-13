#!/usr/bin/env python3
"""
E2E Test Results Analyzer
Generates detailed report from test output
"""

import json
import re
from pathlib import Path

def parse_test_output(filepath):
    """Parse E2E test output and extract metrics"""
    
    if not Path(filepath).exists() or Path(filepath).stat().st_size == 0:
        return None
    
    with open(filepath) as f:
        content = f.read()
    
    results = {
        "raw_size_bytes": len(content),
        "lines": content.count('\n'),
        "tests_started": content.count("🧪 v7.0 E2E TEST:"),
        "tests_completed": content.count("📊 v7.0 TEST SUMMARY:"),
        "tests_passed": len(re.findall(r"Status: ✅ PASS", content)),
        "tests_failed": len(re.findall(r"Status: ❌ FAIL", content)),
        "supervisor_decisions_total": content.count("🎯 Supervisor Decision"),
        "agents_invoked_count": content.count("🚀 Agent Started"),
        "workflow_completed": "✅ Workflow completed" in content,
    }
    
    # Extract test names
    test_names = re.findall(r"🧪 v7.0 E2E TEST: (\w+)", content)
    results["test_names"] = test_names
    
    return results

def format_report(metrics):
    """Format metrics into report"""
    if not metrics:
        return "❌ No test results yet"
    
    report = f"""
{'='*100}
📊 E2E TEST RESULTS
{'='*100}

Tests Started: {metrics['tests_started']}
Tests Completed: {metrics['tests_completed']}
✅ PASSED: {metrics['tests_passed']}
❌ FAILED: {metrics['tests_failed']}

Supervisor Decisions: {metrics['supervisor_decisions_total']}
Agent Invocations: {metrics['agents_invoked_count']}

Test Names: {', '.join(metrics.get('test_names', []))}

{'='*100}
"""
    return report

if __name__ == "__main__":
    filepath = "/Users/dominikfoert/Tests/test_app_e2e/test_complete_results.log"
    metrics = parse_test_output(filepath)
    report = format_report(metrics)
    print(report)