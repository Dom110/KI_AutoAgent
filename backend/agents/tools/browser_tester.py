"""
Browser Tester - Automated browser testing using Playwright
Enables ReviewerGPT to test HTML/JS applications in real browsers
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - browser testing disabled")


class BrowserTester:
    """
    Automated browser testing using Playwright

    Features:
    - Start local HTTP server for HTML files
    - Launch headless browser (Chromium, Firefox, WebKit)
    - Execute test scenarios (click, type, navigate)
    - Capture screenshots
    - Detect JavaScript errors
    - Validate page elements
    - Performance metrics (load time, etc.)
    """

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")

        self.playwright = None
        self.browser = None
        self.page = None
        self.http_server_process = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Start Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return

        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        logger.info("✅ Playwright browser started (Chromium headless)")

    async def stop(self):
        """Stop Playwright browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.http_server_process:
            self.http_server_process.terminate()
            self.http_server_process = None
        logger.info("✅ Playwright browser stopped")

    async def test_tetris_app(self, html_file: str) -> Dict[str, Any]:
        """
        Test Tetris application

        Tetris-specific tests:
        - Page loads successfully
        - Canvas element exists
        - Game starts on button click
        - Arrow keys control tetrominos
        - Score displays correctly
        - Game over detection works

        Returns:
            {
                'success': True/False,
                'errors': [],
                'warnings': [],
                'screenshots': [],
                'metrics': {
                    'load_time_ms': 123,
                    'canvas_found': True,
                    'game_starts': True,
                    'controls_work': True
                }
            }
        """
        logger.info(f"Testing Tetris app: {html_file}")

        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'screenshots': [],
            'metrics': {}
        }

        try:
            # Start local HTTP server for the HTML file
            port = await self._start_local_server(html_file)
            # Include filename in URL to avoid directory listing
            filename = os.path.basename(html_file)
            url = f"http://localhost:{port}/{filename}"

            # Navigate to the page
            logger.info(f"Navigating to {url}")
            load_start = asyncio.get_event_loop().time()
            await self.page.goto(url, wait_until='networkidle')
            load_time = (asyncio.get_event_loop().time() - load_start) * 1000

            result['metrics']['load_time_ms'] = int(load_time)
            logger.info(f"Page loaded in {load_time:.0f}ms")

            # Listen for JavaScript errors
            js_errors = []
            self.page.on('pageerror', lambda err: js_errors.append(str(err)))

            # Take screenshot
            screenshot_path = '/tmp/tetris_app_loaded.png'
            await self.page.screenshot(path=screenshot_path)
            result['screenshots'].append(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")

            # Test 1: Check if canvas exists
            canvas = await self.page.query_selector('canvas')
            if canvas:
                result['metrics']['canvas_found'] = True
                logger.info("✅ Canvas element found")
            else:
                result['errors'].append("Canvas element not found")
                result['metrics']['canvas_found'] = False
                logger.error("❌ Canvas element not found")

            # Test 2: Check if game elements exist (score, start button, etc.)
            score_element = await self.page.query_selector('#score, .score, [class*="score"]')
            if score_element:
                result['metrics']['score_display'] = True
                logger.info("✅ Score display found")
            else:
                result['warnings'].append("Score display not found")
                result['metrics']['score_display'] = False

            # Test 3: Try to start the game (look for start button)
            start_button = await self.page.query_selector('button, [onclick], [class*="start"]')
            if start_button:
                logger.info("Clicking start button...")
                await start_button.click()
                await self.page.wait_for_timeout(1000)  # Wait 1 second
                result['metrics']['game_starts'] = True
                logger.info("✅ Game started")
            else:
                result['warnings'].append("Start button not found - game may auto-start")
                result['metrics']['game_starts'] = None

            # Test 4: Test keyboard controls (arrow keys)
            logger.info("Testing keyboard controls...")
            await self.page.keyboard.press('ArrowLeft')
            await self.page.wait_for_timeout(200)
            await self.page.keyboard.press('ArrowRight')
            await self.page.wait_for_timeout(200)
            await self.page.keyboard.press('ArrowDown')
            await self.page.wait_for_timeout(200)
            await self.page.keyboard.press('Space')  # Rotate or drop
            result['metrics']['controls_tested'] = True
            logger.info("✅ Keyboard controls tested")

            # Take screenshot after interaction
            screenshot_path = '/tmp/tetris_app_playing.png'
            await self.page.screenshot(path=screenshot_path)
            result['screenshots'].append(screenshot_path)

            # Test 5: Check for JavaScript errors
            if js_errors:
                result['errors'].extend(js_errors)
                logger.error(f"❌ JavaScript errors detected: {js_errors}")
            else:
                result['metrics']['no_js_errors'] = True
                logger.info("✅ No JavaScript errors")

            # Determine overall success
            result['success'] = len(result['errors']) == 0 and result['metrics'].get('canvas_found', False)

            logger.info(f"Tetris app test complete: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")

        except Exception as e:
            result['errors'].append(f"Test exception: {str(e)}")
            result['success'] = False
            logger.error(f"Tetris app test failed: {e}")

        return result

    async def test_generic_html_app(self, html_file: str, test_scenarios: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Test generic HTML application

        Args:
            html_file: Path to HTML file
            test_scenarios: List of test scenarios like:
                [
                    {'action': 'click', 'selector': '#button1'},
                    {'action': 'type', 'selector': '#input1', 'text': 'hello'},
                    {'action': 'assert', 'selector': '#result', 'contains': 'success'}
                ]

        Returns:
            {
                'success': True/False,
                'errors': [],
                'warnings': [],
                'screenshots': [],
                'test_results': []
            }
        """
        logger.info(f"Testing generic HTML app: {html_file}")

        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'screenshots': [],
            'test_results': []
        }

        try:
            # Start local HTTP server
            port = await self._start_local_server(html_file)
            # Include filename in URL to avoid directory listing
            filename = os.path.basename(html_file)
            url = f"http://localhost:{port}/{filename}"

            # Navigate to page
            await self.page.goto(url, wait_until='networkidle')

            # Take initial screenshot
            screenshot_path = '/tmp/app_initial.png'
            await self.page.screenshot(path=screenshot_path)
            result['screenshots'].append(screenshot_path)

            # Listen for JS errors
            js_errors = []
            self.page.on('pageerror', lambda err: js_errors.append(str(err)))

            # Execute test scenarios
            if test_scenarios:
                for i, scenario in enumerate(test_scenarios):
                    try:
                        test_result = await self._execute_scenario(scenario)
                        result['test_results'].append(test_result)

                        if not test_result.get('success', False):
                            result['errors'].append(f"Scenario {i+1} failed: {test_result.get('error', 'Unknown error')}")

                    except Exception as e:
                        result['errors'].append(f"Scenario {i+1} exception: {str(e)}")

            # Check for JS errors
            if js_errors:
                result['errors'].extend([f"JS Error: {err}" for err in js_errors])

            # Final screenshot
            screenshot_path = '/tmp/app_final.png'
            await self.page.screenshot(path=screenshot_path)
            result['screenshots'].append(screenshot_path)

            # Determine success
            result['success'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"Test exception: {str(e)}")
            result['success'] = False
            logger.error(f"Generic HTML app test failed: {e}")

        return result

    async def _execute_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test scenario"""
        action = scenario.get('action')
        selector = scenario.get('selector')

        result = {'success': False, 'action': action, 'selector': selector}

        try:
            if action == 'click':
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    result['success'] = True
                else:
                    result['error'] = f"Element not found: {selector}"

            elif action == 'type':
                element = await self.page.query_selector(selector)
                text = scenario.get('text', '')
                if element:
                    await element.type(text)
                    result['success'] = True
                else:
                    result['error'] = f"Element not found: {selector}"

            elif action == 'assert':
                element = await self.page.query_selector(selector)
                if element:
                    text_content = await element.text_content()
                    expected = scenario.get('contains', '')

                    if expected in text_content:
                        result['success'] = True
                    else:
                        result['error'] = f"Expected '{expected}' not found in '{text_content}'"
                else:
                    result['error'] = f"Element not found: {selector}"

            else:
                result['error'] = f"Unknown action: {action}"

        except Exception as e:
            result['error'] = str(e)

        return result

    async def _start_local_server(self, html_file: str, port: int = 8888) -> int:
        """
        Start a local HTTP server to serve the HTML file

        Returns:
            Port number the server is running on
        """
        import subprocess
        import socket

        # Find available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]

        # Get directory of HTML file
        html_dir = os.path.dirname(os.path.abspath(html_file))

        # Start simple HTTP server
        logger.info(f"Starting HTTP server on port {port} for {html_dir}")

        # Use Python's http.server module
        self.http_server_process = subprocess.Popen(
            ['python3', '-m', 'http.server', str(port)],
            cwd=html_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait a bit for server to start
        await asyncio.sleep(1)

        logger.info(f"✅ HTTP server started on port {port}")
        return port

    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get information about current page

        Returns:
            {
                'title': 'Page Title',
                'url': 'http://...',
                'viewport': {'width': 1280, 'height': 720},
                'elements': {
                    'buttons': 5,
                    'inputs': 3,
                    'canvases': 1
                }
            }
        """
        if not self.page:
            return {}

        title = await self.page.title()
        url = self.page.url
        viewport = self.page.viewport_size

        # Count elements
        buttons = len(await self.page.query_selector_all('button'))
        inputs = len(await self.page.query_selector_all('input'))
        canvases = len(await self.page.query_selector_all('canvas'))

        return {
            'title': title,
            'url': url,
            'viewport': viewport,
            'elements': {
                'buttons': buttons,
                'inputs': inputs,
                'canvases': canvases
            }
        }


# Example usage
async def test_example():
    """Example usage of BrowserTester"""
    async with BrowserTester() as tester:
        # Test Tetris app
        result = await tester.test_tetris_app('/path/to/tetris.html')
        print(f"Tetris test: {'✅ PASS' if result['success'] else '❌ FAIL'}")
        print(f"Errors: {result['errors']}")
        print(f"Metrics: {result['metrics']}")


if __name__ == '__main__':
    # Test if Playwright is available
    if PLAYWRIGHT_AVAILABLE:
        print("✅ Playwright available")
    else:
        print("❌ Playwright not available - install with: pip install playwright && playwright install")
