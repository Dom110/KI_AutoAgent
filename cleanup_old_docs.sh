#!/bin/bash
# Script to archive old documentation files
# Date: 2025-10-13

# Create archive directory
ARCHIVE_DIR="docs_archive_$(date +%Y%m%d)"
mkdir -p "$ARCHIVE_DIR"

echo "📁 Moving old documentation to $ARCHIVE_DIR/"

# Move old version-specific docs (keeping only current v6.2)
OLD_VERSION_DOCS=(
    "MIGRATION_GUIDE_v4.md"
    "V4_RELEASE_SUMMARY.md"
    "RELEASE_NOTES_4.0.1.md"
    "VERSION_5.0.0_RELEASE_NOTES.md"
    "RELEASE_NOTES_v5.2.3.md"
    "V6_0_0_INTEGRATION_COMPLETE.md"
    "V6_0_ARCHITECTURE.md"
    "V6_0_COMPLETE_TEST_PLAN.md"
    "V6_0_DEBUGGING.md"
    "V6_0_KNOWN_ISSUES.md"
    "V6_0_MIGRATION_LOG.md"
    "V6_0_MIGRATION_PLAN.md"
    "V6_0_PHASE_8_STATUS.md"
    "V6_0_TEST_RESULTS.md"
    "V6_1_MIGRATION_COMPLETE.md"
    "V6_1_STATUS.md"
    "V6_AUTONOMOUS_IMPLEMENTATION_SESSION.md"
    "V6_COMPLETE_AUDIT.md"
    "V6_FINAL_IMPLEMENTATION_REPORT.md"
    "V6_FINAL_SYSTEM_DOCUMENTATION.md"
    "V6_IMPLEMENTATION_ANALYSIS.md"
    "V6_IMPLEMENTATION_STATUS.md"
    "V6_INTEGRATION_COMPLETE.md"
    "V6_SESSION_2_IMPLEMENTATION_REPORT.md"
)

# Move old session summaries (keeping only recent ones)
OLD_SESSION_DOCS=(
    "SESSION_SUMMARY_2025-10-10_COMPLETE.md"
    "SESSION_SUMMARY_2025-10-10_FINAL.md"
    "SESSION_SUMMARY_2025-10-10_PHASE1_COMPLETE.md"
    "SESSION_SUMMARY_2025-10-10_PHASE2_PART2_COMPLETE.md"
    "SESSION_SUMMARY_2025-10-10_PHASE2_PART3_COMPLETE.md"
    "SESSION_SUMMARY_2025-10-11_BUGFIX.md"
    "SESSION_SUMMARY_2025-10-11_COMPLETE.md"
    "SESSION_FINAL_2025-10-11_COMPLETE.md"
)

# Move old test results (keeping only recent ones)
OLD_TEST_DOCS=(
    "E2E_TEST_RESULTS_20251011_214459.md"
    "E2E_TEST_RESULTS_20251011_220807.md"
    "TEST_FINDINGS_2025-10-09.md"
    "TEST_RESULTS_2025-10-10.md"
)

# Move old Python/system docs (keeping only current)
OLD_SYSTEM_DOCS=(
    "PYTHON_3.13_COMPLIANCE_REPORT.md"
    "PYTHON_3.13_IMPLEMENTATION_PLAN.md"
    "PYTHON_3.13_IMPLEMENTATION_COMPLETE.md"
    "PYTHON_MODERNIZATION_v5.9.0.md"
    "SYSTEM_ARCHITECTURE_v5.9.0.md"
    "PERFORMANCE_OPTIMIZATION_REPORT_v5.9.0.md"
    "CODE_AUDIT_REPORT_v5.9.0.md"
    "CONTINUATION_PLAN_v5.9.0.md"
    "TEST_FEATURES_v5.9.0.md"
    "TEST_REPORT_v5.9.0.md"
    "BUG_FIXES_v5.9.0.md"
    "VERSION_NOTES_v5.9.0.md"
)

# Move old analysis/implementation docs
OLD_IMPLEMENTATION_DOCS=(
    "ARCHITECTURE_ANALYSIS_2025-10-09.md"
    "ARCHITECTURE_DECISION_INCREMENTAL_BUILD.md"
    "ACTUAL_PERFORMANCE_REPORT_2025-10-10.md"
    "DEPENDENCY_RESOLUTION_REPORT.md"
    "EXTENSION_ANALYSIS.md"
    "IMPLEMENTATION_LOG.md"
    "INTELLIGENT_FLOW_DESIGN.md"
    "ISSUES_AND_PLAN_v5.9.2.md"
    "PHASE_3_COMPLETE.md"
    "PRODUCTION_DEPLOYMENT_2025-10-10.md"
)

# Old feature docs (superseded by v6.2)
OLD_FEATURE_DOCS=(
    "BUG_FIXES_V6_1.md"
    "E2E_TEST_RESULTS_V6_2_PHASE2.md"
    "V6.2_IMPLEMENTATION_ROADMAP.md"  # Superseded by ARCHITECTURE_v6.2_CURRENT.md
)

# Function to move files
move_file() {
    if [ -f "$1" ]; then
        echo "  📄 Moving: $1"
        mv "$1" "$ARCHIVE_DIR/"
    fi
}

# Move all old docs
echo "📚 Moving old version documentation..."
for doc in "${OLD_VERSION_DOCS[@]}"; do
    move_file "$doc"
done

echo "📅 Moving old session summaries..."
for doc in "${OLD_SESSION_DOCS[@]}"; do
    move_file "$doc"
done

echo "🧪 Moving old test results..."
for doc in "${OLD_TEST_DOCS[@]}"; do
    move_file "$doc"
done

echo "🐍 Moving old system documentation..."
for doc in "${OLD_SYSTEM_DOCS[@]}"; do
    move_file "$doc"
done

echo "🔧 Moving old implementation docs..."
for doc in "${OLD_IMPLEMENTATION_DOCS[@]}"; do
    move_file "$doc"
done

echo "📝 Moving superseded feature docs..."
for doc in "${OLD_FEATURE_DOCS[@]}"; do
    move_file "$doc"
done

# Count moved files
MOVED_COUNT=$(ls -1 "$ARCHIVE_DIR" 2>/dev/null | wc -l)

echo ""
echo "✅ Archive complete!"
echo "   📁 Files moved to: $ARCHIVE_DIR/"
echo "   📊 Total files archived: $MOVED_COUNT"
echo ""
echo "📌 Current documentation kept:"
echo "   - ARCHITECTURE_v6.2_CURRENT.md (main architecture)"
echo "   - CHANGELOG_v6.2.0-alpha.md (latest changelog)"
echo "   - CLAUDE.MD (Claude instructions)"
echo "   - README.md (project readme)"
echo "   - MISSING_FEATURES.md (feature tracking)"
echo "   - V6.1_ROADMAP.md (future planning)"
echo "   - PYTHON_BEST_PRACTICES.md (coding standards)"
echo "   - CLAUDE_BEST_PRACTICES.md (Claude usage)"
echo "   - MCP_* docs (MCP integration)"
echo "   - E2E test docs (recent tests)"