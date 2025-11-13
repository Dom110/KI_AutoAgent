# 🔧 Centralized Error Handler - User Guidance System

## Overview

Die neue `error_handler.py` Utility bietet eine **zentrale Fehlerbehandlung**, die bei JEDEM kritischen Fehler folgende Nachricht **genau einmal** anzeigt:

```
================================================================================
                    📞 WELCHE DATEI LESEN?
================================================================================

WENN...                              DANN LESE...
───────────────────────────────────────────────────────────────────────────────
Ich weiß nicht wie ich starte        → START_HERE.md
Ich brauche schnelle Hilfe           → DEUTSCHE_ANLEITUNG.md
Ich will alles verstehen             → START_SERVER_GUIDE.md
Ich brauche technische Details       → COMPLETION_SUMMARY.md
Ich muss berichten                   → EXECUTIVE_SUMMARY_DE.txt
Ich deploye auf Production           → PRODUCTION_STATUS.md
Ich brauche einen Quick Check        → README_LATEST.md
Ich suche eine spezifische Info      → FILES_OVERVIEW.txt (diese!)

================================================================================
```

## Features

### ✅ Features der Error Handler

1. **Einmalige Nachricht** - Wird nur EINMAL pro Session angezeigt (global Flag)
2. **Strukturierte Fehlerbehandlung** - Unterschiedliche Fehlertypen mit spezifischen Formaten
3. **Hilfhafte Kontexte** - Zeigt Error-spezifische Suggestions an
4. **Automatische Integration** - Bereits in allen kritischen Fehlerpunkten eingebaut

## Implementierte Funktionen

### 1. `print_help_message_once()`
Zeigt die Dokumentations-Navigations-Nachricht **genau einmal**.

```python
from backend.utils.error_handler import print_help_message_once

# Diese Funktion zeigt die Nachricht einmal
print_help_message_once()

# Weitere Aufrufe: Werden ignoriert
print_help_message_once()  # Keine Ausgabe!
```

### 2. `handle_critical_error(error_type, error_message, show_help=True)`
Behandelt kritische Fehler mit strukturiertem Format.

```python
from backend.utils.error_handler import handle_critical_error

handle_critical_error(
    error_type="DATABASE_ERROR",
    error_message="Connection to database failed: Connection refused",
    show_help=True  # Zeigt Hilf-Nachricht
)
```

### 3. `handle_startup_error(error_message, suggestions=None)`
Speziell für Startup-Fehler mit Fix-Suggestions.

```python
from backend.utils.error_handler import handle_startup_error

handle_startup_error(
    error_message="Python 3.13.8 oder höher erforderlich",
    suggestions=[
        "Installieren Sie Python 3.13.8 oder höher",
        "Oder verwenden Sie pyenv: pyenv install 3.13.8",
        "Aktivieren Sie dann: pyenv shell 3.13.8"
    ]
)
```

### 4. `handle_api_error(api_name, error_message, status_code=None)`
Für API-Fehler (OpenAI, Anthropic, etc.).

```python
from backend.utils.error_handler import handle_api_error

handle_api_error(
    api_name="OpenAI",
    error_message="Insufficient quota. Your account has $0.00 balance.",
    status_code=429
)
```

### 5. `handle_runtime_error(error_message, context=None)`
Für Runtime-Fehler während der Ausführung.

```python
from backend.utils.error_handler import handle_runtime_error

handle_runtime_error(
    error_message="File not found: /path/to/file",
    context="While reading configuration"
)
```

### 6. `reset_help_message_flag()`
Zurücksetzen des Help-Nachricht Flags (für Tests/Debug).

```python
from backend.utils.error_handler import reset_help_message_flag

# Für nächsten Fehler die Nachricht wieder anzeigen
reset_help_message_flag()
```

## Integrationspunkte

Die error_handler ist bereits integriert in:

### 🟢 start_server.py
- ✅ Venv Check (Zeile ~40)
- ✅ Env File Not Found (Zeile ~105-113)
- ✅ Missing Packages (Zeile ~140-147)
- ✅ Port Cleanup Error (Zeile ~168-175)
- ✅ Startup Sequence Failed (Zeile ~243-246)
- ✅ Server Startup Error (Zeile ~282-285)
- ✅ Fatal Error (Zeile ~297-300)

### 🟢 backend/core/supervisor_mcp.py
- ✅ OpenAI API Errors (Zeile ~349-353)
- ✅ Rate Limit Detection (HTTP 429)
- ✅ Quota Errors (insufficient_quota)

### 🟢 backend/api/server_v7_mcp.py
- ✅ Python Version Error (Zeile ~77-82)
- ✅ Direct Startup Error (Zeile ~117-123)
- ✅ Project Root Error (Zeile ~162-168)

## Fehlerbehandlungs-Flow

```
┌─────────────────────────────────────────┐
│         Fehler tritt auf                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    handle_critical_error() / etc        │
│    oder                                 │
│    print_help_message_once()            │
└─────────────────────────────────────────┘
                    ↓
          ┌─────────────────────┐
          │ Fehler-Box          │
          │ mit Details         │
          └─────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │ Hilf-Nachricht?                   │
    │ (nur wenn Flag=False)             │
    └───────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │ Dokumentations-Navigator          │
    │ (nur EINMAL gezeigt)              │
    └───────────────────────────────────┘
```

## Beispiel: Vollständiger Error Flow

### Szenario: Startup-Fehler

```python
# File: start_server.py
if not env_file.exists():
    handle_startup_error(
        f"Environment file not found at: {env_file}",
        suggestions=[
            f"Create the config directory: mkdir -p {env_file.parent}",
            f"Copy your .env template to: {env_file}",
            f"Add your API keys (OPENAI_API_KEY, etc.) to the .env file",
            "Run: python start_server.py again"
        ]
    )
    return False
```

### Output:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ❌ STARTUP ERROR
╚══════════════════════════════════════════════════════════════════════════════╝

Error:
Environment file not found at: /Users/dominikfoert/.ki_autoagent/config/.env

✅ SUGGESTED FIXES:
   1. Create the config directory: mkdir -p /Users/dominikfoert/.ki_autoagent/config
   2. Copy your .env template to: /Users/dominikfoert/.ki_autoagent/config/.env
   3. Add your API keys (OPENAI_API_KEY, etc.) to the .env file
   4. Run: python start_server.py again

================================================================================
                    📞 WELCHE DATEI LESEN?
================================================================================

WENN...                              DANN LESE...
───────────────────────────────────────────────────────────────────────────────
Ich weiß nicht wie ich starte        → START_HERE.md
[... rest der Navigationshilfe ...]
```

## Best Practices

### 1. Nutze spezifische Fehlertypen
```python
# ❌ Falsch: Generic error
handle_critical_error("ERROR", "Something went wrong")

# ✅ Richtig: Specific error type
handle_api_error("OpenAI", "Rate limit exceeded", status_code=429)
handle_startup_error("Missing dependencies", suggestions=[...])
```

### 2. Biete Suggestions an
```python
# ❌ Falsch: Keine Lösungen
handle_startup_error("Port 8002 is already in use")

# ✅ Richtig: Mit Suggestions
handle_startup_error(
    "Port 8002 is already in use",
    suggestions=[
        "Kill the existing process: kill -9 $(lsof -t -i:8002)",
        "Or use a different port: python start_server.py --port 8003"
    ]
)
```

### 3. Nutze Context bei Runtime-Fehlern
```python
handle_runtime_error(
    "Index out of bounds: index=10, length=5",
    context="While processing agent response"
)
```

## Testing der Error Handler

### Test: Help-Nachricht wird nur einmal angezeigt

```python
from backend.utils.error_handler import (
    print_help_message_once,
    reset_help_message_flag
)

# First call - should show message
print("FIRST CALL:")
print_help_message_once()

print("\nSECOND CALL (should be silent):")
print_help_message_once()

# Reset for demo
reset_help_message_flag()

print("\nAFTER RESET:")
print_help_message_once()
```

### Test: Verschiedene Error Types

```python
from backend.utils.error_handler import (
    handle_critical_error,
    handle_startup_error,
    handle_api_error,
    handle_runtime_error,
    reset_help_message_flag
)

# Test 1: Critical Error
reset_help_message_flag()
handle_critical_error("TEST_ERROR", "This is a test critical error")

# Test 2: Startup Error
reset_help_message_flag()
handle_startup_error("Test startup error", suggestions=["Fix 1", "Fix 2"])

# Test 3: API Error
reset_help_message_flag()
handle_api_error("TestAPI", "API error message", status_code=500)

# Test 4: Runtime Error
reset_help_message_flag()
handle_runtime_error("Test runtime error", context="During execution")
```

## Logging Integration

Alle Error-Handler funktionieren auch mit Python's `logging` Modul:

```python
import logging
from backend.utils.error_handler import handle_api_error

logger = logging.getLogger(__name__)

try:
    result = call_openai_api()
except Exception as e:
    logger.error(f"OpenAI call failed: {e}")
    handle_api_error("OpenAI", str(e), status_code=429)
```

Logs werden geschrieben zu:
- Konsole (stdout/stderr)
- Logger output (wenn logging konfiguriert)

## Zukunftserweiterungen

Mögliche Verbesserungen:

1. **Mehsprachigkeit** - Unterstützung für mehrere Sprachen in Help-Nachricht
2. **Error Tracking** - Logging von Errors zu centralem Service
3. **Dynamic Suggestions** - AI-basierte Suggestions basierend auf Fehlertyp
4. **HTML Output** - Formatierte Error Pages für Web UI
5. **Slack Integration** - Error Notifications zu Slack/Discord

## Datei-Struktur

```
backend/utils/error_handler.py
├── Global Flag: _help_message_shown
├── print_help_message_once()
├── handle_critical_error()
├── handle_startup_error()
├── handle_api_error()
├── handle_runtime_error()
└── reset_help_message_flag()
```

## Support

Wenn Fehler auftreten:

1. **Lies die Error Message** - Sie zeigt das exakte Problem
2. **Folge den Suggestions** - Die fehlerhafte Datei zeigt Lösungsschritte
3. **Konsultiere die Help-Nachricht** - Welche Dokumentation passt zu deinem Fall
4. **Schau in die Logs** - Für detaillierte Fehler-Informationen

---

**Status**: ✅ Production Ready
**Integriert in**: start_server.py, supervisor_mcp.py, server_v7_mcp.py
**Help-Nachricht wird gezeigt bei**: Jedem kritischen Fehler (nur 1x pro Session)