#!/bin/bash
"""
KI AutoAgent MCP Server Test Suite

Runs all production MCP server tests:
1. Perplexity Server (3 tests) - Web search
2. Tree-sitter Server (6 tests) - Code analysis
3. Memory Server (8 tests) - Agent memory
4. Asimov Server (10 tests) - Code safety

Total: 27 tests

Usage:
    ./test_all_mcp.sh

Author: KI AutoAgent Team
Version: 1.0.0
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}KI AutoAgent MCP Server Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Use backend venv Python (has all dependencies)
VENV_PYTHON="${SCRIPT_DIR}/backend/venv_v6/bin/python"

# Test 1: Perplexity Server
echo -e "${YELLOW}1️⃣  Testing Perplexity Server...${NC}"
echo ""
if "$VENV_PYTHON" "${SCRIPT_DIR}/test_perplexity_mcp.py"; then
    echo -e "${GREEN}✅ Perplexity Server: PASSED (3/3)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 3))
else
    echo -e "${RED}❌ Perplexity Server: FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 3))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 3))
echo ""

# Test 2: Tree-sitter Server
echo -e "${YELLOW}2️⃣  Testing Tree-sitter Server...${NC}"
echo ""
if "$VENV_PYTHON" "${SCRIPT_DIR}/test_tree_sitter_mcp.py"; then
    echo -e "${GREEN}✅ Tree-sitter Server: PASSED (6/6)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 6))
else
    echo -e "${RED}❌ Tree-sitter Server: FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 6))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 6))
echo ""

# Test 3: Memory Server
echo -e "${YELLOW}3️⃣  Testing Memory Server...${NC}"
echo ""
if "$VENV_PYTHON" "${SCRIPT_DIR}/test_memory_mcp.py"; then
    echo -e "${GREEN}✅ Memory Server: PASSED (8/8)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 8))
else
    echo -e "${RED}❌ Memory Server: FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 8))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 8))
echo ""

# Test 4: Asimov Server
echo -e "${YELLOW}4️⃣  Testing Asimov Rules Server...${NC}"
echo ""
if "$VENV_PYTHON" "${SCRIPT_DIR}/test_asimov_mcp.py"; then
    echo -e "${GREEN}✅ Asimov Server: PASSED (10/10)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 10))
else
    echo -e "${RED}❌ Asimov Server: FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 10))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 10))
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Tests:  ${TOTAL_TESTS}"
echo -e "Passed:       ${GREEN}${PASSED_TESTS} ✅${NC}"
echo -e "Failed:       ${RED}${FAILED_TESTS} ❌${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}MCP Servers Status:${NC}"
    echo -e "  1. ${GREEN}Perplexity${NC} - 3/3 tests passed (Web search)"
    echo -e "  2. ${GREEN}Tree-sitter${NC} - 6/6 tests passed (Code analysis)"
    echo -e "  3. ${GREEN}Memory${NC} - 8/8 tests passed (Agent memory)"
    echo -e "  4. ${GREEN}Asimov${NC} - 10/10 tests passed (Code safety)"
    echo ""
    echo -e "${GREEN}All systems operational! 🚀${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Please review errors above.${NC}"
    exit 1
fi
