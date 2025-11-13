#!/usr/bin/env python3
"""
🔍 API Status Checker - Diagnose OpenAI Rate Limits & Quota

This script helps you understand why OpenAI API calls are failing with 429 errors.

Usage:
    python check_api_status.py
    python check_api_status.py --detailed
    python check_api_status.py --check-quota
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Load environment
home = Path.home()
env_file = home / ".ki_autoagent" / "config" / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 90)
    print(f"🔍 {text}")
    print("=" * 90)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def check_env_file():
    """Check if .env file exists and has API keys"""
    print_header("ENVIRONMENT FILE CHECK")
    
    print(f"\n📁 Looking for: {env_file}")
    
    if not env_file.exists():
        print_error(f"Not found: {env_file}")
        print("\n   Fix:")
        print("   1. mkdir -p ~/.ki_autoagent/config")
        print("   2. Add your API keys to ~/.ki_autoagent/config/.env")
        return False
    
    print_success(f"Found: {env_file}")
    
    # Check file permissions
    stat_info = env_file.stat()
    print(f"📊 File permissions: {oct(stat_info.st_mode)[-3:]}")
    
    if stat_info.st_mode & 0o077:
        print_warning("File is world-readable! Use: chmod 600 ~/.ki_autoagent/config/.env")
    
    # Load and check keys
    with open(env_file) as f:
        content = f.read()
    
    has_openai = "OPENAI_API_KEY" in content
    has_perplexity = "PERPLEXITY_API_KEY" in content
    
    print(f"\n📋 Keys in file:")
    print(f"   {'✅' if has_openai else '❌'} OPENAI_API_KEY: {'Present' if has_openai else 'Missing'}")
    print(f"   {'✅' if has_perplexity else '❌'} PERPLEXITY_API_KEY: {'Present' if has_perplexity else 'Missing'}")
    
    return has_openai

def check_openai_key():
    """Check OpenAI API key"""
    print_header("OPENAI API KEY CHECK")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print_error("OPENAI_API_KEY not set in environment!")
        print("\n   Steps to fix:")
        print("   1. Visit: https://platform.openai.com/api-keys")
        print("   2. Create new secret key")
        print("   3. Add to ~/.ki_autoagent/config/.env")
        return False
    
    # Check key format
    if api_key.startswith("sk-"):
        print_success(f"API Key format correct (starts with 'sk-')")
        print(f"   Key length: {len(api_key)} chars")
        print(f"   First 10 chars: {api_key[:10]}...")
    else:
        print_error(f"API Key format looks wrong (doesn't start with 'sk-')")
        return False
    
    # Try to validate with a simple API call
    print("\n🧪 Testing API connectivity...")
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "KI-AutoAgent/7.0"
        }
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("API Key is VALID - Can reach OpenAI servers")
            models_data = response.json()
            model_count = len(models_data.get("data", []))
            print(f"   Available models: {model_count}")
            return True
        elif response.status_code == 401:
            print_error("API Key is INVALID or expired")
            return False
        elif response.status_code == 429:
            print_warning("API Key works but rate-limited (429)")
            return True
        else:
            print_warning(f"Unexpected response: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Could not test API key: {e}")
        return False

def check_quota_status():
    """Check OpenAI account quota/billing status"""
    print_header("OPENAI QUOTA & BILLING CHECK")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not set")
        return
    
    print("\n📊 How to check your quota manually:")
    print("   1. Visit: https://platform.openai.com/account/billing/overview")
    print("   2. Check your credit balance")
    print("   3. Check your usage at: https://platform.openai.com/account/usage/overview")
    
    print("\n⚠️  COMMON CAUSES OF 429 ERRORS:")
    print("   ❌ Account has $0.00 balance (insufficient_quota)")
    print("   ❌ Account suspended due to policy violation")
    print("   ❌ Billing information not on file")
    print("   ❌ Monthly usage limit exceeded")
    print("   ❌ Too many requests in short time (actual rate limit)")
    
    print("\n✅ HOW TO FIX:")
    print("   1. Log in: https://platform.openai.com/account/billing/overview")
    print("   2. Add payment method or prepaid credits")
    print("   3. Wait 5 minutes for changes to take effect")
    print("   4. Try API call again")

def check_rate_limits():
    """Explain rate limits"""
    print_header("RATE LIMIT EXPLANATION")
    
    print("\n📊 TIER 1 RATE LIMITS (Free Trial):")
    print("   • 3 requests / minute (RPM)")
    print("   • 200,000 tokens / day (TPD)")
    print("   • 1 concurrent request (CR)")
    
    print("\n📊 TIER 2 RATE LIMITS ($5+ spent):")
    print("   • 3,500 requests / minute (RPM)")
    print("   • 90,000 tokens / minute (TPM)")
    print("   • 10 concurrent requests (CR)")
    
    print("\n📊 TIER 5 RATE LIMITS (Heavy usage):")
    print("   • 10,000+ requests / minute (RPM)")
    print("   • 2,000,000+ tokens / minute (TPM)")
    print("   • 200 concurrent requests (CR)")
    
    print("\n⚠️  ERROR CODE MEANINGS:")
    print("   • 429 - Rate limit exceeded")
    print("       - Too many requests in short time")
    print("       - Or: insufficient_quota (no credits)")
    print("   • 401 - API Key invalid")
    print("   • 500 - Server error (retry)")
    print("   • 503 - Service unavailable (retry)")

def check_recent_logs():
    """Check server logs for recent errors"""
    print_header("RECENT API ERRORS FROM LOGS")
    
    log_file = Path("server_startup.log")
    if not log_file.exists():
        print_warning("server_startup.log not found")
        return
    
    print(f"\n📄 Reading: {log_file}\n")
    
    try:
        with open(log_file) as f:
            lines = f.readlines()
        
        # Find API errors
        errors = []
        for i, line in enumerate(lines):
            if "429" in line or "quota" in line.lower() or "insufficient" in line.lower():
                errors.append({
                    "line_num": i,
                    "text": line.strip()[:100],
                    "full_text": line.strip()
                })
        
        if errors:
            print(f"Found {len(errors)} error(s):\n")
            for error in errors[-10:]:  # Show last 10
                print(f"   Line {error['line_num']}: {error['full_text'][:80]}")
        else:
            print_success("No 429 or quota errors found in logs")
            
        # Find successful calls
        success = sum(1 for line in lines if "OPENAI API CALL" in line and "FAILED" not in line)
        failed = sum(1 for line in lines if "OPENAI API CALL" in line and "FAILED" in line)
        
        print(f"\n📊 API Call Statistics:")
        print(f"   ✅ Successful calls: {success}")
        print(f"   ❌ Failed calls: {failed}")
        
    except Exception as e:
        print_error(f"Could not read logs: {e}")

def show_test_command():
    """Show how to run tests"""
    print_header("HOW TO RUN E2E TESTS")
    
    print("\n1️⃣  Start server (Terminal 1):")
    print("   cd /Users/dominikfoert/git/KI_AutoAgent")
    print("   source venv/bin/activate")
    print("   python start_server.py")
    
    print("\n2️⃣  Wait for startup message:")
    print("   INFO:     Application startup complete.")
    print("   INFO:     Uvicorn running on http://0.0.0.0:8002")
    
    print("\n3️⃣  Run tests (Terminal 2):")
    print("   cd /Users/dominikfoert/git/KI_AutoAgent")
    print("   source venv/bin/activate")
    print("   python e2e_test_v7_0_supervisor.py")
    
    print("\n4️⃣  Monitor logs (Terminal 3):")
    print("   tail -f server_startup.log | grep -i 'openai\\|error\\|429'")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Check API status and rate limits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_api_status.py           # Basic check
  python check_api_status.py --detailed  # Full diagnostics
  python check_api_status.py --check-quota  # Quota status
        """
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed diagnostics"
    )
    
    parser.add_argument(
        "--check-quota",
        action="store_true",
        help="Check OpenAI quota status"
    )
    
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Check recent logs for errors"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 90)
    print("🔍 KI AutoAgent v7.0 - API STATUS & RATE LIMIT CHECKER")
    print("=" * 90)
    
    # Run checks
    check_env_file()
    check_openai_key()
    
    if args.detailed or args.check_quota:
        check_quota_status()
        check_rate_limits()
    
    if args.logs:
        check_recent_logs()
    
    if not args.detailed and not args.check_quota and not args.logs:
        print("\n📋 TIP: Run with options for more info:")
        print("   python check_api_status.py --detailed    # Full diagnostics")
        print("   python check_api_status.py --check-quota  # Quota status")
        print("   python check_api_status.py --logs         # Check recent logs")
    
    show_test_command()
    
    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    main()