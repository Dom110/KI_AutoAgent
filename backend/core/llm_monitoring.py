"""
🎯 Ultra-Logging Framework für LLM Agent Monitoring

Trackt:
- Token Usage (Input/Output/Total)
- Memory Usage (RSS, VMS, Resident)
- API Latenz und Performance
- Cost Berechnung pro Provider
- Detaillierte Debugging-Ausgaben

Beispiel Output:
    🤖 Agent: ReviewerGPT
    ├─ 📤 Requesting LLM (gpt-4o-mini)
    ├─ ⏱️  Response in 2.345s
    ├─ 📊 Tokens: Input=1,234 | Output=567 | Total=1,801
    ├─ 💰 Cost: $0.0045
    ├─ 💾 Memory: RSS=245MB | Change=+12MB
    └─ ✅ Success
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from decimal import Decimal

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger_temp = logging.getLogger("agent.llm_monitoring")
    logger_temp.warning("⚠️ prometheus_client not available - Prometheus metrics disabled")

logger = logging.getLogger("agent.llm_monitoring")


# ============================================================================
# Prometheus Metrics (Real-time Monitoring)
# ============================================================================

if PROMETHEUS_AVAILABLE:
    _registry = CollectorRegistry()
    
    llm_calls_total = Counter(
        "llm_calls_total",
        "Total number of LLM API calls",
        ["agent_name", "provider", "model", "status"],
        registry=_registry,
    )
    
    llm_tokens_total = Counter(
        "llm_tokens_total",
        "Total tokens used (input + output)",
        ["agent_name", "provider", "model"],
        registry=_registry,
    )
    
    llm_cost_usd_total = Counter(
        "llm_cost_usd_total",
        "Total cost in USD",
        ["agent_name", "provider", "model"],
        registry=_registry,
    )
    
    llm_memory_rss_mb = Gauge(
        "llm_memory_rss_mb",
        "Resident Set Size memory in MB",
        ["agent_name"],
        registry=_registry,
    )
    
    llm_memory_available_mb = Gauge(
        "llm_memory_available_mb",
        "Available system memory in MB",
        registry=_registry,
    )
    
    llm_active_calls = Gauge(
        "llm_active_calls",
        "Number of active LLM API calls",
        ["agent_name"],
        registry=_registry,
    )
    
    llm_latency_seconds = Histogram(
        "llm_latency_seconds",
        "Total latency of LLM calls in seconds",
        ["agent_name", "provider", "model"],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
        registry=_registry,
    )
    
    llm_api_latency_seconds = Histogram(
        "llm_api_latency_seconds",
        "API latency only (without overhead) in seconds",
        ["agent_name", "provider"],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
        registry=_registry,
    )
    
    llm_input_tokens = Gauge(
        "llm_input_tokens_last_call",
        "Input tokens in the last call",
        ["agent_name", "provider", "model"],
        registry=_registry,
    )
    
    llm_output_tokens = Gauge(
        "llm_output_tokens_last_call",
        "Output tokens in the last call",
        ["agent_name", "provider", "model"],
        registry=_registry,
    )
else:
    llm_calls_total = None
    llm_tokens_total = None
    llm_cost_usd_total = None
    llm_memory_rss_mb = None
    llm_memory_available_mb = None
    llm_active_calls = None
    llm_latency_seconds = None
    llm_api_latency_seconds = None
    llm_input_tokens = None
    llm_output_tokens = None


# ============================================================================
# Token Pricing Configuration
# ============================================================================

class TokenPricingConfig:
    """Token pricing for different LLM providers and models."""
    
    # OpenAI Pricing (USD per 1M tokens, as of 2025)
    OPENAI_PRICING = {
        "gpt-4o": {
            "input": Decimal("5.00"),      # $5 per 1M input tokens
            "output": Decimal("15.00"),    # $15 per 1M output tokens
        },
        "gpt-4o-mini": {
            "input": Decimal("0.15"),      # $0.15 per 1M input tokens
            "output": Decimal("0.60"),     # $0.60 per 1M output tokens
        },
        "gpt-4-turbo": {
            "input": Decimal("10.00"),
            "output": Decimal("30.00"),
        },
        "gpt-4": {
            "input": Decimal("30.00"),
            "output": Decimal("60.00"),
        },
        "gpt-3.5-turbo": {
            "input": Decimal("0.50"),
            "output": Decimal("1.50"),
        },
    }
    
    # Anthropic Pricing (USD per 1M tokens)
    ANTHROPIC_PRICING = {
        "claude-opus": {
            "input": Decimal("15.00"),
            "output": Decimal("75.00"),
        },
        "claude-sonnet": {
            "input": Decimal("3.00"),
            "output": Decimal("15.00"),
        },
        "claude-haiku": {
            "input": Decimal("0.80"),
            "output": Decimal("4.00"),
        },
    }
    
    # Perplexity Pricing
    PERPLEXITY_PRICING = {
        "sonar": {
            "input": Decimal("0.001"),     # Per token
            "output": Decimal("0.001"),
        },
    }
    
    @classmethod
    def get_cost(
        cls,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        """
        Calculate cost for LLM usage.
        
        Args:
            provider: Provider name (openai, anthropic, perplexity)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD as Decimal
        """
        pricing_map = {
            "openai": cls.OPENAI_PRICING,
            "anthropic": cls.ANTHROPIC_PRICING,
            "perplexity": cls.PERPLEXITY_PRICING,
        }
        
        if provider not in pricing_map:
            logger.warning(f"⚠️  Unknown provider: {provider}")
            return Decimal("0.00")
        
        pricing = pricing_map[provider]
        
        # Get model pricing - match longest substring (to handle gpt-4o-mini vs gpt-4o)
        model_key = None
        longest_match = 0
        for key in pricing.keys():
            if key in model and len(key) > longest_match:
                model_key = key
                longest_match = len(key)
        
        if model_key is None:
            # Try exact match
            if model in pricing:
                model_key = model
            else:
                logger.warning(f"⚠️  Unknown model: {model}")
                return Decimal("0.00")
        
        model_pricing = pricing[model_key]
        
        # For Perplexity (per token), calculate directly
        if provider == "perplexity":
            input_cost = Decimal(str(input_tokens)) * model_pricing["input"]
            output_cost = Decimal(str(output_tokens)) * model_pricing["output"]
        else:
            # For others (per 1M tokens)
            input_cost = (Decimal(str(input_tokens)) / Decimal("1000000")) * model_pricing["input"]
            output_cost = (Decimal(str(output_tokens)) / Decimal("1000000")) * model_pricing["output"]
        
        return input_cost + output_cost


# ============================================================================
# Data Classes for Monitoring
# ============================================================================

@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""
    
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    resident_mb: float  # Resident memory in MB
    available_mb: float  # Available memory in MB
    timestamp: datetime = field(default_factory=datetime.now)
    
    def format(self) -> str:
        """Format for logging."""
        return f"RSS={self.rss_mb:.1f}MB | VMS={self.vms_mb:.1f}MB | Available={self.available_mb:.1f}MB"
    
    def delta_from(self, other: "MemorySnapshot") -> str:
        """Get memory change from other snapshot."""
        rss_delta = self.rss_mb - other.rss_mb
        vms_delta = self.vms_mb - other.vms_mb
        sign = "+" if rss_delta > 0 else ""
        return f"{sign}{rss_delta:.1f}MB (RSS)"


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""
    
    agent_name: str
    provider: str
    model: str
    prompt_length: int
    completion_length: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    api_latency_ms: float
    total_latency_ms: float
    cost_usd: Decimal
    memory_start: MemorySnapshot
    memory_end: MemorySnapshot
    status: str  # success, error, timeout, rate_limit
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = ""  # For tracing
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_name": self.agent_name,
            "provider": self.provider,
            "model": self.model,
            "prompt_length": self.prompt_length,
            "completion_length": self.completion_length,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "api_latency_ms": round(self.api_latency_ms, 2),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "cost_usd": str(self.cost_usd),
            "status": self.status,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
        }


@dataclass
class AgentMonitoringContext:
    """Context for monitoring during an LLM call."""
    
    agent_name: str
    provider: str
    model: str
    start_time: float = field(default_factory=time.time)
    memory_start: Optional[MemorySnapshot] = None
    request_id: str = ""
    
    def __post_init__(self):
        if not self.request_id:
            import uuid
            self.request_id = str(uuid.uuid4())[:8]
        if self.memory_start is None:
            self.memory_start = LLMMonitor.capture_memory()


# ============================================================================
# Main Monitoring Class
# ============================================================================

class LLMMonitor:
    """
    Central monitoring system for LLM calls.
    
    Tracks metrics and logs everything with emoji markers.
    """
    
    # Class-level metrics storage
    _metrics: list[LLMCallMetrics] = []
    _max_metrics_history: int = 1000
    _total_cost: Decimal = Decimal("0.00")
    
    @staticmethod
    def capture_memory() -> MemorySnapshot:
        """Capture current memory usage."""
        if not PSUTIL_AVAILABLE:
            logger.debug("⚠️  psutil not available - using placeholder memory metrics")
            return MemorySnapshot(
                rss_mb=0.0,
                vms_mb=0.0,
                resident_mb=0.0,
                available_mb=0.0,
            )
        
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            mem_percent = process.memory_percent()
            
            try:
                available = psutil.virtual_memory().available / (1024 * 1024)
            except (OSError, RuntimeError, AttributeError) as e:
                logger.debug(f"⚠️  Failed to get available memory: {e}")
                available = 0.0
            
            return MemorySnapshot(
                rss_mb=mem_info.rss / (1024 * 1024),
                vms_mb=mem_info.vms / (1024 * 1024),
                resident_mb=mem_percent * (psutil.virtual_memory().total / (1024 * 1024)) / 100,
                available_mb=available,
            )
        except Exception as e:
            logger.debug(f"⚠️  Failed to capture memory: {e}")
            return MemorySnapshot(
                rss_mb=0.0,
                vms_mb=0.0,
                resident_mb=0.0,
                available_mb=0.0,
            )
    
    @staticmethod
    def log_call_start(context: AgentMonitoringContext) -> None:
        """Log the start of an LLM call."""
        logger.info(f"🤖 {context.agent_name} Agent")
        logger.info(f"├─ 🏗️  Requesting structured output")
        logger.info(f"├─ Provider: {context.provider} | Model: {context.model}")
        logger.info(f"├─ Request ID: {context.request_id}")
        logger.info(f"└─ Memory: {context.memory_start.format()}")
    
    @staticmethod
    def log_call_end(
        metrics: LLMCallMetrics,
    ) -> None:
        """Log the end of an LLM call."""
        status_icon = "✅" if metrics.status == "success" else "❌"
        
        logger.info(f"{status_icon} LLM Call Complete: {metrics.status.upper()}")
        logger.info(f"├─ ⏱️  Latency: {metrics.api_latency_ms:.2f}ms (API) + {metrics.total_latency_ms - metrics.api_latency_ms:.2f}ms (overhead) = {metrics.total_latency_ms:.2f}ms total")
        logger.info(f"├─ 📊 Tokens:")
        logger.info(f"│  ├─ Input: {metrics.input_tokens:,}")
        logger.info(f"│  ├─ Output: {metrics.output_tokens:,}")
        logger.info(f"│  └─ Total: {metrics.total_tokens:,} tokens ({metrics.total_latency_ms / metrics.total_tokens if metrics.total_tokens > 0 else 0:.3f}ms/token)")
        logger.info(f"├─ 💰 Cost: ${metrics.cost_usd}")
        logger.info(f"├─ 💾 Memory:")
        logger.info(f"│  ├─ Start: {metrics.memory_start.format()}")
        logger.info(f"│  ├─ End: {metrics.memory_end.format()}")
        logger.info(f"│  └─ Change: {metrics.memory_end.delta_from(metrics.memory_start)}")
        
        if metrics.error_message:
            logger.error(f"└─ Error: {metrics.error_message}")
    
    @classmethod
    def record_metric(cls, metrics: LLMCallMetrics) -> None:
        """Record metrics for an LLM call and update Prometheus metrics."""
        cls._metrics.append(metrics)
        cls._total_cost += metrics.cost_usd
        
        # Keep only last N metrics
        if len(cls._metrics) > cls._max_metrics_history:
            cls._metrics = cls._metrics[-cls._max_metrics_history:]
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            try:
                llm_calls_total.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                    status=metrics.status,
                ).inc()
                
                llm_tokens_total.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                ).inc(metrics.total_tokens)
                
                llm_cost_usd_total.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                ).inc(float(metrics.cost_usd))
                
                llm_memory_rss_mb.labels(
                    agent_name=metrics.agent_name,
                ).set(metrics.memory_end.rss_mb)
                
                llm_memory_available_mb.set(metrics.memory_end.available_mb)
                
                llm_latency_seconds.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                ).observe(metrics.total_latency_ms / 1000.0)
                
                llm_api_latency_seconds.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                ).observe(metrics.api_latency_ms / 1000.0)
                
                llm_input_tokens.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                ).set(metrics.input_tokens)
                
                llm_output_tokens.labels(
                    agent_name=metrics.agent_name,
                    provider=metrics.provider,
                    model=metrics.model,
                ).set(metrics.output_tokens)
                
                logger.debug(
                    f"📊 Prometheus metrics updated | "
                    f"Calls: {metrics.agent_name}, "
                    f"Tokens: {metrics.total_tokens}, "
                    f"Cost: ${metrics.cost_usd}"
                )
            except Exception as e:
                logger.warning(f"⚠️  Failed to update Prometheus metrics: {e}")
        
        logger.debug(f"📈 Metrics recorded | Total cost so far: ${cls._total_cost}")
    
    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        """Get summary of all monitored calls."""
        if not cls._metrics:
            return {
                "total_calls": 0,
                "total_cost": "$0.00",
                "metrics": [],
            }
        
        agents = {}
        total_tokens = 0
        total_cost = Decimal("0.00")
        success_count = 0
        error_count = 0
        
        for metric in cls._metrics:
            if metric.agent_name not in agents:
                agents[metric.agent_name] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": Decimal("0.00"),
                    "errors": 0,
                }
            
            agents[metric.agent_name]["calls"] += 1
            agents[metric.agent_name]["tokens"] += metric.total_tokens
            agents[metric.agent_name]["cost"] += metric.cost_usd
            
            total_tokens += metric.total_tokens
            total_cost += metric.cost_usd
            
            if metric.status == "success":
                success_count += 1
            else:
                error_count += 1
                agents[metric.agent_name]["errors"] += 1
        
        return {
            "total_calls": len(cls._metrics),
            "success_calls": success_count,
            "error_calls": error_count,
            "total_tokens": total_tokens,
            "total_cost": f"${total_cost}",
            "by_agent": {
                agent: {
                    "calls": data["calls"],
                    "tokens": data["tokens"],
                    "cost": f"${data['cost']}",
                    "errors": data["errors"],
                }
                for agent, data in agents.items()
            },
        }
    
    @classmethod
    def export_metrics(cls, filepath: Path | str) -> None:
        """Export all metrics to JSON file."""
        metrics_data = [m.to_dict() for m in cls._metrics]
        summary = cls.get_summary()
        
        export = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "metrics": metrics_data,
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w") as f:
            json.dump(export, f, indent=2, default=str)
        
        logger.info(f"📁 Metrics exported to {filepath}")
    
    @classmethod
    def reset(cls) -> None:
        """Reset all metrics."""
        cls._metrics = []
        cls._total_cost = Decimal("0.00")
        logger.info("🔄 Metrics reset")
    
    @classmethod
    def get_prometheus_metrics(cls) -> bytes:
        """
        Get Prometheus metrics in text format.
        
        Returns:
            Prometheus metrics as bytes (text/plain; version=0.0.4)
        """
        if not PROMETHEUS_AVAILABLE:
            return b"# Prometheus client not available\n"
        
        try:
            metrics_bytes = generate_latest(_registry)
            logger.debug("📊 Prometheus metrics exported")
            return metrics_bytes
        except Exception as e:
            logger.error(f"❌ Failed to export Prometheus metrics: {e}")
            return b"# Error generating Prometheus metrics\n"
    
    @classmethod
    def reset_prometheus(cls) -> None:
        """Reset Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        try:
            # Note: Prometheus client doesn't have a built-in reset for custom registries
            # This is a workaround - recreate the metrics
            global llm_calls_total, llm_tokens_total, llm_cost_usd_total
            global llm_memory_rss_mb, llm_memory_available_mb, llm_active_calls
            global llm_latency_seconds, llm_api_latency_seconds
            global llm_input_tokens, llm_output_tokens
            
            _registry._collector_to_names.clear()
            _registry._names_to_collectors.clear()
            
            logger.info("🔄 Prometheus metrics registry cleared")
        except Exception as e:
            logger.warning(f"⚠️  Failed to reset Prometheus registry: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================

async def monitor_llm_call(
    agent_name: str,
    provider: str,
    model: str,
    prompt: str,
    api_call_coro,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> tuple[Any, LLMCallMetrics]:
    """
    Wrap an LLM API call with monitoring.
    
    Args:
        agent_name: Name of the agent making the call
        provider: LLM provider name
        model: Model name
        prompt: The prompt being sent
        api_call_coro: Coroutine that makes the API call and returns (response, tokens_used)
        input_tokens: Pre-calculated input tokens (if known)
        output_tokens: Pre-calculated output tokens (if known)
        
    Returns:
        Tuple of (response, metrics)
    """
    context = AgentMonitoringContext(
        agent_name=agent_name,
        provider=provider,
        model=model,
    )
    
    LLMMonitor.log_call_start(context)
    
    api_start = time.time()
    memory_start = context.memory_start
    
    try:
        # Execute the API call
        start_time = time.time()
        response, tokens = await api_call_coro()
        api_latency_ms = (time.time() - start_time) * 1000
        
        # Extract token counts
        if isinstance(tokens, dict):
            input_tokens = tokens.get("input_tokens", input_tokens)
            output_tokens = tokens.get("output_tokens", output_tokens)
        elif isinstance(tokens, (tuple, list)) and len(tokens) >= 2:
            input_tokens, output_tokens = tokens[0], tokens[1]
        
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        cost = TokenPricingConfig.get_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        memory_end = LLMMonitor.capture_memory()
        total_latency_ms = (time.time() - api_start) * 1000
        
        metrics = LLMCallMetrics(
            agent_name=agent_name,
            provider=provider,
            model=model,
            prompt_length=len(prompt),
            completion_length=len(str(response)),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            api_latency_ms=api_latency_ms,
            total_latency_ms=total_latency_ms,
            cost_usd=cost,
            memory_start=memory_start,
            memory_end=memory_end,
            status="success",
            request_id=context.request_id,
        )
        
        LLMMonitor.log_call_end(metrics)
        LLMMonitor.record_metric(metrics)
        
        return response, metrics
        
    except Exception as e:
        memory_end = LLMMonitor.capture_memory()
        total_latency_ms = (time.time() - api_start) * 1000
        
        error_type = type(e).__name__
        if "timeout" in str(e).lower():
            status = "timeout"
        elif "rate" in str(e).lower():
            status = "rate_limit"
        else:
            status = "error"
        
        metrics = LLMCallMetrics(
            agent_name=agent_name,
            provider=provider,
            model=model,
            prompt_length=len(prompt),
            completion_length=0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens,
            api_latency_ms=0.0,
            total_latency_ms=total_latency_ms,
            cost_usd=TokenPricingConfig.get_cost(provider, model, input_tokens, 0),
            memory_start=memory_start,
            memory_end=memory_end,
            status=status,
            error_message=f"{error_type}: {str(e)}",
            request_id=context.request_id,
        )
        
        LLMMonitor.log_call_end(metrics)
        LLMMonitor.record_metric(metrics)
        
        raise


# ============================================================================
# Export API
# ============================================================================

__all__ = [
    "LLMMonitor",
    "LLMCallMetrics",
    "MemorySnapshot",
    "AgentMonitoringContext",
    "TokenPricingConfig",
    "monitor_llm_call",
    "PROMETHEUS_AVAILABLE",
    "llm_calls_total",
    "llm_tokens_total",
    "llm_cost_usd_total",
    "llm_memory_rss_mb",
    "llm_memory_available_mb",
    "llm_active_calls",
    "llm_latency_seconds",
    "llm_api_latency_seconds",
    "llm_input_tokens",
    "llm_output_tokens",
]
