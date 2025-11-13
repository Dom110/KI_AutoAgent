# Claude CLI Quick Reference
**For KI AutoAgent Integration**

---

## 🎯 The 3 System Prompt Options

```bash
# 1️⃣ REPLACE (complete control)
claude --system-prompt "Custom prompt..." -p "task"

# 2️⃣ APPEND (keep Claude defaults + add yours) ⭐ RECOMMENDED
claude --append-system-prompt "Your additions..." -p "task"

# 3️⃣ FROM FILE (for team consistency)
claude --system-prompt-file ./prompt.txt -p "task"
```

---

## 📝 Examples by Use Case

### ReviewFix Agent (Code Review with Validation)
```bash
# Proper implementation
claude \
  --append-system-prompt "You are a code reviewer.
Output JSON: {validation_passed: bool, issues: [...]}" \
  -p "Review: $(cat file.py)" \
  --output-format json
```

### Architect Agent (System Design)
```bash
claude \
  --append-system-prompt "You are an architecture expert. 
Provide design decisions in XML format." \
  -p "Design a system for: $(cat requirements.txt)" \
  --output-format json
```

### Research Agent (Knowledge Gathering)
```bash
cat research_task.md | claude \
  --append-system-prompt "You are a research specialist. 
Cite sources and verify facts." \
  -p "Research this topic" \
  --output-format stream-json
```

### Codesmith Agent (Code Generation)
```bash
claude \
  --append-system-prompt "You are a code expert.
Generate production-ready code with tests." \
  -p "Implement: $(cat feature.md)" \
  --output-format json
```

---

## 🤖 Subagents - Define Custom AI Personalities

### Define via CLI (Dynamic)
```bash
claude --agents '{
  "reviewer": {
    "description": "Code review specialist",
    "prompt": "You are a senior code reviewer...",
    "model": "sonnet",
    "tools": ["Read", "Grep", "Bash"]
  },
  "debugger": {
    "description": "Debugging expert",
    "prompt": "You are a debugger...",
    "model": "opus"
  }
}' -p "Use reviewer to check my code"
```

### Define in Files (Persistent)
```bash
# User-level (all projects)
~/.claude/agents/code-reviewer.md

# Project-level (this project only)
.claude/agents/code-reviewer.md
```

**File Format:**
```markdown
---
name: code-reviewer
description: Expert code reviewer for security issues
tools: Read, Grep, Bash
model: sonnet
---

You are a senior code reviewer with expertise in security...

Review checklist:
- No hardcoded secrets
- Input validation
- Error handling
- Performance
```

---

## 📊 Output Formats

```bash
# 1. Default text (human-readable)
claude -p "query" --output-format text

# 2. JSON (structured parsing)
claude -p "query" --output-format json

# 3. Stream JSON (real-time, for WebSockets)
claude -p "query" --output-format stream-json
```

---

## 🔄 Context & Continuation

```bash
# Continue most recent conversation
claude --continue

# Resume specific session
claude --resume SESSION_ID "Continue..."

# Limit agentic turns (prevent infinite loops)
claude -p "query" --max-turns 3
```

---

## 🛠️ Advanced Flags

| Flag | Example | Purpose |
|------|---------|---------|
| `--model` | `--model opus` | Use specific model (sonnet/opus/haiku) |
| `--verbose` | `--verbose` | Show detailed turn-by-turn output |
| `--max-turns` | `--max-turns 5` | Limit agentic iterations |
| `--add-dir` | `--add-dir ../lib` | Add additional working directories |
| `--allowedTools` | `--allowedTools "Bash(git:*)"` | Pre-approve tools |
| `--permission-mode` | `--permission-mode plan` | Set permission level |

---

## 🚀 KI AutoAgent Patterns

### Pattern 1: Dual-Level Prompts (Global + Project)
```bash
# Global instructions (WHO agent is)
GLOBAL=$(cat ~/.ki_autoagent/instructions/reviewfix.md)

# Project instructions (WHAT to do)
PROJECT="Review this PR for security issues"

claude --append-system-prompt "$GLOBAL" -p "$PROJECT" --output-format json
```

### Pattern 2: Pipe Workflow (Unix Philosophy)
```bash
cat codebase.log | claude \
  --append-system-prompt "Analyze logs for errors" \
  -p "Find all ERRORs and suggest fixes" \
  --output-format json
```

### Pattern 3: Subagent Delegation
```bash
claude --agents '{
  "analyzer": {"description": "Code analyzer", "prompt": "..."},
  "implementer": {"description": "Code implementer", "prompt": "..."}
}' -p "analyzer: analyze code; then implementer: implement fixes"
```

### Pattern 4: Multi-Step with Output Capture
```bash
# Step 1: Analysis
ANALYSIS=$(claude -p "Analyze this codebase" --output-format json)

# Step 2: Generate plan
PLAN=$(claude -p "Based on analysis, create plan: $ANALYSIS" --output-format json)

# Step 3: Execute
claude -p "Execute plan: $PLAN" --output-format json
```

---

## ⚠️ Common Mistakes

### ❌ Combining prompts in `-p` (BUG)
```bash
# WRONG: System + task mixed
claude -p "You are a reviewer. Review this code: $(cat file.py)"
# Problem: System instructions lose priority
```

### ✅ Separate prompts (FIX)
```bash
# RIGHT: System and task separated
claude --system-prompt "You are a reviewer" \
       -p "Review this: $(cat file.py)"
```

---

## 🧪 Testing Your Setup

```bash
# Test 1: Basic functionality
claude -p "Hello, what's your name?"

# Test 2: JSON output
echo "1 + 1" | claude -p "Calculate" --output-format json

# Test 3: System prompt
claude --system-prompt "You are a math expert" \
       -p "What is 2 + 2?" --output-format json

# Test 4: Subagents
claude --agents '{"helper":{"description":"Helper","prompt":"Help me"}}' \
       -p "Use helper: solve 5 * 6"
```

---

## 📚 Official References

- **CLI Reference:** https://docs.claude.com/en/docs/claude-code/cli-reference
- **Subagents:** https://docs.claude.com/en/docs/claude-code/sub-agents
- **Best Practices:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices

---

## 💡 Pro Tips

1. **Use `--append-system-prompt`** - Keeps Claude Code defaults while adding your instructions
2. **Always use `--output-format json`** for MCP integration - Makes parsing reliable
3. **Put long prompts in files** - Use `--system-prompt-file` for maintainability
4. **Create team subagents** in `.claude/agents/` - Version controlled, shareable
5. **Use `--verbose`** - Helps debug when things go wrong
6. **Limit `--max-turns`** - Prevents infinite loops in automation

---

## 🔗 Integration with KI AutoAgent

### Current Architecture
```
Supervisor (GPT-4o)
  ↓
Claude CLI (via MCP servers)
  ├─ ReviewFix Agent
  ├─ Architect Agent  
  ├─ Codesmith Agent
  └─ Research Agent
```

### With New Subagents Feature
```
Claude Code (Interactive + CLI)
  ├─ Subagent: code-reviewer
  ├─ Subagent: architect
  ├─ Subagent: implementer
  └─ Subagent: research
```

**Benefit:** No separate MCP servers needed for simple tasks, faster context switches, specialized tools per agent!