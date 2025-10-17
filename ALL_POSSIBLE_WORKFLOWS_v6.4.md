# Alle möglichen Workflows in v6.4.0-beta

**Stand:** 2025-10-17
**Version:** v6.4.0-beta mit WorkflowAwareRouter

---

## 🎯 Workflow-Typen (Hauptkategorien)

### 1. CREATE - Neue Anwendung erstellen
### 2. UPDATE - Bestehende Anwendung erweitern
### 3. FIX - Bugs beheben
### 4. EXPLAIN - Code analysieren (OHNE Änderungen)
### 5. ANALYZE - Sicherheit/Qualität prüfen (OHNE Änderungen)
### 6. REFACTOR - Code umstrukturieren
### 7. CUSTOM - Benutzerdefiniert

---

## 📋 Verfügbare Agenten

### Implementierte Agenten (existieren im Graph):
1. **research** - Informationen sammeln, analysieren
   - Modes: `research`, `explain`, `analyze`, `index`
2. **architect** - Architektur planen
   - Modes: `scan`, `design`, `post_build_scan`, `re_scan`
3. **codesmith** - Code generieren/ändern
   - Modes: `default`
4. **reviewfix** - Code prüfen und korrigieren
   - Modes: `default`
5. **explain** - DEPRECATED (use research mode="explain")
   - Modes: `default`
6. **hitl** - Human-in-the-Loop Interaktion
   - Modes: `default`

### NICHT implementierte Agenten (KeyError wenn verwendet):
- ❌ **debugger** - ENTFERNT! Nutze `codesmith` für Bugfixes

---

## 🔄 Workflow-Patterns mit Bedingungen

### 1. CREATE Pattern
**Zweck:** Neue Anwendung von Grund auf erstellen

```
Workflow-Varianten:

1a) Einfache App:
    research (mode="research")
    → architect (mode="design")
    → codesmith
    → reviewfix

1b) Komplexe App mit Iteration:
    research (mode="research")
    → architect (mode="scan")
    → architect (mode="design", if_success)
    → codesmith (if_success)
    → reviewfix (if_success)
    → architect (mode="post_build_scan", if_quality_low)
    → codesmith (if_failure, max_iterations=2)

1c) Mit Human-in-the-Loop:
    research (mode="research")
    → hitl (if_llm_decides: "needs_approval")
    → architect (mode="design", if_success)
    → codesmith (if_success)
    → reviewfix (if_success)
```

**Bedingungen:**
- `if_success`: Nur wenn vorheriger Agent erfolgreich
- `if_quality_low`: Wenn Qualitätsscore < Threshold (0.7)
- `if_llm_decides`: LLM entscheidet zur Laufzeit
- `max_iterations`: Agent kann wiederholt werden

---

### 2. UPDATE Pattern
**Zweck:** Bestehende App um Features erweitern

```
Workflow-Varianten:

2a) Einfaches Update:
    research (mode="research")
    → codesmith
    → reviewfix

2b) Update mit Architektur-Prüfung:
    research (mode="research")
    → architect (mode="scan")
    → codesmith (if_success)
    → reviewfix (if_success)

2c) Parallele Bearbeitung:
    research (mode="research")
    → [codesmith || architect (mode="scan", parallel)]
    → reviewfix (if_success)
```

**Spezielle Bedingungen:**
- `parallel`: Agenten laufen gleichzeitig
- `if_files_exist`: Nur wenn bestimmte Dateien existieren

---

### 3. FIX Pattern
**Zweck:** Bugs identifizieren und beheben

```
Workflow-Varianten:

3a) Standard Bugfix:
    research (mode="analyze")
    → codesmith
    → reviewfix

3b) Mit Validierung:
    research (mode="analyze")
    → codesmith (if_success)
    → reviewfix (if_success)
    → research (mode="analyze", if_failure)

3c) Nur Analyse (kein Fix):
    research (mode="analyze")
    [ENDE - keine weiteren Agenten]
```

**WICHTIG:** `debugger` Agent existiert NICHT mehr! Immer `codesmith` verwenden!

---

### 4. EXPLAIN Pattern
**Zweck:** Code verstehen und dokumentieren (KEINE Änderungen)

```
Workflow-Varianten:

4a) Einfache Erklärung:
    research (mode="explain")
    [ENDE]

4b) Mit Architektur-Scan:
    architect (mode="scan")
    → research (mode="explain", if_success)

4c) DEPRECATED Alternative:
    explain (agent ist deprecated!)
```

**ACHTUNG:** EXPLAIN Workflows dürfen NIEMALS Code generieren!
- ❌ KEIN codesmith
- ❌ KEIN reviewfix mit Änderungen
- ✅ NUR Analyse und Dokumentation

---

### 5. ANALYZE Pattern
**Zweck:** Sicherheit und Qualität prüfen (KEINE Änderungen)

```
Workflow-Varianten:

5a) Security Analyse:
    research (mode="analyze")
    [ENDE]

5b) Vollständige Analyse:
    architect (mode="scan")
    → research (mode="analyze", if_success)

5c) Mit Index-Erstellung:
    research (mode="index")
    → research (mode="analyze", if_success)
```

**ACHTUNG:** ANALYZE Workflows sind READ-ONLY!
- ❌ KEIN codesmith
- ❌ KEINE Dateiänderungen
- ✅ NUR Berichte und Analysen

---

### 6. REFACTOR Pattern
**Zweck:** Code umstrukturieren ohne Funktionsänderung

```
Workflow-Varianten:

6a) Einfaches Refactoring:
    research (mode="research")
    → codesmith
    → reviewfix

6b) Mit Architektur-Redesign:
    research (mode="research")
    → architect (mode="design")
    → codesmith (if_success)
    → reviewfix (if_success)

6c) Iteratives Refactoring:
    research (mode="research")
    → architect (mode="scan")
    → codesmith (if_success, max_iterations=3)
    → reviewfix (if_success)
    → architect (mode="post_build_scan", if_quality_low)
```

---

### 7. CUSTOM Pattern
**Zweck:** Flexible, aufgabenspezifische Workflows

```
Beispiele:

7a) Datenbank-Migration:
    research (mode="analyze")
    → architect (mode="design")
    → hitl (approval required)
    → codesmith (if_success)
    → reviewfix (if_success)

7b) Performance-Optimierung:
    research (mode="analyze")
    → research (mode="research", if_success)
    → codesmith (if_success)
    → reviewfix (if_success)
```

---

## ⚙️ Bedingungs-Typen (ConditionType)

1. **`always`** - Immer ausführen (default)
2. **`if_success`** - Nur wenn vorheriger Agent erfolgreich
3. **`if_failure`** - Nur wenn vorheriger Agent fehlschlägt
4. **`if_quality_low`** - Wenn quality_score < threshold (0.7)
5. **`if_files_exist`** - Wenn bestimmte Dateien existieren
6. **`if_llm_decides`** - LLM entscheidet zur Laufzeit
7. **`parallel`** - Gleichzeitig mit vorherigem Agent

---

## 🚨 Kritische Regeln

### Research Agent Mode-Regeln:
1. **CREATE** → `mode="research"` (Web-Suche)
2. **UPDATE** → `mode="research"` (Web-Suche)
3. **FIX** → `mode="analyze"` (Code-Analyse)
4. **EXPLAIN** → `mode="explain"` (Erklärung)
5. **ANALYZE** → `mode="analyze"` (Sicherheit/Qualität)
6. **REFACTOR** → `mode="research"` (Best Practices)

### Workflow-Terminierung:
- EXPLAIN/ANALYZE enden nach research (kein Code!)
- FIX kann nach codesmith enden (wenn erfolgreich)
- CREATE/UPDATE müssen immer reviewfix durchlaufen

### Fehlerbehandlung:
- Bei `KeyError: 'debugger'` → Workflow planner falsch konfiguriert
- Bei timeout → MCP Claude Server Problem
- Bei "no agents executed" → Workflow planning fehlgeschlagen

---

## 📊 Entscheidungsbaum für Workflow-Auswahl

```
User Request
    ├── Enthält "create", "new", "build"?
    │   → CREATE Workflow
    ├── Enthält "fix", "bug", "debug"?
    │   → FIX Workflow
    ├── Enthält "add", "implement", "extend"?
    │   → UPDATE Workflow
    ├── Enthält "explain", "understand", "document"?
    │   → EXPLAIN Workflow (READ-ONLY!)
    ├── Enthält "analyze", "security", "audit"?
    │   → ANALYZE Workflow (READ-ONLY!)
    ├── Enthält "refactor", "improve", "optimize"?
    │   → REFACTOR Workflow
    └── Sonst
        → CUSTOM Workflow
```

---

## 🔍 Spezielle Szenarien

### Szenario 1: Workflow-Abbruch
```python
if condition == "if_failure" and previous_agent_failed:
    # Workflow stoppt hier
    return END
```

### Szenario 2: Dynamische Umleitung
```python
if quality_score < 0.7:
    # Router leitet um zu architect für re_scan
    next_agent = "architect"
    mode = "re_scan"
```

### Szenario 3: Parallele Ausführung
```python
agents = [
    {"agent": "codesmith", "parallel": False},
    {"agent": "architect", "parallel": True}  # Läuft gleichzeitig
]
```

### Szenario 4: Human-in-the-Loop
```python
if needs_approval:
    # Workflow pausiert für menschliche Eingabe
    next_agent = "hitl"
    # Wartet auf Bestätigung vor Fortsetzung
```

---

## ❌ Häufige Fehler

1. **`debugger` Agent verwenden** → KeyError! Nutze `codesmith`
2. **Falscher research mode** → Workflow läuft falsch
3. **Code in EXPLAIN/ANALYZE** → Verletzt READ-ONLY Regel
4. **Fehlende Bedingungen** → Alle Agenten laufen immer
5. **Timeout zu kurz** → Claude MCP calls brauchen 2-3 Minuten

---

## ✅ Best Practices

1. **Immer research zuerst** (außer bei reinem refactoring)
2. **reviewfix am Ende** für Qualitätssicherung
3. **Bedingungen nutzen** für robuste Workflows
4. **Parallele Agenten** für Performance
5. **HITL für kritische Änderungen**
6. **Mode korrekt setzen** für research agent

---

## 🔧 Debugging-Hilfen

### Workflow funktioniert nicht?
1. Check: Existiert der Agent im Graph?
2. Check: Ist der Mode gültig für diesen Agent?
3. Check: Sind die Bedingungen erfüllt?
4. Check: Timeout ausreichend (180s+)?

### Agent wird übersprungen?
- `if_success` Bedingung aber vorheriger Agent failed
- `if_files_exist` aber Dateien fehlen
- `if_quality_low` aber Score ist gut

### Workflow hängt?
- MCP Server nicht erreichbar
- Claude API timeout
- WebSocket disconnected
- Infinite loop in conditions

---

Diese Dokumentation deckt ALLE möglichen Workflow-Kombinationen in v6.4.0-beta ab!