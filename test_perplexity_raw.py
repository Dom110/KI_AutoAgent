#!/usr/bin/env python3
"""
Direct test of Perplexity API
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_path)

api_key = os.getenv("PERPLEXITY_API_KEY")
print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")

# Direct API test
url = "https://api.perplexity.ai/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "sonar",
    "messages": [
        {
            "role": "user",
            "content": "What is 2+2?"
        }
    ],
    "max_tokens": 100
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success!")
        print(f"Response: {data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
    else:
        print(f"\n❌ Error: {response.text}")
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()