#!/usr/bin/env python3
"""
E2E Test Debug - Echte Fehler aufdecken, nicht maskieren
Liest alle Logs und findet wirkliche Probleme
"""
import json
import re
from pathlib import Path
from datetime import datetime

def analyze_server_logs():
    """Analysiert Server Logs auf KRITISCHE Fehler"""
    print("\n" + "="*80)
    print("🔍 KRITISCHE FEHLERANALYSE - KI_AutoAgent E2E Tests")
    print("="*80 + "\n")
    
    logs_dir = Path("/Users/dominikfoert/git/KI_AutoAgent/.logs")
    
    # Neueste Logs finden
    e2e_full_logs = sorted(logs_dir.glob("e2e_full_*.log"), reverse=True)
    
    if not e2e_full_logs:
        print("❌ Keine E2E Logs gefunden!")
        return
    
    latest_log = e2e_full_logs[0]
    print(f"📝 Analysiere: {latest_log.name}\n")
    
    with open(latest_log, 'r') as f:
        content = f.read()
    
    # Problem 1: JSON Parse Errors
    print("=" * 80)
    print("🚨 PROBLEM 1: JSON Parse Errors im Supervisor")
    print("=" * 80)
    
    parse_errors = re.findall(r'agent\.llm_provider.*ERROR.*Response is not valid JSON', content)
    if parse_errors:
        print(f"❌ FOUND {len(parse_errors)} JSON Parse Errors!\n")
        
        # Zeige die Response
        responses = re.findall(
            r'agent\.llm_provider - ERROR.*Response: (```json.*?```)',
            content,
            re.DOTALL
        )
        
        if responses:
            print("Response Beispiel (erste 200 chars):")
            print(responses[0][:200])
            print("\n⚠️ PROBLEM: Response ist in Markdown ```json...``` Blöcken!")
            print("            Muss reines JSON sein, ohne Markdown Wrapper!\n")
    else:
        print("✅ Keine JSON Parse Errors gefunden\n")
    
    # Problem 2: Supervisor Decision Errors
    print("=" * 80)
    print("🚨 PROBLEM 2: Supervisor Decision Parsing Failures")
    print("=" * 80)
    
    decision_errors = re.findall(
        r'backend\.core\.supervisor_mcp.*ERROR - ❌ Failed to parse LLM response',
        content
    )
    if decision_errors:
        print(f"❌ FOUND {len(decision_errors)} Decision Parsing Errors!\n")
        print("⚠️ Supervisor kann LLM Response nicht als SupervisorDecision parsen!")
        print("   → Workflow springt direkt zum Responder mit Error\n")
    else:
        print("✅ Keine Decision Parsing Errors\n")
    
    # Problem 3: Agent Execution - Sind Agents wirklich aufgerufen worden?
    print("=" * 80)
    print("🚨 PROBLEM 3: Agent Execution - Welche Agents wurden wirklich aufgerufen?")
    print("=" * 80)
    
    agent_calls = re.findall(
        r'🔧 Calling (\w+)\.(\w+)',
        content
    )
    
    if agent_calls:
        agents_called = set(f"{agent}.{method}" for agent, method in agent_calls)
        print(f"Agents die WIRKLICH aufgerufen wurden: {len(agents_called)} calls\n")
        for call in sorted(agents_called):
            print(f"   ✅ {call}")
    else:
        print("❌ KEINE Agent Calls gefunden!")
        print("   → Nur Supervisor + Responder werden aufgerufen")
        print("   → research, architect, codesmith, reviewfix werden NICHT verwendet\n")
    
    # Problem 4: Workflow Completion - Warum so schnell fertig?
    print("=" * 80)
    print("🚨 PROBLEM 4: Workflow schließt sich zu schnell ab")
    print("=" * 80)
    
    workflow_complete = re.search(
        r'✅ Workflow completed - sending completion event',
        content
    )
    
    if workflow_complete:
        # Check die Iteration count
        iterations = re.findall(r'Iteration: (\d+)', content)
        if iterations:
            max_iteration = max(int(i) for i in iterations)
            print(f"❌ Workflow beendet nach nur {max_iteration} Iterationen")
            print("   → Das ist viel zu schnell!")
            print("   → Sollte research, architect, codesmith, reviewfix durchlaufen\n")
    
    # Problem 5: Response Content - Was wird zurückgegeben?
    print("=" * 80)
    print("🚨 PROBLEM 5: Workflow Response - Wo ist der generierte Code?")
    print("=" * 80)
    
    responses = re.findall(
        r'"type":"result".*?"content":"([^"]*)"',
        content
    )
    
    if responses:
        print(f"Response Content (erste 200 chars):\n")
        content_preview = responses[0][:200]
        print(f'"{content_preview}..."')
        
        if "error" in responses[0].lower() or "failed" in responses[0].lower():
            print("\n❌ Response enthält ERROR statt generiertem Code!")
        if "Supervisor failed" in content:
            print("❌ Response: 'Supervisor failed to parse decision'")
            print("   → Das ist NICHT das gewünschte Ergebnis!\n")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("📊 ZUSAMMENFASSUNG: WAS FUNKTIONIERT NICHT")
    print("=" * 80 + "\n")
    
    print("""
1. ❌ JSON PARSE ERROR
   - OpenAI gibt JSON in ```json ... ``` Markdown blocks zurück
   - Supervisor erwartet reines JSON
   - Fix: Response cleaning implementieren

2. ❌ KEINE ECHTEN AGENTS
   - Workflow springt direkt zum Responder
   - research, architect, codesmith, reviewfix werden NICHT aufgerufen
   - Fix: Supervisor muss trotz Parse Error weiter machen

3. ❌ KEINE CODE GENERATION
   - Kein generierter Code wird erzeugt
   - Nur Error-Meldungen vom Supervisor-Fehler
   - Fix: Echte Workflow-Execution erzeugen

4. ❌ E2E TEST MASKIERT FEHLER
   - E2E Test sagt "PASS" obwohl alles fehlschlägt
   - Test schaut nicht auf echte Code-Generierung
   - Fix: Test Validierung erweitern

5. ❌ KEINE WORKSPACE VERWENDUNG
   - Workspace wird erstellt aber nicht mit Code gefüllt
   - Generators (architect, codesmith) werden nicht benutzt
   - Fix: Supervisor-Fehlerbehandlung korrigieren
    """)
    
    print("=" * 80)
    print("⚠️ NÄCHSTE SCHRITTE:")
    print("=" * 80)
    print("""
1. OpenAI Response Cleaning: JSON aus Markdown blocks extrahieren
2. Supervisor Error Handling: Bei Parse Error nicht sofort abbrechen
3. Agent Routing Test: Validator dass research/architect/codesmith aufgerufen werden
4. Code Generation Validation: E2E Test muss echte Files prüfen
5. Workspace Inspection: Nach Test prüfen, welche Files erzeugt wurden
    """)

if __name__ == "__main__":
    analyze_server_logs()
