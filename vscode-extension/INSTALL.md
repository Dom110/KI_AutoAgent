# KI AutoAgent VS Code Extension Installation Guide

## 🚀 Quick Installation

### Method 1: Development Installation (Recommended)

1. **Navigate to the extension directory:**
   ```bash
   cd vscode-extension
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Compile the extension:**
   ```bash
   npm run compile
   ```

4. **Install in VS Code:**
   ```bash
   # Option A: Create VSIX package and install
   npx vsce package
   code --install-extension ki-autoagent-vscode-2.1.2.vsix

   # Option B: Launch development VS Code instance
   code --extensionDevelopmentPath=. .
   ```

### Method 2: Direct Development

1. **Open VS Code in extension directory:**
   ```bash
   cd vscode-extension
   code .
   ```

2. **Press F5** to launch Extension Development Host

3. **The extension will be active in the new VS Code window**

## 📋 Verification Steps

After installation, verify the extension is working:

### 1. Check Output Channel
- Open **View > Output**
- Select **"KI AutoAgent"** from dropdown
- You should see:
  ```
  🤖 KI AutoAgent Extension Activated
  ======================================
  ⏰ Activation Time: [timestamp]
  📦 Extension Version: 2.1.2
  ✅ All components initialized successfully!
  ```

### 2. Test Chat Participants
- Open **Chat Panel** (Ctrl+Shift+I or View > Chat)
- Type `@ki` and you should see the orchestrator
- Test other agents: `@richter`, `@architect`, `@codesmith`, etc.

### 3. Verify Agent List
- Type: `@ki /agents`
- Should show all available agents including **@richter (OpusArbitrator)**

## 🔧 Configuration

### API Keys Setup
1. Open **VS Code Settings** (Ctrl+,)
2. Search for **"KI AutoAgent"**
3. Configure your API keys:
   - **OpenAI API Key**: For GPT models (@architect, @docu, @reviewer)
   - **Anthropic API Key**: For Claude models (@richter, @codesmith, @fixer, @tradestrat)
   - **Perplexity API Key**: For research (@research)

### Service Mode
- **API Mode**: Uses your API keys directly
- **Web Mode**: Uses Claude Pro web session (requires proxy server)

## 🐛 Troubleshooting

### Extension Not Appearing
```bash
# 1. Check if extension is loaded
# Open Command Palette (Ctrl+Shift+P)
# Type: "Extensions: Show Installed Extensions"
# Look for "KI AutoAgent"

# 2. Reload VS Code window
# Command Palette > "Developer: Reload Window"

# 3. Check VS Code developer console
# Help > Toggle Developer Tools > Console tab
# Look for KI AutoAgent related logs
```

### Output Channel Not Showing
```bash
# 1. Manual open output channel
# View > Output > Select "KI AutoAgent" from dropdown

# 2. Check extension activation
# Command Palette > "Developer: Show Extension Host Log"

# 3. Restart VS Code completely
```

### Chat Participants Not Working
```bash
# 1. Check VS Code version (minimum 1.90.0 required)
# Help > About

# 2. Reload window
# Command Palette > "Developer: Reload Window"

# 3. Check permissions
# Ensure VS Code has proper file access permissions
```

## 📈 Version Management

### Automatic Version Incrementation
```bash
# Bug fixes and small improvements
npm run version:patch "Description of changes"

# New features and agent updates  
npm run version:minor "Description of changes"

# Breaking changes and major refactoring
npm run version:major "Description of changes"

# Quick build with version bump
npm run build
```

### Manual Version Update
```bash
# Edit package.json version field manually
# Then compile:
npm run compile
```

## 🎯 Usage Examples

Once installed and configured:

```
# Universal orchestrator (auto-routes to best agent)
@ki create a REST API with user authentication

# Supreme judge and conflict resolver
@richter judge which approach is better: microservices vs monolith
@richter resolve disagreement between @architect and @codesmith

# System architecture expert
@architect design a scalable microservices architecture

# Senior developer
@codesmith implement a Python class for user management

# Trading strategy expert  
@tradestrat develop a momentum trading strategy with risk management

# Research expert
@research find the latest Python testing frameworks
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dominikfoert/KI_AutoAgent/issues)
- **Documentation**: Check CLAUDE.md for detailed system information
- **Logs**: Always check the Output Channel for detailed error messages

## 🎉 Success!

If you see the **KI AutoAgent** output channel with activation messages and can interact with agents like `@ki` and `@richter`, the installation was successful!

The **@richter (OpusArbitrator)** agent is now properly visible and available for supreme judgment and conflict resolution using Claude Opus 4.1.