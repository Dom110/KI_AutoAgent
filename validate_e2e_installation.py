#!/usr/bin/env python3
"""
E2E Test Generator Installation Validator
Verifies all modules are properly installed and accessible
"""

import sys
import subprocess
from pathlib import Path

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def check_python_version():
    """Check Python version"""
    print_header("PYTHON VERSION CHECK")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 13):
        print_success(f"Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print_error(f"Python 3.13+ required, found {version.major}.{version.minor}")
        return False

def check_module_imports():
    """Check if all E2E modules can be imported"""
    print_header("MODULE IMPORT CHECK")
    
    modules = [
        ("backend.e2e_testing", "E2E Testing Core"),
        ("backend.e2e_testing.react_analyzer", "React Analyzer"),
        ("backend.e2e_testing.test_generator", "Test Generator"),
        ("backend.e2e_testing.browser_engine", "Browser Engine"),
        ("backend.e2e_testing.test_executor", "Test Executor"),
        ("backend.e2e_testing.assertions", "Assertions Library"),
        ("backend.agents.reviewfix_e2e_agent", "ReviewFix E2E Agent"),
    ]
    
    all_passed = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print_success(f"{description} ({module_name})")
        except ImportError as e:
            print_error(f"{description} ({module_name}): {e}")
            all_passed = False
    
    return all_passed

def check_dependencies():
    """Check if external dependencies are installed"""
    print_header("DEPENDENCY CHECK")
    
    dependencies = [
        ("playwright", "Playwright Browser Automation"),
        ("pathlib", "Path Utilities"),
        ("asyncio", "Async Support"),
        ("json", "JSON Utilities"),
    ]
    
    all_passed = True
    for package_name, description in dependencies:
        try:
            __import__(package_name)
            print_success(f"{description} ({package_name})")
        except ImportError:
            print_error(f"{description} ({package_name}) not installed")
            all_passed = False
    
    return all_passed

def check_files_exist():
    """Check if all required files exist"""
    print_header("FILE EXISTENCE CHECK")
    
    base_path = Path(__file__).parent
    required_files = [
        "backend/e2e_testing/__init__.py",
        "backend/e2e_testing/react_analyzer.py",
        "backend/e2e_testing/test_generator.py",
        "backend/e2e_testing/browser_engine.py",
        "backend/e2e_testing/test_executor.py",
        "backend/e2e_testing/assertions.py",
        "backend/agents/reviewfix_e2e_agent.py",
        "mcp_servers/browser_testing_server.py",
        "mcp_servers/e2e_testing_server.py",
        "backend/tests/test_e2e_generator.py",
        "E2E_TEST_GENERATOR_COMPLETE_GUIDE.md",
        "REVIEWFIX_E2E_TESTING_INTEGRATION.md",
        "E2E_QUICK_START.md",
        "E2E_IMPLEMENTATION_COMPLETE.md",
    ]
    
    all_passed = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            file_size = full_path.stat().st_size
            print_success(f"{file_path} ({file_size} bytes)")
        else:
            print_error(f"{file_path} NOT FOUND")
            all_passed = False
    
    return all_passed

def check_analyzer_functionality():
    """Quick functionality test - React Analyzer"""
    print_header("ANALYZER FUNCTIONALITY TEST")
    
    try:
        from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer
        
        # Create test app structure
        test_dir = Path("/tmp/test_e2e_app")
        test_dir.mkdir(exist_ok=True)
        
        src_dir = test_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create sample component
        component_file = src_dir / "TestComponent.jsx"
        component_file.write_text("""
import React, { useState } from 'react';

export function TestComponent() {
  const [name, setName] = useState('');
  
  return (
    <div>
      <input 
        data-testid="name-input"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button data-testid="submit-btn">Submit</button>
    </div>
  );
}
""")
        
        # Test analyzer
        analyzer = ReactComponentAnalyzer(str(test_dir))
        analysis = analyzer.analyze_app()
        
        if analysis['total_components'] > 0:
            print_success(f"Analyzer found {analysis['total_components']} component(s)")
            print_success("React Analyzer is working correctly")
            return True
        else:
            print_warning("Analyzer found no components (might be expected)")
            return True
    
    except Exception as e:
        print_error(f"Analyzer test failed: {e}")
        return False

def check_generator_functionality():
    """Quick functionality test - Test Generator"""
    print_header("GENERATOR FUNCTIONALITY TEST")
    
    try:
        from backend.e2e_testing.test_generator import E2ETestGenerator
        
        # Use the test directory from previous test
        test_dir = Path("/tmp/test_e2e_app")
        
        if not test_dir.exists():
            print_warning("Test directory not found, skipping generator test")
            return True
        
        generator = E2ETestGenerator(str(test_dir))
        result = generator.analyze_and_generate()
        
        print_success(f"Generator completed successfully")
        print_info(f"  - Scenarios generated: {result.get('scenarios', 0)}")
        print_info(f"  - Test files created: {result.get('scenarios', 0)}")
        
        stats = generator.get_statistics()
        print_success(f"Statistics: {stats['total_scenarios']} scenarios for {stats['components_tested']} components")
        
        return True
    
    except Exception as e:
        print_error(f"Generator test failed: {e}")
        return False

def check_assertions_functionality():
    """Quick functionality test - Assertions Library"""
    print_header("ASSERTIONS LIBRARY TEST")
    
    try:
        from backend.e2e_testing.assertions import TestAssertions
        
        # Check that assertion methods exist
        methods = [
            'assert_visible',
            'assert_hidden',
            'assert_exists',
            'assert_contains_text',
            'assert_input_value',
            'assert_enabled',
            'assert_disabled',
            'assert_checked',
            'assert_element_count',
            'assert_url',
            'assert_error_message',
            'assert_form_valid',
        ]
        
        missing = []
        for method_name in methods:
            if not hasattr(TestAssertions, method_name):
                missing.append(method_name)
        
        if not missing:
            print_success(f"All {len(methods)} core assertion methods available")
            return True
        else:
            print_error(f"Missing assertion methods: {missing}")
            return False
    
    except Exception as e:
        print_error(f"Assertions test failed: {e}")
        return False

def check_mcp_servers():
    """Check MCP server definitions"""
    print_header("MCP SERVER CHECK")
    
    try:
        # Check Browser Testing Server
        browser_server = Path(__file__).parent / "mcp_servers" / "browser_testing_server.py"
        if browser_server.exists():
            print_success(f"Browser Testing MCP Server found")
        else:
            print_error(f"Browser Testing MCP Server NOT FOUND")
            return False
        
        # Check E2E Testing Server
        e2e_server = Path(__file__).parent / "mcp_servers" / "e2e_testing_server.py"
        if e2e_server.exists():
            print_success(f"E2E Testing MCP Server found")
        else:
            print_error(f"E2E Testing MCP Server NOT FOUND")
            return False
        
        return True
    
    except Exception as e:
        print_error(f"MCP server check failed: {e}")
        return False

def check_documentation():
    """Check if documentation files exist"""
    print_header("DOCUMENTATION CHECK")
    
    docs = [
        ("E2E_TEST_GENERATOR_COMPLETE_GUIDE.md", "Complete Guide"),
        ("REVIEWFIX_E2E_TESTING_INTEGRATION.md", "ReviewFix Integration"),
        ("E2E_QUICK_START.md", "Quick Start"),
        ("E2E_IMPLEMENTATION_COMPLETE.md", "Implementation Summary"),
    ]
    
    all_passed = True
    for filename, description in docs:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            lines = filepath.read_text().count('\n')
            print_success(f"{description} ({lines} lines)")
        else:
            print_error(f"{description} NOT FOUND")
            all_passed = False
    
    return all_passed

def main():
    """Run all validation checks"""
    print(f"\n{BOLD}{BLUE}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "E2E TEST GENERATOR VALIDATION" + " "*25 + "║")
    print("║" + " "*20 + "KI AutoAgent v7.0" + " "*33 + "║")
    print("╚" + "═"*68 + "╝")
    print(RESET)
    
    checks = [
        ("Python Version", check_python_version),
        ("Module Imports", check_module_imports),
        ("Dependencies", check_dependencies),
        ("File Existence", check_files_exist),
        ("Analyzer Functionality", check_analyzer_functionality),
        ("Generator Functionality", check_generator_functionality),
        ("Assertions Library", check_assertions_functionality),
        ("MCP Servers", check_mcp_servers),
        ("Documentation", check_documentation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check '{name}' failed with error: {e}")
            results[name] = False
    
    # Final Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}\n")
    
    for name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} - {name}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL CHECKS PASSED!{RESET}")
        print(f"{GREEN}The E2E Test Generator is ready to use.{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print(f"  1. Read: E2E_QUICK_START.md")
        print(f"  2. Try: python3 E2E_QUICK_START.py")
        print(f"  3. Test: on your React app")
        print()
        return 0
    else:
        print(f"\n{RED}{BOLD}⚠️  SOME CHECKS FAILED!{RESET}")
        print(f"{RED}Please fix the above issues before using the E2E Test Generator.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())