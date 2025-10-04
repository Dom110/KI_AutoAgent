# 🔄 KI AutoAgent Update Guide

Kompletter Guide für Updates von KI AutoAgent mit Fokus auf das neue **Instruction Update System** in v5.8.0.

---

## 📋 Übersicht

KI AutoAgent v5.8.0 führt ein intelligentes Update-System ein, das dir volle Kontrolle über Instruction-Updates gibt:

- **📊 Diff-Anzeige**: Siehe genau was sich ändert
- **🎯 Selective Updates**: Wähle pro Datei: Update, Keep oder Merge
- **💾 Backup System**: Automatische Backups vor Änderungen
- **🔀 Merge Workflows**: Interactive, Overwrite, Preserve oder Backup Mode

---

## 🚀 Quick Update

### Standard Update (empfohlen)

```bash
# 1. Repository aktualisieren
cd /path/to/KI_AutoAgent
git pull

# 2. Update mit interaktivem Instruction-Management
./update.sh --instructions interactive
```

Das Update Script:
1. ✅ Checkt aktuelle Version
2. ✅ Erstellt Backup der Backend-Dateien
3. ✅ Updated Backend Code
4. ✅ Zeigt Instruction-Changes mit Diff
5. ✅ Fragt dich für jede geänderte Datei
6. ✅ Updated Python Dependencies
7. ✅ Aktualisiert version.json

---

## 📝 Instruction Update Modes

### Mode 1: Interactive (Empfohlen)

**Wann verwenden**: Erste Updates, wichtige Changes, wenn du eigene Anpassungen hast

```bash
./update.sh --instructions interactive
```

**Was passiert**:
```
📊 Instructions Update Summary:
════════════════════════════════════════════════════════════

🆕 New files (1):
  + performance-bot-instructions.md

✏️  Changed files (2):
  ~ architect-v2-instructions.md (+15 lines, -3 lines)
  ~ codesmith-v2-instructions.md (+8 lines, -2 lines)

════════════════════════════════════════════════════════════

📝 architect-v2-instructions.md
────────────────────────────────────────────────────────────
[1] Update (overwrite)
[2] Keep current
[3] Save new as .new (manual merge)
[4] Show diff
Your choice: _
```

**Optionen erklärt**:

- **[1] Update**: Überschreibt mit neuer Version (Backup wird erstellt)
- **[2] Keep**: Behält deine Version, ignoriert Update
- **[3] Save as .new**: Speichert neue als `filename.md.new` → du mergst manuell
- **[4] Show diff**: Zeigt vollständigen Diff, dann erneute Auswahl

**Beispiel-Workflow**:
```bash
# Choice [4] → Diff ansehen
────────────────────────────────────────────────────────────
--- current/architect-v2-instructions.md
+++ new/architect-v2-instructions.md
@@ -45,6 +45,18 @@

 ## Architecture Patterns

+### NEW: Microservices Support
+- Design service boundaries
+- Define inter-service communication
+- Handle distributed transactions
+
...
────────────────────────────────────────────────────────────

# Choice [1] → Update akzeptieren
✅ Updated architect-v2-instructions.md
💾 Backup: ~/.ki_autoagent/config/instructions_updates/backups/20251004_103045/
```

### Mode 2: Overwrite (CI/CD)

**Wann verwenden**: Automatisierte Updates, keine eigenen Anpassungen, CI/CD Pipelines

```bash
./update.sh --instructions overwrite --no-prompt
```

**Was passiert**:
- Erstellt Backup aller Instructions
- Überschreibt ALLE Instructions mit neuer Version
- Keine User-Interaktion
- Zeigt Backup-Pfad an

**Output**:
```
💾 Creating backup...
   ✓ Backup created: ~/.ki_autoagent/config/instructions_updates/backups/20251004_103045

📦 Updating backend code...
   ✓ Backend updated

📝 Updating base instructions...
   ✓ All instructions updated (backup: ...)

🐍 Updating Python dependencies...
   ✓ Dependencies updated

✅ Update Complete!
```

### Mode 3: Preserve (Stable Production)

**Wann verwenden**: Production Systems, custom Instructions, nur neue Agents wollen

```bash
./update.sh --instructions preserve
```

**Was passiert**:
- Updated Backend Code
- Updated Dependencies
- Installiert NUR neue Instruction-Dateien
- Überschreibt KEINE existierenden Dateien

**Output**:
```
📝 Updating base instructions...
✅ Installed new file: performance-bot-instructions.md
⏭️  Preserved 9 existing files

✅ Update complete (preserve mode)
```

### Mode 4: Backup/Staging (Manuelle Review)

**Wann verwenden**: Komplexe Updates, mehrere Team-Members, Code-Review Prozess

```bash
./update.sh --instructions backup
```

**Was passiert**:
- Updated Backend Code
- Kopiert NEUE Instructions in Staging Area
- Erstellt CHANGES.md mit allen Änderungen
- Keine Änderungen an live Instructions

**Output**:
```
💾 New instructions saved to: ~/.ki_autoagent/config/instructions_updates/v5.9.0/
📝 Review changes and merge manually

# Staging Area Struktur:
~/.ki_autoagent/config/instructions_updates/v5.9.0/
├── architect-v2-instructions.md          # Neue Version
├── codesmith-v2-instructions.md          # Neue Version
├── performance-bot-instructions.md       # Neue Datei
└── CHANGES.md                            # Changelog
```

**CHANGES.md Beispiel**:
```markdown
# Instructions Changes for v5.9.0

Generated: 2025-10-04 10:30:45

## Summary
- **New**: 1 file(s)
- **Changed**: 2 file(s)
- **Deleted**: 0 file(s)
- **Unchanged**: 7 file(s)

## File Details

### architect-v2-instructions.md
**Status**: changed
**Changes**: +15 lines, -3 lines

### codesmith-v2-instructions.md
**Status**: changed
**Changes**: +8 lines, -2 lines

### performance-bot-instructions.md
**Status**: new
```

**Manuelles Merge**:
```bash
# Review Changes
cat ~/.ki_autoagent/config/instructions_updates/v5.9.0/CHANGES.md

# Compare specific file
diff ~/.ki_autoagent/config/instructions/architect-v2-instructions.md \
     ~/.ki_autoagent/config/instructions_updates/v5.9.0/architect-v2-instructions.md

# Merge manually (z.B. mit VSCode)
code --diff \
  ~/.ki_autoagent/config/instructions/architect-v2-instructions.md \
  ~/.ki_autoagent/config/instructions_updates/v5.9.0/architect-v2-instructions.md

# Wenn fertig: Kopieren
cp ~/.ki_autoagent/config/instructions_updates/v5.9.0/architect-v2-instructions.md \
   ~/.ki_autoagent/config/instructions/
```

---

## 🔍 Update Workflows (Szenarien)

### Szenario 1: Erste Nutzung von v5.8.0+

**Situation**: Du hast v5.7.0 oder älter, erstes Update auf v5.8.0+

```bash
# Update
git pull
./update.sh --instructions interactive

# Erwartung:
# Alle Instruction-Dateien werden als "new" angezeigt
# (Weil sie vorher nicht in config/instructions/ waren)

# Empfehlung:
# Choice [1] für alle → akzeptiere neue Struktur
```

### Szenario 2: Regelmäßiges Update (keine eigenen Änderungen)

**Situation**: Du nutzt Standard-Instructions, willst immer neueste Version

```bash
# Simple Auto-Update
./update.sh --instructions overwrite --no-prompt

# Oder interaktiv mit schneller Auswahl
./update.sh --instructions interactive
# → Choice [1] für alles
```

### Szenario 3: Custom Instructions (eigene Anpassungen)

**Situation**: Du hast Instructions manuell angepasst, willst Updates aber sehen

**Workflow 1 - Selective Merge**:
```bash
./update.sh --instructions interactive

# Für files MIT eigenen Anpassungen:
Your choice: 3  # Save as .new

# Dann manuell mergen:
vimdiff ~/.ki_autoagent/config/instructions/architect-v2-instructions.md \
        ~/.ki_autoagent/config/instructions/architect-v2-instructions.md.new
```

**Workflow 2 - Staging Review**:
```bash
# Staging nutzen
./update.sh --instructions backup

# Review in Ruhe
cd ~/.ki_autoagent/config/instructions_updates/v5.8.0/
cat CHANGES.md

# Selective Copy
cp performance-bot-instructions.md ../../instructions/  # New file: take it
# architect-v2-instructions.md → manual merge later
```

### Szenario 4: Team Environment

**Situation**: Mehrere Entwickler, gemeinsame Instructions, Code-Review

```bash
# Lead Developer:
./update.sh --instructions backup

# Review Changes
cd ~/.ki_autoagent/config/instructions_updates/v5.8.0/
git add .
git commit -m "chore: staged v5.8.0 instruction updates"
git push origin instruction-updates-v5.8.0

# Open PR for Team Review

# Nach Approval:
cp -r ~/.ki_autoagent/config/instructions_updates/v5.8.0/* \
      ~/.ki_autoagent/config/instructions/
```

---

## 🛡️ Backup & Restore

### Automatische Backups

Jedes Update erstellt automatisch Backups:

```bash
~/.ki_autoagent/config/instructions_updates/backups/
├── 20251004_100530/    # Erster Update-Versuch
│   ├── architect-v2-instructions.md
│   └── ...
├── 20251004_103045/    # Zweiter Update (nach Fehler)
│   ├── architect-v2-instructions.md
│   └── ...
└── ...
```

### Manuelles Backup (vor Major Updates)

```bash
# Full Backup
tar -czf ~/ki-autoagent-backup-$(date +%Y%m%d).tar.gz ~/.ki_autoagent/

# Nur Instructions Backup
tar -czf ~/ki-instructions-backup-$(date +%Y%m%d).tar.gz \
  ~/.ki_autoagent/config/instructions/
```

### Restore von Backup

```bash
# Komplettes Restore
tar -xzf ~/ki-autoagent-backup-20251004.tar.gz -C ~/ --overwrite

# Nur Instructions Restore
tar -xzf ~/ki-instructions-backup-20251004.tar.gz -C ~/ --overwrite

# Specific File Restore
cp ~/.ki_autoagent/config/instructions_updates/backups/20251004_103045/architect-v2-instructions.md \
   ~/.ki_autoagent/config/instructions/
```

---

## 🐛 Troubleshooting

### Problem: Update zeigt keine Änderungen

```bash
# Check Version
cat ~/.ki_autoagent/version.json

# Check Remote
cd /path/to/KI_AutoAgent
git fetch
git status

# Force Update Check
./update.sh --instructions interactive
```

### Problem: Instruction Diff ist leer

```bash
# Verify file hash
md5 ~/.ki_autoagent/config/instructions/architect-v2-instructions.md
md5 backend/.ki_autoagent/instructions/architect-v2-instructions.md

# Should be different if update available
# If same: No update needed ✅
```

### Problem: Update schlägt fehl

```bash
# Check Logs
cat ~/.ki_autoagent/logs/update.log

# Rollback
cp -r ~/.ki_autoagent/backups/$(ls -t ~/.ki_autoagent/backups/ | head -1)/backend \
      ~/.ki_autoagent/

# Retry
./update.sh --instructions interactive
```

### Problem: Backend startet nach Update nicht

```bash
# Check Dependencies
~/.ki_autoagent/venv/bin/pip list

# Reinstall Dependencies
source ~/.ki_autoagent/venv/bin/activate
pip install -r ~/.ki_autoagent/backend/requirements.txt --force-reinstall

# Check Python Version
python --version  # Should be 3.8+

# Test Start
cd ~/.ki_autoagent/backend
python api/server_langgraph.py
```

---

## 📊 Version Tracking

### Check Current Version

```bash
# From version.json
cat ~/.ki_autoagent/version.json | jq

# Output:
{
  "installed_version": "5.8.0",
  "installation_date": "2025-10-04T10:00:00",
  "instructions_version": "5.8.0",
  "last_update_check": "2025-10-04T10:30:00",
  "previous_version": "5.7.0",
  "update_date": "2025-10-04T10:30:00"
}
```

### Update History

```bash
# Git History (Instructions)
cd ~/.ki_autoagent/config/instructions_updates/
ls -la backups/  # All backup timestamps

# Git History (Code)
cd /path/to/KI_AutoAgent
git log --oneline | grep "v5\."
```

---

## 🎯 Best Practices

### Vor dem Update

- ✅ Backup erstellen: `tar -czf ~/ki-backup-$(date +%Y%m%d).tar.gz ~/.ki_autoagent/`
- ✅ Backend stoppen: `~/.ki_autoagent/stop.sh`
- ✅ Aktuelle Version notieren: `cat ~/.ki_autoagent/version.json`

### Während dem Update

- ✅ Interactive Mode nutzen für erste Updates
- ✅ Diffs genau lesen (Choice [4])
- ✅ Bei Unsicherheit: Save as .new (Choice [3])
- ✅ Testing: Erst auf Dev, dann auf Prod

### Nach dem Update

- ✅ Status checken: `~/.ki_autoagent/status.sh`
- ✅ Health Check: `curl http://localhost:8001/health`
- ✅ Instructions testen: Check Agent-Verhalten
- ✅ Backup aufbewahren (mindestens 7 Tage)

### Team Updates

- ✅ Nutze Backup Mode für Review
- ✅ PR für Instruction-Changes
- ✅ Dokumentiere Custom Changes
- ✅ Sync `.ki_autoagent_ws/instructions/` (project-specific)

---

## 📚 Weiterführende Dokumentation

- **[INSTALLATION.md](INSTALLATION.md)** - Erste Installation
- **[README.md](../README.md)** - Grundlegende Nutzung
- **[CLAUDE.md](../CLAUDE.md)** - Entwickler-Dokumentation und Architektur

---

**Bereit für dein erstes Update? → [Quick Update](#-quick-update)** 🚀
