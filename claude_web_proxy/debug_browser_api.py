#!/usr/bin/env python3
"""
Debug Script: Playwright Browser API Analysis
Analyze verfügbare Methoden auf Browser und Context Objekten
"""
import asyncio
import sys
from pathlib import Path
import traceback

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
import structlog

logger = structlog.get_logger()

async def analyze_browser_api():
    """Analyze Browser and BrowserContext API methods"""
    print("🔍 DEBUG: Starting Browser API Analysis")
    print("=" * 60)
    
    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            print(f"✅ Browser launched: {type(browser)}")
            
            # Create context  
            context = await browser.new_context()
            print(f"✅ Context created: {type(context)}")
            
            # Create page
            page = await context.new_page()
            print(f"✅ Page created: {type(page)}")
            
            print("\n" + "="*60)
            print("🔍 BROWSER API ANALYSIS")
            print("="*60)
            
            # Analyze Browser methods
            browser_methods = [method for method in dir(browser) 
                             if not method.startswith('_')]
            print(f"📊 Browser methods total: {len(browser_methods)}")
            
            # Look for close-related methods
            browser_close_methods = [method for method in browser_methods 
                                   if 'close' in method.lower()]
            print(f"🔍 Browser close-related methods: {browser_close_methods}")
            
            # Look for status/state methods
            browser_status_methods = [method for method in browser_methods 
                                    if any(word in method.lower() for word in ['status', 'state', 'connect', 'alive', 'running'])]
            print(f"🔍 Browser status-related methods: {browser_status_methods}")
            
            print("\n" + "="*60)
            print("🔍 BROWSER CONTEXT API ANALYSIS")
            print("="*60)
            
            # Analyze Context methods  
            context_methods = [method for method in dir(context) 
                             if not method.startswith('_')]
            print(f"📊 Context methods total: {len(context_methods)}")
            
            # Look for close-related methods
            context_close_methods = [method for method in context_methods 
                                   if 'close' in method.lower()]
            print(f"🔍 Context close-related methods: {context_close_methods}")
            
            # Look for status/state methods
            context_status_methods = [method for method in context_methods 
                                    if any(word in method.lower() for word in ['status', 'state', 'connect', 'alive', 'running'])]
            print(f"🔍 Context status-related methods: {context_status_methods}")
            
            print("\n" + "="*60)
            print("🔍 PAGE API ANALYSIS")  
            print("="*60)
            
            # Analyze Page methods
            page_methods = [method for method in dir(page) 
                           if not method.startswith('_')]
            
            # Look for close-related methods
            page_close_methods = [method for method in page_methods 
                                if 'close' in method.lower()]
            print(f"🔍 Page close-related methods: {page_close_methods}")
            
            # Look for status methods
            page_status_methods = [method for method in page_methods 
                                 if any(word in method.lower() for word in ['status', 'state', 'connect', 'alive', 'running', 'closed'])]
            print(f"🔍 Page status-related methods: {page_status_methods}")
            
            print("\n" + "="*60)
            print("🔍 TESTING ALTERNATIVE STATUS METHODS")
            print("="*60)
            
            # Test verschiedene Status-Checking Ansätze
            print("Testing Browser status checks:")
            
            # Test 1: Browser connected check
            try:
                connected = browser.is_connected()
                print(f"✅ browser.is_connected(): {connected}")
            except AttributeError as e:
                print(f"❌ browser.is_connected() not available: {e}")
            except Exception as e:
                print(f"⚠️  browser.is_connected() error: {e}")
                
            # Test 2: Context pages check
            try:
                pages = context.pages
                print(f"✅ context.pages count: {len(pages)}")
                print(f"✅ context.pages available: {len(pages) > 0}")
            except Exception as e:
                print(f"❌ context.pages error: {e}")
                
            # Test 3: Page is_closed check
            try:
                page_closed = page.is_closed()
                print(f"✅ page.is_closed(): {page_closed}")
            except AttributeError as e:
                print(f"❌ page.is_closed() not available: {e}")
            except Exception as e:
                print(f"⚠️  page.is_closed() error: {e}")
            
            print("\n" + "="*60)
            print("🔍 RECOMMENDED BROWSER STATUS CHECK")
            print("="*60)
            
            # Empfohlener Status-Check Ansatz
            def recommended_browser_status_check():
                try:
                    # Check 1: Browser und Context existieren
                    if not browser or not context:
                        return False
                        
                    # Check 2: Context hat verfügbare Pages
                    pages = context.pages
                    if len(pages) == 0:
                        return False
                        
                    # Check 3: Erste Page ist nicht geschlossen (falls is_closed verfügbar)
                    first_page = pages[0]
                    try:
                        if hasattr(first_page, 'is_closed') and first_page.is_closed():
                            return False
                    except:
                        pass  # Fallback: ignoriere is_closed error
                        
                    return True
                except Exception:
                    return False
            
            recommended_status = recommended_browser_status_check()
            print(f"✅ Recommended status check result: {recommended_status}")
            
            # Test Code für fastapi_server.py Replacement
            print("\n" + "="*60)
            print("🔧 FASTAPI_SERVER.PY FIX CODE")
            print("="*60)
            
            fix_code = '''
# REPLACE THIS (Line 114):
# browser_running = claude_browser.browser is not None and not claude_browser.browser.is_closed()

# WITH THIS:
def check_browser_running(self) -> bool:
    """Safe browser status check without is_closed()"""
    try:
        if not self.browser or not self.context:
            return False
        
        # Check if context has active pages
        pages = self.context.pages
        if len(pages) == 0:
            return False
            
        # Optional: Check if first page is not closed (if method exists)
        try:
            first_page = pages[0]
            if hasattr(first_page, 'is_closed') and first_page.is_closed():
                return False
        except:
            pass  # Ignore is_closed errors, use pages count as indicator
            
        return True
    except Exception:
        return False

# Usage in fastapi_server.py:
browser_running = claude_browser.check_browser_running() if claude_browser else False
            '''
            print(fix_code)
            
            print("\n" + "="*60)
            print("🔍 CLAUDE BROWSER OBJECT CONFUSION ANALYSIS")
            print("="*60)
            
            # Test the ClaudeBrowser confusion
            print("Testing launch_persistent_context vs launch:")
            
            # Method 1: launch_persistent_context (wie ClaudeBrowser)
            persistent_context = await p.chromium.launch_persistent_context(
                user_data_dir="./temp_profile",
                headless=True
            )
            
            print(f"✅ launch_persistent_context returns: {type(persistent_context)}")
            print(f"✅ Has .pages: {hasattr(persistent_context, 'pages')}")
            print(f"✅ Has .new_page(): {hasattr(persistent_context, 'new_page')}")
            print(f"✅ Has .close(): {hasattr(persistent_context, 'close')}")
            print(f"❌ Has .is_connected(): {hasattr(persistent_context, 'is_connected')}")
            print(f"❌ Has .is_closed(): {hasattr(persistent_context, 'is_closed')}")
            
            # Method 2: Regular launch (echter Browser)
            regular_browser = await p.chromium.launch(headless=True)
            print(f"\n✅ launch returns: {type(regular_browser)}")
            print(f"❌ Has .pages: {hasattr(regular_browser, 'pages')}")
            print(f"❌ Has .new_page(): {hasattr(regular_browser, 'new_page')}")
            print(f"✅ Has .close(): {hasattr(regular_browser, 'close')}")
            print(f"✅ Has .is_connected(): {hasattr(regular_browser, 'is_connected')}")
            print(f"❌ Has .is_closed(): {hasattr(regular_browser, 'is_closed')}")
            
            print("\n" + "="*60)
            print("🎯 CLAUDE BROWSER NAMING CONFUSION SOLVED!")
            print("="*60)
            print("❌ PROBLEM: ClaudeBrowser.browser is actually a BrowserContext!")
            print("✅ SOLUTION: Use BrowserContext methods for status checking")
            
            print("\n🔧 CORRECT STATUS CHECK FOR BROWSERCONTEXT:")
            
            correct_status_code = '''
def check_browser_context_status(context) -> bool:
    """Correct status check for BrowserContext (not Browser)"""
    try:
        if not context:
            return False
        
        # BrowserContext status via pages
        pages = context.pages
        if len(pages) == 0:
            return False
        
        # Check if first page is not closed
        first_page = pages[0]
        return not first_page.is_closed()
        
    except Exception:
        return False

# Usage in fastapi_server.py:
# WRONG: browser_running = claude_browser.browser.is_connected()  # ❌
# CORRECT: browser_running = check_browser_context_status(claude_browser.browser)  # ✅
            '''
            print(correct_status_code)
            
            # Test the correct status check
            print("\n🧪 Testing correct BrowserContext status check:")
            try:
                pages = persistent_context.pages
                if len(pages) > 0:
                    first_page = pages[0]
                    page_closed = first_page.is_closed()
                    context_status = len(pages) > 0 and not page_closed
                    print(f"✅ BrowserContext status check result: {context_status}")
                else:
                    print("✅ BrowserContext status: No pages (not ready)")
            except Exception as e:
                print(f"❌ BrowserContext status check error: {e}")
            
            print("\n🎉 Browser API Analysis Complete!")
            
            # Cleanup
            try:
                await persistent_context.close()
                await regular_browser.close()
            except:
                pass
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            
        finally:
            try:
                await browser.close()
                print("✅ Browser closed successfully")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(analyze_browser_api())