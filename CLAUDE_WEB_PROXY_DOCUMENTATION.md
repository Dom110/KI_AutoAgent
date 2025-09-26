# Claude Web Proxy Documentation
## Status: DEPRECATED - Replaced by ClaudeCodeService
## Date: 2025-09-26

## Overview
Claude Web Proxy was the original method for integrating Claude into the KI AutoAgent system before the Claude Code CLI became available. It has been completely replaced by ClaudeCodeService which uses the official Claude Code CLI.

## Migration History
- **Original**: ClaudeWebProxy (browser automation)
- **Current**: ClaudeCodeService (Claude Code CLI)
- **Migration Date**: September 2025

## Deprecated Components

### 1. Claude Web Proxy Folder (`claude_web_proxy/`)
**Status**: Keep temporarily for reference
**Contents**:
- Browser automation scripts using Playwright
- Login flow automation
- Cookie management
- Session handling
- Test scripts

**Files**:
- `api_client.py` - Main API client for browser automation
- `browser_api.py` - Browser control interface
- `debug_browser_api.py` - Debug version with temp_profile
- `quick_test.py` - Test script
- `setup_and_test.py` - Setup verification
- `setup_report.md` - Setup documentation

### 2. Browser Profile (`temp_profile/`)
**Status**: DELETED
**Purpose**: Stored browser profile for persistent sessions
**Usage**: Only used by debug_browser_api.py

### 3. Integration Files (Archived)
**Location**: `archived_typescript_implementation/claude_web_related/`
- `debug_login_flow.py` - Login debugging
- `claude_web_integration_complete.py` - Full integration test

### 4. Example Files
**Location**: `examples/`
- `multi_agent_claude_web_demo.py` - Multi-agent demo (deprecated)
- `claude_web_integration_example.py` - Integration example (deprecated)

## Current System: ClaudeCodeService

### Location
`backend/utils/claude_code_service.py`

### Features
- Direct integration with Claude Code CLI
- No browser automation needed
- Official API support
- Streaming responses
- Tool usage support
- Faster and more reliable

### Usage by Agents
Currently used by:
- CodeSmithAgent
- FixerBotAgent
- TradeStratAgent
- OpusArbitratorAgent

## Why Claude Web Proxy Was Replaced

1. **Reliability**: Browser automation was fragile
2. **Performance**: CLI is much faster
3. **Official Support**: Claude Code CLI is officially supported
4. **Maintenance**: No need to maintain browser automation
5. **Security**: No cookie/session management needed

## Cleanup Recommendations

### Can Delete Now:
- ✅ `temp_profile/` - Already deleted
- ✅ Old TypeScript agents using ClaudeWebProxy - Already archived

### Keep for Reference (30 days):
- ⏸️ `claude_web_proxy/` folder - Document browser automation approach
- ⏸️ Example files - Show migration path

### After 30 Days:
- Delete `claude_web_proxy/` folder completely
- Delete deprecated examples
- Remove from .gitignore

## Migration Checklist

✅ **Completed**:
- [x] All agents migrated to ClaudeCodeService
- [x] No active code uses ClaudeWebProxy
- [x] temp_profile deleted
- [x] Old agents archived
- [x] Backend fully uses ClaudeCodeService

⏸️ **Pending** (after stability verification):
- [ ] Delete claude_web_proxy folder (after 30 days)
- [ ] Clean examples folder
- [ ] Update documentation to remove references

## Configuration Changes

### Old (ClaudeWebProxy):
```python
from claude_web_proxy.api_client import ClaudeWebAPIClient
client = ClaudeWebAPIClient()
await client.login()
response = await client.send_message(prompt)
```

### New (ClaudeCodeService):
```python
from backend.utils.claude_code_service import ClaudeCodeService
service = ClaudeCodeService(model="claude-sonnet-4-20250514")
response = await service.send_message(prompt)
```

## Notes
- The claude_web_proxy folder is 3MB and contains valuable documentation about browser automation approaches
- Keep for historical reference and potential future needs
- The approach might be useful for other browser automation projects
- Complete removal scheduled for: **2025-10-26** (30 days from now)