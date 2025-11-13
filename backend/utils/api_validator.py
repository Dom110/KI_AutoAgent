"""
API Key Validator Utility

Provides reusable API key validation for all MCP servers.
Each server validates its own keys independently.

Best Practices:
- Specific exception handling (not bare Exception)
- Minimal try block scope
- Clear error messages for debugging
- Non-blocking for optional services
"""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_openai_key(api_key: Optional[str] = None, exit_on_fail: bool = True) -> bool:
    """
    Validate OpenAI API key connectivity.
    
    Args:
        api_key: Optional API key. If None, reads from OPENAI_API_KEY env var
        exit_on_fail: If True, sys.exit(1) on validation failure
        
    Returns:
        True if valid, False otherwise (only if exit_on_fail=False)
        
    Raises:
        SystemExit: If validation fails and exit_on_fail=True
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    
    if not key or key == "":
        msg = "❌ OPENAI_API_KEY not set or empty!"
        logger.error(msg)
        logger.error("   Required for: GPT-4o Supervisor, Embeddings")
        logger.error("   Set in: ~/.ki_autoagent/config/.env")
        
        if exit_on_fail:
            sys.exit(1)
        return False
    
    # Test connectivity
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=key)
        client.models.list()  # Quick API test
        logger.info("✅ OPENAI_API_KEY: Valid")
        return True
        
    except (ImportError, ModuleNotFoundError) as e:
        msg = f"❌ OpenAI package not installed: {e}"
        logger.error(msg)
        
        if exit_on_fail:
            sys.exit(1)
        return False
        
    except Exception as e:
        msg = f"❌ OPENAI_API_KEY: Invalid - {str(e)[:80]}"
        logger.error(msg)
        logger.error("   Update your key in: ~/.ki_autoagent/config/.env")
        
        if exit_on_fail:
            sys.exit(1)
        return False


def validate_perplexity_key(api_key: Optional[str] = None, exit_on_fail: bool = False) -> bool:
    """
    Validate Perplexity API key connectivity.
    
    Args:
        api_key: Optional API key. If None, reads from PERPLEXITY_API_KEY env var
        exit_on_fail: If True, sys.exit(1) on validation failure (default: False for optional)
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        SystemExit: If validation fails and exit_on_fail=True
    """
    key = api_key or os.environ.get("PERPLEXITY_API_KEY")
    
    if not key or key == "":
        msg = "⚠️ PERPLEXITY_API_KEY not set or empty!"
        logger.warning(msg)
        logger.warning("   Optional for: Research Agent (web search & real-time data)")
        logger.warning("   Get your key from: https://www.perplexity.ai/api")
        
        if exit_on_fail:
            sys.exit(1)
        return False
    
    # Test connectivity
    try:
        import requests
        
        # First: Check format (Perplexity keys usually have pattern)
        if not key or len(key) < 10:
            raise RuntimeError("Key format invalid - too short")
        
        # Second: Quick HEAD request to verify connectivity (faster than POST)
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        # Try HEAD request first (fastest check)
        try:
            response = requests.head(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                timeout=3,
                allow_redirects=True
            )
            # If HEAD fails with 400+ codes, try POST with minimal data
            if response.status_code >= 500:
                raise RuntimeError(f"API server error: {response.status_code}")
        except (requests.Timeout, requests.ConnectionError):
            # HEAD timeout/connection error - try lightweight POST
            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1
            }
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=8
            )
        
        # Status codes that indicate valid key:
        # 200=success, 400=param error (but auth OK), 401=auth fail, 
        # 429=rate limited (but auth OK), 503=server down
        if response.status_code in (200, 400, 429):
            logger.info("✅ PERPLEXITY_API_KEY: Valid")
            return True
        elif response.status_code == 401:
            raise RuntimeError("Unauthorized - key is invalid")
        else:
            logger.warning(f"⚠️ PERPLEXITY_API_KEY: Connectivity uncertain (HTTP {response.status_code})")
            logger.warning("   Will attempt to use the key anyway")
            return True  # Give benefit of doubt
            
    except (ImportError, ModuleNotFoundError) as e:
        logger.warning(f"⚠️ requests package not installed: {e}")
        logger.warning("   Skipping Perplexity key validation")
        return False
        
    except Exception as e:
        msg = f"⚠️ PERPLEXITY_API_KEY: Validation error - {str(e)[:80]}"
        logger.warning(msg)
        logger.warning("   Proceeding anyway - may fail at runtime")
        
        if exit_on_fail:
            sys.exit(1)
        return False


def validate_all_required_keys() -> None:
    """
    Validate all required API keys for the application.
    
    Exits with error code 1 if any required key is missing or invalid.
    Used by central server on startup.
    """
    logger.info("🔑 Validating API keys...")
    
    # OpenAI is required
    validate_openai_key(exit_on_fail=True)
    
    # Perplexity is optional but nice to have
    validate_perplexity_key(exit_on_fail=False)
    
    logger.info("🔑 API key validation complete")


__all__ = [
    "validate_openai_key",
    "validate_perplexity_key", 
    "validate_all_required_keys"
]