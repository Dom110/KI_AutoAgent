#!/usr/bin/env python3
"""
Script to remove old evaluate_task() methods from all agent subgraphs.

v6.6: Agents no longer have evaluate_task() - routing is done by
MultiAgentOrchestrator using LLM (GPT-4o-mini).

This script removes:
1. evaluate_task() function definition
2. compiled_graph.evaluate_task = evaluate_task assignment
"""

import re
from pathlib import Path


def fix_subgraph_file(file_path: Path):
    """Remove evaluate_task from a subgraph file."""
    print(f"Processing: {file_path}")

    # Read file
    content = file_path.read_text()

    # Pattern 1: Remove entire evaluate_task function
    # Find start: "async def evaluate_task"
    # Find end: next "async def" or "def " at same indentation level

    # Split by lines
    lines = content.split('\n')

    # Track which lines to keep
    keep_lines = []
    in_evaluate_task = False
    evaluate_task_indent = 0

    for i, line in enumerate(lines):
        # Check if this is the evaluate_task start
        if 'async def evaluate_task' in line:
            in_evaluate_task = True
            # Get indentation level
            evaluate_task_indent = len(line) - len(line.lstrip())
            print(f"  Found evaluate_task at line {i+1}, indent={evaluate_task_indent}")
            continue

        # If we're in evaluate_task, check if we've reached the next function
        if in_evaluate_task:
            # Check for next function at same or lower indentation
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)

            # End of evaluate_task if we find:
            # 1. Another function at same/lower indentation
            # 2. Or a comment block at same indentation (for next section)
            if stripped.startswith('async def ') or stripped.startswith('def '):
                if current_indent <= evaluate_task_indent:
                    print(f"  End of evaluate_task at line {i+1}")
                    in_evaluate_task = False
                    # Keep this line (it's the next function)
                    keep_lines.append(line)
                    continue

            # Check for section markers (# ===)
            if stripped.startswith('# =') and current_indent <= evaluate_task_indent:
                print(f"  End of evaluate_task at section marker line {i+1}")
                in_evaluate_task = False
                keep_lines.append(line)
                continue

            # Still in evaluate_task, skip this line
            continue

        # Check for evaluate_task attachment line
        if 'compiled_graph.evaluate_task = evaluate_task' in line:
            print(f"  Removing attachment at line {i+1}")
            continue

        # Keep this line
        keep_lines.append(line)

    # Write back
    new_content = '\n'.join(keep_lines)
    file_path.write_text(new_content)
    print(f"  ✅ Fixed {file_path.name}")


def main():
    """Fix all agent subgraph files."""
    backend_dir = Path(__file__).parent / 'backend' / 'subgraphs'

    files_to_fix = [
        backend_dir / 'research_subgraph_v6_1.py',
        backend_dir / 'architect_subgraph_v6_3.py',
        backend_dir / 'codesmith_subgraph_v6_1.py',
        backend_dir / 'reviewfix_subgraph_v6_1.py'
    ]

    for file_path in files_to_fix:
        if file_path.exists():
            fix_subgraph_file(file_path)
        else:
            print(f"❌ File not found: {file_path}")

    print("\n✅ All files fixed!")


if __name__ == '__main__':
    main()
