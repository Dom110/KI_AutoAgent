#!/bin/bash
# Monitor E2E Test Progress
# Checks every 30 seconds until Phase 3 is reached

LOG_FILE="/tmp/e2e_test_output.log"
CHECK_INTERVAL=30

echo "🔍 Monitoring E2E Test Progress..."
echo "   Log file: $LOG_FILE"
echo "   Checking every ${CHECK_INTERVAL}s"
echo ""

while true; do
    # Check if log file exists
    if [ ! -f "$LOG_FILE" ]; then
        echo "❌ Log file not found: $LOG_FILE"
        exit 1
    fi

    # Get current timestamp
    NOW=$(date '+%H:%M:%S')

    # Check for Phase 1 completion
    if grep -q "✅ Phase 1: COMPLETE" "$LOG_FILE"; then
        if ! grep -q "PHASE 1 COMPLETED" /tmp/e2e_monitor_state 2>/dev/null; then
            echo "[$NOW] ✅ Phase 1: COMPLETE"
            echo "PHASE 1 COMPLETED" >> /tmp/e2e_monitor_state
        fi
    fi

    # Check for Phase 2 start
    if grep -q "PHASE 2: AUTOMATIC BUILD VALIDATION" "$LOG_FILE"; then
        if ! grep -q "PHASE 2 STARTED" /tmp/e2e_monitor_state 2>/dev/null; then
            echo "[$NOW] 🚀 Phase 2: STARTED"
            echo "PHASE 2 STARTED" >> /tmp/e2e_monitor_state
        fi
    fi

    # Check for Phase 2 completion
    if grep -q "✅ Phase 2: COMPLETE" "$LOG_FILE"; then
        if ! grep -q "PHASE 2 COMPLETED" /tmp/e2e_monitor_state 2>/dev/null; then
            echo "[$NOW] ✅ Phase 2: COMPLETE"
            echo "PHASE 2 COMPLETED" >> /tmp/e2e_monitor_state
        fi
    fi

    # Check for Phase 3 start (MANUAL REVIEW)
    if grep -q "PHASE 3: MANUAL REVIEW WITH PLAYGROUND" "$LOG_FILE"; then
        echo ""
        echo "================================================================================"
        echo "🎯 PHASE 3 REACHED - MANUAL REVIEW REQUIRED"
        echo "================================================================================"
        echo ""
        echo "Phase 1 & 2 completed successfully!"
        echo "Now starting Phase 3: Manual Review with Playground"
        echo ""
        echo "Next steps:"
        echo "  1. Check the output above for application location"
        echo "  2. Start backend and frontend"
        echo "  3. Test all features manually"
        echo "  4. Run Claude Code playground review"
        echo "  5. Press Enter in the test terminal when done"
        echo ""
        echo "The test is waiting for your input..."
        echo ""

        # Mark as reached
        echo "PHASE 3 REACHED" >> /tmp/e2e_monitor_state

        # Exit monitoring
        exit 0
    fi

    # Check for errors
    if grep -q "❌ E2E TEST FAILED" "$LOG_FILE"; then
        echo ""
        echo "❌ Test failed - check logs for details"
        tail -50 "$LOG_FILE"
        exit 1
    fi

    # Show progress indicator
    echo -n "."

    # Wait before next check
    sleep $CHECK_INTERVAL
done
