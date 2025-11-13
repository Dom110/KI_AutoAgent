#!/usr/bin/env python3
"""
🔍 Debug MCP Server Crash Issue
Analyze what's causing the research_agent server to restart
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger(__name__)

def analyze_mcp_logs():
    """Analyze MCP server logs to find crash reasons"""
    
    log_file = Path("/tmp/mcp_research_agent.log")
    if not log_file.exists():
        log.error("❌ No research agent log found")
        return
    
    lines = log_file.read_text().splitlines()
    
    log.info("=" * 80)
    log.info("🔍 ANALYZING RESEARCH AGENT MCP SERVER LOGS")
    log.info("=" * 80)
    
    # Find all server start messages
    start_times = []
    for i, line in enumerate(lines):
        if "🚀 Research MCP Server starting" in line:
            start_times.append((i, line))
    
    log.info(f"\n📊 Found {len(start_times)} server restarts:")
    for idx, (line_num, line) in enumerate(start_times):
        log.info(f"   #{idx + 1} at line {line_num}: {line[60:]}")
    
    # Analyze gaps between restarts
    log.info("\n⏱️ ANALYZING GAPS BETWEEN RESTARTS:")
    for i in range(len(start_times) - 1):
        start_line = start_times[i][0]
        next_start_line = start_times[i + 1][0]
        
        # Get last 20 lines before next restart
        gap_lines = lines[max(0, start_line):next_start_line]
        
        log.info(f"\n   Gap #{i+1}: Lines {start_line} to {next_start_line}")
        log.info(f"   ⚠️ Duration before restart: {next_start_line - start_line} lines")
        
        # Look for errors or unusual activity
        for j, line in enumerate(gap_lines[-20:], start=len(gap_lines)-20):
            if "ERROR" in line or "error" in line.lower():
                log.info(f"      ❌ ERROR at line {start_line + j}: {line[60:]}")
            elif "Exception" in line or "exception" in line.lower():
                log.info(f"      ❌ EXCEPTION at line {start_line + j}: {line[60:]}")
            elif "Traceback" in line:
                log.info(f"      ❌ TRACEBACK at line {start_line + j}")
            elif "receive_response_headers.started" in line:
                log.info(f"      🌐 OpenAI request at line {start_line + j}: {line[60:]}")
            elif "receive_response_body" in line:
                log.info(f"      📥 Receiving response at line {start_line + j}")
    
    # Find OpenAI request/response activity
    log.info("\n🌐 OPENAI API ACTIVITY:")
    openai_starts = []
    openai_completes = []
    
    for i, line in enumerate(lines):
        if "receive_response_headers.started" in line and "openai" in lines[max(0, i-5):i].__str__().lower():
            openai_starts.append((i, line))
        elif "receive_response_headers.complete" in line:
            openai_completes.append((i, line))
        elif "HTTP Request:" in line and "200 OK" in line:
            log.info(f"   ✅ HTTP 200 OK at line {i}")
    
    log.info(f"   Started: {len(openai_starts)} requests")
    log.info(f"   Completed: {len(openai_completes)} responses")
    
    if len(openai_starts) > len(openai_completes):
        log.warning(f"   ⚠️ {len(openai_starts) - len(openai_completes)} requests without responses!")
    
    # Find the exact restart point
    if start_times and len(start_times) > 1:
        restart_line = start_times[1][0]
        log.info(f"\n📍 EXAMINING RESTART POINT (line {restart_line}):")
        
        # Show context around restart
        context_start = max(0, restart_line - 10)
        context_end = min(len(lines), restart_line + 5)
        
        for i in range(context_start, context_end):
            marker = " >>> " if i == restart_line else "     "
            log.info(f"{marker} Line {i}: {lines[i][60:100] if len(lines[i]) > 60 else lines[i]}")
    
    # Check for resource issues
    log.info("\n🔧 CHECKING FOR RESOURCE/TIMEOUT ISSUES:")
    for i, line in enumerate(lines[-100:], start=len(lines)-100):
        if "timeout" in line.lower():
            log.warning(f"   ⏱️ Timeout at line {i}: {line[60:]}")
        elif "killed" in line.lower() or "SIGTERM" in line or "SIGKILL" in line:
            log.error(f"   💀 Process killed at line {i}: {line[60:]}")
        elif "Memory" in line or "memory" in line.lower():
            log.warning(f"   💾 Memory issue at line {i}: {line[60:]}")
    
    log.info("\n" + "=" * 80)
    log.info("✅ ANALYSIS COMPLETE")
    log.info("=" * 80)


if __name__ == "__main__":
    analyze_mcp_logs()
