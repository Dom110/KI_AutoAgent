#!/usr/bin/env python3
"""Final manual fixes for remaining mutations"""
import re
from pathlib import Path

content = Path("backend/langgraph_system/workflow.py").read_text()

# Fix pattern: current_step.status = "failed" in exception handlers
# Followed by state["errors"].append or return
content = re.sub(
    r'(\s+)(current_step)\.status = "failed"\s*\n'
    r'(\s+\2\.error = str\(e\)\s*\n)?'
    r'(\s+state\["errors"\]\.append\(',
    r'\1# v5.8.3: Immutable exception handling\n'
    r'\1state.update(update_step_status(state, \2.id, "failed", error=str(e)))\n'
    r'\4',
    content
)

# Fix pattern: current_step.status = "completed" (without prior result assignment)
# Followed by logger or send_agent_activity
content = re.sub(
    r'(\s+)(current_step)\.status = "completed"\s*\n'
    r'(\s+logger\.info)',
    r'\1# v5.8.3: Immutable completion\n'
    r'\1state.update(update_step_status(state, \2.id, "completed"))\n'
    r'\3',
    content
)

# Fix pattern: step.status = "completed" in route functions
# With step.result assignment before
content = re.sub(
    r'(\s+)(step)\.status = "completed"\s*\n'
    r'(\s+\2\.result = )',
    r'\1# v5.8.3: Immutable stub - result first, then status\n'
    r'\3',
    content
)

# Then fix the pattern where result comes AFTER (swap order)
content = re.sub(
    r'(\s+# v5\.8\.3: Immutable stub - result first, then status\s*\n'
    r'\s+)(step)\.result = (.+)\n',
    r'\1updated_result = \3\n'
    r'\1state.update(update_step_status(state, \2.id, "completed", result=updated_result))\n',
    content
)

# Fix: step.status = "in_progress" at end (routing function)
content = re.sub(
    r'(\s+)(step)\.status = "in_progress"\s*\n'
    r'(\s+# v5\.4\.3: Track.+\s*\n'
    r'\s+step\.started_at = datetime\.now\(\)\s*\n'
    r'\s+step\.start_time = datetime\.now\(\))',
    r'\1# v5.8.3: Immutable in_progress with timestamps\n'
    r'\1now = datetime.now()\n'
    r'\1state.update(merge_state_updates(\n'
    r'\1    update_step_status(state, \2.id, "in_progress"),\n'
    r'\1    {"current_step_id": \2.id}\n'
    r'\1))\n'
    r'\1# Also update started_at via dataclass_replace\n'
    r'\1updated_step = dataclass_replace(\2, started_at=now, start_time=now)\n'
    r'\1state["execution_plan"] = [updated_step if s.id == \2.id else s for s in state["execution_plan"]]',
    content
)

Path("backend/langgraph_system/workflow.py").write_text(content)

# Count remaining
import subprocess
result = subprocess.run(
    ["grep", "-c", r"\.status\s*=\s*\"", "backend/langgraph_system/workflow.py"],
    capture_output=True,
    text=True
)
remaining = int(result.stdout.strip()) if result.returncode == 0 else 0

print(f"✅ Manual fixes applied")
print(f"📊 Remaining mutations: {remaining}")
if remaining == 0:
    print("🎉 ALL MUTATIONS COMPLETELY FIXED!")
