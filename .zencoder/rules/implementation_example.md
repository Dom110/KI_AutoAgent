# 🔧 Implementation Example: Loading Global & Project Instructions

**Version**: 1.0  
**Focus**: Practical code examples for dual-level instruction loading

---

## 📂 File Organization Example

### Step 1: Create Global Instructions

Create this directory structure under `~/.ki_autoagent/instructions/`:

```bash
mkdir -p ~/.ki_autoagent/instructions/
```

**File**: `~/.ki_autoagent/instructions/reviewfix.md`

```markdown
# ReviewFix Agent - Global Role Definition

## Identity
You are ReviewFix, a meticulous code review and quality assurance expert.

## Core Capabilities
1. **Bug Detection**: Find logical errors, edge cases, and runtime issues
2. **Code Quality**: Assess readability, maintainability, and design
3. **Security Analysis**: Identify vulnerabilities and security issues
4. **Performance Review**: Detect bottlenecks and optimization opportunities
5. **Fix Generation**: Provide corrected code with explanations
6. **Validation**: Verify fixes work correctly with tests

## Validation Output Format (CRITICAL)
You MUST respond with valid JSON:

\`\`\`json
{
  "validation_passed": true,        // Boolean: true ONLY if all checks pass
  "bugs_found": [
    {
      "file": "src/app.js",
      "line": 42,
      "bug": "Missing null check",
      "severity": "high",
      "fix": "Add if (user) check"
    }
  ],
  "fixes_applied": [
    "Added null check on line 42",
    "Implemented error handling in catch block"
  ],
  "test_results": {
    "unit_tests": "PASS (5/5)",
    "integration_tests": "PASS (3/3)"
  },
  "remaining_errors": [],
  "summary": "Code review complete. All issues fixed and tests pass."
}
\`\`\`

## Validation Rules
- validation_passed: true ONLY if:
  - NO bugs found in code
  - ALL tests pass
  - Code follows best practices
  - All requirements met
- validation_passed: false if:
  - ANY bug found
  - ANY test fails
  - Code quality issues exist
  - Requirements not fully met

## Tool Access
- Read: View project files
- Edit: Modify files to fix issues
- Bash: Run tests and validation commands

## Response Style
- Be thorough but concise
- Explain what's wrong and why
- Always provide working fixes
- Always validate fixes work before returning

## Remember
Your primary mission: FIND AND FIX BUGS. Never return validation_passed=true unless you're 100% certain.
```

### Step 2: Create Project-Specific Instructions

Create this directory structure under `.ki_autoagent_ws/instructions/`:

```bash
mkdir -p .ki_autoagent_ws/instructions/
```

**File**: `.ki_autoagent_ws/instructions/current-task.md`

```markdown
# Current Task: ReviewFix Generated Code

## Context
- Generated files need validation and bug fixing
- Project: React Web App with FastAPI Backend
- Tech Stack: TypeScript, React, FastAPI, SQLite

## Files to Review
- `src/App.tsx`: Main component (generated)
- `src/api/client.ts`: API client (generated)
- `tests/app.test.ts`: Unit tests (generated)

## What to Do
1. Review the generated code for bugs
2. Identify any issues (logic errors, security, performance)
3. Fix all issues
4. Run tests to validate fixes
5. Return validation result in JSON format

## Success Criteria
- [ ] All code reviewed without errors
- [ ] All bugs fixed
- [ ] Tests pass (100%)
- [ ] JSON validation response returned
- [ ] validation_passed: true or false with explanation

## File Paths (ABSOLUTE)
- Workspace: /Users/dev/my-project/.ki_autoagent_ws
- Generated files: /Users/dev/my-project/src/generated/
- Tests: /Users/dev/my-project/tests/

## Important Notes
- Do NOT modify production files
- Only review generated code
- Return validation JSON, nothing else
```

---

## 🐍 Python Implementation

### Method 1: Agent Server (Load Global + Project Instructions)

```python
# File: mcp_servers/reviewfix_agent_server.py
# Location: _get_system_prompt() method

import os
from pathlib import Path

def _get_system_prompt(self) -> str:
    """
    Load ReviewFix system prompt from global instructions.
    
    Loading order:
    1. Load global role from ~/.ki_autoagent/instructions/reviewfix.md
    2. Load project context from .ki_autoagent_ws/instructions/current-task.md
    3. Combine into final system prompt
    """
    
    # Step 1: Load global role (who is ReviewFix?)
    home = Path.home()
    global_instructions_path = home / ".ki_autoagent" / "instructions" / "reviewfix.md"
    
    if global_instructions_path.exists():
        with open(global_instructions_path) as f:
            global_role = f.read()
        logger.info(f"✅ Loaded global ReviewFix role: {len(global_role)} chars")
    else:
        logger.warning(f"⚠️ Global instructions not found: {global_instructions_path}")
        global_role = """You are ReviewFix, a code review expert.
        Review code for bugs, security issues, and quality problems.
        Return JSON with validation_passed: true/false"""
    
    # Step 2: Load project-specific context (what is the current task?)
    project_instructions_path = Path(".ki_autoagent_ws/instructions/current-task.md")
    
    if project_instructions_path.exists():
        with open(project_instructions_path) as f:
            project_context = f.read()
        logger.info(f"✅ Loaded project context: {len(project_context)} chars")
    else:
        project_context = ""
    
    # Step 3: Combine into final system prompt
    system_prompt = f"""{global_role}

## Current Project Context
{project_context}

---

## Implementation Notes
- Global role defines WHO you are and HOW to behave
- Project context defines WHAT to do RIGHT NOW
- Always return JSON validation response
- Use the JSON format defined above
"""
    
    logger.info(f"📋 Final system prompt: {len(system_prompt)} chars")
    return system_prompt


def _build_review_prompt(
    self,
    instructions: str,
    generated_files: list,
    validation_errors: list,
    iteration: int
) -> str:
    """
    Build user prompt for ReviewFix task.
    
    This becomes the USER PROMPT (passed with -p flag),
    separate from the SYSTEM PROMPT (passed with --system-prompt flag).
    """
    
    # Step 1: Load project-specific constraints
    constraints_path = Path(".ki_autoagent_ws/instructions/constraints.md")
    constraints = ""
    if constraints_path.exists():
        with open(constraints_path) as f:
            constraints = f.read()
    
    # Step 2: Build task-specific prompt
    prompt = f"""## Review Instructions
{instructions}

## Iteration
This is iteration {iteration} of the review process.

## Generated Files to Review
{self._format_file_list(generated_files)}

## Validation Errors from Previous Run
{self._format_errors(validation_errors)}

## Technical Constraints
{constraints}

## Your Task
1. Analyze all generated files above
2. Identify any bugs or issues
3. Fix the issues by modifying files
4. Run tests to validate fixes
5. Return JSON response with results

Remember: ALWAYS return JSON validation response!
"""
    
    return prompt
```

### Method 2: Claude CLI Wrapper (Use --system-prompt Flag)

```python
# File: backend/adapters/claude_cli_simple.py
# Location: _call_cli_sync() method

import subprocess
import json
from pathlib import Path

def _call_cli_sync(self, messages: list) -> dict:
    """
    Call Claude CLI with proper system prompt separation.
    
    CRITICAL: Use --system-prompt flag for system instructions!
    """
    
    # Extract system and user prompts
    system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)
    
    # Log prompt sizes
    logger.info(f"📋 System prompt: {len(system_prompt)} chars")
    logger.info(f"📋 User prompt: {len(user_prompt)} chars")
    
    # Build agent definition
    agent_definition = {
        self.agent_name: {
            "description": self.agent_description,
            "prompt": "You are a helpful assistant.",  # Minimal prompt
            "tools": self.agent_tools
        }
    }
    
    # ✅ CORRECT: Use --system-prompt flag
    cmd = [
        self.cli_path,
        "--model", self.model,
        "--permission-mode", self.permission_mode,
        "--allowedTools", " ".join(self.allowed_tools),
        "--agents", json.dumps(agent_definition),
        "--output-format", "stream-json",
        "--verbose",
        "--system-prompt", system_prompt,  # 🎯 Global instructions
        "-p", user_prompt                 # 🎯 Task-specific
    ]
    
    logger.debug(f"Calling Claude CLI with proper prompt separation")
    logger.debug(f"  System prompt: {len(system_prompt)} chars")
    logger.debug(f"  User prompt: {len(user_prompt)} chars")
    
    # Execute Claude CLI
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=self.workspace_path
        )
        
        # Parse response (details omitted for brevity)
        return self._parse_response(result.stdout, result.stderr)
        
    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timeout after 300 seconds")
        raise
    except Exception as e:
        logger.error(f"Claude CLI error: {e}")
        raise
```

### Method 3: Supervisor (Pass Instructions to ReviewFix)

```python
# File: mcp_servers/supervisor_agent_server.py
# Location: _route_to_agent() method

async def _route_to_reviewfix(
    self,
    generated_files: list,
    validation_errors: list,
    iteration: int = 1
) -> dict:
    """
    Route to ReviewFix agent with proper task instructions.
    """
    
    # Build instructions (will be user prompt)
    instructions = f"""Please review the following generated code:

{self._format_files_for_review(generated_files)}

Previous validation errors to fix:
{self._format_errors(validation_errors)}

This is iteration {iteration} of the fix process. 
Fix all issues and return validation_passed: true when complete."""
    
    # Call ReviewFix via MCP
    reviewfix_result = await self.client.call_tool(
        "review_and_fix",
        arguments={
            "instructions": instructions,  # User prompt
            "generated_files": generated_files,
            "validation_errors": validation_errors,
            "workspace_path": self.workspace_path,
            "iteration": iteration
        }
    )
    
    return reviewfix_result
```

---

## 🧪 Testing the Implementation

### Test 1: Verify System Prompt is Loaded

```bash
# Enable DEBUG mode
DEBUG_MODE=true python debug_prompts_sent_to_claude.py

# Output should show:
# ✅ Global ReviewFix role loaded: 2543 chars
# ✅ Project context loaded: 1234 chars
# 📋 Final system prompt: 3777 chars
```

### Test 2: Verify ReviewFix Returns JSON

```bash
python debug_reviewfix_validation_logic.py

# Output should show:
# ReviewFix Response:
# {
#   "validation_passed": true,
#   "bugs_found": [],
#   "fixes_applied": [...],
#   "test_results": {"unit_tests": "PASS"},
#   "remaining_errors": [],
#   "summary": "All checks passed"
# }
```

### Test 3: Verify Full Workflow

```bash
# Create test workspace
python -c "
from pathlib import Path
Path('test_project/.ki_autoagent_ws/instructions').mkdir(parents=True, exist_ok=True)
"

# Run E2E test
python e2e_test_v7_0_supervisor.py

# Should complete without infinite loops
```

---

## 📊 Comparison: Before vs After

### ❌ BEFORE (Bug: Combined Prompts)

```python
# Problem: System instructions diluted
combined = f"{system_prompt}\n\n{user_prompt}"
cmd = ["claude", "-p", combined]
# Result: validation_passed always false (instructions lost)
```

```
System Prompt (LOST):
- ReviewFix identity
- JSON format requirement
- Validation rules
- validation_passed guidance

User Prompt (ALL MIXED IN):
- Task description
- File context
- Error list
```

### ✅ AFTER (Fix: Separated Prompts)

```python
# Solution: Proper separation
cmd = ["claude", 
       "--system-prompt", system_prompt,
       "-p", user_prompt]
# Result: validation_passed works correctly
```

```
System Prompt (PRESERVED):
├─ ReviewFix identity ✅
├─ JSON format requirement ✅
├─ Validation rules ✅
└─ validation_passed guidance ✅

User Prompt (CLEAR):
├─ Task description ✅
├─ File context ✅
└─ Error list ✅
```

---

## 🎯 Key Takeaways

1. **Two-Level Loading**
   - Load global instructions from `~/.ki_autoagent/instructions/`
   - Load project context from `.ki_autoagent_ws/instructions/`
   - Combine them into final system prompt

2. **Proper CLI Usage**
   - `--system-prompt` flag for global instructions
   - `-p` parameter for task-specific prompts
   - NEVER combine them!

3. **Prompt Structure**
   - System prompt = WHO am I? HOW should I behave?
   - User prompt = WHAT should I do?
   - Clear separation = Better Claude understanding

4. **Testing**
   - Verify prompts are loaded correctly
   - Check JSON responses are valid
   - Test full workflow end-to-end

---

## 📚 Next Steps

1. Create global instruction files
2. Create project instruction templates
3. Update agent servers to load from new structure
4. Test with ReviewFix validation
5. Monitor for validation_passed working correctly
6. Expand to other agents (Architect, CodeSmith, etc.)
