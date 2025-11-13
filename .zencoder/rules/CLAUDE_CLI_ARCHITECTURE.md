# Claude CLI Architecture für KI AutoAgent
**Based on:** Official Claude Docs (v2.0+)  
**Last Updated:** 2025-01-12  
**Status:** READY FOR IMPLEMENTATION

---

## 📋 Executive Summary

KI AutoAgent kann die **neuen Claude Code Subagents-Feature** nutzen, um:
- ✅ Spezialisierte Agenten mit separaten Context Windows zu schaffen
- ✅ Flexible System Prompts (`--system-prompt`, `--append-system-prompt`)
- ✅ Strukturierte JSON-Ausgaben (`--output-format json/stream-json`)
- ✅ Team-spezifische Konfigurationen (`.claude/agents/`)

---

## 🎯 Die Richtige CLI-Verwendung

### ❌ Falsch (aktueller Fehler)
```bash
# PROBLEM: System prompt + user prompt vermischt in -p
claude -p "You are a reviewer. Please review: $(cat code.py)"
# Result: System instructions verlieren Priorität, Validierungsformat wird nicht befolgt
```

### ✅ Richtig (nach Anthropic Docs)
```bash
# LÖSUNG 1: Separate Prompts mit --system-prompt
claude \
  --system-prompt "You are a code reviewer specializing in security..." \
  -p "Review this code for vulnerabilities: $(cat code.py)" \
  --output-format json

# LÖSUNG 2: Append zur Standard-Claude-Prompt (EMPFOHLEN für CLI)
claude \
  --append-system-prompt "You are a code reviewer. Output must be JSON: {validation_passed: bool, issues: [...]}" \
  -p "Review this code: $(cat code.py)" \
  --output-format json

# LÖSUNG 3: Subagent für spezialisierte Aufgaben
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer for security issues",
    "prompt": "You are a senior code reviewer...",
    "model": "sonnet"
  }
}' -p "Use code-reviewer: Review this code"
```

---

## 🏗️ Empfohlene Architektur für KI AutoAgent

### Option A: Subagents (Neu, empfohlen)

**Vorteil:** Separate Context Windows, spezialisierte Tools, weniger MCP Server nötig

```
┌─ Supervisor (Claude Code Interactive)
│
├─ Agent: Reviewer (Subagent)
│  ├─ Model: sonnet
│  ├─ Tools: Read, Grep, Bash
│  └─ Prompt: Code review expertise
│
├─ Agent: Architect (Subagent)
│  ├─ Model: opus
│  ├─ Tools: Read, Write, Bash
│  └─ Prompt: Architecture design expertise
│
└─ Agent: Codesmith (Subagent)
   ├─ Model: sonnet
   ├─ Tools: Read, Write, Bash, Edit
   └─ Prompt: Code generation expertise
```

**Implementation als JSON:**
```bash
claude --agents '{
  "reviewer": {
    "description": "Code review specialist for security and performance",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Bash"],
    "model": "sonnet"
  },
  "architect": {
    "description": "System architecture and design expert",
    "prompt": "You are an architecture expert...",
    "tools": ["Read", "Write", "Bash"],
    "model": "opus"
  },
  "codesmith": {
    "description": "Code generation and implementation specialist",
    "prompt": "You are a code generation expert...",
    "tools": ["Read", "Write", "Edit", "Bash"],
    "model": "sonnet"
  }
}' -p "reviewer: Review this PR for issues"
```

### Option B: Hybrid (MCP + Subagents)

**Vorteil:** Kombiniert MCP für Complex Tasks mit Subagents für einfache Tasks

```
MCP Servers (für komplexe Orchestration):
├─ supervisor_server.py          # Main orchestrator
│  └─ Routes zu Subagents oder MCP Servers
├─ research_agent_server.py      # WebSearch, Knowledge
└─ perplexity_server.py          # External API

Claude Code Subagents (für spezialisierteste Tasks):
├─ code-reviewer
├─ debugger
└─ code-optimizer
```

---

## 🔧 Praktische Implementation für ReviewFix

### Szenario: ReviewFix validiert Code und gibt JSON zurück

**Before (Broken):**
```python
# Problem: System instructions verloren
cmd = [
    "claude",
    "-p",  # BEIDES vermischt!
    f"You are a code reviewer.\n\n"
    f"Code to review:\n{code}\n\n"
    f"Output JSON: {{validation_passed: bool, issues: []}}"
]
# Result: validation_passed ist IMMER false → infinite loops!
```

**After (Fixed):**
```python
import subprocess
import json

def review_code_with_claude(code: str) -> dict:
    """ReviewFix using Claude CLI with proper prompt separation."""
    
    # Global instructions (WHO: Reviewer role, capabilities, FORMAT)
    system_prompt = """You are a code review expert specializing in Python.

Your responsibilities:
1. Analyze code for bugs, security issues, performance problems
2. Check PEP 8 compliance
3. Validate error handling

Output format is strict JSON (no markdown, no extra text):
{
  "validation_passed": true/false,
  "issues": [
    {"severity": "critical/warning/info", "description": "..."}
  ],
  "score": 1-10
}

CRITICAL: Response must be valid JSON only."""

    # Project-specific instructions (WHAT: This task)
    user_prompt = f"""Review this code for bugs and issues:

```python
{code}
```

Respond with JSON only."""

    cmd = [
        "claude",
        "--append-system-prompt", system_prompt,  # ✅ GLOBAL instructions
        "-p", user_prompt,                         # ✅ TASK instructions
        "--output-format", "json"                  # ✅ Structured output
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {
                "validation_passed": False,
                "error": result.stderr
            }
    except json.JSONDecodeError:
        return {
            "validation_passed": False,
            "error": "Invalid JSON response from Claude"
        }

# Usage
code = """
def divide(a, b):
    return a / b  # BUG: No zero check!
"""

result = review_code_with_claude(code)
print(result)
# Output:
# {
#   "validation_passed": false,
#   "issues": [
#     {"severity": "critical", "description": "Division by zero not handled"}
#   ],
#   "score": 3
# }
```

---

## 📁 File Organization

### Option 1: Global Subagents (User-level)
```bash
~/.claude/agents/
├─ code-reviewer.md
├─ debugger.md
├─ architect.md
└─ codesmith.md
```

### Option 2: Project-level Subagents (Team-specific)
```bash
.claude/agents/
├─ reviewfix-v2.md
├─ architect-v2.md
└─ research-agent.md
```

### Subagent File Format
```markdown
---
name: code-reviewer
description: Expert code reviewer for security and performance issues
tools: Read, Grep, Bash
model: sonnet
---

You are a senior code reviewer with 10+ years experience in Python.

When reviewing code:
1. Run git diff to see changes
2. Focus on security issues first
3. Check for performance problems
4. Validate error handling

Review checklist:
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Error handling complete
- [ ] No unhandled exceptions

Output format for each issue:
- Severity: critical/warning/suggestion
- Location: file:line
- Problem: Description
- Fix: Specific solution
```

---

## ⚙️ MCP Server Integration

### ReviewFix MCP Server (Updated)
```python
# mcp_servers/reviewfix_agent_server.py

from mcp.server import Server
import subprocess
import json

server = Server("reviewfix_agent")

@server.call_tool()
async def review_code(code: str, context: str = "") -> str:
    """Call Claude CLI with proper prompt separation."""
    
    # Load global instructions
    with open(
        Path.home() / ".ki_autoagent/instructions/reviewfix.md"
    ) as f:
        global_instructions = f.read()
    
    # Build command with PROPER prompt separation
    cmd = [
        "claude",
        "--append-system-prompt", global_instructions,
        "-p", f"Code context:\n{context}\n\nReview this code:\n{code}",
        "--output-format", "json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        # Parse structured JSON response
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "validation_passed": False,
            "error": f"Failed to parse Claude response: {result.stderr}"
        }

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

---

## 🎯 Key Differences: Old vs New

| Aspekt | Alt (Bug) | Neu (Fix) | Vorteil |
|--------|----------|----------|---------|
| **Prompt Separation** | Combined in `-p` | `--system-prompt` + `-p` | System instructions preserved |
| **Role Definition** | In user prompt | In `--system-prompt` | Role not diluted by task |
| **Output Format** | Plain text | `--output-format json` | Parseable, structured |
| **Specialization** | Single large prompt | Subagents | Focused, isolated context |
| **Model Selection** | Fixed | `--agents` per role | Optimized per task |
| **Validation** | Always false (bug) | True/False correctly | No infinite loops |

---

## 🧪 Testing Strategy

### Test 1: Basic Prompt Separation
```bash
# Global instructions
GLOBAL="You are a code reviewer. Always output JSON."

# Test command
claude \
  --system-prompt "$GLOBAL" \
  -p "Review: def foo(): pass" \
  --output-format json | jq .
```

### Test 2: ReviewFix Validation Loop
```python
# test_reviewfix_cli.py
import subprocess
import json

def test_validation_detection():
    """Ensure ReviewFix correctly identifies bugs."""
    
    buggy_code = """
def divide(a, b):
    return a / b  # BUG: No zero check!
"""
    
    system_prompt = """You are a code reviewer.
Output JSON: {validation_passed: bool, issues: []}"""
    
    cmd = [
        "claude",
        "--system-prompt", system_prompt,
        "-p", f"Review this code:\n{buggy_code}",
        "--output-format", "json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    # BEFORE (BUG): Always False
    # AFTER (FIX): Should be False for buggy code
    assert data["validation_passed"] == False
    assert len(data["issues"]) > 0
    print("✓ Correctly detected bugs")

def test_clean_code_validation():
    """Ensure ReviewFix correctly accepts clean code."""
    
    clean_code = """
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
"""
    
    # ... same setup ...
    
    # AFTER (FIX): Should be True for clean code
    assert data["validation_passed"] == True
    print("✓ Correctly accepted clean code")
```

---

## 📊 Migration Roadmap

### Phase 1: Update CLAUDE_BEST_PRACTICES.md ✅
- ✅ Document correct `--system-prompt` usage
- ✅ Document `--agents` (subagents)
- ✅ Document `--output-format` options

### Phase 2: Update ReviewFix Agent
- [ ] Implement proper prompt separation
- [ ] Use `--append-system-prompt` for global role
- [ ] Use `-p` for task-specific instructions
- [ ] Parse JSON output correctly

### Phase 3: Create Subagent Files
- [ ] `~/.claude/agents/code-reviewer.md`
- [ ] `~/.claude/agents/architect.md`
- [ ] `~/.claude/agents/codesmith.md`

### Phase 4: Test & Validate
- [ ] Unit tests for prompt separation
- [ ] Integration tests for ReviewFix workflow
- [ ] E2E tests for supervisor routing

---

## 🔗 Official References

- **CLI Reference:** https://docs.claude.com/en/docs/claude-code/cli-reference
- **Subagents Guide:** https://docs.claude.com/en/docs/claude-code/sub-agents
- **Prompt Best Practices:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- **System Prompts:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/system-prompts

---

## ⚡ Quick Reference

```bash
# System prompt (global role)
--system-prompt "You are..."

# Append to default (add instructions, keep defaults)
--append-system-prompt "Also, always..."

# User prompt (task)
-p "Analyze this..."

# Output format
--output-format json|text|stream-json

# Subagents
--agents '{"reviewer": {...}}'

# All together (ReviewFix pattern)
claude \
  --append-system-prompt "$(cat ~/.ki_autoagent/instructions/reviewfix.md)" \
  -p "Review: $(cat code.py)" \
  --output-format json
```