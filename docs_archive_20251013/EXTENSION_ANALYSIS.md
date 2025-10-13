# VSCode Extension Analysis - Complete Inventory

**Date:** 2025-10-09
**Purpose:** Identify all functions, settings, v6 compatibility issues
**Files:** 11 TypeScript files, 5626 lines total

---

## File Overview

| File | Lines | Status | Issues |
|------|-------|--------|--------|
| MultiAgentChatPanel.ts | 2478 | 🔴 OLD | Many v5 patterns, needs refactor |
| SystemKnowledge.ts | 547 | ⚠️  CHECK | May have v5 dependencies |
| BackendClient.ts | 527 | ✅ FIXED | v6 messages added |
| UnifiedChatMixin.ts | 403 | 🔴 OLD | v5 patterns |
| modelSettings.ts | 379 | ⚠️  PARTIAL | Model discovery disabled for v6 |
| IntentTypes.ts | 337 | ⚠️  CHECK | Intent classification |
| extension.ts | 294 | ✅ FIXED | BackendManager removed |
| index.ts | 191 | ℹ️  TYPES | Type exports |
| Memory.ts | 173 | ⚠️  CHECK | Memory types |
| BackendManager.ts | 162 | 🔴 UNUSED | Should be removed! |
| AgentConfiguration.ts | 135 | ⚠️  CHECK | Agent configs |

---

## Detailed Analysis

### 1. extension.ts (294 lines) - ENTRY POINT

**Status:** ✅ v6 Compatible (after fixes)

**Functions:**
- `activate()` - Extension activation, connects to v6 backend
- `deactivate()` - Cleanup
- `setupBackendEventHandlers()` - WebSocket event handlers
- `registerCommandsEarly()` - Register commands before backend ready
- `registerBackendCommands()` - Register backend-dependent commands

**Commands Registered:**
1. `ki-autoagent.showChat` - Open chat panel
2. `ki-autoagent.showHelp` - Show help
3. `ki-autoagent.restartBackend` - Reconnect to backend
4. `ki-autoagent.showBackendStatus` - Check connection status
5. `ki-autoagent.showBackendInstructions` - Show manual start instructions

**Settings Used:**
- `kiAutoAgent.backend.url` (default: localhost:8002)
- `kiAutoAgent.models.autoDiscover` (disabled for v6)

**v6 Compatibility:**
- ✅ Connects to ws://localhost:8002
- ✅ No BackendManager auto-start
- ✅ Handles v6 message types
- ⚠️  Still has OLD model discovery code (disabled but present)

**Needs:**
- Remove BackendManager import (unused)
- Remove syncSettingsToEnv (removed but import might remain)
- Clean up old comments

---

### 2. BackendClient.ts (527 lines) - WEBSOCKET CLIENT

**Status:** ✅ v6 Compatible (after fixes)

**Main Class:** `BackendClient extends EventEmitter`

**Key Methods:**
```typescript
connect() - Connect to WebSocket
disconnect() - Close connection
sendMessage(message: BackendMessage) - Send to backend
handleMessage(message: BackendMessage) - Process incoming
```

**Message Types Handled:**
- ✅ connected, initialized, init
- ✅ status, approval_request, approval_response, workflow_complete
- ⚠️  agent_response, agent_thinking, agent_progress (v5 patterns)
- ⚠️  pause, resume, stopAndRollback (v5 features)
- ⚠️  clarificationNeeded, architectureProposal (v5 features)

**v6 Compatibility:**
- ✅ Has v6 message types (approval, workflow_complete)
- ✅ Correct field access (action_type, quality_score)
- ⚠️  Many v5 message handlers still present
- ⚠️  Session restore, pause/resume not in v6

**Needs:**
- Mark v5-only handlers as deprecated
- Document which messages v6 actually uses
- Remove or adapt v5-specific features

---

### 3. MultiAgentChatPanel.ts (2478 lines!) - MAIN UI

**Status:** 🔴 MOSTLY v5 CODE - NEEDS MAJOR REFACTOR

**THIS IS THE BIGGEST PROBLEM FILE!**

**Functions (excerpt):**
```typescript
createOrShow() - Create chat panel
sendMessageToPanel() - Send message to UI
_initializeWebview() - Setup webview
_handleWebviewMessage() - Handle UI events
_renderChat() - Render HTML
_injectChatScript() - Inject JS into webview
```

**Features (many v5-specific):**
- Multi-agent chat UI
- Architecture approval workflow (v5)
- Pause/Resume/Rollback (v5)
- Session management (v5)
- Model selection UI
- Conversation history
- Agent selection dropdown

**v6 Issues:**
- 🔴 Architecture approval UI (not in v6 workflow)
- 🔴 Pause/Resume buttons (not in v6)
- 🔴 Agent selection (v6 uses orchestrator only)
- 🔴 Session restore (different in v6)
- ⚠️  Hard-coded agent list (research, architect, codesmith, etc.)

**Settings Used:**
```typescript
kiAutoAgent.defaultAgent
kiAutoAgent.conversationAutoSave
kiAutoAgent.ui.theme
kiAutoAgent.ui.fontSize
```

**Needs:**
- MAJOR refactor for v6
- Remove v5-only UI elements
- Simplify agent selection (v6 = orchestrator only)
- Update approval flow for v6 Approval Manager
- Remove pause/resume/rollback
- Update message rendering for v6 messages

---

### 4. BackendManager.ts (162 lines) - UNUSED!

**Status:** 🔴 SHOULD BE DELETED

**Purpose:** Auto-start Python backend (removed in v6)

**Why unused:**
- v6 requires manual backend start
- Extension now connects directly to ws://localhost:8002
- No child process management in v6

**Action:** DELETE THIS FILE

---

### 5. modelSettings.ts (379 lines) - MODEL CONFIGURATION

**Status:** ⚠️  PARTIALLY COMPATIBLE

**Purpose:** Manage AI model settings

**Functions:**
```typescript
discoverModelsOnStartup() - Fetch models from backend
getAvailableModels() - Get model list
getModelDescription() - Get model details
refreshAvailableModels() - Update model list
registerCommands() - Register model commands
```

**Settings:**
```typescript
kiAutoAgent.models.autoDiscover
kiAutoAgent.models.research.provider
kiAutoAgent.models.research.model
kiAutoAgent.models.architect.provider
... (one per agent)
```

**v6 Issues:**
- ⚠️  Model discovery endpoint doesn't exist in v6 (404 suppressed)
- ⚠️  Per-agent model config (v6 uses global config?)
- ℹ️  Uses /api/models/descriptions (not in v6)

**Needs:**
- Decide: Keep model selection or remove?
- If keep: Implement v6 endpoint
- If remove: Simplify to single model setting

---

### 6. IntentTypes.ts (337 lines) - INTENT CLASSIFICATION

**Status:** ⚠️  v5 FEATURE - NOT IN v6?

**Purpose:** Classify user intents (coding, trading, etc.)

**Types Defined:**
```typescript
IntentType = "coding" | "trading" | "research" | "chat" | "task_management" | ...
AgentRole = "architect" | "codesmith" | "reviewer" | "research" | ...
```

**Functions:**
```typescript
classifyIntent() - Determine intent from message
selectAgentForIntent() - Pick agent based on intent
```

**v6 Compatibility:**
- ⚠️  v6 has Query Classifier (server-side)
- ⚠️  Intent classification may be duplicate
- ℹ️  v6 orchestrator decides agents, not client

**Needs:**
- Check if v6 Query Classifier makes this obsolete
- If yes: Remove client-side classification
- If no: Update to match v6 types

---

### 7. SystemKnowledge.ts (547 lines) - KNOWLEDGE BASE

**Status:** ⚠️  v5 FEATURE

**Purpose:** Client-side knowledge about system capabilities

**Content:**
- Agent capabilities descriptions
- Tool descriptions
- Workflow descriptions
- Best practices

**v6 Compatibility:**
- ⚠️  v6 has server-side knowledge base
- ⚠️  May be outdated for v6
- ℹ️  Describes v5 workflows

**Needs:**
- Update knowledge base for v6
- Or remove if v6 backend provides this

---

### 8. Memory.ts (173 lines) - MEMORY TYPES

**Status:** ⚠️  CHECK COMPATIBILITY

**Purpose:** Types for memory system

**Types:**
```typescript
MemoryEntry
MemoryContext
MemoryQuery
```

**v6 Compatibility:**
- ℹ️  v6 has Memory System v6
- ⚠️  Types may not match v6 API

**Needs:**
- Compare with v6 Memory System API
- Update types if needed

---

### 9. AgentConfiguration.ts (135 lines) - AGENT CONFIG

**Status:** ⚠️  v5 PATTERNS

**Purpose:** Agent configuration types

**Content:**
- Agent names, roles, capabilities
- Model assignments per agent
- Workflow definitions

**v6 Compatibility:**
- ⚠️  v6 uses different agent structure
- ⚠️  May hardcode v5 agent names

**Needs:**
- Update for v6 agent structure
- Check if still needed

---

### 10. UnifiedChatMixin.ts (403 lines) - CHAT MIXIN

**Status:** 🔴 v5 PATTERNS

**Purpose:** Mixin for chat functionality

**Features:**
- Message handling
- Conversation management
- UI helpers

**v6 Compatibility:**
- ⚠️  Uses v5 message patterns
- ⚠️  May expect v5 responses

**Needs:**
- Review and update for v6
- Or remove if obsolete

---

### 11. index.ts (191 lines) - TYPE EXPORTS

**Status:** ℹ️  TYPE DEFINITIONS ONLY

**Purpose:** Re-export all types

**Action:** Update when other types are updated

---

## Settings Inventory

### Extension Settings (package.json)

```json
{
  "kiAutoAgent.backend.url": "localhost:8002",
  "kiAutoAgent.openai.apiKey": "",
  "kiAutoAgent.anthropic.apiKey": "",
  "kiAutoAgent.perplexity.apiKey": "",

  "kiAutoAgent.defaultAgent": "orchestrator",
  "kiAutoAgent.conversationAutoSave": true,

  "kiAutoAgent.models.autoDiscover": true,
  "kiAutoAgent.models.research.provider": "openai",
  "kiAutoAgent.models.research.model": "gpt-4",
  // ... per-agent model settings ...

  "kiAutoAgent.ui.theme": "dark",
  "kiAutoAgent.ui.fontSize": 14
}
```

### v6 Compatibility:

| Setting | v6 Status | Action |
|---------|-----------|--------|
| backend.url | ✅ Used | Keep |
| apiKey.* | ⚠️  Backend manages | Mark deprecated? |
| defaultAgent | ⚠️  v6 = orchestrator only | Update description |
| models.* | ⚠️  No discovery in v6 | Disable or remove |
| ui.* | ✅ Used | Keep |

---

## Priority Issues for v6

### HIGH PRIORITY (Blocking v6 usage):

1. **MultiAgentChatPanel.ts** - 2478 lines of mostly v5 code
   - Remove architecture approval UI
   - Remove pause/resume/rollback
   - Update agent selection for v6
   - Fix message rendering for v6 types

2. **BackendManager.ts** - Should be deleted
   - Remove file
   - Remove imports

3. **Model Settings** - Discovery doesn't work
   - Either implement v6 endpoint
   - Or remove feature

### MEDIUM PRIORITY (Works but suboptimal):

4. **IntentTypes.ts** - Duplicate of v6 Query Classifier
   - Check if needed
   - Update or remove

5. **SystemKnowledge.ts** - Outdated knowledge
   - Update for v6
   - Or fetch from backend

6. **Agent Configurations** - v5 patterns
   - Update for v6 structure

### LOW PRIORITY (Not critical):

7. **Memory types** - May not match v6
   - Verify and update

8. **UnifiedChatMixin** - v5 patterns
   - Review and modernize

---

## Recommendations

### For Now (Quick Fixes):

1. DELETE BackendManager.ts
2. Mark v5-only features as "Not available in v6"
3. Disable model discovery permanently
4. Update MultiAgentChatPanel to show v6 messages

### For Later (Major Refactor):

1. Rewrite MultiAgentChatPanel for v6
2. Remove all v5-specific UI elements
3. Simplify agent selection (orchestrator only)
4. Update type definitions for v6
5. Clean up unused code

---

## Next Steps

1. Run REAL test to see what actually breaks
2. Fix critical bugs found in test
3. Mark v5 features as disabled
4. Plan major refactor for post-v6.0.0

**Total Code Debt:** ~3000 lines of v5 code needs refactor/removal
**Critical Files:** 3 (MultiAgentChatPanel, BackendManager, modelSettings)
**Time Estimate:** 1-2 days for critical fixes, 1 week for complete refactor
