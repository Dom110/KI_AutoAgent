#!/usr/bin/env python3
"""
v5.8.3: Fix remaining mutations (exception handlers and special cases)
"""

import re
from pathlib import Path

def fix_exception_mutations(content: str) -> tuple[str, int]:
    """Fix mutations in exception handlers"""

    fixes = 0

    # Pattern: Exception handler with status + error
    # except Exception as e:
    #     logger.error(...)
    #     current_step.status = "failed"
    #     current_step.error = str(e)
    #     state["errors"].append(...)
    #     state["execution_plan"] = list(...)

    pattern = re.compile(
        r'(except .+:\s*\n'
        r'\s+logger\.error\(.+\)\s*\n)'
        r'(\s+)(current_step|step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+\3\.error\s*=\s*(.+)\n'
        r'(\s+state\["errors"\]\.append\(.+?\)\s*\n)?'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE | re.DOTALL
    )

    def replace_exception(m):
        nonlocal fixes
        fixes += 1
        except_part = m.group(1)
        indent = m.group(2)
        var = m.group(3)
        status = m.group(4)
        error_expr = m.group(5)
        errors_append = m.group(6) or ""

        return (
            f'{except_part}'
            f'{indent}# v5.8.3: Immutable exception handling\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}", error={error_expr}))\n'
            f'{errors_append}'
        )

    content = pattern.sub(replace_exception, content)

    # Pattern: Simple status mutation in try block (without result)
    # current_step.status = "completed"
    # (followed by return state, not list())

    # Look for: current_step.status = "X" followed by blank line or return
    pattern2 = re.compile(
        r'(\s+)(current_step)\.status\s*=\s*"(\w+)"\s*\n'
        r'(?=\s*\n|\s*#|\s*return\s+state)',
        re.MULTILINE
    )

    def replace_simple(m):
        nonlocal fixes
        fixes += 1
        indent = m.group(1)
        var = m.group(2)
        status = m.group(3)
        return (
            f'{indent}# v5.8.3: Immutable update\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}"))\n'
        )

    content = pattern2.sub(replace_simple, content)

    # Pattern: Route function special cases
    # if agent not in AVAILABLE_NODES:
    #     step.status = "completed"
    #     step.result = "..."
    #     state["execution_plan"] = list(...)
    #     (optional return or continue)

    pattern3 = re.compile(
        r'(if .+ not in .+:\s*\n'
        r'\s+logger\.warning\(.+\)\s*\n)'
        r'(\s+)(step)\.status\s*=\s*"(\w+)"\s*\n'
        r'\s+\3\.result\s*=\s*(.+)\n'
        r'\s+state\["execution_plan"\]\s*=\s*list\(state\["execution_plan"\]\)\s*\n',
        re.MULTILINE | re.DOTALL
    )

    def replace_route(m):
        nonlocal fixes
        fixes += 1
        if_part = m.group(1)
        indent = m.group(2)
        var = m.group(3)
        status = m.group(4)
        result_expr = m.group(5)

        return (
            f'{if_part}'
            f'{indent}# v5.8.3: Immutable stub update\n'
            f'{indent}state.update(update_step_status(state, {var}.id, "{status}", result={result_expr}))\n'
        )

    content = pattern3.sub(replace_route, content)

    return content, fixes


def main():
    workflow_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py")

    print("🔧 Fixing remaining mutations (exception handlers & special cases)")
    print("=" * 60)

    content = workflow_path.read_text()

    fixed_content, fixes = fix_exception_mutations(content)

    workflow_path.write_text(fixed_content)

    print(f"✅ Applied {fixes} additional fixes")
    print("=" * 60)

    # Count remaining
    import subprocess
    result = subprocess.run(
        ["grep", "-c", r"\.status\s*=\s*\"", str(workflow_path)],
        capture_output=True,
        text=True
    )
    remaining = int(result.stdout.strip()) if result.returncode == 0 else 0

    print(f"📊 Remaining mutations: {remaining}")

    if remaining == 0:
        print("🎉 ALL MUTATIONS FIXED!")
    else:
        print(f"⚠️  {remaining} mutations still need manual fixing")


if __name__ == "__main__":
    main()
