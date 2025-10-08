# Changelog

## [5.9.1] - 2025-10-08

### Fixed
- **Critical**: Fixed premature webview disposal causing "Webview disposed" errors
  - Race conditions were marking webview as disposed too early
  - Messages were being dropped even when panel was still active
  - Now only dispose() method sets _isDisposed flag
  - Location: `src/ui/MultiAgentChatPanel.ts:639-643`

### Changed
- Extension version bumped to 5.9.1
- Improved error logging for webview message sending

## [5.9.0] - 2025-10-07

### Added
- Better undefined content filtering in agent thinking messages (Bug #6)

### Fixed
- **Bug #6**: Filter out "undefined" content from agent thinking messages before displaying
  - Added validation in BackendClient thinking event handler
  - Prevents "💭 undefined" from appearing in chat UI
  - Location: `src/ui/MultiAgentChatPanel.ts:185-199`

### Changed (OBSOLETE Marking)
- **Bug #7**: Marked pause/resume backend calls as OBSOLETE (not removed)
  - Backend doesn't support pause/resume message types yet
  - Prevents "Unknown message type: pause/resume" errors
  - UI-only pause/resume functionality still works
  - Backend integration marked for future implementation
  - Location: `src/ui/MultiAgentChatPanel.ts:446-491`
  - **Note**: Code not deleted, marked OBSOLETE per CODE REFACTORING BEST PRACTICES

### Technical Details
- Extension version bumped from 5.8.1 to 5.9.0
- Following OBSOLETE code handling protocol from CLAUDE.md
- All changes maintain backwards compatibility
- No breaking changes to API or user workflow

### Breaking Changes
- None

### Migration Guide
- No migration needed
- Simply reload VS Code window after update
- All existing chats and history remain functional

---

## [5.8.1] - Previous Release
- Multi-client WebSocket architecture
- Backend as global service
- Workspace-specific data isolation

---

**Full Changelog**: https://github.com/dominikfoert/KI_AutoAgent/compare/v5.8.1...v5.9.0
