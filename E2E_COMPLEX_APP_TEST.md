# E2E Test: Complex Application with Full Workflow Generation

**Created:** 2025-10-13
**Version:** v6.2.0-alpha
**Status:** Ready for Execution

---

## 🎯 Test Overview

This E2E test validates the COMPLETE v6.2 system by requesting a complex full-stack application via WebSocket and validating that ALL features work correctly.

### Key Innovation

**The agent receives ONLY a single message:**
```
"Create a full-stack todo application with React frontend, FastAPI backend,
SQLite database, user authentication, and real-time updates via WebSockets.
Include comprehensive tests and deployment configuration."
```

**Everything else is automatic:**
- ✅ Workflow generation (AI-based planning)
- ✅ Agent coordination
- ✅ MCP protocol usage
- ✅ File generation
- ✅ Quality validation

---

## 🧪 Test Features Validated

### 1. Workflow Planning (NEW v6.2!)

**Feature:** `WorkflowPlannerV6` automatically generates optimal workflow

**Validation:**
- ✅ Workflow plan created with AI analysis
- ✅ Correct workflow type detected (CREATE)
- ✅ Complexity level estimated
- ✅ Agent sequence determined
- ✅ Estimated duration calculated

**Expected Workflow:**
```
research → architect → codesmith → reviewfix
```

### 2. All Agents Executed

**Feature:** Complete multi-agent execution

**Validation:**
- ✅ Research agent finds best practices
- ✅ Architect agent designs system
- ✅ Codesmith agent generates code
- ✅ ReviewFix agent validates quality

**Minimum:** All 4 agents must execute

### 3. MCP Protocol Integration

**Feature:** All service calls via MCP

**Validation:**
- ✅ MCP client initialized
- ✅ Perplexity search via MCP
- ✅ Claude CLI via MCP
- ✅ Memory storage via MCP
- ✅ No direct service calls

**Evidence:** MCP call events in WebSocket messages

### 4. Research Findings

**Feature:** Research agent uses Perplexity to find information

**Validation:**
- ✅ Research results returned
- ✅ Sources cited
- ✅ Findings summarized
- ✅ Mode correctly determined (research/explain/analyze)

### 5. Architecture Design

**Feature:** Architect agent creates system design

**Validation:**
- ✅ Architecture document generated
- ✅ Tech stack selected
- ✅ Component structure defined
- ✅ Database schema designed
- ✅ API endpoints specified

### 6. Code Generation

**Feature:** Codesmith agent generates working code

**Validation:**
- ✅ Multiple files created
- ✅ Files in correct locations
- ✅ Code follows architecture
- ✅ Dependencies included
- ✅ Configuration files present

**Minimum Files:**
- `README.md` - Setup instructions
- `requirements.txt` or `package.json` - Dependencies
- `backend/` - Backend code
- `frontend/` - Frontend code
- `tests/` - Test files
- `docker-compose.yml` - Deployment config

### 7. Quality Review

**Feature:** ReviewFix agent validates and fixes issues

**Validation:**
- ✅ Review feedback generated
- ✅ Issues identified (if any)
- ✅ Fixes applied automatically
- ✅ Final quality score > 0.75

### 8. Files in Correct Workspace

**Feature:** Workspace isolation (E2E_TESTING_GUIDE.md)

**Validation:**
- ✅ Files in `~/TestApps/e2e_complex_app/`
- ✅ NOT in development repo
- ✅ No workspace pollution

### 9. No Critical Errors

**Feature:** Error resilience and recovery

**Validation:**
- ✅ No unhandled exceptions
- ✅ No timeout errors
- ✅ No WebSocket disconnections
- ✅ Errors array empty or only warnings

### 10. High Quality Score

**Feature:** Overall execution quality

**Validation:**
- ✅ Quality score > 0.75
- ✅ All agents completed
- ✅ No critical failures

---

## 📋 Test Configuration

### Workspace

```python
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_complex_app"
```

**Critical:** Isolated from development repo!

### WebSocket

```python
WS_URL = "ws://localhost:8002/ws/chat"
WS_TIMEOUT = 900  # 15 minutes
```

### Task Description

```python
complex_task = """
Create a full-stack todo application with the following requirements:
- React frontend with TypeScript and Tailwind CSS
- FastAPI backend with Python 3.13+
- SQLite database with proper schema
- User authentication (JWT tokens)
- Real-time updates via WebSockets
- CRUD operations for todos
- Comprehensive unit and integration tests
- Docker deployment configuration
- Complete README with setup instructions

The application should be production-ready with proper error handling,
validation, and security best practices.
"""
```

---

## 🚀 Running the Test

### Prerequisites

1. **Backend running:**
   ```bash
   cd backend
   ./venv/bin/python main_v6_websocket.py
   ```

2. **MCP servers registered:**
   ```bash
   claude mcp list
   # Should show: perplexity, memory, tree-sitter, asimov, claude (5/6)
   ```

3. **Clean test workspace:**
   ```bash
   rm -rf ~/TestApps/e2e_complex_app/
   ```

### Execute Test

```bash
cd /Users/dominikfoert/git/KI_AutoAgent

# Run with root venv
./venv/bin/python backend/tests/test_e2e_complex_app_workflow.py
```

### Monitor Execution

```bash
# In separate terminal: Watch logs
tail -f /tmp/e2e_complex_app_test.log

# In separate terminal: Watch backend
tail -f /tmp/v6_server.log

# In separate terminal: Check workspace
watch -n 5 'ls -la ~/TestApps/e2e_complex_app/'
```

---

## 📊 Expected Output

### Success Output

```
🧪 E2E TEST: Complex Application with Full Workflow Generation
================================================================================
🧹 Setting up test workspace...
  ✅ Created clean workspace: /Users/.../TestApps/e2e_complex_app
  ✅ Workspace verified clean
🔌 Connecting to ws://localhost:8002/ws/chat
✅ Connected to WebSocket
📡 Sent init with workspace: /Users/.../TestApps/e2e_complex_app
✅ Init response: init_complete
📤 Sending task: Create a full-stack todo application with the following...
✅ Task sent, waiting for response...
📥 Receiving messages (timeout: 900s)...
🎯 Workflow planning: CREATE
  Agents: research → architect → codesmith → reviewfix
🤖 Agent starting: research
🔌 MCP call: perplexity/perplexity_search
✅ Agent completed: research
🤖 Agent starting: architect
✅ Agent completed: architect
🤖 Agent starting: codesmith
🔌 MCP call: claude/claude_generate
✅ Agent completed: codesmith
🤖 Agent starting: reviewfix
✅ Agent completed: reviewfix
🎉 Task completed!
🔌 Disconnected from WebSocket
📂 Verifying workspace files...
  ✅ Found 47 files in 12 directories
    - README.md
    - requirements.txt
    - backend/main.py
    - backend/models.py
    - backend/api/routes.py
    - frontend/package.json
    - frontend/src/App.tsx
    - tests/test_api.py
    - docker-compose.yml
    - .env.example
    ... and 37 more
🔍 Validating results...
  ✅ workflow_planning: Automatic workflow generation using AI
  ✅ all_agents_executed: All 4 agent types executed
  ✅ mcp_protocol: MCP protocol used for services
  ✅ research_findings: Research agent found information
  ✅ architecture_design: Architect agent created design
  ✅ code_generation: Codesmith agent generated files
  ✅ quality_review: ReviewFix agent validated quality
  ✅ files_in_workspace: Files created in correct location
  ✅ no_critical_errors: No critical errors occurred
  ✅ quality_score: High quality score (>0.75)

📊 Validation Summary:
  Passed: 10/10
  Pass Rate: 100.0%
  Success: ✅

================================================================================
📊 TEST SUMMARY
================================================================================
Status: ✅ SUCCESS
Duration: 287.5s
Pass Rate: 100.0%
Features Passed: 10/10
Agents Executed: 4
Files Generated: 47
Quality Score: 0.89
Errors: 0

✅ Test passed - keeping workspace: /Users/.../TestApps/e2e_complex_app
📦 Backup created: /Users/.../TestApps/success_20251013_180245
📝 Test report saved: /tmp/e2e_complex_app_test_report.json
✅ Test PASSED
```

### Failure Output

```
🧪 E2E TEST: Complex Application with Full Workflow Generation
================================================================================
...
❌ Error: Workflow planning failed: No module named 'cognitive.workflow_planner_v6'
🔍 Validating results...
  ✅ workflow_planning: Automatic workflow generation using AI
  ✅ all_agents_executed: All 4 agent types executed
  ❌ mcp_protocol: MCP protocol used for services
  ❌ research_findings: Research agent found information
  ...

📊 Validation Summary:
  Passed: 6/10
  Pass Rate: 60.0%
  Success: ❌

================================================================================
📊 TEST SUMMARY
================================================================================
Status: ❌ FAILED
Duration: 143.2s
Pass Rate: 60.0%
Features Passed: 6/10
Agents Executed: 2
Files Generated: 0
Quality Score: 0.32
Errors: 3

❌ Errors:
  - Workflow planning failed: No module named 'cognitive.workflow_planner_v6'
  - Architect failed: Missing research results
  - Timeout after 900s

Removing workspace: /Users/.../TestApps/e2e_complex_app
✅ Cleanup complete
📝 Test report saved: /tmp/e2e_complex_app_test_report.json
❌ Test FAILED
```

---

## 📈 Success Criteria

### Required (MUST pass):

1. **Workflow Planning:** ✅ AI-generated workflow plan
2. **All Agents:** ✅ 4/4 agents executed
3. **MCP Protocol:** ✅ MCP used for services
4. **Files Generated:** ✅ Files in correct workspace
5. **No Critical Errors:** ✅ Errors array empty

### Quality Indicators (SHOULD pass):

6. **Research Findings:** ✅ Research results present
7. **Architecture Design:** ✅ Design document created
8. **Code Generation:** ✅ Multiple files generated
9. **Quality Review:** ✅ Review feedback present
10. **Quality Score:** ✅ Score > 0.75

**Pass Threshold:** 80% (8/10 features)

---

## 🔍 Test Report Analysis

### Report Location

```bash
cat /tmp/e2e_complex_app_test_report.json
```

### Report Structure

```json
{
  "test_name": "E2E Complex Application",
  "start_time": "2025-10-13T18:00:00",
  "end_time": "2025-10-13T18:05:00",
  "duration": 287.5,
  "status": "success",
  "workspace": "/Users/.../TestApps/e2e_complex_app",
  "results": {
    "workflow_plan": {
      "type": "CREATE",
      "complexity": "complex",
      "agents": ["research", "architect", "codesmith", "reviewfix"],
      "estimated_duration": "~5 minutes"
    },
    "agents_completed": ["research", "architect", "codesmith", "reviewfix"],
    "research_results": { ... },
    "architecture_design": { ... },
    "generated_files": ["README.md", "main.py", ...],
    "review_feedback": { ... },
    "errors": [],
    "quality_score": 0.89,
    "execution_time": 287.5,
    "mcp_enabled": true,
    "messages_received": [
      "init_complete",
      "workflow_planning",
      "agent_start",
      "mcp_call",
      ...
    ]
  },
  "validation": {
    "passed": 10,
    "failed": 0,
    "total": 10,
    "pass_rate": 1.0,
    "success": true,
    "features_tested": {
      "workflow_planning": { "passed": true, "description": "..." },
      ...
    }
  },
  "workspace_files": {
    "workspace_path": "/Users/.../TestApps/e2e_complex_app",
    "total_files": 47,
    "total_dirs": 12,
    "files_found": ["README.md", "main.py", ...]
  }
}
```

---

## 🐛 Debugging Failed Tests

### 1. Check Backend Logs

```bash
tail -100 /tmp/v6_server.log | grep -E "ERROR|WARN|❌"
```

### 2. Check Test Logs

```bash
tail -100 /tmp/e2e_complex_app_test.log | grep -E "ERROR|❌"
```

### 3. Check MCP Servers

```bash
claude mcp list
# Ensure all servers connected
```

### 4. Check Workspace

```bash
ls -la ~/TestApps/e2e_complex_app/
# Verify files exist
```

### 5. Manual WebSocket Test

```bash
# Install wscat if needed: npm install -g wscat
wscat -c ws://localhost:8002/ws/chat

# Send init:
{"type":"init","workspace_path":"/tmp/test"}

# Send task:
{"type":"task","task":"Create simple hello world app"}
```

---

## 📝 Common Issues

### Issue: Workflow Planning Fails

**Symptom:** `workflow_plan` is `None`

**Possible Causes:**
1. WorkflowPlannerV6 not imported
2. GPT-4o-mini API unavailable
3. Invalid workspace_path

**Fix:**
```bash
# Check import
grep -r "WorkflowPlannerV6" backend/workflow_v6_integrated.py

# Check API key
echo $OPENAI_API_KEY
```

### Issue: MCP Calls Fail

**Symptom:** `mcp_enabled` is `False`, errors mention MCP

**Possible Causes:**
1. MCP servers not started
2. MCPClient initialization failed
3. Wrong Python path

**Fix:**
```bash
# Check MCP servers
claude mcp list

# Check MCPClient
grep -A 20 "_setup_mcp" backend/workflow_v6_integrated.py
```

### Issue: Files in Wrong Location

**Symptom:** Files in development repo instead of test workspace

**Possible Causes:**
1. Missing `cwd=workspace_path` in subprocess
2. Wrong workspace_path sent to backend
3. Claude CLI not respecting CWD

**Fix:**
```bash
# Check ClaudeCLISimple
grep "cwd=" backend/adapters/claude_cli_simple.py

# Check init message
grep "workspace_path" /tmp/e2e_complex_app_test.log
```

### Issue: Timeout After 15 Minutes

**Symptom:** Test times out, no completion

**Possible Causes:**
1. Codesmith taking too long
2. Review loop stuck
3. HITL request waiting for response

**Fix:**
```bash
# Check which agent is stuck
tail -50 /tmp/v6_server.log | grep "Agent"

# Check for HITL
grep "hitl_request" /tmp/e2e_complex_app_test.log
```

---

## 🎯 Success Indicators

### System is Working If:

1. ✅ **Workflow Plan Created** - AI determined optimal workflow
2. ✅ **All 4 Agents Executed** - Complete multi-agent coordination
3. ✅ **MCP Protocol Used** - Unified service communication
4. ✅ **47+ Files Generated** - Complex application structure
5. ✅ **Quality Score > 0.75** - High execution quality
6. ✅ **<5 Minutes Execution** - Efficient workflow
7. ✅ **0 Critical Errors** - Robust error handling
8. ✅ **Files in Test Workspace** - Proper workspace isolation

### System Has Issues If:

1. ❌ **No Workflow Plan** - Planner not working
2. ❌ **<4 Agents Executed** - Agent coordination broken
3. ❌ **No MCP Calls** - MCP integration broken
4. ❌ **0 Files Generated** - Codesmith broken
5. ❌ **Quality Score < 0.50** - Major quality issues
6. ❌ **>15 Minutes Execution** - Performance problems
7. ❌ **Critical Errors** - Unhandled exceptions
8. ❌ **Files in Wrong Location** - Workspace pollution

---

## 📚 Related Documentation

- **E2E Testing Guide:** `/E2E_TESTING_GUIDE.md`
- **Critical Failure Instructions:** `/CRITICAL_FAILURE_INSTRUCTIONS.md`
- **System Architecture:** `/ARCHITECTURE_v6.2_CURRENT.md`
- **MCP Implementation:** `/MCP_PHASE_3-8_COMPLETION_REPORT.md`
- **Claude Best Practices:** `/CLAUDE_BEST_PRACTICES.md`

---

## 🏆 Why This Test is Important

### Validates Complete System

This single test validates:
- 🧠 **v6.2 Intelligence** - Workflow planning, learning, adaptation
- 🔌 **MCP Protocol** - All service calls unified
- 🤖 **Multi-Agent Coordination** - 4 agents working together
- 📁 **Workspace Isolation** - No development repo pollution
- 🎯 **Quality Assurance** - ReviewFix validation
- ⚡ **Performance** - <15 minute execution
- 🛡️ **Error Resilience** - Self-healing and recovery

### Simulates Real Usage

The test simulates exactly how a real user would use the system:
1. User sends ONE message via WebSocket
2. System does EVERYTHING automatically
3. User receives working application

**No manual intervention. No hardcoded workflows. Pure automation.**

---

**This test represents the GOLD STANDARD for KI AutoAgent v6.2!** 🏆

---

**Last Updated:** 2025-10-13
**Author:** KI AutoAgent Team
**Version:** v6.2.0-alpha
