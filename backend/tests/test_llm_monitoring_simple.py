#!/usr/bin/env python3
"""
🧪 Ultra-Logging Framework - Simple Direct Tests

Direkter Test ohne Module-Import Probleme
"""

from decimal import Decimal
from pathlib import Path
import tempfile
import json
import sys
import os
from dataclasses import dataclass
from datetime import datetime

# Direct imports from file instead of via package
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the monitoring module directly
import importlib.util
monitoring_path = os.path.join(os.path.dirname(__file__), "..", "core", "llm_monitoring.py")
spec = importlib.util.spec_from_file_location("llm_monitoring", monitoring_path)
monitoring_module = importlib.util.module_from_spec(spec)
sys.modules["llm_monitoring"] = monitoring_module
spec.loader.exec_module(monitoring_module)

# Get classes
LLMMonitor = monitoring_module.LLMMonitor
LLMCallMetrics = monitoring_module.LLMCallMetrics
MemorySnapshot = monitoring_module.MemorySnapshot
TokenPricingConfig = monitoring_module.TokenPricingConfig


# ============================================================================
# Tests: Token Pricing
# ============================================================================

def test_openai_pricing_gpt4o_mini():
    """Test GPT-4o-mini pricing calculation."""
    cost = TokenPricingConfig.get_cost(
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500,
    )
    
    # gpt-4o-mini: $0.15/M input, $0.60/M output
    # Input: 1000 * (0.15 / 1M) = 0.00015
    # Output: 500 * (0.60 / 1M) = 0.0003
    # Total: 0.00045
    
    expected = Decimal("0.00045")
    assert cost == expected, f"Expected {expected}, got {cost}"
    print(f"✅ GPT-4o-mini pricing: ${cost}")


def test_openai_pricing_gpt4o():
    """Test GPT-4o pricing calculation."""
    cost = TokenPricingConfig.get_cost(
        provider="openai",
        model="gpt-4o",
        input_tokens=1_000_000,
        output_tokens=500_000,
    )
    
    # gpt-4o: $5/M input, $15/M output
    # Input: 1_000_000 * (5 / 1M) = 5.00
    # Output: 500_000 * (15 / 1M) = 7.50
    # Total: 12.50
    
    expected = Decimal("12.50")
    assert cost == expected, f"Expected {expected}, got {cost}"
    print(f"✅ GPT-4o pricing: ${cost}")


def test_anthropic_pricing():
    """Test Anthropic pricing."""
    cost = TokenPricingConfig.get_cost(
        provider="anthropic",
        model="claude-sonnet",
        input_tokens=100_000,
        output_tokens=50_000,
    )
    
    # claude-sonnet: $3/M input, $15/M output
    # Input: 100_000 * (3 / 1M) = 0.30
    # Output: 50_000 * (15 / 1M) = 0.75
    # Total: 1.05
    
    expected = Decimal("1.05")
    assert cost == expected, f"Expected {expected}, got {cost}"
    print(f"✅ Claude Sonnet pricing: ${cost}")


# ============================================================================
# Tests: Memory Snapshot
# ============================================================================

def test_memory_snapshot_format():
    """Test memory snapshot formatting."""
    snapshot = MemorySnapshot(
        rss_mb=245.5,
        vms_mb=512.3,
        resident_mb=156.2,
        available_mb=1024.0,
    )
    
    formatted = snapshot.format()
    assert "RSS=" in formatted
    assert "VMS=" in formatted
    print(f"✅ Memory snapshot format: {formatted}")


def test_memory_delta():
    """Test memory delta calculation."""
    snapshot1 = MemorySnapshot(
        rss_mb=200.0,
        vms_mb=400.0,
        resident_mb=150.0,
        available_mb=1024.0,
    )
    
    snapshot2 = MemorySnapshot(
        rss_mb=212.0,
        vms_mb=412.0,
        resident_mb=162.0,
        available_mb=1020.0,
    )
    
    delta = snapshot2.delta_from(snapshot1)
    assert "+12.0MB" in delta
    print(f"✅ Memory delta: {delta}")


# ============================================================================
# Tests: Metrics
# ============================================================================

def test_metrics_creation():
    """Test metrics creation."""
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    metrics = LLMCallMetrics(
        agent_name="ReviewerGPT",
        provider="openai",
        model="gpt-4o-mini",
        prompt_length=500,
        completion_length=300,
        input_tokens=100,
        output_tokens=75,
        total_tokens=175,
        api_latency_ms=1500.0,
        total_latency_ms=1550.0,
        cost_usd=Decimal("0.00045"),
        memory_start=memory_start,
        memory_end=memory_end,
        status="success",
        request_id="test-001",
    )
    
    assert metrics.agent_name == "ReviewerGPT"
    assert metrics.total_tokens == 175
    print(f"✅ Metrics created: {metrics.request_id}")


def test_metrics_dict_serialization():
    """Test metrics serialization."""
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    metrics = LLMCallMetrics(
        agent_name="ReviewerGPT",
        provider="openai",
        model="gpt-4o-mini",
        prompt_length=500,
        completion_length=300,
        input_tokens=100,
        output_tokens=75,
        total_tokens=175,
        api_latency_ms=1500.0,
        total_latency_ms=1550.0,
        cost_usd=Decimal("0.00045"),
        memory_start=memory_start,
        memory_end=memory_end,
        status="success",
        request_id="test-001",
    )
    
    data = metrics.to_dict()
    assert data["agent_name"] == "ReviewerGPT"
    assert isinstance(data["cost_usd"], str)
    print(f"✅ Metrics dict serializable")


# ============================================================================
# Tests: Monitor Recording
# ============================================================================

def test_monitor_recording():
    """Test recording metrics to monitor."""
    LLMMonitor.reset()
    
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    metrics = LLMCallMetrics(
        agent_name="ReviewerGPT",
        provider="openai",
        model="gpt-4o-mini",
        prompt_length=500,
        completion_length=300,
        input_tokens=100,
        output_tokens=75,
        total_tokens=175,
        api_latency_ms=1500.0,
        total_latency_ms=1550.0,
        cost_usd=Decimal("0.00045"),
        memory_start=memory_start,
        memory_end=memory_end,
        status="success",
        request_id="test-001",
    )
    
    LLMMonitor.record_metric(metrics)
    
    summary = LLMMonitor.get_summary()
    assert summary["total_calls"] == 1
    assert "ReviewerGPT" in summary["by_agent"]
    print(f"✅ Monitor recording: {summary['total_calls']} call(s)")


def test_monitor_multiple_calls():
    """Test recording multiple calls."""
    LLMMonitor.reset()
    
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    # Record 3 metrics
    for i in range(3):
        metrics = LLMCallMetrics(
            agent_name=["ReviewerGPT", "CodesmithAgent", "ArchitectAgent"][i],
            provider="openai",
            model="gpt-4o-mini",
            prompt_length=500,
            completion_length=300,
            input_tokens=100 * (i + 1),
            output_tokens=75 * (i + 1),
            total_tokens=175 * (i + 1),
            api_latency_ms=1500.0,
            total_latency_ms=1550.0,
            cost_usd=Decimal("0.00045") * (i + 1),
            memory_start=memory_start,
            memory_end=memory_end,
            status="success",
            request_id=f"test-{i:03d}",
        )
        LLMMonitor.record_metric(metrics)
    
    summary = LLMMonitor.get_summary()
    assert summary["total_calls"] == 3
    assert len(summary["by_agent"]) == 3
    print(f"✅ Multiple calls: {summary['total_calls']} from {len(summary['by_agent'])} agents")


def test_monitor_cost_tracking():
    """Test cost tracking."""
    LLMMonitor.reset()
    
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    costs = [Decimal("0.10"), Decimal("0.20"), Decimal("0.15")]
    
    for i, cost in enumerate(costs):
        metrics = LLMCallMetrics(
            agent_name=f"Agent{i}",
            provider="openai",
            model="gpt-4o-mini",
            prompt_length=500,
            completion_length=300,
            input_tokens=100,
            output_tokens=75,
            total_tokens=175,
            api_latency_ms=1500.0,
            total_latency_ms=1550.0,
            cost_usd=cost,
            memory_start=memory_start,
            memory_end=memory_end,
            status="success",
            request_id=f"test-{i:03d}",
        )
        LLMMonitor.record_metric(metrics)
    
    summary = LLMMonitor.get_summary()
    assert "$0.45" in summary["total_cost"]
    print(f"✅ Cost tracking: {summary['total_cost']}")


# ============================================================================
# Tests: Export
# ============================================================================

def test_monitor_export():
    """Test metrics export to JSON."""
    LLMMonitor.reset()
    
    memory_start = MemorySnapshot(100, 200, 100, 1024)
    memory_end = MemorySnapshot(112, 212, 112, 1020)
    
    metrics = LLMCallMetrics(
        agent_name="ReviewerGPT",
        provider="openai",
        model="gpt-4o-mini",
        prompt_length=500,
        completion_length=300,
        input_tokens=100,
        output_tokens=75,
        total_tokens=175,
        api_latency_ms=1500.0,
        total_latency_ms=1550.0,
        cost_usd=Decimal("0.00045"),
        memory_start=memory_start,
        memory_end=memory_end,
        status="success",
        request_id="test-001",
    )
    
    LLMMonitor.record_metric(metrics)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "metrics.json"
        LLMMonitor.export_metrics(export_path)
        
        assert export_path.exists()
        
        with open(export_path) as f:
            data = json.load(f)
        
        assert "metrics" in data
        assert len(data["metrics"]) == 1
        print(f"✅ Export works: {export_path.name}")


# ============================================================================
# Main
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🧪 Ultra-Logging Framework - Simple Tests")
    print("="*80 + "\n")
    
    print("📊 Token Pricing Tests...")
    test_openai_pricing_gpt4o_mini()
    test_openai_pricing_gpt4o()
    test_anthropic_pricing()
    
    print("\n💾 Memory Snapshot Tests...")
    test_memory_snapshot_format()
    test_memory_delta()
    
    print("\n📈 Metrics Tests...")
    test_metrics_creation()
    test_metrics_dict_serialization()
    
    print("\n📋 Monitor Recording Tests...")
    test_monitor_recording()
    test_monitor_multiple_calls()
    test_monitor_cost_tracking()
    
    print("\n📁 Export Tests...")
    test_monitor_export()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
