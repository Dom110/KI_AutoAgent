# 🧪 E2E Test Plan v6.2 - Comprehensive Feature Validation

**Created:** 2025-10-13
**Version:** v6.2.0-alpha
**Purpose:** Validate ALL Phase 1-4 features are implemented and functional

---

## 🎯 Test Objectives

1. **Verify Feature Creation:** Ensure all cognitive systems create their data files
2. **Verify Feature Reuse:** Ensure agents reuse learning/patterns from previous runs
3. **Test All 4 Phases:** Production Essentials, Intelligence, Workflow, Advanced
4. **End-to-End Validation:** Real WebSocket connection, real app generation

---

## 📋 Feature Tracking Matrix

### Phase 1: Production Essentials

| Feature | Creates | Reuses | Location | Test Method |
|---------|---------|--------|----------|-------------|
| **Perplexity API** | ✅ Search Results | ✅ Cached results | Response | Check web search citations |
| **ASIMOV Rule 3** | ✅ Error search log | ✅ Pattern detection | Logs | Inject error, verify global search |

### Phase 2: Intelligence Systems

| Feature | Creates | Reuses | Location | Test Method |
|---------|---------|--------|----------|-------------|
| **Learning System** | ✅ Pattern DB | ✅ Past patterns | Memory store | 2nd run should suggest patterns |
| **Curiosity System** | ✅ Questions | ✅ Defaults | WebSocket msg | Ambiguous query → questions |
| **Predictive System** | ✅ Predictions | ✅ Duration history | Session metadata | Check duration prediction |

### Phase 3: Workflow Optimization

| Feature | Creates | Reuses | Location | Test Method |
|---------|---------|--------|----------|-------------|
| **Tool Registry** | ✅ Tool list | ✅ Permission cache | Runtime | Check available tools |
| **Approval Manager** | ✅ Approval requests | ✅ Auto-patterns | WebSocket msg | Destructive action → approval |
| **Dynamic Workflow** | ✅ Workflow plan | ✅ Route optimization | Workflow state | Simple query → skip agents |

### Phase 4: Advanced Features

| Feature | Creates | Reuses | Location | Test Method |
|---------|---------|--------|----------|-------------|
| **Neurosymbolic** | ✅ Rule results | ✅ Symbolic rules | Reasoning state | Validate safety rules |
| **Self-Diagnosis** | ✅ Diagnosis log | ✅ Recovery strategies | Error handling | Inject error → self-heal |

---

## 🧪 Test 1: New App Development (All Features)

### **Objective:** Create a new app and verify ALL features are used

### **Setup:**
```bash
# Start backend
cd /Users/dominikfoert/git/KI_AutoAgent
~/.ki_autoagent/venv/bin/python backend/api/server_v6_integrated.py

# Monitor logs in another terminal
tail -f /tmp/v6_server.log | grep -E "🧠|🔮|🎯|📊|🛡️|💭|🔧"
```

### **Test Workspace:**
```bash
# Create fresh test workspace
mkdir -p ~/TestApps/v6_2_comprehensive_test
cd ~/TestApps/v6_2_comprehensive_test
```

### **Test Query (Intentionally Ambiguous):**
```
"Create a task management app"
```

**Expected Behavior:**
1. **Curiosity System:** Ask clarifying questions
   - "Which framework? React, Vue, or vanilla JS?"
   - "TypeScript or JavaScript?"
   - "Backend needed? Express, Fastify, or none?"

2. **Predictive System:** Predict complexity and duration
   - Complexity: MEDIUM (score ~50-60)
   - Duration: ~5-8 minutes
   - Risk: MEDIUM

3. **Dynamic Workflow:** Plan workflow
   - Should include: Research → Architect → Codesmith → ReviewFix

4. **Perplexity API:** Search for best practices
   - Should return citations from web

5. **Learning System:** Record execution
   - Should store patterns for React + TypeScript apps

6. **Tool Registry:** Assign tools
   - Research: Perplexity, Read, Bash
   - Codesmith: Read, Edit, Bash

7. **ASIMOV Permissions:** Validate file operations
   - Codesmith should have CAN_WRITE_FILES
   - Should log all file operations

8. **Neurosymbolic Reasoning:** Validate architecture
   - Should check: "tests_after_implementation"
   - Should check: "backend_before_frontend" (if fullstack)

9. **ReviewFix Build Validation:** TypeScript/JavaScript
   - Run `tsc --noEmit` if TypeScript
   - Run `eslint` if JavaScript

10. **Self-Diagnosis:** Handle any errors gracefully
    - If error occurs, should self-heal

### **Feature Tracking:**

Create test script to track features:

```python
#!/usr/bin/env python3
"""
E2E Test with Feature Tracking
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from pathlib import Path

# Test workspace
WORKSPACE = Path.home() / "TestApps" / "v6_2_comprehensive_test"
WORKSPACE.mkdir(parents=True, exist_ok=True)

# Feature tracking
features_used = {
    "phase1": {
        "perplexity_api": False,
        "asimov_rule3": False,
    },
    "phase2": {
        "learning_system": False,
        "curiosity_system": False,
        "predictive_system": False,
    },
    "phase3": {
        "tool_registry": False,
        "approval_manager": False,
        "dynamic_workflow": False,
    },
    "phase4": {
        "neurosymbolic_reasoning": False,
        "self_diagnosis": False,
    },
}

async def test_create_app():
    """Test new app creation with feature tracking."""

    uri = "ws://localhost:8002/ws/chat"

    async with websockets.connect(uri) as websocket:
        # Initialize session
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": str(WORKSPACE)
        }))

        init_response = json.loads(await websocket.recv())
        print(f"✅ Session initialized: {init_response['session_id']}")

        # Send ambiguous query (triggers Curiosity)
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Create a task management app"
        }))

        # Collect all responses
        responses = []

        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=300)
                data = json.loads(message)
                responses.append(data)

                # Track feature usage
                msg_type = data.get("type")
                content = str(data.get("content", ""))

                # Phase 1
                if "perplexity" in content.lower() or "search" in content.lower():
                    features_used["phase1"]["perplexity_api"] = True
                    print("  🔍 Perplexity API used")

                if "global error search" in content.lower() or "ripgrep" in content.lower():
                    features_used["phase1"]["asimov_rule3"] = True
                    print("  🛡️ ASIMOV Rule 3 triggered")

                # Phase 2
                if "learning" in content.lower() or "pattern" in content.lower():
                    features_used["phase2"]["learning_system"] = True
                    print("  📚 Learning System active")

                if "clarif" in content.lower() or "which framework" in content.lower():
                    features_used["phase2"]["curiosity_system"] = True
                    print("  ❓ Curiosity System asking questions")

                if "predict" in content.lower() or "duration" in content.lower():
                    features_used["phase2"]["predictive_system"] = True
                    print("  🔮 Predictive System made prediction")

                # Phase 3
                if "tool" in content.lower() and "register" in content.lower():
                    features_used["phase3"]["tool_registry"] = True
                    print("  🔧 Tool Registry used")

                if msg_type == "approval_request":
                    features_used["phase3"]["approval_manager"] = True
                    print("  ✋ Approval Manager requested approval")

                if "workflow plan" in content.lower() or "agents:" in content.lower():
                    features_used["phase3"]["dynamic_workflow"] = True
                    print("  🎯 Dynamic Workflow planned")

                # Phase 4
                if "neurosymbolic" in content.lower() or "rule" in content.lower():
                    features_used["phase4"]["neurosymbolic_reasoning"] = True
                    print("  🧠 Neurosymbolic Reasoning applied")

                if "self-diagnosis" in content.lower() or "self-heal" in content.lower():
                    features_used["phase4"]["self_diagnosis"] = True
                    print("  💊 Self-Diagnosis system activated")

                # End conditions
                if msg_type == "result" or msg_type == "complete":
                    print(f"\n✅ Workflow complete: {content[:100]}")
                    break

            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for response")
                break

    # Report feature usage
    print("\n" + "="*60)
    print("📊 FEATURE USAGE REPORT")
    print("="*60)

    for phase, features in features_used.items():
        phase_name = phase.replace("phase", "Phase ").upper()
        print(f"\n{phase_name}:")

        for feature, used in features.items():
            status = "✅ USED" if used else "❌ NOT USED"
            feature_name = feature.replace("_", " ").title()
            print(f"  {status}: {feature_name}")

    # Calculate coverage
    total_features = sum(len(features) for features in features_used.values())
    used_features = sum(sum(1 for used in features.values() if used) for features in features_used.values())
    coverage = (used_features / total_features) * 100

    print(f"\n📈 Overall Coverage: {used_features}/{total_features} ({coverage:.1f}%)")

    # Check files created
    print("\n📂 FILES CREATED:")
    for file in WORKSPACE.rglob("*"):
        if file.is_file():
            print(f"  ✓ {file.relative_to(WORKSPACE)}")

    return features_used, coverage

if __name__ == "__main__":
    asyncio.run(test_create_app())
```

---

## 🧪 Test 2: Extend Existing App (Learning Reuse)

### **Objective:** Verify Learning System reuses patterns from Test 1

### **Setup:**
Use the app created in Test 1

### **Test Query:**
```
"Add user authentication to the task manager app"
```

### **Expected Behavior:**

1. **Learning System:** Suggest patterns from Test 1
   - "I've seen similar React + TypeScript projects before"
   - "Reusing pattern: JWT authentication with Express"

2. **Predictive System:** Use historical data
   - "Based on similar tasks, estimated duration: 3-5 minutes"

3. **Dynamic Workflow:** Optimize routing
   - Skip Research (already knows tech stack)
   - Go directly: Architect → Codesmith → ReviewFix

4. **Neurosymbolic Reasoning:** Validate consistency
   - Ensure auth doesn't break existing tests
   - Check: "api_change_needs_versioning"

5. **ReviewFix:** Incremental validation
   - Only validate new/changed files
   - TypeScript compilation should pass

### **Feature Tracking:**

```python
async def test_extend_app():
    """Test extending existing app (learning reuse)."""

    # Same workspace as Test 1
    WORKSPACE = Path.home() / "TestApps" / "v6_2_comprehensive_test"

    # Track learning reuse
    learning_reused = False
    pattern_suggestions = []

    # ... (similar WebSocket logic)

    # Check for pattern reuse
    if "pattern" in content.lower() or "similar" in content.lower():
        learning_reused = True
        pattern_suggestions.append(content)
        print(f"  📚 Pattern reused: {content[:80]}")

    print(f"\n📊 Learning Reuse: {'✅ YES' if learning_reused else '❌ NO'}")
    print(f"   Patterns suggested: {len(pattern_suggestions)}")
```

---

## 🧪 Test 3: Error Injection (Self-Diagnosis + ASIMOV Rule 3)

### **Objective:** Verify error handling features work

### **Setup:**
Create app with intentional error

### **Test Query:**
```
"Create a Python Flask app with a function that uses undefined variable 'foo'"
```

### **Expected Behavior:**

1. **Codesmith:** Creates app with error

2. **ReviewFix:** Detects error (Python mypy or runtime check)
   - Quality score drops to 0.50

3. **Self-Diagnosis:** Diagnoses NameError
   - Pattern: "NameError"
   - Recovery: "alternative" (define foo or remove usage)

4. **ASIMOV Rule 3:** Global error search
   - Search entire workspace for 'foo' usage
   - Report all occurrences

5. **Fixer:** Apply recovery strategy
   - Fix ALL instances of error

6. **Final Validation:** Build passes
   - Python mypy check succeeds

---

## 🧪 Test 4: Multi-Language App (Build Validation)

### **Objective:** Test all 6 language validators

### **Test Query:**
```
"Create a full-stack app with:
- TypeScript React frontend
- Python FastAPI backend
- Go microservice for image processing
- Rust CLI tool for deployment
- Java Spring Boot admin panel
- JavaScript utility scripts"
```

### **Expected Behavior:**

1. **Build Validation:** All 6 validators run
   - TypeScript: `tsc --noEmit`
   - Python: `mypy`
   - JavaScript: `eslint`
   - Go: `go vet`
   - Rust: `cargo check`
   - Java: `mvn compile -q`

2. **Parallel Execution:** All checks run concurrently

3. **Quality Threshold:** Each language has appropriate threshold
   - TypeScript: 0.90
   - Python: 0.85
   - JavaScript: 0.75
   - Go: 0.85
   - Rust: 0.85
   - Java: 0.80

---

## 📊 Success Criteria

### **Minimum Requirements:**

| Phase | Min Features Used | Target Coverage |
|-------|------------------|-----------------|
| Phase 1 | 2/2 (100%) | ✅ CRITICAL |
| Phase 2 | 2/3 (67%) | ⚠️ RECOMMENDED |
| Phase 3 | 2/3 (67%) | ⚠️ RECOMMENDED |
| Phase 4 | 1/2 (50%) | 🔵 NICE TO HAVE |
| **OVERALL** | **7/10 (70%)** | ✅ **PASS** |

### **Ideal Coverage:**
- **90%+ coverage** = Excellent
- **70-89% coverage** = Good
- **50-69% coverage** = Acceptable
- **<50% coverage** = Needs investigation

---

## 🔍 Monitoring & Logging

### **Key Log Patterns:**

```bash
# Phase 1
grep "🔍.*Perplexity" /tmp/v6_server.log
grep "🛡️.*ASIMOV Rule 3" /tmp/v6_server.log

# Phase 2
grep "📚.*Learning" /tmp/v6_server.log
grep "❓.*Curiosity" /tmp/v6_server.log
grep "🔮.*Predictive" /tmp/v6_server.log

# Phase 3
grep "🔧.*Tool Registry" /tmp/v6_server.log
grep "✋.*Approval" /tmp/v6_server.log
grep "🎯.*Workflow Plan" /tmp/v6_server.log

# Phase 4
grep "🧠.*Neurosymbolic" /tmp/v6_server.log
grep "💊.*Self-Diagnosis" /tmp/v6_server.log
```

### **Feature Files to Check:**

```bash
# Learning patterns
ls ~/.ki_autoagent/data/learning/

# Curiosity data
ls ~/.ki_autoagent/data/curiosity/

# Predictive models
ls ~/.ki_autoagent/data/predictive/

# Memory store
sqlite3 ~/.ki_autoagent/data/memory/embeddings.db "SELECT COUNT(*) FROM memories;"
```

---

## 📝 Test Execution Checklist

- [ ] **Pre-Test:**
  - [ ] Backend running on port 8002
  - [ ] API keys configured (OPENAI_API_KEY, PERPLEXITY_API_KEY)
  - [ ] Clean test workspace created
  - [ ] Logs being monitored

- [ ] **Test 1: New App**
  - [ ] Curiosity questions appear
  - [ ] Predictive duration shown
  - [ ] Workflow plan displayed
  - [ ] Perplexity search results
  - [ ] Files created successfully
  - [ ] Build validation passes
  - [ ] Feature coverage ≥70%

- [ ] **Test 2: Extend App**
  - [ ] Learning patterns suggested
  - [ ] Workflow optimized (skips agents)
  - [ ] Incremental validation only
  - [ ] Neurosymbolic consistency check
  - [ ] Feature reuse confirmed

- [ ] **Test 3: Error Handling**
  - [ ] Self-diagnosis activates
  - [ ] ASIMOV Rule 3 global search
  - [ ] Recovery strategy applied
  - [ ] All error instances fixed
  - [ ] Final build passes

- [ ] **Test 4: Multi-Language**
  - [ ] All 6 validators run
  - [ ] Parallel execution confirmed
  - [ ] Quality thresholds respected
  - [ ] Build errors fed to fixer

- [ ] **Post-Test:**
  - [ ] Feature usage report generated
  - [ ] Coverage metrics calculated
  - [ ] Artifacts saved
  - [ ] Results documented

---

## 🎯 Expected Results

### **Files Created per Test:**

**Test 1 (Task Manager):**
```
v6_2_comprehensive_test/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   └── TaskList.tsx
│   ├── types.ts
│   └── api.ts
├── package.json
├── tsconfig.json
├── .eslintrc.json
└── README.md
```

**Test 2 (Add Auth):**
```
(additions to Test 1)
├── src/
│   ├── auth/
│   │   ├── AuthContext.tsx
│   │   ├── Login.tsx
│   │   └── PrivateRoute.tsx
│   └── utils/
│       └── jwt.ts
```

**Test 3 (Error Fix):**
```
python_flask_test/
├── app.py (with error, then fixed)
├── requirements.txt
└── tests/
    └── test_app.py
```

**Test 4 (Multi-Language):**
```
fullstack_polyglot/
├── frontend/         # TypeScript + React
├── backend/          # Python + FastAPI
├── image-service/    # Go
├── deploy-tool/      # Rust
├── admin-panel/      # Java + Spring Boot
└── scripts/          # JavaScript
```

---

## 🚀 Running the Tests

```bash
# 1. Start backend
cd /Users/dominikfoert/git/KI_AutoAgent
~/.ki_autoagent/venv/bin/python backend/api/server_v6_integrated.py

# 2. In another terminal, run tests
cd backend/tests
python3.10 e2e_comprehensive_v6_2.py

# 3. Monitor logs
tail -f /tmp/v6_server.log | grep -E "🧠|🔮|🎯|📊|🛡️|💭|🔧"
```

---

**Test Plan Version:** 1.0
**Created:** 2025-10-13
**Next Review:** After test execution