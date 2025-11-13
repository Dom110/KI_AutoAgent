#!/usr/bin/env python3
"""
🎯 ReviewerGPTAgent Phase 3b Integration Demo

Zeigt wie die neue AgentLLMFactory mit Ultra-Logging funktioniert:
- Token-Tracking
- Memory-Tracking
- Cost-Calculation
- Performance-Metrics

ACHTUNG: Dieser Test ist ein DEMO - zeigt die neue Integration ohne echte API-Aufrufe
"""

import sys
import os
import json
from decimal import Decimal
from pathlib import Path
from datetime import datetime

# Import der Monitoring Utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import importlib.util
monitoring_path = os.path.join(os.path.dirname(__file__), "..", "core", "llm_monitoring.py")
spec = importlib.util.spec_from_file_location("llm_monitoring", monitoring_path)
monitoring_module = importlib.util.module_from_spec(spec)
sys.modules["llm_monitoring"] = monitoring_module
spec.loader.exec_module(monitoring_module)

LLMMonitor = monitoring_module.LLMMonitor
LLMCallMetrics = monitoring_module.LLMCallMetrics
MemorySnapshot = monitoring_module.MemorySnapshot
TokenPricingConfig = monitoring_module.TokenPricingConfig


# ============================================================================
# Simulated ReviewerGPTAgent Behavior (Phase 3b Pattern)
# ============================================================================

class SimulatedReviewerGPTAgent:
    """
    Simulierter ReviewerGPTAgent mit Phase 3b Pattern:
    - Nutzt AgentLLMFactory (nicht hardcoded ChatOpenAI)
    - Nutzt Ultra-Logging für Monitoring
    """
    
    def __init__(self, agent_name: str = "ReviewerGPT"):
        self.agent_name = agent_name
        self.llm_provider_name = "openai"
        self.llm_model = "gpt-4o-mini-2024-07-18"
        logger_name = f"agent.{agent_name}"
        
        # Setup logging
        import logging
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        self.logger.info(f"🤖 Initializing {agent_name} Agent (Phase 3b)")
        self.logger.info(f"├─ Provider: {self.llm_provider_name}")
        self.logger.info(f"├─ Model: {self.llm_model}")
        self.logger.info(f"└─ Temperature: 0.3")
    
    async def review_code_simulated(self, code_snippet: str) -> dict:
        """
        Simulate code review with monitoring.
        
        In echtem Code würde hier echter API-Aufruf stattfinden:
        ```python
        response = await self.llm_provider.generate_text(...)
        ```
        """
        self.logger.info(f"📋 Reviewing code ({len(code_snippet)} chars)")
        
        # Simuliere LLM-Aufrufe mit Monitoring
        return await self._simulate_review_with_monitoring(code_snippet)
    
    async def _simulate_review_with_monitoring(self, code: str) -> dict:
        """Simuliere mehrere LLM-Aufrufe mit Monitoring."""
        
        import asyncio
        
        # Simuliere 3 sequentielle LLM-Aufrufe (Quality Check, Security Check, Performance)
        reviews = []
        
        steps = [
            ("Quality Analysis", len(code) * 2),  # Simulated token count
            ("Security Scan", len(code) * 1.5),
            ("Performance Review", len(code) * 1.2),
        ]
        
        for step_name, input_tokens in steps:
            self.logger.info(f"\n🔍 {step_name}...")
            
            # Simuliere API-Latenz
            await asyncio.sleep(0.1)
            
            # Simuliere Response
            output_tokens = int(len(code) * 0.5)
            
            # Erstelle Metrics
            memory_start = LLMMonitor.capture_memory()
            
            # Simuliere Verarbeitung
            await asyncio.sleep(0.05)
            
            memory_end = LLMMonitor.capture_memory()
            
            # Berechne Cost
            cost = TokenPricingConfig.get_cost(
                provider=self.llm_provider_name,
                model=self.llm_model,
                input_tokens=int(input_tokens),
                output_tokens=output_tokens,
            )
            
            # Erstelle Metrics
            metrics = LLMCallMetrics(
                agent_name=self.agent_name,
                provider=self.llm_provider_name,
                model=self.llm_model,
                prompt_length=len(code),
                completion_length=output_tokens * 4,  # Rough estimate
                input_tokens=int(input_tokens),
                output_tokens=output_tokens,
                total_tokens=int(input_tokens) + output_tokens,
                api_latency_ms=150.0,  # Simulated
                total_latency_ms=200.0,
                cost_usd=cost,
                memory_start=memory_start,
                memory_end=memory_end,
                status="success",
                request_id=f"{self.agent_name}-{step_name.replace(' ', '-').lower()}",
            )
            
            # Log und Record
            LLMMonitor.log_call_start(
                monitoring_module.AgentMonitoringContext(
                    agent_name=self.agent_name,
                    provider=self.llm_provider_name,
                    model=self.llm_model,
                    request_id=metrics.request_id,
                )
            )
            
            LLMMonitor.log_call_end(metrics)
            LLMMonitor.record_metric(metrics)
            
            reviews.append({
                "step": step_name,
                "status": "✅ Pass",
                "findings": f"Reviewed {len(code)} bytes",
                "tokens_used": metrics.total_tokens,
                "cost": str(cost),
            })
        
        return {
            "code_review_complete": True,
            "steps": len(reviews),
            "reviews": reviews,
        }


# ============================================================================
# Demo: Full Workflow
# ============================================================================

async def run_demo():
    """Run complete demo of Phase 3b ReviewerGPTAgent."""
    
    print("\n" + "="*80)
    print("🎯 Phase 3b ReviewerGPTAgent Integration Demo")
    print("="*80 + "\n")
    
    # Reset monitor
    LLMMonitor.reset()
    
    # Initialize agent
    agent = SimulatedReviewerGPTAgent("ReviewerGPT")
    
    # Sample code to review
    sample_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total

# Usage
results = calculate_total([
    {'price': 10, 'quantity': 2},
    {'price': 20, 'quantity': 1},
])
print(f"Total: {results}")
"""
    
    print("\n📝 Code to Review:")
    print(sample_code)
    
    print("\n" + "="*80)
    print("🚀 Starting Review Process with Ultra-Logging...")
    print("="*80)
    
    # Run review
    result = await agent.review_code_simulated(sample_code)
    
    print("\n" + "="*80)
    print("📊 MONITORING SUMMARY")
    print("="*80)
    
    summary = LLMMonitor.get_summary()
    
    print(f"\n✅ Total API Calls: {summary['total_calls']}")
    print(f"✅ Successful Calls: {summary['success_calls']}")
    print(f"📊 Total Tokens Used: {summary['total_tokens']:,}")
    print(f"💰 Total Cost: {summary['total_cost']}")
    
    print("\n📋 Per-Agent Breakdown:")
    for agent_name, stats in summary['by_agent'].items():
        print(f"\n  {agent_name}:")
        print(f"    - Calls: {stats['calls']}")
        print(f"    - Tokens: {stats['tokens']:,}")
        print(f"    - Cost: {stats['cost']}")
        print(f"    - Errors: {stats['errors']}")
    
    # Export metrics
    print("\n" + "="*80)
    print("📁 Exporting Metrics...")
    print("="*80)
    
    export_path = Path("/tmp/phase3b_reviewer_metrics.json")
    LLMMonitor.export_metrics(export_path)
    print(f"✅ Metrics exported to: {export_path}")
    
    # Show export preview
    with open(export_path) as f:
        metrics_data = json.load(f)
    
    print(f"\n📊 Exported Metrics Preview:")
    print(f"  - Total calls in export: {len(metrics_data['metrics'])}")
    print(f"  - Summary: {json.dumps(metrics_data['summary'], indent=2)[:200]}...")
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80 + "\n")
    
    # Print Key Insights
    print("🔍 KEY INSIGHTS:")
    print(f"  ✓ ReviewerGPT made {summary['total_calls']} API calls")
    print(f"  ✓ Generated {summary['total_tokens']:,} tokens")
    print(f"  ✓ Estimated cost: {summary['total_cost']}")
    print(f"  ✓ Ultra-logging captured every metric")
    print(f"  ✓ Memory tracking (with psutil when available)")
    print(f"  ✓ Performance metrics per call")
    print()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
