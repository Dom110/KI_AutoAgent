"""
Claude Browser Automation
Browser automation for claude.ai using Playwright
"""
import asyncio
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
import structlog
from playwright.async_api import async_playwright, Browser, Page, Playwright

logger = structlog.get_logger()

class ClaudeBrowser:
    """
    Browser automation class for interacting with Claude Web (claude.ai)
    """
    
    def __init__(self, 
                 user_data_dir: Optional[str] = None,
                 headless: bool = False):
        """
        Initialize Claude Browser
        
        Args:
            user_data_dir: Directory to store browser profile (for persistent login)
            headless: Run browser in headless mode
        """
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.headless = headless
        self.user_data_dir = user_data_dir or str(Path.home() / ".claude_proxy" / "browser_profile")
        self.is_logged_in = False
        self.conversation_id: Optional[str] = None
        
        # Ensure user data directory exists
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        
    async def start_browser(self) -> None:
        """Start the browser with persistent profile"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with persistent context
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                args=[
                    '--no-first-run',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                ],
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = await self.browser.new_page()
            
            # Set user agent to avoid detection
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("Browser started successfully", headless=self.headless)
            
        except Exception as e:
            logger.error("Failed to start browser", error=str(e))
            raise
    
    async def check_login_status(self) -> bool:
        """Check if user is logged into Claude"""
        try:
            await self.page.goto('https://claude.ai', wait_until='networkidle', timeout=30000)
            
            # Wait a bit for page to load completely
            await asyncio.sleep(2)
            
            # Check for login indicators
            # If we see the chat interface, we're logged in
            try:
                await self.page.wait_for_selector('[data-testid="chat-input"]', timeout=5000)
                self.is_logged_in = True
                logger.info("User is logged in to Claude")
                return True
            except:
                # Check if we're on login page
                login_elements = [
                    'button:has-text("Continue with Google")',
                    'button:has-text("Continue with Email")', 
                    'input[type="email"]'
                ]
                
                for element in login_elements:
                    try:
                        await self.page.wait_for_selector(element, timeout=2000)
                        self.is_logged_in = False
                        logger.info("User needs to log in to Claude")
                        return False
                    except:
                        continue
                
                # If we can't determine, assume not logged in
                self.is_logged_in = False
                return False
                
        except Exception as e:
            logger.error("Error checking login status", error=str(e))
            return False
    
    async def wait_for_login(self, timeout: int = 300) -> bool:
        """
        Wait for user to log in manually (interactive login)
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            bool: True if login successful
        """
        try:
            logger.info("Waiting for user to log in manually...", timeout=timeout)
            
            # Navigate to Claude if not already there
            current_url = self.page.url
            if 'claude.ai' not in current_url:
                await self.page.goto('https://claude.ai')
            
            # Wait for chat interface to appear (indicates successful login)
            await self.page.wait_for_selector(
                '[data-testid="chat-input"], .chat-input, textarea[placeholder*="message"]', 
                timeout=timeout * 1000
            )
            
            self.is_logged_in = True
            logger.info("Login successful!")
            return True
            
        except Exception as e:
            logger.error("Login timeout or failed", error=str(e))
            return False
    
    async def start_new_conversation(self) -> bool:
        """Start a new conversation"""
        try:
            # Look for new conversation button
            new_chat_selectors = [
                'button:has-text("New Chat")',
                '[data-testid="new-chat-button"]',
                'button[aria-label*="New"]',
                '.new-conversation'
            ]
            
            for selector in new_chat_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    await asyncio.sleep(1)
                    logger.info("Started new conversation")
                    return True
                except:
                    continue
            
            # If no button found, we might already be in a new conversation
            logger.info("No new chat button found, using current conversation")
            return True
            
        except Exception as e:
            logger.error("Failed to start new conversation", error=str(e))
            return False
    
    async def send_message(self, message: str, timeout: int = 120) -> str:
        """
        Send message to Claude and get response
        
        Args:
            message: Message to send
            timeout: Timeout in seconds
            
        Returns:
            Claude's response as string
        """
        try:
            if not self.is_logged_in:
                raise Exception("Not logged in to Claude")
            
            logger.info("Sending message to Claude", message_length=len(message))
            
            # Find input field and send message
            input_selectors = [
                '[data-testid="chat-input"]',
                'textarea[placeholder*="message"]',
                '.chat-input textarea',
                'div[contenteditable="true"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self.page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            if not input_element:
                raise Exception("Could not find chat input field")
            
            # Clear and type message
            await input_element.click()
            await input_element.fill(message)
            
            # Send message (usually Enter or Send button)
            send_selectors = [
                'button[aria-label*="Send"]',
                'button:has-text("Send")',
                '[data-testid="send-button"]',
                'button[type="submit"]'
            ]
            
            # Try to click send button, fallback to Enter key
            sent = False
            for selector in send_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    sent = True
                    break
                except:
                    continue
            
            if not sent:
                # Fallback: press Enter
                await input_element.press('Enter')
            
            # Wait for response to appear
            await asyncio.sleep(2)  # Give Claude time to start responding
            
            # Wait for Claude to finish responding (look for typing indicator to disappear)
            typing_selectors = [
                '.typing-indicator',
                '[data-testid="typing-indicator"]',
                '.is-typing',
                '.streaming'
            ]
            
            # Wait for typing to start (optional)
            for selector in typing_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            # Wait for typing to stop
            await asyncio.sleep(2)
            for selector in typing_selectors:
                try:
                    await self.page.wait_for_selector(selector, state='detached', timeout=timeout * 1000)
                    break
                except:
                    continue
            
            # Give a moment for final content to load
            await asyncio.sleep(2)
            
            # Get the latest response
            response = await self.get_latest_response()
            
            logger.info("Received response from Claude", response_length=len(response))
            return response
            
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            raise
    
    async def get_latest_response(self) -> str:
        """Get the latest response from Claude"""
        try:
            # Common selectors for Claude's response
            response_selectors = [
                '.message-content:last-of-type',
                '[data-testid="message-content"]:last-of-type', 
                '.assistant-message:last-of-type',
                '.response-content:last-of-type'
            ]
            
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Get the last response
                        last_element = elements[-1]
                        response_text = await last_element.inner_text()
                        if response_text.strip():
                            return response_text.strip()
                except:
                    continue
            
            # Fallback: get all message-like content and return the last one
            all_messages = await self.page.query_selector_all('div[class*="message"], div[class*="response"]')
            if all_messages:
                for element in reversed(all_messages):
                    text = await element.inner_text()
                    if text.strip() and len(text.strip()) > 10:  # Ignore very short messages
                        return text.strip()
            
            # Last resort: get all text content and try to find the response
            page_content = await self.page.content()
            logger.warning("Could not find response with selectors, returning generic message")
            return "Response received but could not extract content"
            
        except Exception as e:
            logger.error("Failed to get latest response", error=str(e))
            return f"Error getting response: {str(e)}"
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error("Error closing browser", error=str(e))
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience functions
async def create_claude_browser(headless: bool = False) -> ClaudeBrowser:
    """Create and start a Claude browser instance"""
    browser = ClaudeBrowser(headless=headless)
    await browser.start_browser()
    return browser


if __name__ == "__main__":
    # Test the browser
    async def test_browser():
        async with ClaudeBrowser(headless=False) as browser:
            # Check login status
            logged_in = await browser.check_login_status()
            
            if not logged_in:
                print("Please log in to Claude in the opened browser window...")
                logged_in = await browser.wait_for_login()
            
            if logged_in:
                # Start new conversation
                await browser.start_new_conversation()
                
                # Send test message
                response = await browser.send_message("Hello! Can you tell me what 2+2 equals?")
                print(f"Claude's response: {response}")
            else:
                print("Failed to log in")
    
    asyncio.run(test_browser())