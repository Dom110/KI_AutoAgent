#!/usr/bin/env python3
"""
Analyze code against LangGraph Best Practices
"""

import os
import re
from pathlib import Path

print("\n" + "="*80)
print("📊 BEST PRACTICES COMPLIANCE CHECK - v5.8.5")
print("="*80 + "\n")

# Files to check
backend_path = Path.home() / '.ki_autoagent' / 'backend'
files_to_check = [
    backend_path / 'langgraph_system' / 'workflow.py',
    backend_path / 'langgraph_system' / 'state.py',
    backend_path / 'agents' / 'specialized' / 'architect_agent.py',
    backend_path / 'agents' / 'specialized' / 'orchestrator_agent.py',
]

issues = []
warnings = []
good_practices = []

print("🔍 Checking Files:")
for f in files_to_check:
    print(f"  - {f.name}")
print()

# CHECK 1: State Immutability
print("="*80)
print("1️⃣  STATE IMMUTABILITY CHECK")
print("="*80 + "\n")

mutations_found = []
for file_path in files_to_check:
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        continue

    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    # Look for direct mutations
    mutation_patterns = [
        (r'step\.status\s*=', 'Direct step.status mutation'),
        (r'step\.result\s*=', 'Direct step.result mutation'),
        (r'state\[.+\]\s*=\s*(?!.*update_step|.*merge_state)', 'Direct state mutation (not using helpers)'),
    ]

    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        for pattern, desc in mutation_patterns:
            if re.search(pattern, line):
                # Check if it's in an OBSOLETE section
                if 'OBSOLETE' in '\n'.join(lines[max(0, i-20):i+5]):
                    continue  # Skip OBSOLETE code

                # Check if using dataclass_replace
                if 'dataclass_replace' in line or 'replace(' in line:
                    continue  # This is OK

                # Check if it's a return statement
                if 'return' in line and ('update_step' in line or 'merge_state' in line):
                    continue  # This is OK

                mutations_found.append({
                    'file': file_path.name,
                    'line': i,
                    'code': line.strip(),
                    'issue': desc
                })

if mutations_found:
    print(f"❌ Found {len(mutations_found)} potential state mutations:\n")
    for m in mutations_found[:10]:  # Show first 10
        print(f"  {m['file']}:{m['line']}")
        print(f"    Issue: {m['issue']}")
        print(f"    Code: {m['code'][:80]}...")
        print()
    issues.append(f"State Immutability: {len(mutations_found)} mutations found")
else:
    print("✅ No direct state mutations found")
    good_practices.append("State Immutability: Clean")

# CHECK 2: Reducer Pattern
print("\n" + "="*80)
print("2️⃣  REDUCER PATTERN CHECK")
print("="*80 + "\n")

state_file = backend_path / 'langgraph_system' / 'state.py'
if state_file.exists():
    with open(state_file, 'r') as f:
        content = f.read()

    # Check for custom reducer
    has_custom_reducer = 'merge_execution_steps' in content
    has_annotated = 'Annotated[List[ExecutionStep], merge_execution_steps]' in content

    if has_custom_reducer and has_annotated:
        print("✅ Custom reducer implemented correctly")
        print("  - merge_execution_steps() function exists")
        print("  - execution_plan uses Annotated with reducer")
        good_practices.append("Reducer Pattern: Implemented")
    else:
        print("❌ Reducer pattern not properly implemented")
        if not has_custom_reducer:
            print("  - Missing merge_execution_steps() function")
        if not has_annotated:
            print("  - execution_plan not using Annotated with reducer")
        issues.append("Reducer Pattern: Not properly implemented")
else:
    print("⚠️  state.py not found")
    warnings.append("Reducer Pattern: Cannot verify")

# CHECK 3: Error Handling
print("\n" + "="*80)
print("3️⃣  ERROR HANDLING CHECK")
print("="*80 + "\n")

workflow_file = backend_path / 'langgraph_system' / 'workflow.py'
if workflow_file.exists():
    with open(workflow_file, 'r') as f:
        content = f.read()

    # Check for try/except blocks in nodes
    try_count = content.count('try:')
    except_count = content.count('except')

    # Check for error state updates
    has_error_status = 'status="failed"' in content or 'status="error"' in content
    has_error_field = 'error=' in content

    print(f"Found {try_count} try blocks and {except_count} except blocks")
    if has_error_status:
        print("✅ Error status updates found")
    if has_error_field:
        print("✅ Error field updates found")

    if try_count > 5 and has_error_status and has_error_field:
        print("\n✅ Error handling appears comprehensive")
        good_practices.append("Error Handling: Comprehensive")
    else:
        print("\n⚠️  Error handling could be improved")
        warnings.append("Error Handling: Could be more comprehensive")
else:
    print("⚠️  workflow.py not found")

# CHECK 4: Hybrid Orchestrator Implementation
print("\n" + "="*80)
print("4️⃣  HYBRID ORCHESTRATOR CHECK (v5.8.5)")
print("="*80 + "\n")

orchestrator_file = backend_path / 'agents' / 'specialized' / 'orchestrator_agent.py'
if orchestrator_file.exists():
    with open(orchestrator_file, 'r') as f:
        content = f.read()

    has_validate_arch = 'def validate_architecture' in content
    has_validate_code = 'def validate_code' in content
    has_execute_llm = 'def _execute_llm_request' in content

    print("Validation Methods:")
    print(f"  - validate_architecture(): {'✅' if has_validate_arch else '❌'}")
    print(f"  - validate_code(): {'✅' if has_validate_code else '❌'}")
    print(f"  - _execute_llm_request(): {'✅' if has_execute_llm else '❌'}")

    if has_validate_arch and has_validate_code and has_execute_llm:
        print("\n✅ Hybrid Orchestrator validation methods implemented")
        good_practices.append("Hybrid Orchestrator: Implemented")
    else:
        print("\n❌ Hybrid Orchestrator validation methods missing")
        issues.append("Hybrid Orchestrator: Incomplete implementation")
else:
    print("⚠️  orchestrator_agent.py not found")

# Check workflow routing
if workflow_file.exists():
    with open(workflow_file, 'r') as f:
        content = f.read()

    has_validate_arch_mode = 'orchestrator_mode == "validate_architecture"' in content
    has_validate_code_mode = 'orchestrator_mode == "validate_code"' in content
    has_hybrid_routing = 'hybrid_validation_enabled' in content

    print("\nWorkflow Routing:")
    print(f"  - validate_architecture mode: {'✅' if has_validate_arch_mode else '❌'}")
    print(f"  - validate_code mode: {'✅' if has_validate_code_mode else '❌'}")
    print(f"  - hybrid_validation_enabled flag: {'✅' if has_hybrid_routing else '❌'}")

    if has_validate_arch_mode and has_hybrid_routing:
        print("\n✅ Hybrid Orchestrator routing implemented")
        good_practices.append("Hybrid Routing: Implemented")
    else:
        print("\n❌ Hybrid Orchestrator routing incomplete")
        issues.append("Hybrid Routing: Not implemented")

# CHECK 5: State Fields for Hybrid Pattern
print("\n" + "="*80)
print("5️⃣  HYBRID STATE FIELDS CHECK")
print("="*80 + "\n")

if state_file.exists():
    with open(state_file, 'r') as f:
        content = f.read()

    required_fields = [
        'orchestrator_mode',
        'validation_feedback',
        'validation_passed',
        'last_validated_agent',
        'validation_history'
    ]

    print("Required State Fields:")
    all_present = True
    for field in required_fields:
        present = f'{field}:' in content or f'"{field}"' in content
        print(f"  - {field}: {'✅' if present else '❌'}")
        if not present:
            all_present = False

    if all_present:
        print("\n✅ All hybrid state fields present")
        good_practices.append("Hybrid State: Complete")
    else:
        print("\n❌ Some hybrid state fields missing")
        issues.append("Hybrid State: Incomplete")

# SUMMARY
print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80 + "\n")

print(f"✅ Good Practices: {len(good_practices)}")
for gp in good_practices:
    print(f"  - {gp}")

print(f"\n⚠️  Warnings: {len(warnings)}")
for w in warnings:
    print(f"  - {w}")

print(f"\n❌ Issues: {len(issues)}")
for i in issues:
    print(f"  - {i}")

# Calculate score
total_checks = 5
passed = len(good_practices)
score = (passed / total_checks) * 100

print(f"\n📈 Compliance Score: {score:.1f}% ({passed}/{total_checks} checks passed)")

if score >= 90:
    print("\n🎉 Excellent! Code follows Best Practices")
elif score >= 70:
    print("\n✅ Good! Some minor improvements needed")
elif score >= 50:
    print("\n⚠️  Fair! Several issues to address")
else:
    print("\n❌ Poor! Major refactoring needed")

print("\n" + "="*80)
