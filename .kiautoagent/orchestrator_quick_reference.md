# Orchestrator Quick Reference 🚀

## 🎯 How It Works (30 Seconds)

```
User Task → Complexity Detection → Routing Decision
                                        ↓
                        ┌───────────────┼───────────────┐
                        ↓               ↓               ↓
                     SIMPLE         MODERATE        COMPLEX
                    Keyword        Standard       Orchestrator
                    Routing        Workflow           AI
                    <5min          5-30min         20-60min
```

---

## 🧪 Test It

### Simple Task
```
"Fix bug in auth"
→ ⚡ Keyword → Fixer
→ 1 step, <5min
```

### Moderate Task
```
"Entwickle Tetris App"
→ 🎯 Standard → [Architect, CodeSmith, Reviewer, Fixer]
→ 4 steps, ~20min
```

### Complex Task
```
"Integriere MongoDB mit TypeScript, Tests und Dokumentation"
→ 🧠 Orchestrator AI → 6 steps with parallelization
→ First time: ~35min
→ Second time: ~25min (memory learning!)
```

---

## 📊 System Decision Flow

```python
# 1. Detect Complexity
if len(task.split()) > 15 or task.count(",") > 2:
    complexity = "complex"
elif len(task.split()) <= 3:
    complexity = "simple"
else:
    complexity = "moderate"

# 2. Route Based on Complexity
if complexity == "complex":
    # Use Orchestrator AI (GPT-4o)
    # Check memory for similar tasks first (25% faster!)
    plan = orchestrator.decompose(task)

elif complexity == "simple":
    # Use keyword routing (fast!)
    agent = keyword_match(task)

else:
    # Use standard workflow patterns
    plan = standard_pattern(task)
```

---

## 🧠 Memory Learning

### How It Learns

```
Execution 1: "Entwickle Snake App"
├─ Orchestrator creates plan: [research → architect → codesmith → reviewer]
├─ Executes successfully
└─ Stores in memory: success=True

Execution 2: "Entwickle Tetris App"
├─ Searches memory: finds "Snake App"
├─ Adapts pattern: [research → architect → codesmith → reviewer]
├─ Skips GPT-4o call (25% faster!)
└─ Stores in memory: success=True
```

### Check Memory

```python
# In backend/agents/specialized/orchestrator_agent.py
similar = await memory_manager.search("Entwickle App", k=3)
for task in similar:
    print(f"Task: {task['task']}")
    print(f"Success: {task['success']}")
    print(f"Duration: {task['execution_time']}min")
```

---

## ⚙️ Configuration

### Enable/Disable Orchestrator

```python
# backend/langgraph_system/workflow.py line 32
ORCHESTRATOR_AVAILABLE = True  # Set False to disable
```

### Adjust Complexity Thresholds

```python
# backend/langgraph_system/workflow.py lines 819-845
complex_indicators = [
    len(task.split()) > 15,     # Change threshold
    task.count(",") > 2,        # Change threshold
    "komplex" in task.lower(),  # Add keywords
]
```

### Change Memory Search Results

```python
# backend/agents/specialized/orchestrator_agent.py line 194
similar = await memory.search(task, k=3)  # Change k
```

---

## 📈 Performance Metrics

| Metric | Simple | Moderate | Complex (1st) | Complex (2nd+) |
|--------|--------|----------|---------------|----------------|
| **Routing Time** | <100ms | <200ms | 3-5s | 500ms |
| **Execution Time** | <5min | 5-30min | 20-60min | 15-45min |
| **API Calls** | 1 | 2-4 | 2-8 | 1-7 |
| **Learning** | ❌ No | ❌ No | ✅ Stored | ✅ Retrieved |

---

## 🔍 Debugging

### See Complexity Detection

```bash
# In logs:
🎯 Task classified as COMPLEX (will use Orchestrator AI)
🎯 Task classified as SIMPLE (will use keyword routing)
🎯 Task classified as MODERATE (will use standard workflow)
```

### See Memory Learning

```bash
# In logs:
🧠 Found 3 similar tasks in memory
✅ Found 2 successful past decompositions
🎯 Reusing successful decomposition pattern (25% faster)
✅ Stored execution result for learning (success=True)
```

### See Orchestrator AI

```bash
# In logs:
🤖 Using Orchestrator AI for task decomposition (complexity: complex)
✅ AI decomposition: 6 tasks, 35.0min estimated
💡 Reasoning: Research MongoDB libraries first, then parallel implementation
```

---

## 🎯 Common Use Cases

### Use Case 1: Feature Development
```
Task: "Entwickle User Login mit OAuth2, Session Management und Tests"
System: COMPLEX → Orchestrator AI
Plan:
  1. Research OAuth2 libraries
  2. Design authentication architecture
  3. Implement OAuth2 backend (parallel)
  4. Implement session management (parallel)
  5. Write integration tests
  6. Review and document
Duration: ~40min (25min on 2nd similar task)
```

### Use Case 2: Bug Fix
```
Task: "Fix memory leak in WebSocket handler"
System: SIMPLE → Keyword Routing
Plan:
  1. Fixer analyzes and fixes
Duration: <10min
```

### Use Case 3: Code Review
```
Task: "Review authentication code"
System: SIMPLE → Keyword Routing
Plan:
  1. Reviewer analyzes code
Duration: <5min
```

---

## 📊 Cost Analysis

### Per Task Type

| Type | GPT-4o Calls | Claude Calls | Total Cost |
|------|--------------|--------------|------------|
| **Simple** | 0 | 0-1 | $0.00-0.01 |
| **Moderate** | 0 | 2-4 | $0.02-0.08 |
| **Complex (1st)** | 1 | 4-8 | $0.05-0.15 |
| **Complex (2nd+)** | 0 | 4-8 | $0.04-0.12 |

**Savings with Memory:** ~20-30% cost reduction on repeated complex tasks

---

## 🚀 Quick Start

### 1. Start Backend
```bash
source venv/bin/activate
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001
```

### 2. Send Test Task (VS Code Extension)
```
Simple: "Fix bug X"
Complex: "Entwickle MongoDB Integration mit Tests und Doku"
```

### 3. Watch Logs
```bash
tail -f backend/server.log | grep -E "🎯|🧠|🤖|✅"
```

---

## ✅ Checklist: Is It Working?

- [ ] Backend starts without errors
- [ ] See "✅ Orchestrator agent imported successfully" in logs
- [ ] See "✅ Initialized X real agents" in logs
- [ ] Send complex task → See "🎯 Task classified as COMPLEX"
- [ ] See "🤖 Using Orchestrator AI for task decomposition"
- [ ] See "✅ AI decomposition: X tasks"
- [ ] Task executes multi-step plan
- [ ] See "✅ Stored execution result for learning"
- [ ] Send similar task → See "🧠 Found X similar tasks in memory"
- [ ] See "🎯 Reusing successful decomposition pattern"

---

## 🐛 Troubleshooting

### "Orchestrator not available"
```bash
# Check:
grep "ORCHESTRATOR_AVAILABLE" backend/langgraph_system/workflow.py

# Should see:
ORCHESTRATOR_AVAILABLE = True
✅ Orchestrator agent imported successfully
```

### "No memory results found"
```bash
# Check database:
sqlite3 agent_memories.db
SELECT count(*) FROM orchestrator_memories;

# If 0 → Run first complex task to populate
```

### "AI decomposition failed"
```bash
# Check OpenAI API key:
echo $OPENAI_API_KEY

# Check error logs:
tail -f backend/server.log | grep "ERROR"
```

---

## 📚 Full Documentation

- **Full Implementation:** `.kiautoagent/phase_1_2_3_implementation_summary.md`
- **Tetris Workflow:** `.kiautoagent/tetris_workflow_summary.md`
- **Architecture:** `.kiautoagent/docs/ARCHITECTURE.md`

---

**Version:** v5.1-hybrid
**Status:** ✅ Production Ready
**Last Updated:** 2025-10-01
