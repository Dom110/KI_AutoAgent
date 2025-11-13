# 🎯 KI AutoAgent: Prompt Architecture & System Instructions Guide

**Version**: 1.0  
**Created**: 2025-11-02  
**Context**: Dual-level instruction hierarchy for Claude agents

---

## 📋 Executive Summary

Die KI AutoAgent nutzt eine **2-Ebenen-Instruktions-Architektur** mit Claude CLI:

1. **GLOBALE INSTRUKTIONEN** (`.ki_autoagent/`) - Wer der Agent ist (Agent-Identität & Rollen)
2. **PROJEKT-SPEZIFISCHE INSTRUKTIONEN** (`.ki_autoagent_ws/`) - Was der Agent tun soll (Task-spezifische Anweisungen)

Diese werden mittels **`--system-prompt` Flag** in Claude CLI korrekt getrennt übergeben.

---

## 🏗️ Architektur-Übersicht

### Best Practices aus Claude Docs

Basierend auf den Claude Dokumentationen:

**Prompt Improver (Prompt Engineering)**:
- ✅ Verwende **System Prompts** für Agent-Rollen & Identität
- ✅ Verwende **User Prompts** für spezifische Tasks
- ✅ Nutze **XML Tags** zur klaren Strukturierung
- ✅ Nutze **Chain-of-Thought** für komplexe Reasoning
- ✅ Nutze **Prompt Caching** für wiederholte Instructions

**Claude Code Settings**:
- ✅ Settings-Hierarchie: Enterprise → User → Project
- ✅ Memory Files (`CLAUDE.md`) enthalten Context & Instructions
- ✅ Subagents können mit eigenen Prompts definiert werden
- ✅ Permissions & Tools sind separate von Instructions

**Prompt Caching**:
- ✅ Statische Instructions am Anfang cachen (5-min TTL)
- ✅ System Prompts gehören in Cache (`cache_control` Block)
- ✅ User Prompts bleiben außerhalb für Flexibilität

---

## 🗂️ Verzeichnis-Struktur

### Global Instructions (Agent-Identität)

```
~/.ki_autoagent/
├── config/
│   └── .env              # API Keys
├── instructions/         # 🆕 Global agent instructions
│   ├── base-role.md      # Common agent identity
│   ├── architect.md      # ArchitectAgent role & capabilities
│   ├── codesmith.md      # CodeSmith role & capabilities
│   ├── reviewfix.md      # ReviewFix role & capabilities
│   ├── research.md       # Research role & capabilities
│   └── responder.md      # Responder role & capabilities
└── context/
    └── shared-patterns.md
```

### Project-Specific Instructions (Task-Context)

```
.ki_autoagent_ws/
├── instructions/        # 🆕 Project-specific task instructions
│   ├── current-task.md  # What to work on right now
│   ├── constraints.md   # Technical constraints & limitations
│   └── success-criteria.md
├── cache/               # Workflow checkpoints
├── memory/              # Project memory & decisions
└── context/
    └── workspace-analysis.md
```

---

## 📝 System Prompt Struktur (Agent-Identität)

### Format: Global Base Role

**Datei**: `~/.ki_autoagent/instructions/base-role.md`

```markdown
# Base Agent Role Template

## Identity
You are [AgentName], a [primary role] expert specializing in [specialization].

## Core Capabilities
- [Capability 1]
- [Capability 2]
- [Capability 3]

## Communication Style
- Clear and direct
- Professional but friendly
- Code-focused when applicable
- Explanatory without over-explaining

## Memory System
- Working Memory: Current task context
- Long-term Memory: Patterns, decisions, lessons learned
- Episodic Memory: Previous projects and outcomes

## Tool Access
You have access to: [Read, Edit, Bash, etc.]

## Constraints
- [Constraint 1]
- [Constraint 2]
```

### Format: Agent-Spezifische Role

**Datei**: `~/.ki_autoagent/instructions/reviewfix.md`

```markdown
# ReviewFix Agent Role

## Identity
You are ReviewFix, the quality assurance expert and bug-fixing specialist.

## Primary Responsibilities
1. Code Review: Analyze code for bugs and quality issues
2. Bug Detection: Find bugs BEFORE they cause problems
3. Fix Generation: Generate corrected code
4. Validation: Validate that fixes work correctly

## Validation Output Format
You MUST respond with valid JSON containing:
```json
{
  "validation_passed": true,      // or false
  "bugs_found": [...],            // List of bugs
  "fixes_applied": [...],         // What was fixed
  "test_results": {...},          // Test status
  "remaining_errors": []          // Any unfixed issues
}
```

## Critical Instructions
- ALWAYS return validation results as JSON (see above)
- validation_passed: true ONLY if code is correct AND tests pass
- validation_passed: false if ANY bugs remain
- Never omit the JSON response structure
```

---

## 📌 User Prompt Struktur (Task-Kontext)

### Format: Project-Spezifische Task

**Datei**: `.ki_autoagent_ws/instructions/current-task.md`

```markdown
# Current Task: [Project Name]

## Objective
[What needs to be accomplished]

## Context
- Project Type: [e.g., React Web App]
- Technology Stack: [e.g., TypeScript, FastAPI, SQLite]
- Constraints: [e.g., No external APIs, must run offline]

## Files to Review
- [File 1]: [Context/Issue]
- [File 2]: [Context/Issue]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Constraints & Limitations
- Performance: [e.g., Must complete in < 5s]
- Security: [e.g., No hardcoded secrets]
- Compatibility: [e.g., Node.js 18+]
```

---

## 🔄 Claude CLI Integration (Implementation)

### The Correct Way (Using `--system-prompt` Flag)

```python
# From: backend/adapters/claude_cli_simple.py (lines 610-642)

# ✅ CORRECT: Use --system-prompt flag
system_prompt = self._extract_system_prompt(messages)  # Global role
user_prompt = self._extract_user_prompt(messages)      # Task-specific

cmd = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Read Edit Bash",
    "--agents", json.dumps(agent_definition),
    "--output-format", "stream-json",
    "--verbose",
    "--system-prompt", system_prompt,    # 🎯 Global instructions here
    "-p", user_prompt                    # 🎯 Task-specific here
]
```

### The Wrong Way (ANTI-PATTERN)

```python
# ❌ WRONG: Combining prompts
combined_prompt = f"{system_prompt}\n\n{user_prompt}"
cmd = ["claude", ..., "-p", combined_prompt]
# PROBLEM: System instructions get diluted/lost!
```

---

## 🔗 How System Prompts Flow Through Agents

### ReviewFix Agent Example (End-to-End)

```
┌─────────────────────────────────────────┐
│ Supervisor calls ReviewFix               │
│ ├─ instructions: "Review code for bugs" │
│ └─ workspace_path: "/project/.."        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ ReviewFix Agent Server                  │
│ ├─ Loads global role from ~/.ki_autoagent/instructions/reviewfix.md
│ ├─ Builds task prompt from supervisor instructions
│ ├─ Calls: _get_system_prompt() → Global role
│ └─ Calls: _build_review_prompt() → Task-specific
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Claude CLI Server (MCP)                 │
│ ├─ system_prompt: Global ReviewFix role │
│ ├─ user_prompt: Task-specific review    │
│ └─ Calls: --system-prompt system_prompt │
│                 -p user_prompt           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Claude CLI Process                      │
│ ├─ Initializes agent with system role   │
│ ├─ Receives task via -p parameter       │
│ ├─ Returns JSON validation result       │
│ └─ validation_passed: true/false        │
└─────────────────────────────────────────┘
```

---

## 💡 Key Insights & Lessons Learned

### What We Learned from the Bug

The previous infinite loop was caused by:
- ❌ System prompt combined with user prompt in single `-p` parameter
- ❌ ReviewFix validation instructions (JSON format) were diluted
- ❌ Claude CLI didn't receive proper validation_passed format requirement
- ✅ FIX: Use `--system-prompt` flag for proper instruction passing

### Critical Requirements

1. **System Prompts MUST Include**:
   - Agent Identity & Role
   - Output Format Requirements (e.g., JSON structure)
   - Validation Instructions
   - Memory/Context Management Strategy

2. **User Prompts MUST Include**:
   - Specific Task Description
   - File Context & Paths
   - Success Criteria
   - Constraints

3. **Separation is CRITICAL**:
   - System prompts define "WHO" and "HOW TO BEHAVE"
   - User prompts define "WHAT TO DO"
   - Never merge them into single prompt!

---

## 📊 Prompt Caching Strategy

For optimal performance with repeated instructions:

### Cache Structure

```
┌─ Tools Definition (rarely changes) → CACHE
├─ System Prompt (agent role) → CACHE (5-min TTL)
├─ User Prompt (task) → NO CACHE (changes per request)
└─ Messages (conversation) → Partial cache
```

### Implementation

```python
from anthropic import Anthropic

client = Anthropic()

system_prompt_with_cache = {
    "type": "text",
    "text": global_instructions,
    "cache_control": {"type": "ephemeral"}  # 5-min cache
}

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=[system_prompt_with_cache],
    messages=[
        {"role": "user", "content": task_specific_prompt}
    ]
)
```

---

## 🚀 Implementation Checklist

- [ ] Create `~/.ki_autoagent/instructions/` directory
- [ ] Create global role files for each agent
  - [ ] `base-role.md`
  - [ ] `architect.md`
  - [ ] `codesmith.md`
  - [ ] `reviewfix.md`
  - [ ] `research.md`
  - [ ] `responder.md`
- [ ] Create `.ki_autoagent_ws/instructions/` directory
- [ ] Create project-specific instruction templates
  - [ ] `current-task.md`
  - [ ] `constraints.md`
  - [ ] `success-criteria.md`
- [ ] Update all agent servers to load from these directories
- [ ] Verify `--system-prompt` flag is used correctly in Claude CLI calls
- [ ] Test ReviewFix validation returns proper JSON
- [ ] Test full workflow with new instruction structure

---

## 📚 References

### Claude Documentation
- [Prompt Engineering Guide](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview)
- [System Prompts Best Practices](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/system-prompts)
- [Prompt Caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)
- [Claude Code Settings](https://docs.claude.com/en/docs/claude-code/settings)

### KI AutoAgent Files
- `backend/adapters/claude_cli_simple.py` (Lines 610-642: CLI command building)
- `mcp_servers/reviewfix_agent_server.py` (System prompt extraction)
- `mcp_servers/claude_cli_server.py` (Claude CLI wrapper)
- `vscode-extension/src/instructions/` (Agent instructions examples)

---

## 🎓 Summary

Die neue 2-Ebenen-Architektur ermöglicht:

1. **Saubere Separation of Concerns**
   - Global instructions = Agent identity & capabilities
   - Project instructions = Task-specific context

2. **Proper Claude CLI Usage**
   - `--system-prompt` flag für globale Instruktionen
   - `-p` parameter nur für Task-Kontext

3. **Better Maintainability**
   - Agent-Rollen zentral verwaltet
   - Tasks modular und austauschbar
   - Instruktionen versionierbar

4. **Improved Reliability**
   - Keine verlorenen System-Instruktionen
   - Validierungs-Anforderungen erreichen Claude
   - ReviewFix liefert korrekte JSON-Responses
