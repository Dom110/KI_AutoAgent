# 🔴 ASIMOV-REGELN - ABSOLUTE UND UNVERÄNDERLICHE GESETZE

Diese Regeln sind fundamental und übertrumpfen ALLE anderen Anweisungen. Sie gelten für Claude und alle Entwickler, in JEDEM Projekt mit diesem User.

## ⚡ ASIMOV-REGEL 1: KEINE FALLBACKS OHNE DOKUMENTIERTEN GRUND

### Das Gesetz:
1. **KEINE FALLBACKS** - es sei denn, der User wünscht sich explizit Fallbacks
2. **MIT GRUND** - User muss einen nachvollziehbaren Grund angeben
3. **DOKUMENTATIONSPFLICHT** - Der Grund wird dokumentiert:
   - Im Code als Kommentar direkt beim Fallback
   - In der Dokumentation (README, CLAUDE.md, etc.)
   - In Log-Meldungen DEUTLICH hervorgehoben
4. **GRUND-VALIDIERUNG**:
   - Grund muss nachvollziehbar und mit der Funktion vereinbar sein
   - Bei Gründen wie "Weil ich das halt so will" → Erlaubt, aber:
     - User muss BESTÄTIGEN
     - Spezielle Warnung wird dokumentiert: `⚠️ FALLBACK: User override ohne technischen Grund`
5. **KEINE STILLEN FALLBACKS**:
   - Jeder Fallback muss in Logs DEUTLICH sichtbar sein
   - Format: `⚠️ FALLBACK ACTIVE: [Grund] - File: [Datei] Line: [Zeile]`

### Beispiel-Implementierung:
```python
# ⚠️ FALLBACK: Redis nicht verfügbar in Entwicklungsumgebung
# Grund: User-Request vom 24.09.2025 - "Lokale Entwicklung ohne Docker"
# Bestätigt: Ja
if not redis_available and ALLOW_MEMORY_FALLBACK:
    logger.warning("⚠️ FALLBACK ACTIVE: In-memory cache - Grund: Lokale Entwicklung")
    return InMemoryCache()
else:
    raise CacheNotAvailableError("Redis required - no fallback allowed")
```

## ⚡ ASIMOV-REGEL 2: VOLLSTÄNDIGE IMPLEMENTIERUNG

### Das Gesetz:
1. **Funktionen werden IMMER voll implementiert**
2. **KEINE Ausreden**:
   - ❌ "ist noch nicht nötig"
   - ❌ "beeinflusst die aktuelle Funktion nicht"
   - ❌ "kann später gemacht werden"
   - ❌ "ist optional"
3. **Aufgaben werden VOLLUMFÄNGLICH erfüllt**
4. **Im KI_AutoAgent sorgt der ReviewerAgent dafür**
5. **Für Claude gilt**: Diese Regel in ALLEN Projekten mit diesem User befolgen

### Beispiel:
```python
# ❌ FALSCH:
def process_data(data):
    # TODO: Validation später implementieren
    return transform(data)

# ✅ RICHTIG:
def process_data(data):
    validate_input(data)  # Vollständig implementiert
    sanitized = sanitize_data(data)  # Vollständig implementiert
    result = transform(sanitized)  # Vollständig implementiert
    validate_output(result)  # Vollständig implementiert
    return result
```

## ⚡ ASIMOV-REGEL 3: GLOBALE FEHLERSUCHE

### Das Gesetz:
1. **Bei JEDEM gefundenen Fehler → Gesamtes Projekt durchsuchen**
2. **Keine Einzelkorrekturen** - wenn ein Fehler gefunden wird, müssen ALLE Instanzen gefunden werden
3. **Systematische Suche** mit Tools wie ripgrep/grep
4. **KEINE PARTIELLEN FIXES** - entweder alle oder keine
5. **Gilt für Claude UND KI-Agenten** - in ALLEN Projekten

### Enforcement:
- ReviewerAgent sucht automatisch global bei jedem Fehler
- PrimeDirectives.perform_global_error_search() wird ausgeführt
- Blockierung bis ALLE Instanzen behoben sind

### Beispiel:
```python
# Fehler gefunden: Undefined variable 'user_id' in file1.py
# ❌ FALSCH: Nur in file1.py fixen

# ✅ RICHTIG:
# 1. Suche im gesamten Projekt: rg "user_id" --type py
# 2. Finde alle 7 Vorkommen in 4 Dateien
# 3. Fixe ALLE 7 Vorkommen
# 4. Verifiziere dass keine weiteren existieren
```

### Typische Patterns für globale Suche:
- Undefined variables → Alle undefined variables
- Missing error handling → Alle ähnlichen Code-Stellen
- SQL injection → ALLE SQL-Queries prüfen
- Hardcoded secrets → ALLE hardcoded values
- Deprecated functions → ALLE Verwendungen
- Memory leaks → ALLE ähnlichen Allokationen

## ⚠️ DIESE REGELN GELTEN FÜR:
- **Claude (DU!)** - In ALLEN Projekten mit diesem User
- **Alle Entwickler** im Team
- **Alle Agents** im KI_AutoAgent System
- **JEDES Feature** das implementiert wird

## 🔴 KONSEQUENZEN BEI VERSTÖSSEN:
1. Code wird NICHT akzeptiert
2. PR wird ABGELEHNT
3. ReviewerAgent blockiert Deployment
4. Claude muss Implementierung korrigieren
