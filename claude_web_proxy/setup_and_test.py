#!/usr/bin/env python3
"""
Claude Web Proxy - Setup and Testing Script
Automated setup, testing, and validation for the Claude Web Proxy system
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
import structlog

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from claude_web_proxy.claude_browser import ClaudeBrowser
from claude_web_proxy.fastapi_server import run_server
import multiprocessing
import subprocess
import signal

logger = structlog.get_logger()

class ClaudeWebProxyTester:
    """Comprehensive testing and setup for Claude Web Proxy"""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.server_process: Optional[subprocess.Popen] = None
        
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required dependencies are installed"""
        dependencies = {}
        
        try:
            import playwright
            dependencies['playwright'] = True
        except ImportError:
            dependencies['playwright'] = False
            
        try:
            import fastapi
            dependencies['fastapi'] = True
        except ImportError:
            dependencies['fastapi'] = False
            
        try:
            import uvicorn
            dependencies['uvicorn'] = True
        except ImportError:
            dependencies['uvicorn'] = False
            
        try:
            import aiohttp
            dependencies['aiohttp'] = True
        except ImportError:
            dependencies['aiohttp'] = False
            
        return dependencies
    
    def install_playwright_browsers(self) -> bool:
        """Install Playwright browser binaries"""
        try:
            logger.info("Installing Playwright browsers...")
            result = subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Playwright browsers installed successfully")
                return True
            else:
                logger.error("Failed to install Playwright browsers", error=result.stderr)
                return False
                
        except Exception as e:
            logger.error("Exception during Playwright installation", error=str(e))
            return False
    
    def start_server(self) -> bool:
        """Start the FastAPI server in a separate process"""
        try:
            # Start server process
            self.server_process = subprocess.Popen([
                "python", "-m", "uvicorn",
                "claude_web_proxy.fastapi_server:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], cwd=Path(__file__).parent.parent)
            
            # Wait for server to start
            time.sleep(5)
            
            return self.server_process.poll() is None
            
        except Exception as e:
            logger.error("Failed to start server", error=str(e))
            return False
    
    def stop_server(self):
        """Stop the FastAPI server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            finally:
                self.server_process = None
    
    async def test_server_health(self) -> bool:
        """Test if the server is responding"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("Server health check passed", data=data)
                        return True
                    else:
                        logger.error("Server health check failed", status=response.status)
                        return False
                        
        except Exception as e:
            logger.error("Failed to connect to server", error=str(e))
            return False
    
    async def test_browser_automation(self) -> bool:
        """Test direct browser automation without server"""
        try:
            logger.info("Testing direct browser automation...")
            
            async with ClaudeBrowser(headless=True) as browser:
                # Check login status
                logged_in = await browser.check_login_status()
                logger.info("Browser automation test", logged_in=logged_in)
                
                if not logged_in:
                    logger.info("User not logged in - this is expected for first run")
                    logger.info("Manual login will be required for full functionality")
                
                return True  # Browser automation works even if not logged in
                
        except Exception as e:
            logger.error("Browser automation test failed", error=str(e))
            return False
    
    async def test_server_endpoints(self) -> Dict[str, bool]:
        """Test all server endpoints"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test status endpoint
            try:
                async with session.get(f"{self.server_url}/claude/status") as response:
                    results['status'] = response.status == 200
                    if results['status']:
                        data = await response.json()
                        logger.info("Status endpoint test passed", data=data)
            except Exception as e:
                logger.error("Status endpoint test failed", error=str(e))
                results['status'] = False
            
            # Test setup endpoint (this will likely fail without manual login)
            try:
                setup_data = {"headless": True, "timeout": 10}
                async with session.post(f"{self.server_url}/claude/setup", json=setup_data) as response:
                    # Accept both success and authentication failure as valid responses
                    results['setup'] = response.status in [200, 400, 401]
                    if response.status == 200:
                        logger.info("Setup endpoint test passed")
                    else:
                        text = await response.text()
                        logger.info("Setup endpoint responded as expected", status=response.status, response=text)
            except Exception as e:
                logger.error("Setup endpoint test failed", error=str(e))
                results['setup'] = False
        
        return results
    
    async def test_crewai_integration(self) -> bool:
        """Test CrewAI integration components"""
        try:
            from claude_web_proxy.crewai_integration import ClaudeWebLLM, create_claude_web_llm
            
            # Create LLM instance
            llm = create_claude_web_llm(server_url=self.server_url)
            
            # Test model info
            info = llm.get_model_info()
            logger.info("CrewAI integration test passed", model_info=info)
            
            # Test generate method (will fail without server/login, but shouldn't crash)
            try:
                response = llm.generate("Test message", timeout=5)
                logger.info("Generate method test", response_length=len(response))
            except Exception as e:
                logger.info("Generate method failed as expected without proper setup", error=str(e))
            
            return True
            
        except Exception as e:
            logger.error("CrewAI integration test failed", error=str(e))
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        results = {
            "timestamp": time.time(),
            "dependencies": {},
            "playwright_install": False,
            "browser_automation": False,
            "server_start": False,
            "server_health": False,
            "endpoints": {},
            "crewai_integration": False,
            "overall_success": False
        }
        
        print("🚀 Starting Claude Web Proxy Setup and Testing...")
        print("=" * 60)
        
        # Check dependencies
        print("\n📦 Checking dependencies...")
        results["dependencies"] = await self.check_dependencies()
        for dep, installed in results["dependencies"].items():
            status = "✅" if installed else "❌"
            print(f"{status} {dep}")
        
        # Install Playwright browsers
        print("\n🌐 Installing Playwright browsers...")
        results["playwright_install"] = self.install_playwright_browsers()
        status = "✅" if results["playwright_install"] else "❌"
        print(f"{status} Playwright browsers")
        
        # Test browser automation
        print("\n🤖 Testing browser automation...")
        results["browser_automation"] = await self.test_browser_automation()
        status = "✅" if results["browser_automation"] else "❌"
        print(f"{status} Browser automation")
        
        # Start server
        print("\n🖥️  Starting server...")
        results["server_start"] = self.start_server()
        status = "✅" if results["server_start"] else "❌"
        print(f"{status} Server startup")
        
        if results["server_start"]:
            # Test server health
            print("\n🏥 Testing server health...")
            results["server_health"] = await self.test_server_health()
            status = "✅" if results["server_health"] else "❌"
            print(f"{status} Server health")
            
            # Test endpoints
            print("\n🔗 Testing endpoints...")
            results["endpoints"] = await self.test_server_endpoints()
            for endpoint, success in results["endpoints"].items():
                status = "✅" if success else "❌"
                print(f"{status} {endpoint} endpoint")
        
        # Test CrewAI integration
        print("\n🔧 Testing CrewAI integration...")
        results["crewai_integration"] = await self.test_crewai_integration()
        status = "✅" if results["crewai_integration"] else "❌"
        print(f"{status} CrewAI integration")
        
        # Stop server
        self.stop_server()
        
        # Overall success
        critical_tests = [
            results["browser_automation"],
            results["server_start"],
            results["crewai_integration"]
        ]
        results["overall_success"] = all(critical_tests)
        
        print("\n" + "=" * 60)
        if results["overall_success"]:
            print("🎉 All critical tests passed! Claude Web Proxy is ready to use.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return results
    
    def generate_setup_report(self, results: Dict[str, Any]) -> str:
        """Generate a setup report"""
        report = f"""
# Claude Web Proxy Setup Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results
"""
        
        if results["overall_success"]:
            report += "✅ **Overall Status: READY**\n\n"
        else:
            report += "❌ **Overall Status: NEEDS ATTENTION**\n\n"
        
        report += "### Dependencies\n"
        for dep, installed in results["dependencies"].items():
            status = "✅" if installed else "❌"
            report += f"- {status} {dep}\n"
        
        report += "\n### Core Components\n"
        components = [
            ("Browser Automation", results["browser_automation"]),
            ("Server Startup", results["server_start"]),
            ("CrewAI Integration", results["crewai_integration"])
        ]
        
        for name, success in components:
            status = "✅" if success else "❌"
            report += f"- {status} {name}\n"
        
        if results["endpoints"]:
            report += "\n### API Endpoints\n"
            for endpoint, success in results["endpoints"].items():
                status = "✅" if success else "❌"
                report += f"- {status} {endpoint}\n"
        
        report += "\n## Next Steps\n"
        
        if results["overall_success"]:
            report += """
1. **Manual Login Required**: Open browser and log into Claude.ai manually
2. **Start Server**: Run `python claude_web_proxy/setup_and_test.py --server-only`
3. **Test Integration**: Use the example scripts in the documentation

The system is technically ready but requires manual authentication with Claude.ai.
"""
        else:
            report += """
1. **Install Missing Dependencies**: Check the dependency list above
2. **Fix Browser Issues**: Ensure Playwright is properly installed
3. **Check Server Configuration**: Verify port 8000 is available
4. **Re-run Setup**: Execute this script again after fixes

Please address the failed components before proceeding.
"""
        
        return report


async def main():
    """Main setup and testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Web Proxy Setup and Testing")
    parser.add_argument("--server-only", action="store_true", help="Only start the server")
    parser.add_argument("--test-only", action="store_true", help="Only run tests")
    parser.add_argument("--report", action="store_true", help="Generate setup report")
    
    args = parser.parse_args()
    
    tester = ClaudeWebProxyTester()
    
    if args.server_only:
        print("🖥️  Starting Claude Web Proxy server...")
        print("Server will run at http://localhost:8000")
        print("Press Ctrl+C to stop")
        
        try:
            run_server(port=8000, reload=True)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
    
    elif args.test_only:
        results = await tester.run_comprehensive_test()
        if args.report:
            report = tester.generate_setup_report(results)
            print(report)
    
    else:
        # Full setup and test
        results = await tester.run_comprehensive_test()
        
        # Save results
        results_file = Path(__file__).parent / "setup_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate report
        report = tester.generate_setup_report(results)
        report_file = Path(__file__).parent / "setup_report.md"
        with open(report_file, "w") as f:
            f.write(report)
        
        print(f"\n📄 Results saved to: {results_file}")
        print(f"📋 Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())