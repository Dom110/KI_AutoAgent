#!/bin/bash
# Monitor E2E Test Progress
# Shows latest test output and backend logs

echo "🔍 E2E Test Monitor"
echo "===================="
echo ""

echo "📊 Test Output (last 20 lines):"
echo "--------------------------------"
tail -20 test_comprehensive_output.log 2>/dev/null || echo "No test output yet"

echo ""
echo "🖥️  Backend Logs (last 10 lines):"
echo "--------------------------------"
tail -10 /tmp/v6_server.log 2>/dev/null || echo "No backend logs"

echo ""
echo "📁 Generated Files:"
echo "-------------------"
ls -lh ~/TestApps/v6_2_comprehensive_test/ 2>/dev/null | tail -10 || echo "No files yet"

echo ""
echo "⏱️  Updated: $(date '+%H:%M:%S')"
