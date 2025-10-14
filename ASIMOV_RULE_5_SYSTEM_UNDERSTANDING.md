# ASIMOV RULE 5: System Understanding Protocol

**Version:** 1.0.0
**Date:** 2025-10-14
**Status:** ACTIVE

---

## Core Principle

**NO CHANGES WITHOUT SYSTEM UNDERSTANDING**

The Architect agent MUST create and maintain system understanding through architecture documentation. This documentation serves as the "source of truth" for all modifications.

---

## The Problem (Historical)

**Before v6.3:**

```
CREATE Workflow:
1. Research → 2. Architect (design) → 3. Codesmith (build) → 4. ReviewFix
   ❌ Problem: Architect analyzes EMPTY workspace (waste)
   ❌ Problem: NO system documentation created after build
   ❌ Result: System exists but is UNDOCUMENTED

UPDATE Workflow (later):
1. Research (optional) → 2. Architect (update) → 3. Codesmith → 4. ReviewFix
   ❌ Problem: Architect has NO system understanding!
   ❌ Problem: Changes made BLIND to existing structure
   ❌ Result: Architecture drift, inconsistencies, breaking changes
```

**Key Insight:**
> "Das bedeutet du callst einen Call machen um die App zu verändern und prüfen ob diese Daten benutzt werden um das System zu verstehen und zu verbessern"

Translation: You make changes without using system understanding data to improve the system.

---

## The Solution (v6.3+)

### **CREATE Workflow** - Build THEN Document

```
1. Research (mode="research", optional/forced)
2. Architect: Design architecture
3. HITL: Architecture approval
4. Codesmith: Build system
5. ReviewFix: Validate
6. ✅ Architect: POST-BUILD SCAN ← NEW!
   - Scan actual codebase with tree-sitter
   - Generate architecture documentation
   - Save to .ki_autoagent/architecture/
7. System documented and ready for future updates
```

**Rationale:**
- Don't scan empty workspace (waste)
- Scan AFTER build captures actual implementation
- Creates baseline for future modifications

### **UPDATE Workflow** - Understand THEN Modify

```
1. ✅ Architect: SCAN FIRST ← MANDATORY!
   - Load existing architecture from .ki_autoagent/architecture/
   - Scan current codebase with tree-sitter
   - Verify consistency
   - Build complete system understanding
2. Research (mode="research", optional/forced)
3. Architect: Update Proposal
   - Designs changes WITH system context
   - Identifies impact on existing components
   - Ensures architectural consistency
4. HITL: Proposal approval
5. Codesmith: Implement changes
6. ReviewFix: Validate
7. ✅ Architect: RE-SCAN ← MANDATORY!
   - Scan updated codebase
   - Update architecture documentation
   - Document changes made
```

**Rationale:**
- ALWAYS understand system before changes
- Prevent architectural drift
- Maintain consistency
- Enable intelligent modifications

---

## Architecture Documentation Structure

**Location:** `{workspace}/.ki_autoagent/architecture/`

**Files Managed:**

1. **system_overview.md** - High-level system description
2. **components.json** - Component definitions, responsibilities, relationships
3. **tech_stack.yaml** - Languages, frameworks, libraries, tools
4. **patterns.md** - Design patterns and best practices used
5. **api_spec.yaml** - API definitions (optional)
6. **database_schema.sql** - Database structure (optional)
7. **metadata.json** - Version, creation date, workspace info

**Example components.json:**
```json
[
  {
    "name": "AuthenticationService",
    "type": "service",
    "files": ["backend/services/auth.py"],
    "responsibilities": "User authentication, JWT token management",
    "dependencies": ["database", "redis_cache"],
    "api_endpoints": ["/login", "/logout", "/refresh"]
  },
  {
    "name": "UserAPI",
    "type": "api",
    "files": ["backend/api/users.py"],
    "responsibilities": "User CRUD operations",
    "dependencies": ["AuthenticationService", "UserModel"]
  }
]
```

---

## Architect Agent Responsibilities

### **Scan Mode** (UPDATE workflows)

1. **Load Existing Architecture**
   ```python
   architecture = await architecture_manager.load_architecture()
   ```

2. **Scan Current Codebase**
   ```python
   tree_sitter_analysis = await mcp.call(
       server="tree-sitter",
       tool="analyze_codebase",
       arguments={"workspace_path": workspace_path}
   )
   ```

3. **Verify Consistency**
   ```python
   consistency = await architecture_manager.verify_consistency(
       tree_sitter_analysis
   )
   # Returns: {"consistent": bool, "score": 0.0-1.0, "discrepancies": [...]}
   ```

4. **Build System Understanding**
   - Combine documented architecture + actual code structure
   - Identify components, dependencies, patterns
   - Prepare context for update proposal

### **Design Mode** (CREATE workflows, UPDATE after scan)

**CREATE:**
- Design architecture from requirements
- Plan component structure
- Define tech stack

**UPDATE:**
- Design changes WITH system understanding
- Ensure compatibility with existing components
- Minimize breaking changes
- Update architecture documentation

### **Post-Build Scan Mode** (CREATE workflows)

1. **Scan Generated Code**
   ```python
   tree_sitter_analysis = await mcp.call(
       server="tree-sitter",
       tool="analyze_codebase",
       arguments={"workspace_path": workspace_path}
   )
   ```

2. **Generate Architecture Documentation**
   ```python
   architecture = await architecture_manager.generate_architecture_from_code(
       tree_sitter_analysis
   )
   ```

3. **Save Documentation**
   ```python
   await architecture_manager.save_architecture(architecture)
   ```

### **Re-Scan Mode** (UPDATE workflows)

1. **Scan Updated Code**
2. **Update Architecture Documentation**
   ```python
   await architecture_manager.update_architecture(changes)
   ```
3. **Document Changes Made**

---

## Human-in-the-Loop (HITL) Integration

**HITL Trigger Points:**

1. **Architecture Design** (CREATE)
   - Present proposed architecture to user
   - Get approval before build

2. **Update Proposal** (UPDATE)
   - Present proposed changes
   - Show impact on existing system
   - Get approval before modification

3. **Uncertainty Detection** (ANY workflow)
   - Agent uncertain about approach
   - Missing critical information
   - Conflicting best practices

**HITL Request Format:**
```json
{
  "title": "Architecture Review Required",
  "question": "Proposed architecture for task manager app...",
  "options": [
    {
      "label": "Approve",
      "description": "Proceed with this architecture",
      "pros": ["Well-structured", "Scalable"],
      "cons": ["Complex for simple app"],
      "action": "approve"
    },
    {
      "label": "Modify",
      "description": "I'll suggest changes",
      "pros": ["Customized to needs"],
      "cons": ["Takes more time"],
      "action": "modify"
    },
    {
      "label": "Research More",
      "description": "Research alternative approaches",
      "pros": ["Data-driven decision"],
      "cons": ["Delays start"],
      "action": "research"
    }
  ]
}
```

---

## Research Integration

**Research is OPTIONAL but can be:**

1. **User-Forced**
   - User explicitly requests research
   - Always honored

2. **AI-Decided** (GPT-4o-mini)
   - Agent requests research during execution
   - GPT-4o-mini evaluates necessity
   - Research triggered if score > 0.7

3. **Uncertainty-Triggered**
   - Agent uncertain about approach
   - Missing critical information
   - Research suggested as option in HITL

**Research Capability:**
```python
from backend.agents.research_capability import ResearchCapability

research = ResearchCapability()

# Check if research needed
decision = await research.should_research(
    task="Add authentication to app",
    agent="architect",
    context={"tech_stack": ["FastAPI", "React"]},
    forced=False,
    mcp_client=mcp
)

if decision["should_research"]:
    result = await research.perform_research(
        query="Best practices for JWT authentication in FastAPI",
        mcp_client=mcp
    )
```

---

## Uncertainty Detection

**Triggers HITL when agent is unsure:**

```python
from backend.agents.agent_uncertainty import AgentUncertaintyDetector

detector = AgentUncertaintyDetector(threshold=0.7)

analysis = await detector.analyze_response(
    agent_name="architect",
    agent_response=architect_output,
    context={"workspace_path": workspace_path},
    mcp_client=mcp
)

if analysis["uncertain"]:
    # Present HITL request to user
    hitl_request = analysis["hitl_request"]
    # Wait for user decision
    user_decision = await present_hitl(hitl_request)
```

**Uncertainty Indicators:**
- "I'm not sure", "unclear", "maybe", "possibly"
- Multiple conflicting approaches without clear winner
- Explicit requests for clarification
- Missing critical information

---

## Implementation Components

### **New Modules (v6.3)**

1. **backend/utils/architecture_manager.py**
   - Manages architecture documentation
   - Save/load/update architecture
   - Verify consistency with code
   - Generate from code
   - Export diagrams

2. **backend/agents/agent_uncertainty.py**
   - Detects agent uncertainty
   - Analyzes responses with GPT-4o-mini
   - Generates HITL requests
   - Provides decision options

3. **backend/agents/research_capability.py**
   - Unified research capability
   - AI-based necessity evaluation
   - Integrates with research subgraph
   - Batch research support

### **Updated Modules**

1. **backend/cognitive/workflow_planner_v6.py**
   - Added UPDATE workflow type
   - Updated patterns and examples
   - Validation for UPDATE workflows

2. **backend/workflow_v6_integrated.py**
   - Implement CREATE workflow with post-build scan
   - Implement UPDATE workflow with mandatory scans
   - HITL integration points

3. **backend/subgraphs/architect_subgraph_v6_1.py**
   - Scan mode for UPDATE workflows
   - Post-build scan mode for CREATE
   - Re-scan mode for UPDATE
   - Architecture documentation integration

---

## Validation Rules

**CREATE Workflow:**
- ✅ MUST have Architect post-build scan at END
- ✅ MUST save architecture documentation
- ✅ Architecture files MUST exist after completion

**UPDATE Workflow:**
- ✅ MUST start with Architect scan
- ✅ MUST load existing architecture
- ✅ MUST verify consistency before changes
- ✅ MUST end with Architect re-scan
- ✅ MUST update architecture documentation

**Architecture Documentation:**
- ✅ MUST be saved in `.ki_autoagent/architecture/`
- ✅ MUST include system_overview.md and components.json
- ✅ MUST be version-controlled
- ✅ MUST be updated after every modification

---

## Benefits

1. **Consistency** - All changes based on documented architecture
2. **Safety** - Understand system before modifying
3. **Quality** - Architecture drift prevention
4. **Maintenance** - Always up-to-date documentation
5. **Intelligence** - Context-aware modifications
6. **Traceability** - Track architectural evolution

---

## Migration from v6.2

**For existing projects WITHOUT architecture:**

1. Run UPDATE workflow on first modification
2. Architect scans and generates architecture
3. User reviews and approves
4. Future modifications use existing architecture

**For new projects:**

1. Use CREATE workflow
2. Architecture automatically documented after build
3. Ready for future modifications

---

## References

- **Architecture Manager:** `/backend/utils/architecture_manager.py`
- **Uncertainty Detector:** `/backend/agents/agent_uncertainty.py`
- **Research Capability:** `/backend/agents/research_capability.py`
- **Workflow Planner:** `/backend/cognitive/workflow_planner_v6.py`
- **ASIMOV RULE 4 (HITL):** `/ASIMOV_RULE_4_HITL.md`

---

## Version History

- **v1.0.0** (2025-10-14) - Initial version, defines system understanding protocol

---

**This rule is MANDATORY for all workflows starting v6.3.**

**Violation = Architectural drift, inconsistencies, breaking changes.**
