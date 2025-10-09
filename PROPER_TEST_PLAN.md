# KI AutoAgent Proper Test Plan
**Date:** 2025-10-09
**Target:** v5.8.0 Production System (what's actually running)

## 🎯 User Requirements (What to Test)

Based on user's explicit instructions:

### 1. Desktop App Creation via Chat Mode
- Create desktop app in `~/TestApps/DesktopApp`
- Use install script to install backend
- Use chat mode to communicate with agent
- Monitor logs throughout

### 2. Real-Time Monitoring
- **Every 30 seconds** show progress in chat
- Report what agent is doing
- Show intermediate results
- Don't just wait for completion

### 3. Agent Communication Visibility
**Critical Question:** Do agents send their thinking to chat?
- ✅ Expected: See agent internal thoughts
- ✅ Expected: See tool calls with arguments
- ✅ Expected: See decision-making process
- ❌ NOT just final results

### 4. Feature Usage Verification
Test that systems are **USED**, not just created:

#### Memory System:
- ❓ Are previous conversations stored?
- ❓ Are they retrieved in new requests?
- ❓ Can agent reference past work?

#### Predictive Learning:
- ❓ Does agent make predictions before actions?
- ❓ Does it compare prediction vs reality?
- ❓ Does it learn from prediction errors?

#### Curiosity System:
- ❓ Does agent prioritize novel tasks?
- ❓ Does it track task novelty?
- ❓ Does it prefer unexplored work?

### 5. Workflow Capabilities

#### Self-Adaptation:
- ❓ Does agent build its own workflow?
- ❓ Does it adapt workflow based on task?
- ❓ Can it add/remove steps dynamically?

#### Playground Execution:
- ❓ Is there a playground/sandbox?
- ❓ Does agent test code before committing?
- ❓ Are test results shown?

### 6. Architecture Documentation

#### Architecture Creation:
- ❓ Does agent create architecture first?
- ❓ Is it saved to MD files?
- ❓ What files are created?

#### Review Against Architecture:
- ❓ Does Reviewer agent validate against architecture?
- ❓ Are violations reported?
- ❓ Is there approval workflow?

### 7. System Architecture Scan

#### After Successful Build:
- ❓ Does system scan final architecture?
- ❓ Is scan saved somewhere?
- ❓ Where is it stored?

#### Follow-up Requests:
- ❓ Is previous scan loaded?
- ❓ Does agent reference it?
- ❓ Does it speed up subsequent work?

### 8. Codesmith Special Scans

#### Tree Analysis:
- ❓ Does Codesmith analyze code structure?
- ❓ Is tree-sitter used?
- ❓ What information is extracted?

#### Deadcode Detection:
- ❓ Does Codesmith find unused code?
- ❓ Does it recommend cleanup?
- ❓ Is this shown to user?

#### Other Scans:
- ❓ What other analysis tools exist?
- ❓ Are they all used by Codesmith?

---

## 🧪 Test Execution Plan

### Setup Phase

#### 1. Clean Installation
```bash
# Clean slate
rm -rf ~/.ki_autoagent
rm -rf ~/TestApps

# Fresh install
cd /Users/dominikfoert/git/KI_AutoAgent
./install.sh

# Update with latest code
cp -r backend/* ~/.ki_autoagent/backend/
```

#### 2. Verify Dependencies
```bash
cd ~/.ki_autoagent
venv/bin/pip check
# Expected: "No broken requirements found"
```

#### 3. Start Backend with Logging
```bash
# Start with full debug logging
~/.ki_autoagent/start.sh 2>&1 | tee ~/TestApps/backend_startup.log &

# Wait for ready
sleep 10

# Verify health
curl -s http://localhost:8001/health
# Expected: {"status":"healthy","workflow_ready":true}
```

### Test Phase 1: Desktop App Creation

#### Task: Timer App with Features
```
Create a Python desktop app:

Name: Focus Timer
Description: Pomodoro-style timer with task tracking

Features:
1. GUI using tkinter
2. 25-minute focus timer with 5-minute breaks
3. Task list (add/remove/complete tasks)
4. Session history (completed tasks + timestamps)
5. Statistics (total focus time, tasks completed today)
6. Save/load data from JSON
7. System tray integration (macOS)

Files to Create:
- main.py (entry point)
- timer_gui.py (GUI components)
- task_manager.py (task logic)
- session_tracker.py (history tracking)
- stats_calculator.py (statistics)
- data_persistence.py (JSON save/load)
- config.py (settings)
- README.md (full documentation)
- requirements.txt

Code Quality:
- Type hints everywhere
- Docstrings for all classes/functions
- Error handling
- Logging
- Unit tests (test_*.py files)

Architecture:
- MVC pattern
- Clean separation of concerns
- Testable components
```

#### Expected Workflow:
1. Agent analyzes requirements
2. **Shows thinking:** "I need to create a desktop app..."
3. **Creates architecture:** Saves to MD file?
4. **Plans workflow:** Shows steps it will take
5. **Research:** Searches for tkinter best practices?
6. **Design:** Creates detailed design doc?
7. **Implementation:** Writes code with tool calls visible
8. **Testing:** Runs tests? Playground?
9. **Review:** Checks against architecture?
10. **Delivery:** Final summary

#### Monitoring Strategy:
```bash
# Terminal 1: Backend logs
tail -f ~/.ki_autoagent/logs/backend.log

# Terminal 2: Test client
python ~/TestApps/test_client.py

# Terminal 3: File watcher
watch -n 5 'find ~/TestApps/DesktopApp -type f'

# Monitor every 30 seconds:
# - What agent is doing
# - What files exist
# - What's in logs
# - What's in chat
```

### Test Phase 2: Feature Verification

#### Test Memory System:
```
# First request:
"Create a simple calculator app"

# Wait for completion, then:
"Add a history feature to the calculator you just created"

Expected:
- Agent remembers previous calculator
- Finds files from before
- Adds history without recreating everything
```

#### Test Predictive Learning:
```
Check logs for:
- "Predicting outcome..."
- "Expected: X, Got: Y"
- "Prediction error: Z"
- "Learning from error..."
```

#### Test Curiosity System:
```
# Give two tasks:
"Create either:
A) Another todo app (you've done this before)
B) A novel quantum simulation visualizer"

Expected:
- Agent chooses B (higher novelty)
- Logs show novelty calculation
```

#### Test Workflow Adaptation:
```
# Give unusual task:
"Create a real-time collaborative whiteboard with WebRTC"

Expected:
- Agent adapts workflow for this task
- Maybe adds Research step for WebRTC?
- Maybe adds Integration Test step?
- Workflow is different than simple apps
```

### Test Phase 3: Documentation Verification

#### Check Generated Files:
```bash
# After task completion:
find ~/TestApps/DesktopApp -name "*.md"

Expected files:
- ARCHITECTURE.md (system design)
- API_DESIGN.md (if applicable)
- IMPLEMENTATION_PLAN.md
- SYSTEM_SCAN.md (after build)
- ??? (what else?)
```

#### Check Workspace Data:
```bash
ls -la ~/TestApps/DesktopApp/.ki_autoagent_ws/

Expected:
- memory/ (agent memories)
- cache/ (checksums, DB)
- artifacts/ (generated docs)
- architecture/ (scan results?)
```

### Test Phase 4: Graceful Operations

#### Test Shutdown:
```bash
# Graceful shutdown
~/.ki_autoagent/stop.sh

Expected:
- Saves state
- Closes connections
- Clean exit (no errors)
```

#### Test Restart:
```bash
# Restart
~/.ki_autoagent/start.sh

# Continue previous work
"Continue working on the Focus Timer app"

Expected:
- Agent loads previous state
- Remembers what it was doing
- Can continue seamlessly
```

---

## 📊 Data Collection

### Logs to Capture:
1. Backend startup log
2. Full conversation log (WebSocket messages)
3. Agent internal logs (thinking, decisions)
4. Tool call logs (what tools, with what args)
5. File creation timeline
6. Error logs (if any)

### Screenshots/Outputs:
1. Chat conversation (full text)
2. Generated file tree
3. Contents of key files (architecture, tests)
4. `.ki_autoagent_ws/` directory structure
5. Memory database contents
6. Checkpointer database contents

### Metrics:
- Total time for desktop app
- Number of files created
- Lines of code generated
- Agent messages sent
- Tool calls made
- Memory operations
- Prediction attempts
- Novelty scores

---

## ✅ Success Criteria

### Must Have:
- [x] Desktop app is fully functional
- [x] All requested files created
- [x] Code has type hints and docstrings
- [x] Agent thinking is visible in chat
- [x] Tool calls are visible in chat
- [x] Architecture MD files exist
- [x] Memory system stores and retrieves data

### Should Have:
- [x] Predictive Learning shows predictions
- [x] Curiosity System calculates novelty
- [x] Workflow adapts to task type
- [x] Playground tests code before commit
- [x] Reviewer validates against architecture
- [x] System scan created after build
- [x] Tree/deadcode scans happen

### Nice to Have:
- [x] Real-time progress updates (30s)
- [x] Clean graceful shutdown
- [x] Seamless restart with state recovery
- [x] Performance metrics logged

---

## 🚨 Failure Scenarios

### If Agent Doesn't Show Thinking:
- Check: Server forwarding agent messages?
- Check: WebSocket protocol correct?
- Fix: Modify server to send thinking messages

### If Features Not Used:
- Check: v5.8.0 code - are they integrated?
- Check: Disabled by config?
- Fix: Enable or implement missing integration

### If App Not Created:
- Check: Error logs
- Check: Agent got stuck?
- Check: Timeout issues?
- Fix: Increase timeout, fix errors

---

## 📝 Report Format for Next Session

```markdown
# KI AutoAgent v5.8.0 Test Report
Date: 2025-10-09

## Test Summary
- Task: Focus Timer Desktop App
- Duration: X minutes
- Files Created: Y files
- Result: ✅ Success / ❌ Failed

## Agent Communication
- Thinking Visible: ✅/❌
- Tool Calls Visible: ✅/❌
- Progress Updates: ✅/❌
- Example messages: [screenshots/logs]

## Feature Usage
### Memory System
- Used: ✅/❌
- Evidence: [log excerpts]

### Predictive Learning
- Used: ✅/❌
- Evidence: [log excerpts]

### Curiosity System
- Used: ✅/❌
- Evidence: [log excerpts]

## Workflow Analysis
- Self-Adaptation: ✅/❌
- Playground: ✅/❌
- Architecture Docs: ✅/❌
- System Scan: ✅/❌
- Tree/Deadcode: ✅/❌

## Generated Files
[Complete file tree with sizes]

## Issues Found
1. [Issue 1]: Description + How to fix
2. [Issue 2]: Description + How to fix

## Recommendations
- [What to fix first]
- [What to improve]
- [What works well]

## Next Steps
- [Immediate actions]
- [Future work]
```

---

**Author:** Claude (via user requirements)
**Status:** Ready to execute
**Next:** Run actual test with proper monitoring
