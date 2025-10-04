#!/usr/bin/env python3
"""
Test script for API keys
Tests all AI service connections
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

print("🔍 Testing API Keys...\n")

# Test OpenAI
print("1️⃣ Testing OpenAI API...")
try:
    from utils.openai_service import OpenAIService, OpenAIConfig
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found in environment")
    else:
        print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
        print(f"   Key length: {len(api_key)} characters")
        
        # Initialize service
        config = OpenAIConfig(api_key=api_key)
        service = OpenAIService(config)
        
        # Test API call
        async def test_openai():
            try:
                response = await service.complete(
                    prompt="Say 'API working' in 3 words",
                    max_tokens=10
                )
                print(f"✅ OpenAI API Response: {response}")
                return True
            except Exception as e:
                print(f"❌ OpenAI API Error: {e}")
                return False
        
        success = asyncio.run(test_openai())
        
except Exception as e:
    print(f"❌ Error testing OpenAI: {e}")

print("\n" + "="*50)

# Test Anthropic
print("\n2️⃣ Testing Anthropic API...")
try:
    from utils.anthropic_service import AnthropicService
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  No Anthropic API key found (optional)")
    else:
        print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
        service = AnthropicService()
        
        async def test_anthropic():
            try:
                response = await service.get_completion(
                    user_prompt="Say 'API working' in 3 words",
                    max_tokens=10
                )
                print(f"✅ Anthropic API Response: {response}")
                return True
            except Exception as e:
                print(f"❌ Anthropic API Error: {e}")
                return False
        
        asyncio.run(test_anthropic())
        
except Exception as e:
    print(f"⚠️  Error testing Anthropic: {e}")

print("\n" + "="*50)

# Test Perplexity
print("\n3️⃣ Testing Perplexity API...")
api_key = os.getenv("PERPLEXITY_API_KEY")
if not api_key:
    print("⚠️  No Perplexity API key found (optional)")
else:
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
    print("   (Perplexity service not yet implemented)")

print("\n" + "="*50)

# Alternative test with requests
print("\n4️⃣ Direct OpenAI API Test with requests...")
try:
    import requests
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test models endpoint
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Direct API test successful!")
            print(f"   Available models: {len(models['data'])}")
            # Show GPT-4 models
            gpt4_models = [m['id'] for m in models['data'] if 'gpt-4' in m['id']]
            if gpt4_models:
                print(f"   GPT-4 models: {', '.join(gpt4_models[:3])}...")
        else:
            print(f"❌ Direct API test failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
except Exception as e:
    print(f"❌ Direct API test error: {e}")

print("\n" + "="*50)
print("\n📋 Summary:")
print("1. Check if the API key is correct")
print("2. Make sure you're using a valid OpenAI API key")
print("3. The key should start with 'sk-' or 'sk-proj-'")
print("4. Check your OpenAI account for billing/quota issues")
print("\nGet your key at: https://platform.openai.com/api-keys")
