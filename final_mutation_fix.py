#!/usr/bin/env python3
"""
Final mutation fix - handles ALL remaining edge cases
"""

import re
from pathlib import Path

content = Path("backend/langgraph_system/workflow.py").read_text()

# Fix 1: codesmith completed (line ~1457)
content = re.sub(
    r'(current_step\.result = result\s*\n'
    r'\s+)current_step\.status = "completed"\s*\n'
    r'(\s+logger\.info\(.+set step.+completed\))',
    r'\1# v5.8.3: Immutable update\n'
    r'\1state.update(update_step_status(state, current_step.id, "completed", result=result))\n'
    r'\2',
    content
)

# Fix 2-4: Exception handlers (codesmith, reviewer, etc)
content = re.sub(
    r'(logger\.error\(.+failed.+\)\s*\n'
    r'\s+)current_step\.status = "failed"\s*\n'
    r'\s+current_step\.error = str\(e\)\s*\n'
    r'(\s+# .+ FIX: .+\s*\n)?'
    r'\s+state\["execution_plan"\] = list\(state\["execution_plan"\]\)',
    r'\1# v5.8.3: Immutable exception handling\n'
    r'\1state.update(update_step_status(state, current_step.id, "failed", error=str(e)))',
    content
)

# Fix 5-7: Route stub cases (agent not in AVAILABLE_NODES)
content = re.sub(
    r'(logger\.warning\(.+has no workflow node.+\)\s*\n'
    r'\s+)step\.status = "completed"\s*\n'
    r'\s+step\.result = (.+)\n'
    r'\s+state\["execution_plan"\] = list\(state\["execution_plan"\]\)',
    r'\1# v5.8.3: Immutable stub\n'
    r'\1state.update(update_step_status(state, step.id, "completed", result=\2))',
    content
)

# Fix 8: Architecture approval special case (line ~2284)
content = re.sub(
    r'(for step in state\["execution_plan"\]:\s*\n'
    r'\s+if step\.agent == "architect" and step\.status == "in_progress":\s*\n'
    r'\s+)step\.status = "completed"\s*\n'
    r'\s+step\.result = "Architecture proposal approved by user"',
    r'\1# v5.8.3: Immutable approval update\n'
    r'\1state.update(update_step_status(state, step.id, "completed", result="Architecture proposal approved by user"))',
    content
)

# Fix 9: route_to_next_agent step.status = "in_progress" (line ~2364)
content = re.sub(
    r'(\s+if step\.status == "pending".+:\s*\n'
    r'(?:\s+#.+\n)*'  # Skip comments
    r'\s+)step\.status = "in_progress"\s*\n'
    r'(\s+# v5\.4\.3: Track.+\s*\n'
    r'\s+step\.started_at = datetime\.now\(\)\s*\n'
    r'\s+step\.start_time = datetime\.now\(\))',
    r'\1# v5.8.3: Immutable start\n'
    r'\1updated_step = dataclass_replace(step, status="in_progress", started_at=datetime.now(), start_time=datetime.now())\n'
    r'\1state["execution_plan"] = [updated_step if s.id == step.id else s for s in state["execution_plan"]]\n'
    r'\1# Keep step reference for compatibility\n'
    r'\1step = updated_step',
    content
)

Path("backend/langgraph_system/workflow.py").write_text(content)

# Verify
import subprocess
result = subprocess.run(
    ["grep", "-c", r"\.status\s*=\s*\"", "backend/langgraph_system/workflow.py"],
    capture_output=True,
    text=True
)
remaining = int(result.stdout.strip()) if result.returncode == 0 else 0

print(f"✅ Final fixes applied")
print(f"📊 Remaining mutations: {remaining}")

if remaining == 0:
    print("🎉 ALL MUTATIONS COMPLETELY FIXED!")
else:
    print(f"⚠️  {remaining} mutations require manual attention")
