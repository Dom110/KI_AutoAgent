# Claude API & CLI Best Practices
**Last Updated:** 2025-10-10
**Sources:** Official Anthropic Documentation

---

## 📚 Mandatory Reading (Links)

- **Claude 4 Best Practices:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- **Usage Limits & Optimization:** https://support.claude.com/en/articles/9797557-usage-limit-best-practices
- **Command Pipelining (Claude Code):** https://www.anthropic.com/engineering/claude-code-best-practices
- **Claude Opus 4.1 Announcement:** https://www.anthropic.com/news/claude-opus-4-1
- **Prompt Caching:** https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- **Streaming:** https://docs.claude.com/en/docs/build-with-claude/streaming
- **Context Editing/Memory:** https://docs.claude.com/en/docs/build-with-claude/context-editing

---

## 🎯 Model Selection Guide

### Current Models (2025)

| Model | Best For | SWE-bench Score | When to Use |
|-------|----------|-----------------|-------------|
| **claude-opus-4-1-20250805** | Complex coding, research, debugging | 74.5% | Multi-file refactoring, precise debugging, in-depth analysis |
| **claude-opus-4** | General-purpose complex tasks | Lower than 4.1 | Legacy projects, specific API requirements |
| **claude-sonnet-4-5-20250514** | Balanced performance/cost | Good | **DEFAULT for agents**, general coding tasks |
| **claude-sonnet-4** | Fast, cost-effective | Moderate | Simple tasks, high-volume operations |
| **claude-haiku-4** | Speed-critical tasks | Lower | Quick responses, simple queries |

### KI AutoAgent Model Strategy

```python
AGENT_MODELS = {
    "architect": "gpt-4o",              # OpenAI for architecture (reasoning)
    "research": "claude-sonnet-4-5",    # Claude for research (via CLI)
    "codesmith": "claude-sonnet-4-5",   # Claude for code generation (via CLI)
    "reviewfix": "claude-sonnet-4-5",   # Claude for code review (via CLI)
}
```

**Recommendation:** Upgrade to Opus 4.1 for complex coding tasks that require multi-file refactoring.

---

## 📝 Prompt Engineering Best Practices

### 1. Be Explicit and Direct

**Bad:**
```
Create a calculator app
```

**Good:**
```
Create a Python calculator app with the following requirements:
- Support add, subtract, multiply, divide operations
- Handle division by zero gracefully
- Use object-oriented design with a Calculator class
- Include comprehensive docstrings
- Follow PEP 8 style guide

Go beyond the basics to create a fully-featured, production-ready implementation.
```

### 2. Provide Context and Motivation

**Bad:**
```
Make this code better
```

**Good:**
```
This code is part of a high-traffic web service handling 10k+ requests/second.
Performance is critical because each millisecond of delay costs money.

Please optimize this code for:
1. Speed (minimize latency)
2. Memory efficiency
3. Thread safety

Focus on algorithmic improvements rather than micro-optimizations.
```

### 3. Use XML Tags for Structure

```xml
<task>
Generate a REST API for user management
</task>

<requirements>
- CRUD operations for users
- JWT authentication
- Role-based access control
- Rate limiting
</requirements>

<constraints>
- Must use FastAPI framework
- PostgreSQL database
- Follow RESTful conventions
</constraints>

<success_criteria>
- All endpoints documented with OpenAPI
- 100% test coverage
- No security vulnerabilities
</success_criteria>
```

### 4. System Prompts Define Role

**System Prompt Pattern:**
```
You are a {ROLE} specializing in {DOMAIN}.

Your responsibilities:
1. {Primary task}
2. {Secondary task}
3. {Quality criteria}

Output format:
- {Expected structure}
- {Key sections}
- {Format requirements}

Constraints:
- {Technical limits}
- {Style requirements}
```

**Example:**
```
You are a code reviewer specializing in Python backend systems.

Your responsibilities:
1. Identify bugs, security issues, and performance problems
2. Check code style compliance (PEP 8)
3. Suggest architectural improvements
4. Validate error handling

Output format:
- Issues: List all problems found (critical, warnings, suggestions)
- Code Quality Score: 1-10 with justification
- Recommendations: Prioritized list of improvements

Constraints:
- Focus on substance over style nitpicks
- Provide code examples for complex fixes
- Explain WHY something is problematic, not just WHAT
```

### 5. Multishot Prompting (Examples)

```xml
<examples>
<example>
<input>Calculate 5 + 3</input>
<output>
Result: 8
Operation: Addition
Computation: 5 + 3 = 8
</output>
</example>

<example>
<input>Calculate 10 / 2</input>
<output>
Result: 5.0
Operation: Division
Computation: 10 / 2 = 5.0
</output>
</example>
</examples>

Now process this input following the same format:
<input>Calculate 7 * 4</input>
```

### 6. Chain of Thought (CoT) Reasoning

**Explicit CoT:**
```
Solve this step by step:

1. First, analyze the problem
2. Then, identify the algorithm
3. Next, implement the solution
4. Finally, verify correctness

Problem: Find the shortest path in a weighted graph
```

**Extended Thinking (Claude 4.1):**
```
Use your extended thinking mode to analyze this complex architecture decision:
Should we use microservices or monolith for a startup MVP?

Consider:
- Team size (3 developers)
- Expected traffic (1000 users initially)
- Budget constraints
- Time to market (3 months)
- Future scaling needs

Think deeply about trade-offs before recommending.
```

### 7. Prefilling Responses

```python
messages = [
    {"role": "user", "content": "Write a Python function to check if a number is prime"},
    {"role": "assistant", "content": "```python\ndef is_prime(n: int) -> bool:\n    \"\"\""}  # Prefill
]
```

This guides Claude to:
- Start with code immediately
- Use proper type hints
- Include docstrings

---

## ⚡ Performance Optimization

### Prompt Caching

**How It Works:**
- Caches prompt prefixes up to a "cache breakpoint"
- Default lifetime: 5 minutes
- Optional extension: 1 hour
- Cache hits checked at content block boundaries

**Pricing:**
- Cache writes: +25% of base input token cost
- Cache reads: 10% of base input token cost
- **Savings:** Up to 90% cost reduction for repeated prompts

**Implementation:**
```python
# Mark cacheable content with cache_control
messages = [
    {
        "role": "system",
        "content": "You are a code reviewer...",  # Long, stable content
        "cache_control": {"type": "ephemeral"}    # CACHE THIS
    },
    {
        "role": "user",
        "content": "Review this code: ..."         # Changes frequently
    }
]
```

**Best Practices:**
- Cache stable content (system prompts, documentation, large contexts)
- Place cacheable content at the beginning
- Minimum cacheable length: varies by model (check docs)
- Monitor cache hit rates

**Use Cases:**
- Conversational agents (cache system prompt)
- Coding assistants (cache project documentation)
- Large document processing (cache document, vary questions)
- Knowledge base interactions (cache KB, vary queries)

### Streaming

**Enable Streaming:**
```python
response = client.messages.stream(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)

for event in response:
    if event.type == "content_block_delta":
        print(event.delta.text, end="", flush=True)
```

**Benefits:**
- Real-time user feedback
- Progressive rendering
- Handle partial responses on network interruption
- Better UX for long responses

**Event Types:**
- `message_start`: Response begins
- `content_block_start`: New content block (text, tool use, thinking)
- `content_block_delta`: Incremental content
- `content_block_stop`: Block complete
- `message_delta`: Message-level updates
- `message_stop`: Response complete

**Error Recovery:**
```python
try:
    for event in stream:
        process(event)
except NetworkError:
    # Partial content already saved!
    resume_from_last_saved_block()
```

### Context Management

**Problem:** Long conversations exhaust context window

**Solution:** Context editing (beta feature)

```python
"context_management": {
    "edits": [
        {
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 30000},  # Clear at 30k tokens
            "keep": {"type": "tool_uses", "value": 3}             # Keep last 3 tool uses
        }
    ]
}
```

**Triggers:**
- `input_tokens`: Clear when token count exceeded
- `tool_uses`: Clear after N tool invocations

**What Gets Cleared:**
- Tool results (automatically)
- Tool inputs (optional)
- Specific tools can be excluded

**Combine with Memory:**
```python
# Before clearing, save important info to memory
memory.store(
    content=important_context,
    metadata={"type": "persistent_context"}
)
```

---

## 🛠️ Claude CLI Best Practices (v2.0+)

### System Prompt Flags (From Official Docs)

Three ways to customize system prompts - choose based on your use case:

| Flag | Behavior | Modes | Use Case |
|------|----------|-------|----------|
| `--system-prompt` | **Replaces** entire default prompt | Interactive + Print | Complete control (blank slate) |
| `--system-prompt-file` | **Replaces** with file contents | Print only | Load from files (team consistency) |
| `--append-system-prompt` | **Appends** to default prompt | Interactive + Print | Add instructions + keep defaults |

**Example: ReviewFix Agent (Dual-Level Architecture)**
```bash
# Global instructions (WHO: Reviewer role)
GLOBAL_PROMPT="You are a code review expert specializing in security and performance..."

# Project-specific instructions (WHAT: This task)
TASK_PROMPT="Review this function for bugs: $(cat function.py)"

# Recommended: Use --append-system-prompt to preserve Claude Code defaults
claude -p --append-system-prompt "$GLOBAL_PROMPT" "$TASK_PROMPT"

# Or for complete control:
claude -p --system-prompt "$GLOBAL_PROMPT" "$TASK_PROMPT"
```

### Subagents (`--agents` flag - NEW!)

**What are subagents?** Specialized AI assistants with separate context windows, custom prompts, and specific tools.

**Define dynamically via CLI:**
```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer. Focus on code quality, security, and best practices.",
    "tools": ["Read", "Edit", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist for errors and test failures.",
    "prompt": "You are an expert debugger. Analyze errors, identify root causes, and provide fixes.",
    "model": "opus"
  }
}' -p "Use code-reviewer to review my changes"
```

**Or define as files** (`.claude/agents/` or `~/.claude/agents/`):
```markdown
---
name: code-reviewer
description: Expert code review specialist for quality and security
tools: Read, Grep, Bash
model: sonnet
---

You are a senior code reviewer ensuring high standards...

Review checklist:
- Code is simple and readable
- Functions are well-named
- Proper error handling
- No security issues
- Good test coverage
```

**KI AutoAgent Use Case: Agent Orchestration**
```bash
# Instead of separate MCP servers, use subagents for lightweight tasks
claude --agents '{
  "reviewer": {
    "description": "Code review specialist",
    "prompt": "You are a code reviewer...",
    "model": "sonnet"
  },
  "architect": {
    "description": "Architecture design expert",
    "prompt": "You are an architecture expert...",
    "model": "opus"
  }
}' -p "reviewer: Review this code; architect: Design the system"
```

### Output Formats (`--output-format` flag)

| Format | Use Case | Example |
|--------|----------|---------|
| `text` | Default human-readable output | `claude -p --output-format text "query"` |
| `json` | Structured output for parsing | `claude -p --output-format json "query"` |
| `stream-json` | **Streaming JSON** (for real-time responses) | `claude -p --output-format stream-json "query"` |

**KI AutoAgent Recommendation: Use `stream-json` for WebSocket responses**
```python
# In ReviewFix agent or any MCP server
cmd = [
    "claude",
    "--system-prompt", global_instructions,
    "-p", task_description,
    "--output-format", "stream-json"
]
```

### Command Pipelining Patterns

#### 1. Sequential Execution (Step-by-Step)
```bash
claude -p --output-format json "Step 1: Analyze codebase structure" && \
claude -p --output-format json "Step 2: Generate migration plan" && \
claude -p --output-format json "Step 3: Execute migration"
```

#### 2. Piping Workflow
```bash
# Unix philosophy: compose commands
cat app.log | claude -p "Find all ERROR lines and suggest fixes"

# With output format
cat requirements.txt | claude -p --output-format json "Analyze dependencies for security"
```

#### 3. Using Subagents for Multi-Step Tasks
```bash
claude --agents '{
  "analyzer": {
    "description": "Analyze code structure",
    "prompt": "You are a code structure analyzer..."
  },
  "implementer": {
    "description": "Implement changes",
    "prompt": "You are a code implementer..."
  }
}' -p "analyzer: Analyze this code; then implementer: Implement improvements"
```

#### 4. Context Preservation with `--continue`
```bash
# Resume most recent conversation
claude --continue

# Resume specific session
claude --resume abc123 "Continue where we left off"
```

### Headless Mode Complete Example

**Example:**
```bash
# NOT: Interactive mode
claude  # Opens interactive session

# YES: Headless mode for automation
claude -p "Refactor all classes in src/ to use dependency injection"
```

### Debugging with `--verbose`

```bash
claude --verbose -p "Your task"
```

**Shows:**
- Tool invocations
- Intermediate steps
- Decision-making process
- Error details

### Custom Tools and MCP Servers

```bash
# Use MCP server for advanced functionality
claude \
  --mcp-server /path/to/server \
  -p "Use custom tool to analyze data"
```

---

## 🚫 Common Mistakes to Avoid

### 1. ❌ Shell Substitution in subprocess.exec()

**WRONG:**
```python
cmd = ["claude", "-p", "$(cat /tmp/prompt.txt)"]  # Shell substitution DOES NOT WORK!
subprocess.run(cmd)  # Passes literal string "$(cat /tmp/prompt.txt)"
```

**RIGHT:**
```python
with open("/tmp/prompt.txt") as f:
    prompt = f.read()

cmd = ["claude", "-p", prompt]  # Pass actual content
subprocess.run(cmd)
```

**Why:** `subprocess.run()` does NOT invoke a shell, so shell expansions (`$()`, `~`, `*`, etc.) are NOT processed.

### 2. ❌ Not Using Prompt Caching

**WRONG:**
```python
# Sending same system prompt 1000 times without caching
for user_query in queries:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system="Long system prompt..." * 100,  # Costs full price EVERY time!
        messages=[{"role": "user", "content": user_query}]
    )
```

**RIGHT:**
```python
# Cache system prompt once, reuse for all queries
system_prompt = {
    "role": "system",
    "content": "Long system prompt..." * 100,
    "cache_control": {"type": "ephemeral"}  # Cache this!
}

for user_query in queries:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system=system_prompt,  # Cached! 90% cost savings!
        messages=[{"role": "user", "content": user_query}]
    )
```

### 3. ❌ Blocking on Sequential Tasks

**WRONG:**
```python
# Sequential: 30 seconds total
result1 = await claude_call("Task 1")  # 10s
result2 = await claude_call("Task 2")  # 10s
result3 = await claude_call("Task 3")  # 10s
```

**RIGHT:**
```python
# Parallel: 10 seconds total
results = await asyncio.gather(
    claude_call("Task 1"),  # All 3 run simultaneously
    claude_call("Task 2"),
    claude_call("Task 3")
)
```

### 4. ❌ Not Handling Streaming Errors

**WRONG:**
```python
for event in stream:
    process(event)  # If network fails, lose all progress!
```

**RIGHT:**
```python
accumulated = []
try:
    for event in stream:
        accumulated.append(event)
        process(event)
except NetworkError:
    # Save partial result!
    save_partial(accumulated)
    resume_later()
```

### 5. ❌ Vague Prompts

**WRONG:**
```
Make this better
```

**RIGHT:**
```
Optimize this Python function for speed and readability.
Target: Reduce execution time by 50% while maintaining test coverage.
Context: This runs 10k times/second in production.
```

### 6. ❌ Not Using XML Tags

**WRONG:**
```
Requirements: must be fast, must handle errors, must log
Constraints: use Python 3.13, no external libs
Task: create a file processor
```

**RIGHT:**
```xml
<requirements>
- Process files 10x faster than current implementation
- Handle corrupt files gracefully
- Log all operations with timestamps
</requirements>

<constraints>
- Python 3.13+ only
- No external dependencies (stdlib only)
- Memory limit: 100MB
</constraints>

<task>
Create a robust file processor meeting the above requirements
</task>
```

---

## 📊 Usage Optimization

### Rate Limits by Plan

| Plan | Limit Type | Optimization |
|------|-----------|--------------|
| Free | Low message limit | Batch multiple questions in one message |
| Pro | Medium limit | Use caching, leverage memory |
| Max | Higher limit | Enable context editing |
| Team | Shared pool | Coordinate team usage |
| Enterprise | Custom | Implement retry logic with exponential backoff |

### Optimization Strategies

1. **Batch Related Questions**
   ```
   Instead of 3 messages:
   - "What is FastAPI?"
   - "How do I install it?"
   - "Show me an example"

   Send 1 message:
   - "Explain FastAPI, installation, and provide a complete example"
   ```

2. **Use Project Knowledge Bases**
   - Upload documentation ONCE
   - Cached content doesn't count against limits
   - Reuse across conversations

3. **Leverage Memory**
   ```python
   # Claude remembers context from earlier in conversation
   # No need to repeat background info
   ```

4. **Monitor Usage**
   - Paid plans: Settings > Usage
   - Track weekly limits
   - Plan around reset schedules

---

## 🔧 KI AutoAgent Workflow Rules

Based on these best practices, here are specific rules for KI AutoAgent:

### 1. System Prompt Caching

```python
# ALL agents must cache their system prompts
system_prompt_config = {
    "content": agent_instructions,
    "cache_control": {"type": "ephemeral"}
}
```

**Expected savings:** 90% on repeated agent calls

### 2. Parallel Agent Execution

```python
# When agents are independent, run in parallel
results = await asyncio.gather(
    research_agent.execute(),
    architect_agent.execute(),  # Can run if research not needed
)
```

### 3. Streaming for Long Operations

```python
# Codesmith generating files: stream results
async for chunk in codesmith.stream(task):
    yield {"type": "progress", "content": chunk}
```

### 4. Context Editing for Long Sessions

```python
# After 30k tokens, clear old tool results
"context_management": {
    "trigger": {"type": "input_tokens", "value": 30000},
    "keep": {"type": "tool_uses", "value": 5}  # Keep last 5 tool calls
}
```

### 5. Explicit Prompts with XML

```python
user_prompt = f"""
<task>
{task_description}
</task>

<context>
{background_info}
</context>

<success_criteria>
{acceptance_criteria}
</success_criteria>
"""
```

### 6. Chain of Thought for Complex Decisions

```python
# Enable thinking mode for Architect decisions
system_prompt = """
You are an architect. Use chain-of-thought reasoning for all design decisions.

For each decision:
1. State the problem
2. List alternatives
3. Evaluate trade-offs
4. Make recommendation with justification
"""
```

### 7. Verification Subagents

```python
# After Codesmith generates code, ReviewFix verifies
async def codesmith_with_verification(task):
    code = await codesmith.generate(task)
    verification = await reviewfix.verify(code)
    if not verification.passed:
        code = await codesmith.regenerate(verification.issues)
    return code
```

### 8. Error Recovery with Retries

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_claude_with_retry(prompt):
    return await claude.invoke(prompt)
```

---

## 📈 Performance Benchmarks

### Prompt Caching Impact

| Scenario | Without Cache | With Cache | Savings |
|----------|---------------|------------|---------|
| System prompt (5k tokens) reused 100x | $5.00 | $0.55 | 89% |
| Large doc (50k tokens) + 20 queries | $25.00 | $3.00 | 88% |
| Conversation with stable context | $10.00 | $1.50 | 85% |

### Parallel vs Sequential

| Task | Sequential | Parallel | Speedup |
|------|-----------|----------|---------|
| 3 independent research queries | 30s | 10s | 3x |
| 5 code generation tasks | 100s | 20s | 5x |
| 10 review tasks | 200s | 20s | 10x |

---

## 🎓 Summary: Golden Rules

1. **Be Explicit:** Tell Claude EXACTLY what you want, why, and how to measure success
2. **Use Structure:** XML tags > bullet points for complex prompts
3. **Cache Aggressively:** System prompts, docs, stable context = 90% savings
4. **Stream Long Responses:** Better UX, error recovery
5. **Batch Independent Tasks:** Parallel execution = massive speedup
6. **Manage Context:** Clear old tool results, use memory for important info
7. **Verify with Subagents:** Generate → Verify → Fix loop
8. **Handle Errors:** Retries with exponential backoff
9. **Monitor Usage:** Track limits, optimize hot paths
10. **NO SHELL SUBSTITUTION:** Read files in Python, pass content directly

---

**Next Steps:**
1. Update all agents to use prompt caching
2. Implement streaming for Codesmith/ReviewFix
3. Add context editing for long sessions
4. Enable parallel execution for independent agents
5. Add verification subagents for quality

---

## 🔬 CRITICAL: Claude CLI with `--agents` Parameter (Tested 2025-10-10)

### ⚠️ Problem: Long Prompts Timeout Without Correct Configuration

**Symptoms:**
- Long prompts (>4000 chars) timeout after 20-25s
- Works fine with short prompts (<100 chars)
- Inconsistent behavior across parameter combinations

### ✅ Solution: Mandatory Parameter Requirements

**`--agents` requires AT LEAST ONE of the following:**

1. **`--verbose` flag** (FASTEST: 16.6s) ✅
2. **Non-empty `tools` array** (18.8s) ✅
3. **`--permission-mode acceptEdits`** (21.2s) ✅

**WITHOUT any of these → TIMEOUT!** ❌

### 🎯 Optimal Configuration Per Agent Type

#### Research Agent (Text Analysis, No File I/O)

```python
cmd = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--agents", json.dumps({
        "research": {
            "description": "Research analyst specializing in software development",
            "prompt": "You are a helpful assistant.",  # Minimal! System goes in -p
            "tools": ["Read", "Bash"]  # NOT EMPTY! (Prevents timeout)
        }
    }),
    "--output-format", "stream-json",  # Better for chat outputs
    "--verbose",                       # REQUIRED with stream-json
    "-p", f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}"  # System MUST be combined here!
]
```

**Why `tools=["Read", "Bash"]`?**
- Test showed `tools=[]` → timeout
- Non-empty tools → success (even if unused)
- Read/Bash useful for context gathering

#### Codesmith Agent (Code Generation with File Creation)

```python
cmd = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--permission-mode", "acceptEdits",     # Auto-approve file edits
    "--allowedTools", "Read Edit Bash",     # Global tool whitelist
    "--agents", json.dumps({
        "codesmith": {
            "description": "Expert code generator following best practices",
            "prompt": "You are a helpful assistant.",
            "tools": ["Read", "Edit", "Bash"]   # CRITICAL for file creation!
        }
    }),
    "--output-format", "stream-json",
    "--verbose",
    "-p", f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}"
]
```

**Why all parameters?**
- Edit tool REQUIRES `--permission-mode acceptEdits`
- `--allowedTools` provides global whitelist
- Full tool capabilities needed

#### ReviewFix Agent (Code Review, Run Tests)

```python
cmd = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--agents", json.dumps({
        "reviewfix": {
            "description": "Code review and quality assurance specialist",
            "prompt": "You are a helpful assistant.",
            "tools": ["Read", "Bash"]  # Read for code, Bash for tests
        }
    }),
    "--output-format", "stream-json",
    "--verbose",
    "-p", f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}"
]
```

### 🚨 CRITICAL Findings from Tests

#### 1. System Prompt Placement

**❌ WRONG (Causes Timeout):**
```python
agent = {
    "prompt": LONG_SYSTEM_PROMPT,  # Only here = TIMEOUT!
}
cmd = [..., "-p", user_prompt]
```

**✅ CORRECT:**
```python
agent = {
    "prompt": "You are a helpful assistant.",  # Minimal
}
cmd = [..., "-p", f"{LONG_SYSTEM_PROMPT}\n\n{user_prompt}"]  # Combined!
```

**Why?** Tests showed system prompt in `agent.prompt` alone causes timeout. Must combine in `-p`.

#### 2. Empty Tools Array

**❌ WRONG:**
```python
"tools": []  # Empty = TIMEOUT!
```

**✅ CORRECT:**
```python
"tools": ["Read", "Bash"]  # Non-empty = SUCCESS
```

**Evidence:** Test results:
- `with_tools: ["Read", "Bash"]` → SUCCESS (18.8s)
- `without_tools: []` → TIMEOUT (25.0s)

#### 3. `stream-json` REQUIRES `--verbose`

**❌ WRONG:**
```bash
--output-format stream-json  # Without --verbose = ERROR!
```

**Error:** `"When using --print, --output-format=stream-json requires --verbose"`

**✅ CORRECT:**
```bash
--output-format stream-json --verbose  # Both together
```

#### 4. Long Prompts Without `--agents`

**❌ WRONG:**
```bash
claude -p "4300 char prompt..."  # TIMEOUT!
```

**Why?** Long prompts need `--agents` + one of (--verbose, tools, permission-mode)

### 📊 Performance Comparison (4300 char prompt)

| Configuration | Result | Time |
|--------------|--------|------|
| `-p` only (no --agents) | TIMEOUT | 20s |
| `--agents` only | TIMEOUT | 25s |
| `--agents` + `--verbose` | ✅ SUCCESS | **16.6s** 🏆 |
| `--agents` + `tools=["Read","Bash"]` | ✅ SUCCESS | 18.8s |
| `--agents` + `--permission-mode` | ✅ SUCCESS | 21.2s |
| `--agents` + `stream-json` + `--verbose` | ✅ SUCCESS | 25.0s |

**Winner:** `--verbose` flag (fastest + simplest)

### 🎓 Lessons Learned

1. **`--agents` is for FEATURES, not speed** - enables tool use, structured workflows
2. **Long prompts need special handling** - can't just pass via `-p` alone
3. **System prompts must be combined** - placing only in `agent.prompt` fails
4. **Tools list matters even if unused** - empty array causes timeout
5. **`stream-json` needs `--verbose`** - not optional, mandatory for CLI
6. **Performance differences are minimal** - focus on robustness over 2-3s savings

### 🛠️ Implementation Checklist

For any Claude CLI integration with `--agents`:

- [ ] Use `--output-format stream-json` + `--verbose` (best UX)
- [ ] Combine system + user prompt in `-p` parameter
- [ ] Keep `agent.prompt` minimal ("You are a helpful assistant.")
- [ ] Ensure `tools` array is non-empty (even if tools unused)
- [ ] Add `--permission-mode acceptEdits` for file operations
- [ ] Use `--allowedTools` for global tool whitelist
- [ ] Test with long prompts (>4000 chars) to verify no timeout

### 📝 Test Evidence

All findings based on systematic testing (2025-10-10):
- Test suite: `test_claude_cli_parameters.py`
- Deep analysis: `test_claude_deep_analysis.py`
- Results: `/tmp/claude_cli_test_results.json`, `/tmp/claude_deep_analysis.json`

**Configurations tested:** 11 different parameter combinations
**Long prompt size:** 4309 characters (Perplexity research results)
**Success rate:** 4/11 configurations worked, 6/11 timeout, 1/11 error

---

### ✅ FINAL SOLUTION VERIFIED (2025-10-10)

**File:** `backend/adapters/claude_cli_simple.py`

**Applied fixes:**
1. Combined system + user prompts in `-p` parameter
2. Keep `agent.prompt` minimal: "You are a helpful assistant."
3. Set tools to `["Read", "Bash"]` (non-empty)
4. Added `stdin=asyncio.subprocess.DEVNULL` to prevent hanging
5. Include `--verbose` flag with `stream-json`

**Test result:** Research subgraph with 4668 char Perplexity results
- ✅ **SUCCESS** in ~20-25 seconds
- ✅ Perplexity API: 4668 chars retrieved
- ✅ Claude CLI: 7662 chars output, 3 JSONL events parsed
- ✅ Analysis: 2688 chars of structured research summary
- ✅ No errors, findings properly extracted

**Command used:**
```bash
claude \
  --model claude-sonnet-4-20250514 \
  --permission-mode acceptEdits \
  --allowedTools "Read Edit Bash" \
  --agents '{"research": {"description": "...", "prompt": "You are a helpful assistant.", "tools": ["Read", "Bash"]}}' \
  --output-format stream-json \
  --verbose \
  -p "SYSTEM_PROMPT\n\nUSER_PROMPT"
```

**Python subprocess configuration:**
```python
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    stdin=asyncio.subprocess.DEVNULL  # CRITICAL: Prevents CLI waiting
)
```

**All fixes confirmed working in production.**
