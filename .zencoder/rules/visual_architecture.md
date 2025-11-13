# 🎨 Visual Architecture: Prompt Flow & Instruction Hierarchy

**Version**: 1.0  
**Format**: Mermaid diagrams for understanding the system

---

## 📊 Diagram 1: Instruction Hierarchy (Settings Precedence)

```mermaid
graph TD
    A["🌍 GLOBAL LEVEL<br/>~/.ki_autoagent/instructions/"] -->|Lower Priority| B["👤 USER LEVEL<br/>~/.claude/settings.json"]
    B -->|Lower Priority| C["📁 PROJECT LEVEL<br/>.claude/settings.json"]
    C -->|Higher Priority| D["🔒 ENTERPRISE LEVEL<br/>managed-settings.json"]
    
    style A fill:#e1f5ff,stroke:#01579b
    style B fill:#f3e5f5,stroke:#4a148c
    style C fill:#e8f5e9,stroke:#1b5e20
    style D fill:#fff3e0,stroke:#e65100
    
    E["🎯 RESULT<br/>Final Combined Instructions"]
    D --> E
    C --> E
    B --> E
    A --> E
```

---

## 📊 Diagram 2: Dual-Level Instruction Architecture

```mermaid
graph LR
    subgraph GLOBAL ["🌍 GLOBAL (Agent Identity)"]
        G1["🆔 base-role.md<br/>Who am I?"]
        G2["🎭 [agent]-instructions.md<br/>My capabilities"]
        G3["📋 shared-protocols.md<br/>How I communicate"]
    end
    
    subgraph PROJECT ["📁 PROJECT (Task Context)"]
        P1["📝 current-task.md<br/>What to do?"]
        P2["⚙️ constraints.md<br/>Technical limits"]
        P3["✅ success-criteria.md<br/>How to succeed"]
    end
    
    subgraph AGENT ["🤖 AGENT SERVER"]
        A1["Load Global Instructions"]
        A2["Load Project Context"]
        A3["Combine & Enhance"]
        A4["Build Final Prompts"]
    end
    
    subgraph CLI ["⚙️ CLAUDE CLI"]
        C1["--system-prompt flag<br/>Global + Context"]
        C2["-p flag<br/>Task"]
        C3["Claude Model"]
    end
    
    GLOBAL --> A1
    PROJECT --> A2
    A1 --> A3
    A2 --> A3
    A3 --> A4
    A4 --> C1
    A4 --> C2
    C1 --> C3
    C2 --> C3
    
    style GLOBAL fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style PROJECT fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px
    style AGENT fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style CLI fill:#fce4ec,stroke:#880e4f,stroke-width:3px
```

---

## 📊 Diagram 3: ReviewFix Agent - Complete Flow

```mermaid
graph TD
    U["👤 User Request<br/>via Supervisor"]
    
    subgraph LOAD ["STEP 1: Load Instructions"]
        L1["📂 ~/.ki_autoagent/instructions/reviewfix.md<br/>▶ ReviewFix Identity<br/>▶ Capabilities<br/>▶ JSON format requirement"]
        L2["📂 .ki_autoagent_ws/instructions/<br/>▶ Current task context<br/>▶ Constraints<br/>▶ Success criteria"]
    end
    
    subgraph BUILD ["STEP 2: Build Prompts"]
        B1["🔨 Build System Prompt<br/>WHO: ReviewFix agent<br/>WHAT CAPABILITIES: Review, validate, fix<br/>HOW: Return JSON validation"]
        B2["🔨 Build User Prompt<br/>WHAT: Specific files to review<br/>WHERE: File paths<br/>WHY: Previous validation errors"]
    end
    
    subgraph CALL ["STEP 3: Call Claude CLI"]
        C1["⚙️ Command:<br/>claude --model sonnet<br/>  --system-prompt B1<br/>  -p B2<br/>  --output-format stream-json"]
    end
    
    subgraph PROCESS ["STEP 4: Claude Processes"]
        P1["🧠 Initialize with ReviewFix role from B1"]
        P2["🧠 Receive task from B2"]
        P3["🧠 Review files for bugs"]
        P4["🧠 Generate fixes"]
        P5["🧠 Validate with tests"]
    end
    
    subgraph RESPONSE ["STEP 5: Return Response"]
        R1["📤 JSON Response<br/>validation_passed: true/false<br/>bugs_found: [...]<br/>fixes_applied: [...]<br/>test_results: {...}"]
    end
    
    subgraph RESULT ["STEP 6: Result"]
        RES1["✅ validation_passed: true<br/>→ Continue with deployment"]
        RES2["❌ validation_passed: false<br/>→ Return to CodeSmith for fixes"]
    end
    
    U --> LOAD
    L1 --> BUILD
    L2 --> BUILD
    BUILD --> CALL
    CALL --> PROCESS
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> RESPONSE
    RESPONSE --> RESULT
    RES1 --> END1["✨ Deployment Ready"]
    RES2 --> END2["🔄 Fix Loop"]
    
    style LOAD fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style BUILD fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style CALL fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    style PROCESS fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style RESPONSE fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style RESULT fill:#b2dfdb,stroke:#00695c,stroke-width:2px
```

---

## 📊 Diagram 4: Prompt Layering (Depth)

```mermaid
graph TB
    subgraph LAYER1 ["LAYER 1: Foundation<br/>(Static - Cached)"]
        L1["🆔 Agent Identity<br/>You are ReviewFix...<br/>Your role is...<br/>You are an expert in..."]
    end
    
    subgraph LAYER2 ["LAYER 2: Capabilities<br/>(Static - Cached)"]
        L2["⚙️ Tool & Capability Definition<br/>You have access to: Read, Edit, Bash<br/>You can perform: Bug detection, fixing, validation<br/>You understand: JSON, TypeScript, Python..."]
    end
    
    subgraph LAYER3 ["LAYER 3: Output Format<br/>(Static - Cached)"]
        L3["📋 Response Structure (CRITICAL)<br/>Return JSON with these fields:<br/>- validation_passed: boolean<br/>- bugs_found: array<br/>- fixes_applied: array<br/>- test_results: object"]
    end
    
    subgraph LAYER4 ["LAYER 4: Memory Context<br/>(Dynamic - Per-project)"]
        L4["🧠 Project Memory<br/>Previous decisions<br/>Known patterns<br/>Past failures"]
    end
    
    subgraph LAYER5 ["LAYER 5: Task Context<br/>(Dynamic - Per-request)"]
        L5["📝 Current Task<br/>Files to review<br/>Errors to fix<br/>Constraints<br/>Success criteria"]
    end
    
    subgraph LAYER6 ["LAYER 6: File Context<br/>(Dynamic - Per-request)"]
        L6["📂 Specific Files<br/>Generated code<br/>Test files<br/>Previous validation errors"]
    end
    
    LAYER1 --> LAYER2
    LAYER2 --> LAYER3
    LAYER3 --> LAYER4
    LAYER4 --> LAYER5
    LAYER5 --> LAYER6
    
    style LAYER1 fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style LAYER2 fill:#c5cae9,stroke:#3f51b5,stroke-width:2px
    style LAYER3 fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    style LAYER4 fill:#d1c4e9,stroke:#512da8,stroke-width:2px
    style LAYER5 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style LAYER6 fill:#ffccbc,stroke:#d84315,stroke-width:2px
```

---

## 📊 Diagram 5: File Organization Structure

```mermaid
graph TD
    HOME["🏠 Home Directory<br/>$HOME"]
    
    subgraph GLOBAL_DIR ["~/.ki_autoagent/<br/>(Global - All Projects)"]
        GC["config/<br/>API keys, settings"]
        GI["instructions/ (NEW)<br/>Agent roles"]
        GC1["└─ base-role.md"]
        GC2["└─ architect.md"]
        GC3["└─ codesmith.md"]
        GC4["└─ reviewfix.md"]
        GC5["└─ research.md"]
        GC6["└─ responder.md"]
    end
    
    subgraph PROJECT_DIR [".ki_autoagent_ws/<br/>(Project - This Project Only)"]
        PI["instructions/ (NEW)<br/>Task-specific"]
        PI1["└─ current-task.md"]
        PI2["└─ constraints.md"]
        PI3["└─ success-criteria.md"]
        PC["cache/<br/>Checkpoints"]
        PM["memory/<br/>Decisions"]
    end
    
    HOME --> GLOBAL_DIR
    HOME --> PROJECT_DIR
    
    GLOBAL_DIR --> GC
    GLOBAL_DIR --> GI
    GI --> GC1
    GI --> GC2
    GI --> GC3
    GI --> GC4
    GI --> GC5
    GI --> GC6
    
    PROJECT_DIR --> PI
    PROJECT_DIR --> PC
    PROJECT_DIR --> PM
    PI --> PI1
    PI --> PI2
    PI --> PI3
    
    style HOME fill:#fafafa,stroke:#424242,stroke-width:2px
    style GLOBAL_DIR fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style PROJECT_DIR fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style GI fill:#ffe0b2,stroke:#e65100,stroke-width:1px
    style PI fill:#f8bbd0,stroke:#c2185b,stroke-width:1px
```

---

## 📊 Diagram 6: Claude CLI Command Pipeline

```mermaid
graph LR
    subgraph INPUT ["INPUT"]
        I1["System Prompt<br/>Global role"]
        I2["User Prompt<br/>Task specific"]
    end
    
    subgraph CMD ["COMMAND BUILD"]
        C0["Base Command"]
        C1["--model sonnet"]
        C2["--system-prompt<br/>SYSTEM_PROMPT"]
        C3["-p<br/>USER_PROMPT"]
        C4["--output-format<br/>stream-json"]
        C5["--verbose"]
    end
    
    subgraph CLI ["CLAUDE CLI EXECUTION"]
        CLI1["Parse --system-prompt"]
        CLI2["Parse -p"]
        CLI3["Initialize Agent"]
        CLI4["Process Task"]
        CLI5["Stream JSON Response"]
    end
    
    subgraph OUTPUT ["OUTPUT"]
        O1["JSON Stream<br/>Events"]
    end
    
    I1 --> C0
    I2 --> C0
    C0 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    
    C2 --> CLI1
    C3 --> CLI2
    CLI1 --> CLI3
    CLI2 --> CLI3
    CLI3 --> CLI4
    CLI4 --> CLI5
    CLI5 --> O1
    
    style INPUT fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style CMD fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style CLI fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style OUTPUT fill:#ffccbc,stroke:#d84315,stroke-width:2px
```

---

## 📊 Diagram 7: Prompt Caching Strategy

```mermaid
graph TD
    subgraph CACHE_SECTION1 ["CACHE BLOCK 1<br/>Duration: 5 min"]
        T1["🔒 Tools Definition<br/>(Read, Edit, Bash)"]
    end
    
    subgraph CACHE_SECTION2 ["CACHE BLOCK 2<br/>Duration: 5 min"]
        T2["🔒 System Prompt<br/>Agent role & identity<br/>Capabilities & constraints<br/>Output format"]
    end
    
    subgraph NO_CACHE ["NO CACHE<br/>(Changes per request)"]
        T3["💨 User Prompt<br/>Current task<br/>File context<br/>Success criteria"]
    end
    
    subgraph USAGE ["USAGE TRACKING"]
        U1["📊 cache_creation_input_tokens<br/>Tokens written to cache"]
        U2["📊 cache_read_input_tokens<br/>Tokens read from cache"]
        U3["📊 input_tokens<br/>New tokens processed"]
    end
    
    CACHE_SECTION1 --> USAGE
    CACHE_SECTION2 --> USAGE
    NO_CACHE --> USAGE
    
    USAGE --> BENEFIT["✨ BENEFITS<br/>50-90% cost reduction<br/>Faster response time<br/>Lower latency"]
    
    style CACHE_SECTION1 fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style CACHE_SECTION2 fill:#c5cae9,stroke:#3f51b5,stroke-width:2px
    style NO_CACHE fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    style USAGE fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style BENEFIT fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

---

## 🔄 Diagram 8: Comparison - Before vs After

```mermaid
graph TD
    subgraph BEFORE ["❌ BEFORE (Bug)"]
        B1["Input:<br/>system_prompt + user_prompt"]
        B2["Combine:<br/>combined = sys + user"]
        B3["Command:<br/>claude -p combined"]
        B4["Result:<br/>System instructions diluted ⚠️"]
        B5["Output:<br/>validation_passed: always false"]
        B1 --> B2
        B2 --> B3
        B3 --> B4
        B4 --> B5
    end
    
    subgraph AFTER ["✅ AFTER (Fix)"]
        A1["Input:<br/>system_prompt + user_prompt"]
        A2["Separate:<br/>Keep distinct"]
        A3["Command:<br/>claude --system-prompt sys -p user"]
        A4["Result:<br/>Instructions preserved ✅"]
        A5["Output:<br/>validation_passed: correct"]
        A1 --> A2
        A2 --> A3
        A3 --> A4
        A4 --> A5
    end
    
    style BEFORE fill:#ffebee,stroke:#c62828,stroke-width:3px
    style B5 fill:#e53935,color:#fff
    style AFTER fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style A5 fill:#43a047,color:#fff
```

---

## 📋 Quick Reference: Prompt Checklist

```mermaid
graph TD
    START["Start: Building Prompt"] --> Q1{Is this a<br/>SYSTEM PROMPT?}
    
    Q1 -->|YES| S1["✓ Include Agent Identity<br/>✓ Include Output Format<br/>✓ Include Capabilities<br/>✓ Include Constraints<br/>✓ Include Validation Rules"]
    
    Q1 -->|NO| Q2{Is this a<br/>USER PROMPT?}
    
    Q2 -->|YES| U1["✓ Include Task Description<br/>✓ Include File Context<br/>✓ Include Success Criteria<br/>✓ Include Constraints<br/>✓ Include Examples"]
    
    S1 --> Q3{Pass to<br/>Claude CLI?}
    U1 --> Q3
    
    Q3 -->|YES - System| S2["Use: --system-prompt flag<br/>📌 Never mix with -p!"]
    Q3 -->|YES - User| U2["Use: -p flag<br/>📌 Never combine with system!"]
    
    S2 --> END["✨ Success!<br/>Proper prompt separation"]
    U2 --> END
    
    style START fill:#fff9c4,stroke:#f57f17
    style S1 fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style U1 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style S2 fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style U2 fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style END fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
```

---

## 📊 Key Points from Diagrams

### Hierarchy
- Global < User < Project < Enterprise (in Claude Code)
- But in KI AutoAgent: Global Instructions always loaded for agent identity

### Layering
- Foundation (identity) → Capabilities → Format → Context → Task
- Each layer builds on previous
- Enables proper caching at different levels

### File Organization
- Global: `~/.ki_autoagent/instructions/`
- Project: `.ki_autoagent_ws/instructions/`
- Clear separation of concerns

### CLI Usage
- CRITICAL: `--system-prompt` for global instructions
- User prompt goes to `-p` parameter ONLY
- Never combine them!

### Caching
- Static content (identity, format) = cacheable
- Dynamic content (task, files) = not cached
- Enables cost reduction 50-90%

---

## 🎓 Summary

These diagrams illustrate:

1. **Hierarchy** - Where instructions come from
2. **Flow** - How instructions move through the system
3. **Layering** - How prompts are structured
4. **Organization** - Where files are stored
5. **Pipeline** - How CLI is called
6. **Caching** - What gets cached and why
7. **Comparison** - Before/after bug fix
8. **Checklist** - What to include in prompts

Use these as reference when implementing the dual-level instruction architecture!
