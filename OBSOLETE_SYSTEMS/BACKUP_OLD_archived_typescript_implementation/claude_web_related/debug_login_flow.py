#!/usr/bin/env python3
"""
Debug script to test Claude Web Proxy login detection
This script helps test the enhanced login detection capabilities
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from claude_web_proxy.claude_browser import ClaudeBrowser
import structlog

# Set up logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_login_detection():
    """Test the comprehensive login detection system"""
    
    print("🧪 Claude Web Proxy - Login Detection Debug Tool")
    print("=" * 60)
    
    browser = None
    try:
        # Create browser instance (non-headless for testing)
        print("🚀 Starting browser...")
        browser = ClaudeBrowser(headless=False)
        await browser.start_browser()
        
        print("✅ Browser started successfully")
        print()
        
        # Test 1: Initial login status check
        print("🧪 TEST 1: Initial login status check")
        print("-" * 40)
        initial_status = await browser.check_login_status()
        print(f"Initial login status: {initial_status}")
        print()
        
        if not initial_status:
            # Test 2: Wait for manual login
            print("🧪 TEST 2: Manual login detection")
            print("-" * 40)
            print("👤 Please log in to Claude in the browser window...")
            print("🔍 The system will monitor for login completion...")
            print()
            
            login_success = await browser.wait_for_login(timeout=300)  # 5 minutes
            
            if login_success:
                print("✅ Login detected successfully!")
            else:
                print("❌ Login not detected (timeout or error)")
        else:
            print("ℹ️  Already logged in, skipping manual login test")
        
        print()
        
        # Test 3: Final status verification
        print("🧪 TEST 3: Final status verification")
        print("-" * 40)
        final_status = await browser.check_login_status()
        print(f"Final login status: {final_status}")
        
        print()
        print("🔍 Final debug analysis:")
        await browser.debug_login_detection()
        
        print()
        if final_status:
            print("🎉 SUCCESS: Login detection is working correctly!")
        else:
            print("⚠️  WARNING: Login detection may need further improvement")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"💥 Error during testing: {e}")
        logger.error("Test failed", error=str(e))
    finally:
        if browser:
            print("\n🧹 Cleaning up...")
            await browser.close()
            print("✅ Browser closed")

async def test_comprehensive_checks():
    """Test only the comprehensive login check methods"""
    
    print("🔬 Testing Comprehensive Login Check Methods")
    print("=" * 60)
    
    browser = None
    try:
        browser = ClaudeBrowser(headless=False)
        await browser.start_browser()
        
        # Navigate to Claude
        await browser.page.goto('https://claude.ai')
        await asyncio.sleep(3)
        
        print("🔍 Running debug login detection...")
        await browser.debug_login_detection()
        
        print()
        print("🧪 Running comprehensive login check...")
        result = await browser._comprehensive_login_check()
        print(f"Comprehensive check result: {result}")
        
        print()
        print("Press Enter to exit...")
        input()
        
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        if browser:
            await browser.close()

def main():
    """Main function with menu"""
    print("🔧 Claude Web Proxy Debug Tool")
    print("Choose a test mode:")
    print("1. Full login flow test (recommended)")
    print("2. Comprehensive check methods only")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print()
        asyncio.run(test_login_detection())
    elif choice == "2":
        print()
        asyncio.run(test_comprehensive_checks())
    elif choice == "3":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice. Exiting.")
        return

if __name__ == "__main__":
    main()