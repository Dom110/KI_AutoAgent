# Cleanup Plan v6.1

**Created:** 2025-10-12
**Status:** Planning Phase
**Goal:** Remove obsolete code and tests, streamline repository

---

## 📊 Current Repository Analysis

### Obsolete Files Count
```bash
# Total obsolete Python files: 3,278
# OBSOLETE_SYSTEMS size: 131 MB
# Obsolete directories: 4+
```

### Identified Obsolete Directories

#### 1. **OBSOLETE_SYSTEMS/** (131 MB)
- `BACKUP_OLD_archived_typescript_implementation/`
- `langgraph_system_v5/` (replaced by v6)
- `old_tests/` (calculator app tests from v5.8.5)
- **Action:** Keep as archive (already clearly marked)
- **Reason:** Historical reference, may contain useful patterns

#### 2. **BACKUP_OLD_ki_autoagent/** (size TBD)
- Old backup from previous migration
- **Action:** DELETE (redundant with OBSOLETE_SYSTEMS)
- **Reason:** Duplicate backup

#### 3. **test_workspace_e2e_v586/**
- Old E2E test workspace from v5.8.6
- **Action:** DELETE
- **Reason:** v6 uses different workspace structure

#### 4. **tests/** (root level, not backend/tests/)
- Old test structure from v5
- Contains: test_agent_file_capabilities.py, test_integration.py, etc.
- **Action:** REVIEW then DELETE
- **Reason:** All v6 tests are in backend/tests/

---

## 🗑️ Cleanup Actions

### Phase 1: Safe Deletions (Low Risk)

#### Delete Redundant Backups
```bash
# These are duplicates or clearly obsolete
rm -rf BACKUP_OLD_ki_autoagent/
rm -rf test_workspace_e2e_v586/
rm -rf .kiautoagent/  # If exists - old config structure
```

**Impact:** ~50-100 MB freed
**Risk:** LOW (clear duplicates)

#### Delete Root-Level Old Tests
```bash
# Move to OBSOLETE_SYSTEMS first (safety)
mkdir -p OBSOLETE_SYSTEMS/old_root_tests_v5
mv tests/ OBSOLETE_SYSTEMS/old_root_tests_v5/

# After verification (1-2 days), delete:
# rm -rf OBSOLETE_SYSTEMS/old_root_tests_v5/
```

**Impact:** ~5-10 MB freed
**Risk:** LOW (v6 tests all in backend/tests/)

### Phase 2: Test File Audit (Medium Risk)

#### Review backend/tests/
Current test files (23 total):
- ✅ **KEEP:** `test_websocket_simple.py` (v6 E2E test)
- ✅ **KEEP:** `test_build_validation.py` (v6.0 feature)
- ✅ **KEEP:** `test_build_validation_e2e.py` (v6.0 feature)
- ✅ **KEEP:** `test_e2e_comprehensive_v6.py` (v6 comprehensive test)

**Old Tests to Archive:**
- ⏳ `test_chat_anthropic_direct.py` - v6.0 development test
- ⏳ `test_claude_cli_adapter.py` - v6.0 development test
- ⏳ `test_phase_7_full_workflow.py` - v6 migration test
- ⏳ `test_phase_8_workflow_execution.py` - v6 migration test
- ⏳ `test_phases_4_5_structure.py` - v6 migration test
- ⏳ `test_research_structure_v6.py` - structure test (may keep)
- ⏳ `test_reviewfix_structure.py` - structure test (may keep)

**Action Plan:**
1. Run all tests to see which still work
2. Archive non-functional tests to OBSOLETE_SYSTEMS/
3. Keep only working v6.1 tests

### Phase 3: Code Audit (High Risk - Manual Review)

#### Search for TODOs/FIXMEs
```bash
# Found 1,412 TODOs in backend/ (from earlier grep)
grep -r "TODO\|FIXME\|HACK\|XXX" backend/ --include="*.py" > TODO_AUDIT.txt
```

**Action:**
1. Review TODO_AUDIT.txt
2. Categorize TODOs:
   - Critical (must fix)
   - Nice-to-have (roadmap)
   - Obsolete (delete)
3. Create GitHub issues for critical TODOs
4. Remove obsolete TODOs

#### Identify Dead Code
```bash
# Files not imported or used anywhere
# Use tools like: vulture, coverage.py
pip install vulture
vulture backend/ --min-confidence 80 > DEAD_CODE_REPORT.txt
```

**Action:**
1. Review DEAD_CODE_REPORT.txt
2. Verify code is truly unused
3. Move to OBSOLETE_SYSTEMS or delete

---

## 📋 Cleanup Checklist

### Immediate (Today)
- [ ] Delete BACKUP_OLD_ki_autoagent/
- [ ] Delete test_workspace_e2e_v586/
- [ ] Move root tests/ to OBSOLETE_SYSTEMS/old_root_tests_v5/

### Short Term (This Week)
- [ ] Run all backend/tests/ and identify failing tests
- [ ] Archive failing/obsolete tests
- [ ] Create TODO_AUDIT.txt and categorize
- [ ] Create DEAD_CODE_REPORT.txt

### Medium Term (Next Week)
- [ ] Review and fix critical TODOs
- [ ] Remove obsolete TODOs
- [ ] Remove dead code (after verification)
- [ ] Update documentation to reflect cleanup

### Long Term (v6.2)
- [ ] Consider removing entire OBSOLETE_SYSTEMS/ (after 6 months)
- [ ] Archive old documentation files
- [ ] Clean up root-level .md files (100+ files)

---

## 🎯 Expected Results

### Before Cleanup
- Repository size: ~500-600 MB
- Python files: ~4,000+
- Test files: 40+
- Documentation files: 100+

### After Cleanup
- Repository size: ~300-400 MB (33% reduction)
- Python files: ~700-800 (working code only)
- Test files: 10-15 (working v6 tests only)
- Documentation files: 20-30 (current + essential)

### Benefits
- ✅ Faster git operations (clone, pull, checkout)
- ✅ Clearer codebase structure
- ✅ Easier onboarding for new developers
- ✅ Reduced confusion about what's current
- ✅ Better IDE performance (fewer files to index)

---

## ⚠️ Safety Measures

### Before ANY Deletion:
1. **Create backup branch:**
   ```bash
   git checkout -b pre-cleanup-backup
   git push origin pre-cleanup-backup
   ```

2. **Tag current state:**
   ```bash
   git tag v6.1-alpha-pre-cleanup
   git push origin v6.1-alpha-pre-cleanup
   ```

3. **Archive to OBSOLETE_SYSTEMS first:**
   - Never delete directly
   - Always move to OBSOLETE_SYSTEMS/
   - Wait 1-2 days before final deletion

4. **Document what was removed:**
   - Create CLEANUP_LOG.md
   - List all removed files/directories
   - Explain why each was removed

### Recovery Plan
If something breaks after cleanup:
```bash
# Restore from backup tag
git checkout v6.1-alpha-pre-cleanup

# Or restore specific file
git checkout v6.1-alpha-pre-cleanup -- path/to/file.py
```

---

## 🚀 Next Steps

1. **User Approval Required**
   - Review this cleanup plan
   - Approve immediate deletions
   - Prioritize which phases to execute

2. **Execute Phase 1** (if approved)
   - Create backup branch and tag
   - Execute safe deletions
   - Commit and push

3. **Report Results**
   - List freed space
   - List removed files
   - Confirm no breakage

---

**Last Updated:** 2025-10-12
**Next Review:** After Phase 1 execution
