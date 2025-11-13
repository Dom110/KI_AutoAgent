# 🔑 OpenAI API Key einrichten

## Schritt 1: Neuen API Key generieren

1. Gehe zu: https://platform.openai.com/api-keys
2. Logge dich mit deinem OpenAI Account ein
3. Klicke auf "+ Create new secret key"
4. Gib einen Namen ein (z.B. "KI_AutoAgent")
5. Wähle die Permissions (All für vollen Zugriff)
6. Klicke "Create secret key"
7. **WICHTIG**: Kopiere den Key SOFORT (wird nur einmal angezeigt!)

## Schritt 2: Key Format prüfen

Ein gültiger OpenAI API Key:
- Beginnt mit `sk-` oder `sk-proj-`
- Hat normalerweise ~51 Zeichen (NICHT 164!)
- Sieht so aus: `sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

## Schritt 3: Key in .env eintragen

```bash
# Öffne die .env Datei
cd /Users/dominikfoert/git/KI_AutoAgent/backend
nano .env
```

Ersetze die alte Zeile mit:
```env
OPENAI_API_KEY=dein-neuer-key-hier
```

## Schritt 4: Key testen

```bash
# Aktiviere Virtual Environment
source venv/bin/activate

# Teste den Key
python test_api_keys.py
```

## Schritt 5: Backend neu starten

```bash
# Stoppe alten Server
pkill -f "uvicorn.*api.server"

# Starte neu
python -m uvicorn api.server:app --reload --port 8000
```

## 🚨 Häufige Probleme:

### "You exceeded your current quota"
- Füge eine Zahlungsmethode hinzu: https://platform.openai.com/account/billing/payment-methods
- Lade Guthaben auf (min. $5)

### "Invalid API key"
- Prüfe ob der Key vollständig kopiert wurde
- Keine Leerzeichen oder Zeilenumbrüche im Key
- Key nicht mit Anführungszeichen umgeben

### "Rate limit exceeded"
- Warte ein paar Minuten
- Upgrade auf höheres Tier wenn nötig

## 💰 Kosten-Übersicht:

- **GPT-4o**: $5.00 / 1M input tokens, $15.00 / 1M output tokens
- **GPT-4o-mini**: $0.15 / 1M input tokens, $0.60 / 1M output tokens
- Für Tests reichen $5-10 Guthaben völlig aus

## 🧪 Quick Test:

```python
import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("✅ API Key funktioniert!")
    print(f"Antwort: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Fehler: {e}")
```
