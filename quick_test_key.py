#!/usr/bin/env python3
"""
Quick API Key Tester
Einfacher Test für deinen neuen OpenAI API Key
"""

print("🔍 Quick OpenAI API Key Test\n")
print("="*50)

api_key = input("\nBitte gib deinen OpenAI API Key ein\n(beginnt mit 'sk-' oder 'sk-proj-'): ").strip()

if not api_key:
    print("❌ Kein Key eingegeben")
    exit(1)

if not (api_key.startswith('sk-') or api_key.startswith('sk-proj-')):
    print("⚠️  Warnung: Key sollte mit 'sk-' oder 'sk-proj-' beginnen")

print(f"\n🔑 Testing key: {api_key[:20]}...{api_key[-4:]}")
print(f"   Länge: {len(api_key)} Zeichen")

if len(api_key) > 100:
    print("⚠️  Warnung: Key ist sehr lang. Normal sind ~51 Zeichen")

print("\n🚀 Teste API-Verbindung...\n")

try:
    import openai
except ImportError:
    print("Installiere openai...")
    import subprocess
    subprocess.check_call(["pip", "install", "openai", "-q"])
    import openai

# Test the key
client = openai.OpenAI(api_key=api_key)

try:
    # Simple test call
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cheapest model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with exactly: API_KEY_VALID"}
        ],
        max_tokens=10,
        temperature=0
    )
    
    result = response.choices[0].message.content
    
    if "API_KEY_VALID" in result:
        print("✅ SUCCESS! API Key ist gültig und funktioniert!")
        print(f"\n🎆 Antwort vom Model: {result}")
        print("\n👍 Nächste Schritte:")
        print("1. Trage diesen Key in /backend/.env ein:")
        print(f"   OPENAI_API_KEY={api_key}")
        print("2. Starte den Backend Server neu")
        print("3. Fertig! Die Agenten können jetzt mit echter AI arbeiten")
    else:
        print(f"⚠️  Unerwartete Antwort: {result}")
        
except openai.AuthenticationError as e:
    print(f"❌ AUTHENTICATION ERROR: Der API Key ist ungültig")
    print(f"   Details: {e}")
    print("\n🔄 Lösung:")
    print("1. Gehe zu https://platform.openai.com/api-keys")
    print("2. Erstelle einen neuen API Key")
    print("3. Kopiere den KOMPLETTEN Key (ohne Leerzeichen)")
    
except openai.RateLimitError as e:
    print(f"❌ RATE LIMIT: Du hast dein Limit erreicht")
    print(f"   Details: {e}")
    print("\n🔄 Lösung:")
    print("1. Warte ein paar Minuten")
    print("2. Oder upgrade deinen OpenAI Plan")
    
except openai.PermissionDeniedError as e:
    print(f"❌ PERMISSION DENIED: Keine Berechtigung")
    print(f"   Details: {e}")
    print("\n🔄 Lösung:")
    print("1. Prüfe deine OpenAI Account Einstellungen")
    print("2. Füge eine Zahlungsmethode hinzu")
    print("3. Lade mindestens $5 Guthaben auf")
    
except Exception as e:
    print(f"❌ FEHLER: {type(e).__name__}")
    print(f"   Details: {e}")
    
    if "billing" in str(e).lower() or "quota" in str(e).lower():
        print("\n💳 Wahrscheinlich ein Billing-Problem:")
        print("1. Gehe zu https://platform.openai.com/account/billing")
        print("2. Füge eine Zahlungsmethode hinzu")
        print("3. Lade Guthaben auf (min $5)")

print("\n" + "="*50)
