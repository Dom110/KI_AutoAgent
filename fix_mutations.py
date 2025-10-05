#!/usr/bin/env python3
"""
v5.8.3: Automated fix for state mutations in workflow.py
Converts all `step.status = "X"` mutations to immutable pattern
"""

import re

def fix_workflow_mutations(content: str) -> str:
    """Fix all step.status mutations in workflow.py"""

    # Pattern 1: Simple status mutation followed by execution_plan update
    # step.status = "completed"
    # state["execution_plan"] = list(state["execution_plan"])
    # return state

    pattern1 = re.compile(
        r'(\s+)(current_step|step)\.status\s*=\s*"(\w+)"\s*\n'
        r'(\s+)state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace1(m):
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        return (
            f'{indent}# v5.8.3: Use immutable update\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}"))\n'
        )

    content = pattern1.sub(replace1, content)

    # Pattern 2: Status + result mutation
    # current_step.result = result
    # current_step.status = "completed"
    # state["execution_plan"] = list(...)

    pattern2 = re.compile(
        r'(\s+)(current_step|step)\.result\s*=\s*(\w+)\s*\n'
        r'(\s+)\2\.status\s*=\s*"(\w+)"\s*\n'
        r'(\s+)state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE
    )

    def replace2(m):
        indent = m.group(1)
        var = m.group(2)
        result_var = m.group(3)
        status = m.group(5)
        return (
            f'{indent}# v5.8.3: Use immutable update\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}", result={result_var}))\n'
        )

    content = pattern2.sub(replace2, content)

    return content


if __name__ == "__main__":
    import sys

    workflow_path = "/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py"

    with open(workflow_path, 'r') as f:
        content = f.read()

    print(f"Original size: {len(content)} chars")

    fixed_content = fix_workflow_mutations(content)

    print(f"Fixed size: {len(fixed_content)} chars")

    with open(workflow_path, 'w') as f:
        f.write(fixed_content)

    print("✅ Mutations fixed!")
