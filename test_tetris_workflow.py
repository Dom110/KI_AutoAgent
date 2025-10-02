#!/usr/bin/env python3
"""
WebSocket Test Client for Tetris Workflow
Sends request to KI AutoAgent and tracks all agent activations
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

class WorkflowTracker:
    """Track agent activations and workflow metrics"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.agents_activated = []
        self.agent_outputs = {}
        self.quality_scores = []
        self.fixer_iterations = 0
        self.reviewer_iterations = 0
        self.user_interventions = 0
        self.all_messages = []

    def record_agent(self, agent_name: str, timestamp: str = None):
        """Record agent activation"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        self.agents_activated.append({
            "agent": agent_name,
            "timestamp": timestamp
        })
        print(f"  🤖 Agent activated: {agent_name} @ {timestamp}")

    def record_output(self, agent_name: str, output: Any):
        """Record agent output"""
        self.agent_outputs[agent_name] = output

    def record_quality_score(self, score: float, agent: str = "reviewer"):
        """Record quality score from reviewer"""
        self.quality_scores.append({
            "score": score,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        })
        print(f"  ⭐ Quality Score: {score:.2f} (threshold: 0.75)")

    def record_message(self, msg: Dict[str, Any]):
        """Record all messages for analysis"""
        self.all_messages.append(msg)

    def generate_report(self) -> str:
        """Generate detailed test report"""
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0

        report = f"""
{'='*80}
KI AUTOAGENT TETRIS WORKFLOW TEST REPORT
{'='*80}

📊 TEST METRICS
{'='*80}
Total Duration:           {duration:.2f} seconds
Agents Activated:         {len(self.agents_activated)}
User Interventions:       {self.user_interventions}
Fixer Iterations:         {self.fixer_iterations}
Reviewer Iterations:      {self.reviewer_iterations}
Quality Scores:           {len(self.quality_scores)}

🤖 AGENT ACTIVATION SEQUENCE
{'='*80}
"""
        for i, activation in enumerate(self.agents_activated, 1):
            report += f"{i}. {activation['agent']:20s} @ {activation['timestamp']}\n"

        if self.quality_scores:
            report += f"\n⭐ QUALITY SCORES\n{'='*80}\n"
            for i, score_info in enumerate(self.quality_scores, 1):
                report += f"{i}. Score: {score_info['score']:.2f} by {score_info['agent']} @ {score_info['timestamp']}\n"
                if score_info['score'] >= 0.75:
                    report += "   ✅ PASS (>= 0.75)\n"
                else:
                    report += "   ❌ FAIL (< 0.75) → Fixer activated\n"

        report += f"\n📁 AGENT OUTPUTS\n{'='*80}\n"
        for agent, output in self.agent_outputs.items():
            report += f"\n{agent.upper()}:\n"
            if isinstance(output, dict):
                report += json.dumps(output, indent=2)[:500] + "\n"
            else:
                report += str(output)[:500] + "\n"

        # Success criteria
        success = (
            len(self.agents_activated) > 0 and
            self.user_interventions == 0 and
            (not self.quality_scores or self.quality_scores[-1]['score'] >= 0.75)
        )

        report += f"\n🎯 TEST RESULT\n{'='*80}\n"
        if success:
            report += "✅ SUCCESS: Workflow completed without user intervention!\n"
            report += f"   - {len(self.agents_activated)} agents activated\n"
            report += f"   - {self.user_interventions} user interventions (optimal: 0)\n"
            if self.quality_scores:
                report += f"   - Final quality: {self.quality_scores[-1]['score']:.2f}\n"
        else:
            report += "❌ NEEDS IMPROVEMENT: Workflow required user intervention\n"
            report += f"   - {self.user_interventions} user interventions\n"

        report += f"\n{'='*80}\n"
        return report


async def test_tetris_workflow():
    """
    Send Tetris development request to KI AutoAgent
    Track all agent activations and outputs
    """

    tracker = WorkflowTracker()
    tracker.start_time = datetime.now()

    print("\n🚀 STARTING TETRIS WORKFLOW TEST")
    print("="*80)
    print(f"Start Time: {tracker.start_time.isoformat()}")
    print(f"WebSocket:  ws://localhost:8001/ws/chat")
    print("="*80)

    # Test request
    tetris_request = """Entwickle eine einfache Tetris Webaplikation mit HTML, CSS und JavaScript.

Die App soll im Browser laufen und folgende Features haben:
- 10x20 Spielfeld mit Canvas
- 7 Standard Tetrominos (I, O, T, S, Z, J, L) in verschiedenen Farben
- Steuerung: Pfeiltasten (links/rechts/runter) + Leertaste (rotieren)
- Score-Anzeige die sich bei Line Clears erhöht
- Game Over Detection wenn Pieces oben ankommen
- Line Clearing mit Animation
- Gravity: Pieces fallen automatisch nach unten
- Collision Detection: Pieces stoppen bei Kollision

Erstelle 3 Dateien:
1. index.html - Canvas, UI, Controls
2. tetris.js - Game Logic, Pieces, Collision, Rotation
3. styles.css - Responsive Design

Die App muss sofort im Browser lauffähig sein."""

    try:
        print("\n📡 Connecting to WebSocket...")
        async with websockets.connect("ws://localhost:8001/ws/chat") as websocket:
            print("✅ Connected!")

            # Send test request
            message = {
                "type": "chat",
                "content": tetris_request,
                "client_id": "test_client_tetris",
                "timestamp": datetime.now().isoformat()
            }

            print(f"\n📤 Sending request ({len(tetris_request)} chars)...")
            await websocket.send(json.dumps(message))
            print("✅ Request sent, waiting for responses...\n")

            print("📥 AGENT RESPONSES:")
            print("="*80)

            # Receive responses
            response_count = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=300.0)
                    response_count += 1
                    data = json.loads(response)
                    tracker.record_message(data)

                    msg_type = data.get("type", "unknown")

                    # Track different message types
                    if msg_type == "agent_thinking":
                        agent = data.get("agent", "unknown")
                        message_text = data.get("message", "")
                        print(f"  💭 {agent}: {message_text}")
                        tracker.record_agent(agent)

                    elif msg_type == "agent_start":
                        agent = data.get("agent", "unknown")
                        print(f"  ▶️  {agent} started")
                        tracker.record_agent(agent)

                    elif msg_type == "agent_output":
                        agent = data.get("agent", "unknown")
                        output = data.get("content", data.get("output", ""))
                        print(f"  📝 {agent} output: {str(output)[:100]}...")
                        tracker.record_output(agent, output)

                    elif msg_type == "quality_score":
                        score = data.get("score", 0.0)
                        agent = data.get("agent", "reviewer")
                        tracker.record_quality_score(score, agent)

                    elif msg_type == "fixer_iteration":
                        tracker.fixer_iterations += 1
                        print(f"  🔧 Fixer iteration {tracker.fixer_iterations}")

                    elif msg_type == "reviewer_iteration":
                        tracker.reviewer_iterations += 1
                        print(f"  🔍 Reviewer iteration {tracker.reviewer_iterations}")

                    elif msg_type == "workflow_complete":
                        print(f"\n  ✅ Workflow completed!")
                        tracker.end_time = datetime.now()
                        break

                    elif msg_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        print(f"  ❌ Error: {error_msg}")
                        tracker.user_interventions += 1

                    elif msg_type == "response":
                        # Final response
                        content = data.get("content", "")
                        print(f"  📨 Final response ({len(content)} chars)")
                        if len(content) < 500:
                            print(f"     {content}")

                    # Print raw message for debugging
                    if msg_type not in ["agent_thinking", "agent_start", "agent_output"]:
                        print(f"  🔍 Raw: {json.dumps(data, indent=2)[:200]}...")

                except asyncio.TimeoutError:
                    print("\n⏱️  Timeout waiting for response (5 minutes)")
                    tracker.user_interventions += 1
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 Connection closed by server")
                    break

            if tracker.end_time is None:
                tracker.end_time = datetime.now()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        tracker.user_interventions += 1
        if tracker.end_time is None:
            tracker.end_time = datetime.now()

    # Generate and print report
    print("\n" + tracker.generate_report())

    # Save report to file
    report_path = "/Users/dominikfoert/git/KI_AutoAgent/.kiautoagent/tetris_test_report.txt"
    try:
        import os
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(tracker.generate_report())
        print(f"📁 Report saved to: {report_path}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")

    return tracker


if __name__ == "__main__":
    print("🧪 KI AutoAgent Tetris Workflow Test")
    print("Testing multi-agent collaboration and self-correction\n")

    asyncio.run(test_tetris_workflow())
