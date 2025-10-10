# MCP (Model Context Protocol) Server Guide

**Date:** 2025-10-10
**Purpose:** Complete guide for MCP server integration with Claude CLI

---

## 🔍 WAS IST MCP?

**MCP = Model Context Protocol**

Ein von Anthropic entwickeltes Standard-Protokoll für:
- ✅ Tool Integration (externe Funktionen verfügbar machen)
- ✅ Data Sources (Zugriff auf Datenbanken, APIs, etc.)
- ✅ Bidirektionale Kommunikation (Claude ↔ External Tools)
- ✅ Standard Protocol (kein vendor lock-in)

**Vergleich:**
- **Ohne MCP:** Jeder Anbieter hat eigenes Tool-Format
- **Mit MCP:** Standard Protocol, wiederverwendbare Tools

---

## 🛠️ WIE FUNKTIONIERT DAS?

### Traditioneller Ansatz (Unser aktueller v6.1):

```python
# backend/tools/perplexity_tool.py
async def perplexity_search(query: str) -> str:
    # Direct API call
    return await perplexity_api.search(query)

# backend/subgraphs/research_subgraph_v6_1.py
from tools.perplexity_tool import perplexity_search

async def research_node(state):
    # Manual tool call
    results = await perplexity_search(state['query'])
    # ...
```

**Problem:**
- ❌ Tool nur in unserem Code nutzbar
- ❌ Nicht wiederverwendbar
- ❌ Jeder muss es neu implementieren
- ❌ Kein Standard

---

### MCP Ansatz (Neu):

**1. MCP Server schreiben:**

```python
# mcp_servers/perplexity_server.py
from mcp import Server, Tool

server = Server("perplexity")

@server.tool(
    name="perplexity_search",
    description="Search the web using Perplexity API",
    parameters={
        "query": {
            "type": "string",
            "description": "Search query",
            "required": True
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results",
            "default": 5
        }
    }
)
async def search(query: str, max_results: int = 5):
    """Execute Perplexity search."""
    # API call
    results = await perplexity_api.search(
        query=query,
        max_results=max_results
    )

    return {
        "success": True,
        "results": results,
        "count": len(results)
    }

if __name__ == "__main__":
    # Start MCP server (stdio mode)
    server.run()
```

**2. MCP Server registrieren:**

```bash
# One-time setup
claude mcp add perplexity python mcp_servers/perplexity_server.py

# Verify
claude mcp list
# Output:
# perplexity (stdio) - Active
#   Command: python mcp_servers/perplexity_server.py
```

**3. Claude nutzt Tool automatisch:**

```bash
# Claude hat jetzt Zugriff auf perplexity_search Tool
claude "Search for latest Python features using perplexity"

# Claude ruft automatisch perplexity_search Tool auf!
# User sieht in der Ausgabe:
# > Using tool: perplexity_search
# > Query: "latest Python features"
# > Results: [...]
```

**Benefits:**
- ✅ Tool ist jetzt STANDARD
- ✅ Jeder Claude CLI user kann es nutzen
- ✅ Wiederverwendbar
- ✅ Kein code ändern nötig
- ✅ Claude entscheidet wann Tool nötig ist

---

## 📋 MCP COMMANDS IN CLAUDE CLI

### Verfügbare Commands:

```bash
# MCP Server hinzufügen
claude mcp add <name> <command> [args...]

# Beispiele:
claude mcp add perplexity python mcp_servers/perplexity_server.py
claude mcp add tree-sitter python mcp_servers/tree_sitter_server.py
claude mcp add memory python mcp_servers/memory_server.py

# MCP Server listen
claude mcp list

# Server Details anzeigen
claude mcp get perplexity

# Server entfernen
claude mcp remove perplexity

# JSON-basierte Konfiguration
claude mcp add-json perplexity '{
  "command": "python",
  "args": ["mcp_servers/perplexity_server.py"],
  "env": {
    "PERPLEXITY_API_KEY": "..."
  }
}'

# Server aus Claude Desktop importieren
claude mcp add-from-claude-desktop

# MCP Server manuell starten (für debugging)
claude mcp serve
```

---

## 🏗️ MCP SERVER ARCHITEKTUR

### Stdio Protocol (Empfohlen):

```
Claude CLI
    ↓
  stdin/stdout
    ↓
MCP Server Process
    ↓
  API Call
    ↓
External Service (Perplexity, etc.)
```

**Ablauf:**
1. Claude CLI startet MCP Server als subprocess
2. Kommunikation über stdin/stdout (JSON-RPC ähnlich)
3. Claude sendet Tool-Request: `{"tool": "perplexity_search", "params": {...}}`
4. MCP Server führt aus, sendet Response: `{"result": {...}}`
5. Claude nutzt Result im Context

**Vorteile:**
- ✅ Einfach zu debuggen
- ✅ Kein Netzwerk nötig
- ✅ Sicher (kein external port)
- ✅ Fast (direct pipe)

---

### SSE Protocol (Alternative):

```
Claude CLI
    ↓
  HTTP/SSE
    ↓
MCP Server (HTTP endpoint)
    ↓
  API Call
    ↓
External Service
```

**Wann verwenden:**
- MCP Server läuft auf anderem Host
- Shared MCP Server für mehrere Clients
- Web-basierte Integration

---

## 🔧 MCP SERVER IMPLEMENTIERUNG

### Minimal Example:

```python
#!/usr/bin/env python3
"""
Minimal MCP Server Example

Run: python minimal_mcp_server.py
Register: claude mcp add hello python minimal_mcp_server.py
Use: claude "Say hello to World"
"""

import sys
import json
import asyncio

# MCP Protocol uses JSON-RPC over stdin/stdout
async def handle_request(request):
    """Handle incoming MCP request."""

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # List available tools
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "say_hello",
                        "description": "Say hello to someone",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name to greet"
                                }
                            },
                            "required": ["name"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "say_hello":
            name = tool_args.get("name", "World")
            result = f"Hello, {name}! 👋"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }

async def main():
    """Main MCP server loop."""

    # Read requests from stdin, write responses to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = await handle_request(request)

            # Write response to stdout
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
```

**Test:**
```bash
# Register
claude mcp add hello python minimal_mcp_server.py

# Test
claude "Say hello to Claude"

# Expected:
# > Using tool: say_hello
# > Arguments: {"name": "Claude"}
# > Result: Hello, Claude! 👋
```

---

## 🚀 KI AUTOAGENT MCP SERVERS

### Server 1: Perplexity Search

```python
# mcp_servers/perplexity_server.py

@server.tool(
    name="perplexity_search",
    description="Search the web using Perplexity API for research and information gathering",
    parameters={
        "query": {
            "type": "string",
            "description": "Search query",
            "required": True
        }
    }
)
async def search(query: str):
    """Execute Perplexity search."""
    # Use existing perplexity_service.py
    from utils.perplexity_service import PerplexityService

    service = PerplexityService()
    result = await service.search(query)

    return {
        "success": True,
        "query": query,
        "content": result.get("content", ""),
        "sources": result.get("sources", [])
    }
```

---

### Server 2: Tree-sitter Validation

```python
# mcp_servers/tree_sitter_server.py

@server.tool(
    name="validate_syntax",
    description="Validate code syntax using Tree-sitter parser",
    parameters={
        "code": {"type": "string", "required": True},
        "language": {"type": "string", "required": True}
    }
)
async def validate(code: str, language: str):
    """Validate code syntax."""
    from tools.tree_sitter_tools import TreeSitterAnalyzer

    analyzer = TreeSitterAnalyzer()
    is_valid = analyzer.validate_syntax(code, language)

    if is_valid:
        return {"valid": True, "message": "Syntax is valid"}
    else:
        errors = analyzer.get_syntax_errors(code, language)
        return {"valid": False, "errors": errors}

@server.tool(
    name="parse_code",
    description="Parse code and return AST",
    parameters={
        "code": {"type": "string", "required": True},
        "language": {"type": "string", "required": True}
    }
)
async def parse(code: str, language: str):
    """Parse code to AST."""
    from tools.tree_sitter_tools import TreeSitterAnalyzer

    analyzer = TreeSitterAnalyzer()
    tree = analyzer.parse(code, language)

    return {
        "success": True,
        "ast": tree.root_node.sexp()  # S-expression representation
    }
```

---

### Server 3: Memory System

```python
# mcp_servers/memory_server.py

@server.tool(
    name="memory_store",
    description="Store information in agent memory",
    parameters={
        "content": {"type": "string", "required": True},
        "metadata": {"type": "object"}
    }
)
async def store(content: str, metadata: dict = None):
    """Store in memory."""
    from memory.memory_system_v6 import MemorySystem

    memory = MemorySystem(workspace_path="/tmp")
    await memory.initialize()

    await memory.store(content=content, metadata=metadata or {})

    return {"success": True, "stored": True}

@server.tool(
    name="memory_search",
    description="Search agent memory",
    parameters={
        "query": {"type": "string", "required": True},
        "k": {"type": "integer", "default": 5}
    }
)
async def search(query: str, k: int = 5):
    """Search memory."""
    from memory.memory_system_v6 import MemorySystem

    memory = MemorySystem(workspace_path="/tmp")
    await memory.initialize()

    results = await memory.search(query=query, k=k)

    return {
        "success": True,
        "results": results,
        "count": len(results)
    }
```

---

### Server 4: Asimov Rules Validator

```python
# mcp_servers/asimov_server.py

@server.tool(
    name="validate_asimov_rules",
    description="Validate code against Asimov safety rules",
    parameters={
        "code": {"type": "string", "required": True},
        "file_path": {"type": "string", "required": True}
    }
)
async def validate(code: str, file_path: str):
    """Validate Asimov rules."""
    from security.asimov_rules import validate_asimov_rules

    result = validate_asimov_rules(
        code=code,
        file_path=file_path,
        strict=False
    )

    return {
        "valid": result["valid"],
        "violations": result["violations"],
        "summary": result["summary"]
    }
```

---

## 📦 INSTALLATION & USAGE

### Setup MCP Servers:

```bash
# 1. Install servers
claude mcp add perplexity python mcp_servers/perplexity_server.py
claude mcp add tree-sitter python mcp_servers/tree_sitter_server.py
claude mcp add memory python mcp_servers/memory_server.py
claude mcp add asimov python mcp_servers/asimov_server.py

# 2. Verify
claude mcp list

# Output:
# perplexity (stdio) - Active
# tree-sitter (stdio) - Active
# memory (stdio) - Active
# asimov (stdio) - Active

# 3. Use directly in Claude CLI
claude "Research Python async patterns using perplexity"
claude "Validate this Python code syntax: print('hello')"
claude "Store this finding in memory: Python 3.13 has async improvements"
```

---

## ✨ VORTEILE FÜR KI AUTOAGENT

### Before MCP (Current v6.1):

```python
# Manual integration
from tools.perplexity_tool import perplexity_search
from tools.tree_sitter_tools import TreeSitterAnalyzer

# In research agent
results = await perplexity_search(query)

# In codesmith agent
analyzer = TreeSitterAnalyzer()
is_valid = analyzer.validate_syntax(code, language)
```

**Probleme:**
- ❌ Tools nur intern nutzbar
- ❌ Jeder Agent muss Tools importieren
- ❌ Keine Wiederverwendung außerhalb unseres Systems
- ❌ Kein Standard

---

### After MCP:

```bash
# Install MCP servers once
claude mcp add ki-autoagent-tools python mcp_servers/all_tools_server.py

# Use everywhere
claude "Research Python features"  # Uses perplexity automatically
claude "Validate this code"        # Uses tree-sitter automatically
claude "Remember this insight"     # Uses memory automatically

# In anderen Projekten auch nutzbar!
cd ~/other-project
claude "Research React patterns"  # Same perplexity tool works!
```

**Vorteile:**
- ✅ Tools sind Standard
- ✅ Einmal schreiben, überall nutzen
- ✅ Claude entscheidet automatisch wann welches Tool nötig
- ✅ Andere Entwickler können unsere Tools nutzen
- ✅ Wir können Tools anderer nutzen

---

## 🎯 ROADMAP: MCP INTEGRATION

### Phase 1: Research & Prototype (1 Woche)
- [ ] MCP Protocol Spezifikation studieren
- [ ] Minimal MCP Server erstellen (hello world)
- [ ] Mit Claude CLI testen
- [ ] Debugging Setup

### Phase 2: Perplexity MCP Server (1 Woche)
- [ ] Perplexity als MCP Server umsetzen
- [ ] Register mit Claude CLI
- [ ] Testen: `claude "Research X using perplexity"`
- [ ] Documentation schreiben

### Phase 3: Tree-sitter MCP Server (1 Woche)
- [ ] Tree-sitter als MCP Server
- [ ] Syntax validation tool
- [ ] AST parsing tool
- [ ] Testen mit verschiedenen Sprachen

### Phase 4: Memory MCP Server (1 Woche)
- [ ] Memory store/search als MCP tools
- [ ] Vector search integration
- [ ] Test mit agent workflows

### Phase 5: Combined Server (1 Woche)
- [ ] Alle Tools in einem Server bündeln
- [ ] `ki-autoagent-mcp` package
- [ ] Installation Guide
- [ ] Publish auf npm/pypi

---

## 🚀 VISION: ZUKUNFT

**Ein-Befehl Installation:**
```bash
npm install -g ki-autoagent-mcp

# Automatisch registriert alle Tools:
# - perplexity_search
# - validate_syntax
# - parse_code
# - memory_store
# - memory_search
# - validate_asimov_rules
```

**Nutzung:**
```bash
# Jeder kann unsere Tools nutzen!
claude "Research AI safety using perplexity"
claude "Validate this React component syntax"
claude "Store this architecture decision"
```

**Marketplace:**
```
npm search mcp
# ki-autoagent-mcp (⭐⭐⭐⭐⭐ 4.9/5)
#   Complete AI agent toolkit with Perplexity, Tree-sitter, Memory
#   1,234 weekly downloads
```

---

## 📖 RESOURCES

**Official:**
- MCP Specification: https://spec.modelcontextprotocol.io/
- Anthropic MCP Docs: https://docs.anthropic.com/mcp
- Example Servers: https://github.com/anthropics/mcp-servers

**Community:**
- MCP Server Registry: https://mcp-registry.anthropic.com
- Best Practices: https://docs.anthropic.com/mcp/best-practices

---

**Next Steps:**
1. Research MCP Specification
2. Create minimal prototype
3. Implement Perplexity MCP Server
4. Test & iterate
