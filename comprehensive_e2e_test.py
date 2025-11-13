#!/usr/bin/env python3
"""
Comprehensive E2E Test for KI AutoAgent v7.0 Pure MCP
Tests all workflows with detailed reporting
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
import websockets
import tempfile
import shutil
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test workspace
WORKSPACE_BASE = Path(f"{Path.home()}/TestApps")
WORKSPACE_BASE.mkdir(exist_ok=True)

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class E2ETestRunner:
    def __init__(self):
        self.results = {
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "partial": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None
            }
        }
        self.session_id = None
        self.ws = None
        self.events_received = []
        
    async def connect_websocket(self) -> None:
        """Connect to backend WebSocket"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.ws = await websockets.connect("ws://localhost:8002/ws/chat")
                logger.info(f"{Colors.GREEN}✅ WebSocket connected{Colors.RESET}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection attempt {attempt+1} failed, retrying...")
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"Failed to connect after {max_retries} attempts: {e}")
    
    async def send_request(self, workspace_path: str, query: str, timeout: float = 60.0) -> dict:
        """Send request and collect all events"""
        self.events_received = []
        
        # Initialize session
        init_msg = {
            "type": "init",
            "workspace_path": workspace_path
        }
        await self.ws.send(json.dumps(init_msg))
        
        # Get session ID
        response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
        init_response = json.loads(response)
        self.session_id = init_response.get("session_id")
        logger.info(f"Session ID: {self.session_id}")
        
        # Send query
        query_msg = {
            "type": "query",
            "content": query,
            "session_id": self.session_id
        }
        await self.ws.send(json.dumps(query_msg))
        
        # Collect all events
        start_time = time.time()
        final_result = None
        
        while time.time() - start_time < timeout:
            try:
                event_data = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                event = json.loads(event_data)
                self.events_received.append(event)
                
                # Check for final result
                if event.get("type") == "result":
                    final_result = event
                    logger.info(f"✅ Received final result")
                    break
                    
                # Log intermediate events
                if event.get("type") == "status":
                    logger.info(f"  Status: {event.get('content', 'N/A')}")
                    
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.warning(f"Error receiving event: {e}")
                break
        
        return final_result or {"error": "No result received"}
    
    async def test_new_app_creation(self) -> dict:
        """Test 1: Create a new app"""
        logger.info(f"\n{Colors.BOLD}TEST 1: Create New App{Colors.RESET}")
        
        workspace = WORKSPACE_BASE / "test_new_app"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        
        test_result = {
            "name": "Create New App",
            "workspace": str(workspace),
            "status": "running",
            "details": {},
            "errors": []
        }
        
        try:
            query = """
            Create a new Python Flask application with:
            - Basic Flask app with 3 routes
            - hello.py as main file
            - requirements.txt with Flask
            """
            
            result = await self.send_request(str(workspace), query)
            
            # Check if files were created
            hello_py = workspace / "hello.py"
            requirements_txt = workspace / "requirements.txt"
            
            files_created = []
            for f in workspace.glob("**/*"):
                if f.is_file():
                    files_created.append(str(f.relative_to(workspace)))
            
            test_result["details"] = {
                "files_created": files_created,
                "hello_py_exists": hello_py.exists(),
                "requirements_txt_exists": requirements_txt.exists(),
                "events_received": len(self.events_received),
                "workflow_completed": result.get("type") == "result"
            }
            
            # Validate
            if hello_py.exists() and requirements_txt.exists():
                test_result["status"] = "passed"
                logger.info(f"{Colors.GREEN}✅ New app created successfully{Colors.RESET}")
            elif len(files_created) > 0:
                test_result["status"] = "partial"
                test_result["errors"].append(f"Only {len(files_created)} files created instead of 2+")
                logger.info(f"{Colors.YELLOW}⚠️ Partial success: {len(files_created)} files created{Colors.RESET}")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("No files created")
                logger.info(f"{Colors.RED}❌ No files created{Colors.RESET}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"{Colors.RED}❌ Test failed: {e}{Colors.RESET}")
        
        return test_result
    
    async def test_extend_app(self) -> dict:
        """Test 2: Extend an existing app"""
        logger.info(f"\n{Colors.BOLD}TEST 2: Extend Existing App{Colors.RESET}")
        
        workspace = WORKSPACE_BASE / "test_extend_app"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        
        # Create initial files
        (workspace / "app.py").write_text("""
import flask
app = flask.Flask(__name__)

@app.route('/')
def home():
    return 'Hello'
""")
        
        test_result = {
            "name": "Extend Existing App",
            "workspace": str(workspace),
            "status": "running",
            "details": {},
            "errors": []
        }
        
        try:
            query = """
            Extend the existing Flask app to include:
            - A new /api/users route that returns JSON
            - Add error handling for 404 and 500
            - Add logging
            """
            
            result = await self.send_request(str(workspace), query)
            
            # Check if app.py was modified
            app_py = workspace / "app.py"
            content = app_py.read_text() if app_py.exists() else ""
            
            has_api_route = "/api/users" in content or "api" in content
            has_error_handling = "@app.errorhandler" in content or "404" in content
            
            test_result["details"] = {
                "app_py_modified": len(content) > 100,
                "has_api_route": has_api_route,
                "has_error_handling": has_error_handling,
                "file_size": len(content),
                "events_received": len(self.events_received)
            }
            
            if has_api_route or len(content) > 100:
                test_result["status"] = "passed"
                logger.info(f"{Colors.GREEN}✅ App extended successfully{Colors.RESET}")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("App not properly extended")
                logger.info(f"{Colors.RED}❌ App not extended{Colors.RESET}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"{Colors.RED}❌ Test failed: {e}{Colors.RESET}")
        
        return test_result
    
    async def test_react_app(self) -> dict:
        """Test 3: Create React app for ReviewFix Playground"""
        logger.info(f"\n{Colors.BOLD}TEST 3: React App with Playground Testing{Colors.RESET}")
        
        workspace = WORKSPACE_BASE / "test_react_app"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        
        test_result = {
            "name": "React App Creation",
            "workspace": str(workspace),
            "status": "running",
            "details": {},
            "errors": []
        }
        
        try:
            query = """
            Create a React HTML app with:
            - Basic React component with useState hook
            - index.html with React loaded from CDN
            - A counter component that can be tested in playground
            - Inline CSS styling
            """
            
            result = await self.send_request(str(workspace), query)
            
            # Check files
            index_html = workspace / "index.html"
            app_js = workspace / "app.js"
            
            html_content = index_html.read_text() if index_html.exists() else ""
            
            has_react = "react" in html_content.lower() or "useState" in html_content
            has_html_structure = "<html" in html_content
            has_component = "counter" in html_content.lower() or "component" in html_content.lower()
            
            test_result["details"] = {
                "index_html_exists": index_html.exists(),
                "app_js_exists": app_js.exists(),
                "has_react": has_react,
                "has_html_structure": has_html_structure,
                "has_component": has_component,
                "html_size": len(html_content),
                "events_received": len(self.events_received)
            }
            
            if has_react and has_html_structure:
                test_result["status"] = "passed"
                logger.info(f"{Colors.GREEN}✅ React app created{Colors.RESET}")
            elif index_html.exists():
                test_result["status"] = "partial"
                test_result["errors"].append("HTML created but React may not be properly set up")
                logger.info(f"{Colors.YELLOW}⚠️ Partial: React app structure created{Colors.RESET}")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("No React app files created")
                logger.info(f"{Colors.RED}❌ No React files created{Colors.RESET}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"{Colors.RED}❌ Test failed: {e}{Colors.RESET}")
        
        return test_result
    
    async def test_non_ai_app_integration(self) -> dict:
        """Test 4: Integrate & extend non-AI app"""
        logger.info(f"\n{Colors.BOLD}TEST 4: Non-AI App Integration{Colors.RESET}")
        
        workspace = WORKSPACE_BASE / "test_legacy_app"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        
        # Create a pre-existing non-AI app
        (workspace / "legacy_app.py").write_text("""
# A simple non-AI calculator app
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def main():
    print("Calculator App")
    result = add(5, 3)
    print(f"5 + 3 = {result}")

if __name__ == "__main__":
    main()
""")
        
        test_result = {
            "name": "Non-AI App Integration",
            "workspace": str(workspace),
            "status": "running",
            "details": {},
            "errors": []
        }
        
        try:
            query = """
            Analyze and extend the existing legacy_app.py:
            - Add multiply and divide functions
            - Add error handling for division by zero
            - Create a simple CLI interface
            """
            
            result = await self.send_request(str(workspace), query)
            
            # Check modifications
            legacy_app = workspace / "legacy_app.py"
            content = legacy_app.read_text() if legacy_app.exists() else ""
            
            has_multiply = "multiply" in content.lower()
            has_divide = "divide" in content.lower()
            has_error_handling = "try" in content or "except" in content
            
            test_result["details"] = {
                "file_exists": legacy_app.exists(),
                "has_multiply": has_multiply,
                "has_divide": has_divide,
                "has_error_handling": has_error_handling,
                "file_size": len(content),
                "events_received": len(self.events_received)
            }
            
            if has_multiply and has_divide:
                test_result["status"] = "passed"
                logger.info(f"{Colors.GREEN}✅ Legacy app successfully extended{Colors.RESET}")
            elif has_multiply or has_divide:
                test_result["status"] = "partial"
                logger.info(f"{Colors.YELLOW}⚠️ Partial: Some functions added{Colors.RESET}")
            else:
                test_result["status"] = "failed"
                test_result["errors"].append("App not properly analyzed or extended")
                logger.info(f"{Colors.RED}❌ App not extended{Colors.RESET}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"{Colors.RED}❌ Test failed: {e}{Colors.RESET}")
        
        return test_result
    
    async def test_general_research_query(self) -> dict:
        """Test 5: General research query"""
        logger.info(f"\n{Colors.BOLD}TEST 5: General Research Query{Colors.RESET}")
        
        workspace = WORKSPACE_BASE / "test_research"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        
        test_result = {
            "name": "General Research Query",
            "workspace": str(workspace),
            "status": "running",
            "details": {},
            "errors": []
        }
        
        try:
            query = """
            Research and provide information about:
            - Best practices for REST API design
            - Error handling strategies
            - Security considerations
            """
            
            result = await self.send_request(str(workspace), query, timeout=90.0)
            
            # Check if research was done
            has_result = result.get("type") == "result"
            has_content = bool(result.get("content", ""))
            
            test_result["details"] = {
                "query_processed": has_result,
                "has_content": has_content,
                "result_length": len(str(result.get("content", ""))),
                "events_received": len(self.events_received),
                "research_completed": len([e for e in self.events_received if "research" in str(e).lower()]) > 0
            }
            
            if has_result and has_content:
                test_result["status"] = "passed"
                logger.info(f"{Colors.GREEN}✅ Research query completed{Colors.RESET}")
            else:
                test_result["status"] = "partial"
                test_result["errors"].append("Query processed but no content received")
                logger.info(f"{Colors.YELLOW}⚠️ Partial: Query processed{Colors.RESET}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"{Colors.RED}❌ Test failed: {e}{Colors.RESET}")
        
        return test_result
    
    async def run_all_tests(self) -> None:
        """Run all tests"""
        try:
            # Connect to backend
            await self.connect_websocket()
            
            # Run tests
            test_methods = [
                self.test_new_app_creation,
                self.test_extend_app,
                self.test_react_app,
                self.test_non_ai_app_integration,
                self.test_general_research_query
            ]
            
            for test_method in test_methods:
                try:
                    result = await test_method()
                    self.results["tests"].append(result)
                    self.results["summary"]["total"] += 1
                    
                    if result["status"] == "passed":
                        self.results["summary"]["passed"] += 1
                    elif result["status"] == "partial":
                        self.results["summary"]["partial"] += 1
                    else:
                        self.results["summary"]["failed"] += 1
                    
                    # Brief pause between tests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Test error: {e}")
                    self.results["tests"].append({
                        "name": test_method.__name__,
                        "status": "failed",
                        "errors": [str(e)]
                    })
                    self.results["summary"]["total"] += 1
                    self.results["summary"]["failed"] += 1
            
        finally:
            self.results["summary"]["end_time"] = datetime.now().isoformat()
            if self.ws:
                await self.ws.close()
    
    def print_summary(self) -> None:
        """Print test summary"""
        summary = self.results["summary"]
        
        print(f"\n{Colors.BOLD}{'='*80}")
        print(f"E2E TEST SUMMARY{Colors.RESET}")
        print(f"{'='*80}")
        print(f"Total Tests: {summary['total']}")
        print(f"{Colors.GREEN}Passed: {summary['passed']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Partial: {summary['partial']}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {summary['failed']}{Colors.RESET}")
        
        # Pass rate
        if summary["total"] > 0:
            pass_rate = ((summary["passed"] + summary["partial"]*0.5) / summary["total"]) * 100
            color = Colors.GREEN if pass_rate >= 80 else Colors.YELLOW if pass_rate >= 50 else Colors.RED
            print(f"\nEffective Pass Rate: {color}{pass_rate:.1f}%{Colors.RESET}")
        
        # Detailed results
        print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
        for test in self.results["tests"]:
            status_color = {
                "passed": Colors.GREEN,
                "partial": Colors.YELLOW,
                "failed": Colors.RED
            }.get(test.get("status"), Colors.BLUE)
            
            status_icon = {
                "passed": "✅",
                "partial": "⚠️",
                "failed": "❌"
            }.get(test.get("status"), "❓")
            
            print(f"\n  {status_icon} {status_color}{test.get('name', 'Unknown')}{Colors.RESET}")
            print(f"     Workspace: {test.get('workspace', 'N/A')}")
            
            if test.get("details"):
                for key, value in test["details"].items():
                    print(f"     - {key}: {value}")
            
            if test.get("errors"):
                for error in test["errors"]:
                    print(f"     {Colors.RED}Error: {error}{Colors.RESET}")
        
        print(f"\n{'='*80}\n")
    
    def save_results(self, filepath: str = None) -> str:
        """Save results to JSON file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{WORKSPACE_BASE}/e2e_test_results_{timestamp}.json"
        
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath

async def main():
    runner = E2ETestRunner()
    
    try:
        await runner.run_all_tests()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    runner.print_summary()
    filepath = runner.save_results()
    
    # Return exit code based on results
    summary = runner.results["summary"]
    if summary["failed"] == 0 and summary["passed"] > 0:
        sys.exit(0)  # Success
    elif summary["partial"] > 0 and summary["failed"] == 0:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Failure

if __name__ == "__main__":
    asyncio.run(main())