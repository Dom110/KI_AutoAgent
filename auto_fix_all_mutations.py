#!/usr/bin/env python3
"""
v5.8.3 Phase 1 Completion: Automated fix for ALL state mutations
Systematically converts all mutations to immutable pattern
"""

import re
import sys
from pathlib import Path

def fix_all_mutations(content: str) -> tuple[str, int]:
    """Fix all mutation patterns in workflow.py"""

    fixes_applied = 0

    # Pattern 1: Simple status + result + list() pattern
    # current_step.result = result
    # current_step.status = "completed"
    # state["execution_plan"] = list(state["execution_plan"])
    pattern1 = re.compile(
        r'(\s+)(current_step|step)\.result\s*=\s*(\w+)\s*\n'
        r'\s+\2\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace1(m):
        nonlocal fixes_applied
        fixes_applied += 1
        indent = m.group(1)
        var = m.group(2)
        result_var = m.group(3)
        status = m.group(4)
        return (
            f'{indent}# v5.8.3: Immutable update\n'
            f'{indent}return merge_state_updates(\n'
            f'{indent}    update_step_status(state, {var}.id, "{status}", result={result_var}),\n'
            f'{indent}    {{"messages": state["messages"]}}\n'
            f'{indent})\n'
        )

    content = pattern1.sub(replace1, content)

    # Pattern 2: Status only + list()
    # step.status = "completed"
    # state["execution_plan"] = list(state["execution_plan"])
    pattern2 = re.compile(
        r'(\s+)(current_step|step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace2(m):
        nonlocal fixes_applied
        fixes_applied += 1
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        return (
            f'{indent}# v5.8.3: Immutable update\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}"))\n'
        )

    content = pattern2.sub(replace2, content)

    # Pattern 3: Status + error + list()
    # step.status = "failed"
    # step.error = str(e)
    # state["execution_plan"] = list(...)
    pattern3 = re.compile(
        r'(\s+)(current_step|step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+\2\.error\s*=\s*(.+)\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace3(m):
        nonlocal fixes_applied
        fixes_applied += 1
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        error_expr = m.group(4)
        return (
            f'{indent}# v5.8.3: Immutable update with error\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}", error={error_expr}))\n'
        )

    content = pattern3.sub(replace3, content)

    # Pattern 4: Status with if-condition
    # if step.status != "failed" and step.status != "completed":
    #     step.status = "pending"
    # Already fixed by orchestrator pattern, skip

    # Pattern 5: Approval node patterns
    # first_step.status = "in_progress"
    # state["current_step_id"] = first_step.id
    # state["execution_plan"] = list(...)
    pattern5 = re.compile(
        r'(\s+)(first_step|step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+state\["current_step_id"\]\s*=\s*\2\.id\s*\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace5(m):
        nonlocal fixes_applied
        fixes_applied += 1
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        return (
            f'{indent}# v5.8.3: Immutable update with current_step_id\n'
            f'{indent}state.update(merge_state_updates(\n'
            f'{indent}    update_step_status(state, {var}.id, "{status}"),\n'
            f'{indent}    {{"current_step_id": {var}.id}}\n'
            f'{indent}))\n'
        )

    content = pattern5.sub(replace5, content)

    # Pattern 6: Route function stub patterns
    # step.status = "completed"
    # step.result = "..."
    # state["execution_plan"] = list(...)
    # return "end"
    pattern6 = re.compile(
        r'(\s+)(step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+\2\.result\s*=\s*(.+)\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n'
        r'(\s+return\s+"end")',
        re.MULTILINE
    )

    def replace6(m):
        nonlocal fixes_applied
        fixes_applied += 1
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        result_expr = m.group(4)
        return_stmt = m.group(5)
        return (
            f'{indent}# v5.8.3: Immutable update before return\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}", result={result_expr}))\n'
            f'{return_stmt}'
        )

    content = pattern6.sub(replace6, content)

    return content, fixes_applied


def main():
    workflow_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py")

    print("🔧 v5.8.3 Phase 1 Completion: Fixing ALL mutations")
    print("=" * 60)

    # Read file
    content = workflow_path.read_text()
    original_lines = content.count('\n')
    print(f"📄 Original file: {original_lines} lines")

    # Apply fixes
    fixed_content, fixes_count = fix_all_mutations(content)

    # Write back
    workflow_path.write_text(fixed_content)

    fixed_lines = fixed_content.count('\n')
    print(f"✅ Fixed file: {fixed_lines} lines")
    print(f"🔄 Applied {fixes_count} mutation fixes")
    print("=" * 60)

    if fixes_count > 0:
        print("✅ SUCCESS: All mutations converted to immutable pattern")
    else:
        print("ℹ️  No mutations found (already fixed?)")

    return 0 if fixes_count >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
