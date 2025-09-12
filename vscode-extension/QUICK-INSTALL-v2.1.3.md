# KI AutoAgent v2.1.3 - Schnellinstallation

## ✅ Was ist neu in v2.1.3:
- **Command Palette Sichtbarkeit**: Alle KI AutoAgent Commands sind jetzt sichtbar im Command Palette
- **Verbesserte Command-Registrierung**: Kategorisierte Commands für bessere Auffindbarkeit
- **Enhanced Output Channel**: Detaillierte Logging-Informationen bei Extension-Aktivierung

## 🚀 Sofortige Installation:

### Option 1: VSIX Installation
```bash
# Extension direkt installieren
code --install-extension ki-autoagent-vscode-2.1.3.vsix --force
```

### Option 2: Automatisches Install-Script
```bash
# Automated installer ausführen
./install-extension.sh
```

## 🔍 Nach der Installation prüfen:

### 1. Command Palette Test (Ctrl+Shift+P)
Folgende Commands sollten erscheinen:
- ✅ **"KI AutoAgent: Show Chat"**
- ✅ **"KI AutoAgent: Toggle Chat"** 
- ✅ **"KI AutoAgent: Quick Chat"**
- ✅ **"KI AutoAgent: Show Agent Statistics"**
- ✅ **"KI AutoAgent: Show Help"**
- ✅ **"KI AutoAgent: Clear Unread Messages"**

### 2. Output Channel Verification
- **View > Output** > Select **"KI AutoAgent"**
- Erwartete Meldung:
  ```
  🤖 KI AutoAgent Extension Activated
  ======================================
  ⏰ Activation Time: [timestamp]
  📦 Extension Version: 2.1.3
  📋 Commands registered:
    • KI AutoAgent: Show Chat
    • KI AutoAgent: Toggle Chat
    • KI AutoAgent: Quick Chat
    • KI AutoAgent: Clear Unread Messages
  ✅ All components initialized successfully!
  ```

### 3. Chat Agents Test
- **Chat Panel öffnen**: Ctrl+Shift+I oder `KI AutoAgent: Show Chat`
- **Agents testen**:
  - `@ki` - Universal orchestrator
  - `@richter` - Supreme judge (OpusArbitrator)
  - `@architect` - System design expert
  - `@codesmith` - Senior developer
  - etc.

## 🎯 Sofortiger Test:

```
# Im Chat Panel eingeben:
@ki /agents

# Sollte alle Agents anzeigen, einschließlich:
@richter - OpusArbitrator ⚖️ Supreme Quality Judge powered by Claude Opus 4.1
```

## ⚙️ API Keys Configuration:
1. **VS Code Settings** (Ctrl+,)
2. Suche: **"KI AutoAgent"**
3. Konfiguriere:
   - OpenAI API Key (für @architect, @docu, @reviewer)
   - Anthropic API Key (für @richter, @codesmith, @fixer, @tradestrat)
   - Perplexity API Key (für @research)

## 🐛 Troubleshooting:

### Command nicht im Palette sichtbar:
```bash
# 1. Extension neu laden
# Command Palette > "Developer: Reload Window"

# 2. Extension Status prüfen
# Command Palette > "Extensions: Show Installed Extensions"
# Suche nach "KI AutoAgent" - sollte "Enabled" zeigen

# 3. Aktivierung forcieren
# Command Palette > "Developer: Reload Window"
# Dann: "KI AutoAgent: Show Chat"
```

### Output Channel leer:
```bash
# 1. Output Channel manual öffnen
# View > Output > "KI AutoAgent" aus Dropdown wählen

# 2. Extension Status prüfen im Developer Console
# Help > Toggle Developer Tools > Console
# Nach "KI AutoAgent" Logs suchen
```

## 🎉 Erfolgreicher Test:
Wenn Sie **"KI AutoAgent: Show Chat"** im Command Palette sehen und das Output Channel Aktivierungsmeldungen zeigt, ist die Installation erfolgreich!

**Version 2.1.3 behebt alle Command Palette Sichtbarkeitsprobleme! 🚀**