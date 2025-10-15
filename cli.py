#!/usr/bin/env python3
"""
KI AutoAgent CLI - Interactive Command Line Interface
Ermöglicht Tests und Interaktion mit dem Multi-Agent System
"""

import asyncio
import sys
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich import print as rprint

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.master_dispatcher import MasterDispatcher
from agents import AVAILABLE_AGENTS

console = Console()

class KIAutoAgentCLI:
    """
    Command Line Interface for KI AutoAgent System
    """
    
    def __init__(self):
        self.dispatcher = None
        self.history = []
        self.session_start = datetime.now()
        
    async def initialize(self):
        """Initialize the system"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Initialisiere KI AutoAgent System...", total=3)
            
            # Initialize dispatcher
            progress.update(task, description="[cyan]Lade Master Dispatcher...")
            self.dispatcher = MasterDispatcher()
            progress.advance(task)
            
            # Check agents
            progress.update(task, description="[cyan]Überprüfe Agenten...")
            await asyncio.sleep(0.5)  # Simulate loading
            progress.advance(task)
            
            # Load history
            progress.update(task, description="[cyan]Lade Historie...")
            self._load_history()
            progress.advance(task)
        
        # Show welcome message
        self._show_welcome()
    
    def _show_welcome(self):
        """Show welcome message and system info"""
        welcome_text = """
        [bold cyan]KI AutoAgent System v1.0[/bold cyan]
        [dim]Multi-Agent AI Development Platform[/dim]
        
        Verfügbare Agenten:
        • [green]ArchitectGPT[/green] - System Architecture & Design
        • [green]CodeSmithClaude[/green] - Code Implementation
        • [green]DocuBot[/green] - Documentation Generation
        • [green]ReviewerGPT[/green] - Code Review & QA
        • [green]FixerBot[/green] - Bug Fixing & Optimization
        • [green]TradeStrat[/green] - Trading Strategy Development
        • [green]ResearchBot[/green] - Research & Information Gathering
        
        [yellow]Befehle:[/yellow]
        • [cyan]help[/cyan] - Zeige alle Befehle
        • [cyan]task <description>[/cyan] - Stelle eine Aufgabe
        • [cyan]agents[/cyan] - Zeige Agent-Details
        • [cyan]history[/cyan] - Zeige Verlauf
        • [cyan]stats[/cyan] - Zeige Statistiken
        • [cyan]clear[/cyan] - Lösche Bildschirm
        • [cyan]exit[/cyan] - Beende Programm
        """
        
        panel = Panel(welcome_text, title="🤖 Willkommen", border_style="cyan")
        console.print(panel)
    
    async def run(self):
        """Main CLI loop"""
        await self.initialize()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]KI-Agent[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                # Parse command
                command = user_input.split()[0].lower()
                args = user_input[len(command):].strip()
                
                # Handle commands
                if command == "exit" or command == "quit":
                    if Confirm.ask("Wirklich beenden?"):
                        self._save_history()
                        console.print("[yellow]Auf Wiedersehen! 👋[/yellow]")
                        break
                
                elif command == "help":
                    self._show_help()
                
                elif command == "clear":
                    console.clear()
                    self._show_welcome()
                
                elif command == "agents":
                    self._show_agents()
                
                elif command == "history":
                    self._show_history()
                
                elif command == "stats":
                    await self._show_stats()
                
                elif command == "task":
                    if args:
                        await self._process_task(args)
                    else:
                        console.print("[red]Bitte geben Sie eine Aufgabenbeschreibung an.[/red]")
                
                elif command == "test":
                    await self._run_test_scenarios()
                
                else:
                    # Treat entire input as a task
                    await self._process_task(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Verwende 'exit' zum Beenden.[/yellow]")
            except Exception as e:
                console.print(f"[red]Fehler: {str(e)}[/red]")
    
    async def _process_task(self, task_description: str, project_type: Optional[str] = None, project_name: Optional[str] = None):
        """Process a task through the system"""
        console.print(f"\n[cyan]📋 Aufgabe:[/cyan] {task_description}")
        
        if project_type:
            console.print(f"[cyan]🎯 Projekt Typ:[/cyan] {project_type}")
        if project_name:
            console.print(f"[cyan]📁 Projekt Name:[/cyan] {project_name}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Process through dispatcher
            task_id = progress.add_task("[yellow]Verarbeite Anfrage...", total=None)
            
            try:
                # Prepare context
                context = {}
                if project_name:
                    context['project_name'] = project_name
                
                result = await self.dispatcher.process_request(
                    task_description, 
                    context=context, 
                    project_type=project_type
                )
                progress.stop()
                
                # Show results
                self._display_results(result)
                
                # Add to history
                self.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "task": task_description,
                    "project_type": project_type,
                    "project_name": project_name,
                    "result": result
                })
                
            except Exception as e:
                progress.stop()
                console.print(f"[red]❌ Fehler bei der Verarbeitung: {str(e)}[/red]")
    
    def _display_results(self, result: Dict[str, Any]):
        """Display task results in a formatted way"""
        # Status
        status = result.get("status", "unknown")
        status_color = "green" if status == "success" else "yellow" if status == "partial_success" else "red"
        console.print(f"\n[{status_color}]Status: {status}[/{status_color}]")
        
        # Intent
        if result.get("intent"):
            intent = result["intent"]
            console.print(f"\n[cyan]Erkannter Intent:[/cyan] {intent.get('type', 'unknown')}")
            console.print(f"[cyan]Confidence:[/cyan] {intent.get('confidence', 0):.2%}")
        
        # Workflow summary
        if result.get("workflow_summary"):
            summary = result["workflow_summary"]
            console.print(f"\n[cyan]Workflow:[/cyan]")
            console.print(f"  • Schritte gesamt: {summary.get('total_steps', 0)}")
            console.print(f"  • Schritte abgeschlossen: {summary.get('completed_steps', 0)}")
            console.print(f"  • Ausführungszeit: {summary.get('execution_time', 0):.2f}s")
        
        # Project information
        if result.get("project_info"):
            project_info = result["project_info"]
            console.print(f"\n[cyan]Projekt Kontext:[/cyan]")
            console.print(f"  • Typ: {project_info.get('project_type', 'unknown')}")
            console.print(f"  • Name: {project_info.get('project_name', 'Unknown')}")
            console.print(f"  • Domäne: {project_info.get('domain', 'Unknown')}")
            
            quality_gates = project_info.get('quality_gates_applied', [])
            if quality_gates:
                console.print(f"  • Quality Gates: {', '.join(quality_gates)}")
        
        # Final output
        if result.get("final_output"):
            console.print("\n[green]📤 Ausgabe:[/green]")
            output = result["final_output"]
            
            # Check if it's code
            if "```" in output:
                # Extract code blocks
                import re
                code_blocks = re.findall(r'```(\w+)?\n(.*?)```', output, re.DOTALL)
                for lang, code in code_blocks:
                    lang = lang or "python"
                    syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                    console.print(syntax)
            else:
                # Regular text output
                panel = Panel(output[:1000] + "..." if len(output) > 1000 else output,
                            title="Output", border_style="green")
                console.print(panel)
        
        # Errors
        if result.get("errors"):
            console.print("\n[red]⚠️ Fehler:[/red]")
            for error in result["errors"]:
                console.print(f"  • {error}")
    
    def _show_help(self):
        """Show help information"""
        help_table = Table(title="Verfügbare Befehle", show_header=True, header_style="bold cyan")
        help_table.add_column("Befehl", style="cyan", width=20)
        help_table.add_column("Beschreibung", style="white")
        help_table.add_column("Beispiel", style="dim")
        
        help_table.add_row("task <text>", "Stelle eine Aufgabe an das System", "task Erstelle einen Trading Bot")
        help_table.add_row("agents", "Zeige Details aller Agenten", "agents")
        help_table.add_row("history", "Zeige Aufgabenverlauf", "history")
        help_table.add_row("stats", "Zeige System-Statistiken", "stats")
        help_table.add_row("test", "Führe Test-Szenarien aus", "test")
        help_table.add_row("clear", "Lösche Bildschirm", "clear")
        help_table.add_row("help", "Zeige diese Hilfe", "help")
        help_table.add_row("exit", "Beende das Programm", "exit")
        
        console.print(help_table)
    
    def _show_agents(self):
        """Show detailed agent information"""
        agents_table = Table(title="🤖 Agent Details", show_header=True, header_style="bold cyan")
        agents_table.add_column("Agent", style="green", width=20)
        agents_table.add_column("Rolle", style="yellow")
        agents_table.add_column("Model", style="cyan")
        agents_table.add_column("Fähigkeiten", style="white")
        
        # Mock agent details (would be loaded from actual agents)
        agent_details = [
            ("ArchitectGPT", "System Architect", "GPT-4o", "Design, Architecture, Planning"),
            ("CodeSmithClaude", "Python Developer", "Claude 3.5 Sonnet", "Implementation, Testing, Optimization"),
            ("DocuBot", "Documentation", "GPT-4o", "Docs, README, API Reference"),
            ("ReviewerGPT", "Code Reviewer", "GPT-4o-mini", "QA, Security, Performance"),
            ("FixerBot", "Bug Fixer", "Claude 3.5 Sonnet", "Debugging, Patching, Refactoring"),
            ("TradeStrat", "Trading Expert", "Claude 3.5 Sonnet", "Strategies, Backtesting, Risk"),
            ("ResearchBot", "Researcher", "Perplexity Pro", "Web Research, Documentation, Analysis")
        ]
        
        for name, role, model, skills in agent_details:
            agents_table.add_row(name, role, model, skills)
        
        console.print(agents_table)
    
    def _show_history(self):
        """Show task history"""
        if not self.history:
            console.print("[yellow]Noch keine Aufgaben verarbeitet.[/yellow]")
            return
        
        history_table = Table(title="📜 Aufgabenverlauf", show_header=True, header_style="bold cyan")
        history_table.add_column("#", style="dim", width=5)
        history_table.add_column("Zeit", style="cyan", width=20)
        history_table.add_column("Aufgabe", style="white", width=40)
        history_table.add_column("Status", style="green")
        
        for i, entry in enumerate(self.history[-10:], 1):  # Show last 10
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            task = entry["task"][:40] + "..." if len(entry["task"]) > 40 else entry["task"]
            status = entry["result"].get("status", "unknown")
            
            status_icon = "✅" if status == "success" else "⚠️" if status == "partial_success" else "❌"
            history_table.add_row(str(i), timestamp, task, f"{status_icon} {status}")
        
        console.print(history_table)
    
    async def _show_stats(self):
        """Show system statistics"""
        # Get stats from dispatcher
        agent_stats = await self.dispatcher.get_agent_stats()
        
        # Session stats
        session_duration = datetime.now() - self.session_start
        tasks_processed = len(self.history)
        success_rate = sum(1 for h in self.history if h["result"].get("status") == "success") / max(tasks_processed, 1)
        
        stats_panel = f"""
        [cyan]Session Statistiken:[/cyan]
        • Laufzeit: {str(session_duration).split('.')[0]}
        • Aufgaben verarbeitet: {tasks_processed}
        • Erfolgsrate: {success_rate:.1%}
        
        [cyan]Agent Performance:[/cyan]
        """
        
        if agent_stats:
            for agent, stats in agent_stats.items():
                stats_panel += f"\n• {agent}: {stats.get('total_executions', 0)} Ausführungen, {stats.get('success_rate', 0):.1%} Erfolg"
        else:
            stats_panel += "\nNoch keine Agent-Statistiken verfügbar."
        
        panel = Panel(stats_panel, title="📊 System Statistiken", border_style="cyan")
        console.print(panel)
    
    async def _run_test_scenarios(self):
        """Run predefined test scenarios"""
        test_scenarios = [
            "Erstelle eine REST API mit FastAPI für ein Todo-System",
            "Debug diesen Code: def add(a, b): return a - b",
            "Erkläre mir den Unterschied zwischen async und sync in Python",
            "Entwickle eine Momentum Trading Strategie",
            "Dokumentiere diese Klasse: class Calculator: def add(self, a, b): return a + b"
        ]
        
        console.print("\n[cyan]🧪 Führe Test-Szenarien aus...[/cyan]\n")
        
        for i, scenario in enumerate(test_scenarios, 1):
            console.print(f"[yellow]Test {i}/{len(test_scenarios)}:[/yellow] {scenario}")
            
            # Process scenario
            try:
                result = await self.dispatcher.process_request(scenario)
                status = result.get("status", "unknown")
                status_icon = "✅" if status == "success" else "⚠️" if status == "partial_success" else "❌"
                console.print(f"  {status_icon} Status: {status}\n")
            except Exception as e:
                console.print(f"  ❌ Fehler: {str(e)}\n")
        
        console.print("[green]✅ Test-Szenarien abgeschlossen![/green]")
    
    def _load_history(self):
        """Load history from file"""
        history_file = "ki_agent_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, OSError, PermissionError) as e:
                logger.debug(f"Could not load history file: {e}")
                self.history = []
    
    def _save_history(self):
        """Save history to file"""
        history_file = "ki_agent_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)  # Keep last 100 entries
        except (OSError, PermissionError) as e:
            logger.debug(f"Could not save history file: {e}")
            pass

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KI AutoAgent CLI")
    parser.add_argument("--task", "-t", help="Direkte Aufgabe ausführen")
    parser.add_argument("--test", action="store_true", help="Test-Modus ausführen")
    args = parser.parse_args()
    
    cli = KIAutoAgentCLI()
    
    if args.task:
        # Direct task execution
        async def run_task():
            await cli.initialize()
            await cli._process_task(args.task)
        asyncio.run(run_task())
    elif args.test:
        # Test mode
        async def run_tests():
            await cli.initialize()
            await cli._run_test_scenarios()
        asyncio.run(run_tests())
    else:
        # Interactive mode
        asyncio.run(cli.run())

if __name__ == "__main__":
    main()