# ⚡ Phase 3c Quick Reference (for next session)

## 🚀 Get Started in 2 Minutes

### 1. Understand What Was Built
```
Phase 3b: Ultra-Logging Framework (token/cost/memory tracking)
Phase 3c: Prometheus Real-Time Metrics (9 metrics for dashboards)
```

### 2. Key Files
```
Core: backend/core/llm_monitoring.py (★ MODIFIED +90 lines)
Test: backend/tests/test_prometheus_integration.py (7 tests, 100%)
Test: backend/tests/test_reviewer_agent_phase3c_simulation.py (demo)
Docs: PHASE_3C_PROMETHEUS_INTEGRATION.md (read this first)
Docs: backend/CLAUDE.md (Phase 3c section)
```

### 3. Run Tests (30 seconds)
```bash
# Prometheus tests
python3 backend/tests/test_prometheus_integration.py

# Simulation with logging
python3 backend/tests/test_reviewer_agent_phase3c_simulation.py
```

### 4. Next: Real Agent Integration
- [ ] Open: `backend/agents/specialized/reviewer_gpt_agent.py`
- [ ] Find: `self.ai_service.get_completion()` call
- [ ] Wrap: with `monitor_llm_call()` from llm_monitoring
- [ ] Add: 8-phase logging (see simulation example)
- [ ] Test: Run agent with code review task
- [ ] Verify: Prometheus endpoint `/metrics` works

---

## 📊 The 9 Prometheus Metrics at a Glance

### Counters (track rate)
```
llm_calls_total          # Total API calls (with status)
llm_tokens_total         # Total tokens used
llm_cost_usd_total       # Total USD cost
```

### Gauges (current value)
```
llm_memory_rss_mb        # Memory per agent
llm_memory_available_mb  # System memory free
llm_active_calls         # Calls in progress
```

### Histograms (percentiles)
```
llm_latency_seconds      # Total latency p50/p95/p99
llm_api_latency_seconds  # API only latency
```

### Last-Call
```
llm_input_tokens_last_call   # For debugging
llm_output_tokens_last_call  # For debugging
```

---

## 🔄 How Monitoring Works

```
Agent calls LLM
    ↓
LLM call wrapped with monitor_llm_call()
    ↓
1. Capture Memory Start
2. Record Start Time
3. Execute API
4. Extract Tokens
5. Calculate Cost
6. Capture Memory End
7. Create LLMCallMetrics
8. Update Prometheus Counters/Gauges/Histograms
9. Log + Return
    ↓
LLMMonitor.get_prometheus_metrics() → /metrics endpoint
    ↓
Prometheus scrape every 15s
    ↓
Grafana dashboard shows metrics
```

---

## 💻 FastAPI Integration Example

```python
# In your FastAPI app (e.g., api/server_langgraph.py)

from fastapi import FastAPI
from fastapi.responses import Response
from backend.core.llm_monitoring import LLMMonitor

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    data = LLMMonitor.get_prometheus_metrics()
    return Response(data, media_type="text/plain; version=0.0.4")
```

Then: `curl http://localhost:8000/metrics`

---

## 📈 Grafana Query Examples

### 1. Calls per Agent (requests/sec)
```promql
sum(rate(llm_calls_total[1m])) by (agent_name)
```

### 2. Token Usage (last hour)
```promql
increase(llm_tokens_total[1h]) by (agent_name)
```

### 3. P95 Latency
```promql
histogram_quantile(0.95, rate(llm_latency_seconds_bucket[5m])) by (agent_name)
```

### 4. Cost per Hour
```promql
increase(llm_cost_usd_total[1h]) by (agent_name)
```

---

## 🧪 Test Commands

```bash
# All 7 Prometheus tests
python3 backend/tests/test_prometheus_integration.py

# Simulation with detailed logging
python3 backend/tests/test_reviewer_agent_phase3c_simulation.py

# Expected output:
# ✅ 7/7 tests passing
# ✅ Simulation: 4 calls, 536 tokens, $0.000277
```

---

## 📋 ReviewerGPT Integration Checklist

- [ ] Read PHASE_3C_PROMETHEUS_INTEGRATION.md (15 min)
- [ ] Read backend/CLAUDE.md Phase 3c (5 min)
- [ ] Locate reviewer_gpt_agent.py execute() method
- [ ] Find `self.ai_service.get_completion()` call
- [ ] Wrap with `monitor_llm_call()`:
  ```python
  response, metrics = await monitor_llm_call(
      agent_name="ReviewerGPT",
      provider="openai",
      model="gpt-4o-mini",
      prompt=user_prompt,
      api_call_coro=lambda: self.ai_service.get_completion(...)
  )
  ```
- [ ] Add 8-phase logging (copy from simulation)
- [ ] Test with code snippet
- [ ] Verify Prometheus endpoint
- [ ] Move to CodesmithAgent

---

## 🎓 Key Concepts

### Prometheus vs In-Memory
- **In-Memory:** LLMMonitor._metrics (last 1000 calls)
- **Prometheus:** Real-time metrics for dashboards/alerts

### Counters vs Gauges
- **Counter:** Only goes up (llm_calls_total, llm_tokens_total)
- **Gauge:** Can go up/down (llm_memory_rss_mb, llm_active_calls)

### Histogram Buckets
- **Purpose:** Calculate p50, p95, p99 latency
- **Buckets:** 0.1s, 0.5s, 1s, 2.5s, 5s, 10s, ∞
- **Optimized for:** LLM calls (typically 0.1-5s)

### Low Cardinality
- **What:** Labels keep metrics manageable
- **Good:** agent_name, provider, model, status
- **Bad:** request_id, user_id (would explode metrics)

---

## 🚨 Troubleshooting

### prometheus_client not installed?
```bash
python3 -m pip install --break-system-packages prometheus-client prometheus-async
```

### Prometheus metrics not showing?
```python
# Check if available
from backend.core.llm_monitoring import PROMETHEUS_AVAILABLE
print(PROMETHEUS_AVAILABLE)  # Should be True

# Check registry
from backend.core.llm_monitoring import LLMMonitor
print(LLMMonitor.get_prometheus_metrics())  # Should show metrics
```

### Metrics accumulating?
```python
# Reset
LLMMonitor.reset()  # Clears in-memory metrics
LLMMonitor.reset_prometheus()  # Clears Prometheus registry
```

---

## 📚 Documentation Files

1. **Quick Overview:** This file (2 min)
2. **Detailed Tech:** PHASE_3C_PROMETHEUS_INTEGRATION.md (15 min)
3. **Session Context:** PHASE_3C_CONTEXT_SUMMARY_20251110.md (20 min)
4. **Full Delivery:** PHASE_3C_DELIVERY_REPORT.md (reference)
5. **Backend Guide:** backend/CLAUDE.md Phase 3c section

---

## ✅ Success Criteria for Phase 3c.1

- [ ] ReviewerGPTAgent wraps LLM calls with monitoring
- [ ] All 8 logging phases implemented
- [ ] E2E test passes (real code review)
- [ ] Prometheus endpoint responding
- [ ] Metrics visible in query
- [ ] Documentation updated
- [ ] Ready for CodesmithAgent

---

## 🎯 Remember

> **This phase is about observability:** We're not changing agent behavior, just adding visibility into LLM calls. Every call is now tracked, measured, and exported to Prometheus for real-time dashboards.

Next: Make ReviewerGPTAgent visible through logs and metrics. Then repeat for 4 more agents. Then: Build Grafana dashboard. Then: Setup alerts.

**Phase 3c: COMPLETE ✅**  
**Ready for Phase 3c.1 →**
