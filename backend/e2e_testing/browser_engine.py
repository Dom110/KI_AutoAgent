"""
Browser Engine - Playwright-based Browser Automation
Handles browser lifecycle, navigation, interactions, and performance monitoring
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import signal
import os


@dataclass
class BrowserSession:
    """Represents a browser session"""
    session_id: str
    started_at: str
    base_url: str
    dev_server_port: int
    dev_server_process: Optional[Any] = None
    browser_process: Optional[Any] = None
    is_running: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics from browser session"""
    page_load_time: float
    first_contentful_paint: float
    largest_contentful_paint: float
    time_to_interactive: float
    memory_usage: float
    screenshots: List[str]


class BrowserEngine:
    """Manages browser automation with Playwright"""
    
    def __init__(self, app_path: str, config: Optional[Dict[str, Any]] = None):
        self.app_path = Path(app_path)
        self.config = config or {}
        self.sessions: Dict[str, BrowserSession] = {}
        self.performance_data: Dict[str, PerformanceMetrics] = {}
        
        # Default configuration
        self.base_url = self.config.get('base_url', 'http://localhost:3000')
        self.dev_server_port = self.config.get('dev_server_port', 3000)
        self.browser_type = self.config.get('browser', 'chromium')
        self.headless = self.config.get('headless', True)
        self.timeout = self.config.get('timeout', 30000)
        self.slow_mo = self.config.get('slow_mo', 0)
    
    async def start_dev_server(self) -> BrowserSession:
        """Start React dev server"""
        print(f"🚀 Starting dev server for {self.app_path}")
        
        session_id = f"session_{int(time.time())}"
        
        # Check if npm or yarn exists
        package_manager = 'npm' if (self.app_path / 'package-lock.json').exists() else 'yarn'
        
        try:
            # Start dev server
            dev_cmd = f"{package_manager} start"
            proc = subprocess.Popen(
                dev_cmd,
                shell=True,
                cwd=self.app_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Wait for server to be ready
            await self._wait_for_server(self.base_url)
            
            session = BrowserSession(
                session_id=session_id,
                started_at=datetime.now().isoformat(),
                base_url=self.base_url,
                dev_server_port=self.dev_server_port,
                dev_server_process=proc,
                is_running=True,
            )
            
            self.sessions[session_id] = session
            print(f"✅ Dev server started at {self.base_url}")
            
            return session
        
        except Exception as e:
            print(f"❌ Failed to start dev server: {e}")
            raise
    
    async def _wait_for_server(self, url: str, timeout: int = 30):
        """Wait for dev server to be ready"""
        import aiohttp
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            print(f"✅ Server is ready")
                            return
            except:
                pass
            
            await asyncio.sleep(1)
        
        raise Exception(f"Server did not start within {timeout} seconds")
    
    async def navigate_to(self, page, url: str):
        """Navigate to URL"""
        print(f"📍 Navigating to {url}")
        try:
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            print(f"✅ Navigated to {url}")
        except Exception as e:
            print(f"⚠️  Navigation warning: {e}")
    
    async def fill_input(self, page, selector: str, value: str):
        """Fill input field"""
        print(f"✏️  Filling {selector} with '{value}'")
        await page.fill(selector, value)
    
    async def click_element(self, page, selector: str):
        """Click element"""
        print(f"🖱️  Clicking {selector}")
        await page.click(selector)
    
    async def wait_for_element(self, page, selector: str, timeout: int = 5000):
        """Wait for element to appear"""
        print(f"⏳ Waiting for {selector}")
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            print(f"✅ Element found: {selector}")
            return True
        except Exception as e:
            print(f"❌ Element not found: {selector}")
            return False
    
    async def take_screenshot(self, page, name: str, session_id: str) -> str:
        """Take screenshot"""
        screenshot_dir = self.app_path / 'screenshots'
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = screenshot_dir / f"{name}_{timestamp}.png"
        
        await page.screenshot(path=str(filepath))
        print(f"📸 Screenshot saved: {filepath}")
        
        if session_id not in self.performance_data:
            self.performance_data[session_id] = PerformanceMetrics(
                page_load_time=0,
                first_contentful_paint=0,
                largest_contentful_paint=0,
                time_to_interactive=0,
                memory_usage=0,
                screenshots=[],
            )
        
        self.performance_data[session_id].screenshots.append(str(filepath))
        
        return str(filepath)
    
    async def get_page_content(self, page) -> str:
        """Get page HTML content"""
        return await page.content()
    
    async def evaluate_script(self, page, script: str) -> Any:
        """Evaluate JavaScript on page"""
        print(f"🔧 Executing script")
        result = await page.evaluate(script)
        return result
    
    async def collect_performance_metrics(self, page, session_id: str) -> PerformanceMetrics:
        """Collect performance metrics"""
        try:
            # Get performance data from browser
            metrics_script = """
            () => {
              const perfData = performance.timing;
              const perfEntries = performance.getEntriesByType('navigation')[0];
              
              return {
                pageLoadTime: perfData.loadEventEnd - perfData.navigationStart,
                fcp: perfEntries?.firstContentfulPaint || 0,
                lcp: performance.getEntriesByType('largest-contentful-paint').pop()?.renderTime || 0,
                tti: perfData.loadEventEnd - perfData.navigationStart,
              };
            }
            """
            
            perf_data = await page.evaluate(metrics_script)
            
            # Get memory usage
            memory_script = """
            () => {
              if (performance.memory) {
                return performance.memory.usedJSHeapSize / 1048576; // Convert to MB
              }
              return 0;
            }
            """
            
            memory_mb = await page.evaluate(memory_script)
            
            metrics = PerformanceMetrics(
                page_load_time=perf_data.get('pageLoadTime', 0),
                first_contentful_paint=perf_data.get('fcp', 0),
                largest_contentful_paint=perf_data.get('lcp', 0),
                time_to_interactive=perf_data.get('tti', 0),
                memory_usage=memory_mb,
                screenshots=self.performance_data.get(session_id, PerformanceMetrics(0, 0, 0, 0, 0, [])).screenshots,
            )
            
            self.performance_data[session_id] = metrics
            
            print(f"📊 Performance Metrics:")
            print(f"   Page Load: {metrics.page_load_time}ms")
            print(f"   FCP: {metrics.first_contentful_paint}ms")
            print(f"   LCP: {metrics.largest_contentful_paint}ms")
            print(f"   Memory: {metrics.memory_usage:.2f}MB")
            
            return metrics
        
        except Exception as e:
            print(f"⚠️  Could not collect metrics: {e}")
            return PerformanceMetrics(0, 0, 0, 0, 0, [])
    
    async def check_accessibility(self, page) -> Dict[str, Any]:
        """Check page accessibility"""
        try:
            # Import axe-core for accessibility testing
            await page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js')
            
            result = await page.evaluate("""
            () => {
              return new Promise((resolve) => {
                axe.run((error, results) => {
                  resolve({
                    passes: results.passes.length,
                    violations: results.violations.length,
                    incomplete: results.incomplete.length,
                  });
                });
              });
            }
            """)
            
            print(f"♿ Accessibility Check:")
            print(f"   Passes: {result['passes']}")
            print(f"   Violations: {result['violations']}")
            
            return result
        
        except Exception as e:
            print(f"⚠️  Could not check accessibility: {e}")
            return {'passes': 0, 'violations': 0, 'incomplete': 0}
    
    async def mock_api_response(self, page, url_pattern: str, response_data: Dict[str, Any], status: int = 200):
        """Mock API response"""
        print(f"🎭 Mocking API: {url_pattern}")
        
        async def handle_route(route):
            await route.respond(
                status=status,
                content_type='application/json',
                body=json.dumps(response_data),
            )
        
        await page.route(url_pattern, handle_route)
    
    async def abort_api_call(self, page, url_pattern: str):
        """Abort API call (simulate network error)"""
        print(f"🚫 Aborting API: {url_pattern}")
        
        async def handle_route(route):
            await route.abort('internet-disconnected')
        
        await page.route(url_pattern, handle_route)
    
    async def handle_dialog(self, page, handler: Callable):
        """Handle browser dialogs (alerts, confirms, prompts)"""
        page.on('dialog', handler)
    
    async def get_console_messages(self, page) -> List[Dict[str, Any]]:
        """Capture console messages"""
        messages = []
        
        def on_console(msg):
            messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location,
            })
        
        page.on('console', on_console)
        return messages
    
    async def stop_dev_server(self, session_id: str):
        """Stop dev server"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.dev_server_process:
                print(f"🛑 Stopping dev server")
                session.dev_server_process.terminate()
                try:
                    session.dev_server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    session.dev_server_process.kill()
                print(f"✅ Dev server stopped")
    
    async def cleanup(self, session_id: str):
        """Cleanup session"""
        await self.stop_dev_server(session_id)
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def export_performance_report(self, output_file: str):
        """Export performance data to JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sessions': {
                sid: {
                    'session': asdict(session),
                    'metrics': asdict(self.performance_data.get(sid, PerformanceMetrics(0, 0, 0, 0, 0, []))),
                }
                for sid, session in self.sessions.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Performance report exported: {output_file}")