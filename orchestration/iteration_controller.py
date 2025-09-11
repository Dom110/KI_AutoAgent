"""
Iteration Control System
Manages iteration limits and user decisions for iterative agent workflows
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class IterationReason:
    """Record of why an iteration was needed"""
    iteration_number: int
    reason: str
    agent: str
    quality_score: float
    critical_issues: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class IterationSummary:
    """Summary of iteration history and analysis"""
    total_iterations: int
    reasons: List[IterationReason]
    common_issues: List[str]
    problematic_areas: List[str]
    agent_performance: Dict[str, Dict]
    time_spent: float
    recommendation: str

class IterationController:
    """
    Controls iteration limits and manages user decisions
    """
    
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.iteration_reasons: List[IterationReason] = []
        self.start_time = datetime.now()
        
    def record_iteration(self, reason: str, agent: str, quality_score: float, critical_issues: List[str]):
        """Record why an iteration was needed"""
        iteration_reason = IterationReason(
            iteration_number=len(self.iteration_reasons) + 1,
            reason=reason,
            agent=agent,
            quality_score=quality_score,
            critical_issues=critical_issues
        )
        self.iteration_reasons.append(iteration_reason)
    
    async def check_iteration_limit(self, current_iteration: int, quality_result: Dict) -> Dict:
        """
        Check if iteration limit reached and prepare user decision
        """
        if current_iteration >= self.max_iterations:
            summary = self._generate_iteration_summary()
            
            return {
                "limit_reached": True,
                "require_user_decision": True,
                "iteration_summary": summary,
                "quality_status": quality_result,
                "user_options": self._generate_user_options(summary),
                "recommendation": self._get_primary_recommendation(summary)
            }
        
        # Check if we should continue iterating based on quality
        should_continue = quality_result.get("requires_iteration", False)
        
        if should_continue:
            # Record this iteration reason
            self.record_iteration(
                reason=quality_result.get("summary", "Quality issues detected"),
                agent=quality_result.get("last_agent", "unknown"),
                quality_score=quality_result.get("score", 0.0),
                critical_issues=quality_result.get("critical_failures", [])
            )
        
        return {
            "limit_reached": False,
            "continue_iteration": should_continue,
            "current_iteration": current_iteration,
            "remaining_iterations": self.max_iterations - current_iteration
        }
    
    def _generate_iteration_summary(self) -> IterationSummary:
        """Generate comprehensive iteration analysis"""
        if not self.iteration_reasons:
            return IterationSummary(
                total_iterations=0,
                reasons=[],
                common_issues=[],
                problematic_areas=[],
                agent_performance={},
                time_spent=0.0,
                recommendation="No iterations performed"
            )
        
        # Analyze common issues
        all_issues = []
        for reason in self.iteration_reasons:
            all_issues.extend(reason.critical_issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze agent performance
        agent_performance = {}
        for reason in self.iteration_reasons:
            agent = reason.agent
            if agent not in agent_performance:
                agent_performance[agent] = {
                    "iterations_caused": 0,
                    "avg_quality_score": 0.0,
                    "issues": []
                }
            
            agent_performance[agent]["iterations_caused"] += 1
            agent_performance[agent]["avg_quality_score"] += reason.quality_score
            agent_performance[agent]["issues"].extend(reason.critical_issues)
        
        # Calculate averages
        for agent, stats in agent_performance.items():
            stats["avg_quality_score"] /= stats["iterations_caused"]
            stats["issues"] = list(set(stats["issues"]))  # Remove duplicates
        
        # Identify problematic areas
        problematic_areas = self._identify_problem_areas()
        
        # Calculate time spent
        time_spent = (datetime.now() - self.start_time).total_seconds()
        
        # Generate recommendation
        recommendation = self._generate_recommendation(common_issues, agent_performance)
        
        return IterationSummary(
            total_iterations=len(self.iteration_reasons),
            reasons=self.iteration_reasons,
            common_issues=[issue for issue, count in common_issues],
            problematic_areas=problematic_areas,
            agent_performance=agent_performance,
            time_spent=time_spent,
            recommendation=recommendation
        )
    
    def _identify_problem_areas(self) -> List[str]:
        """Identify recurring problem areas"""
        problem_patterns = {
            "RON Strategy Implementation": ["ron_strategy", "vwap", "fibonacci", "ema9", "crv"],
            "Engine Parity": ["engine_parity", "future_leak", "iterative_processing", "backtest"],
            "Financial Calculations": ["decimal_precision", "pnl_calculation", "crv_calculation"],
            "Risk Management": ["position_validation", "stop_loss", "exposure_limits"],
            "Code Quality": ["function_size", "type_annotations", "documentation"],
            "Error Handling": ["exception_handling", "fallback_policy", "graceful_degradation"],
            "Trading Compliance": ["market_hours", "audit_trail", "live_data_policy"]
        }
        
        problematic_areas = []
        all_issues_text = " ".join([reason.reason for reason in self.iteration_reasons])
        all_critical_issues = []
        for reason in self.iteration_reasons:
            all_critical_issues.extend(reason.critical_issues)
        
        combined_text = (all_issues_text + " " + " ".join(all_critical_issues)).lower()
        
        for area, keywords in problem_patterns.items():
            keyword_matches = sum(1 for keyword in keywords if keyword in combined_text)
            if keyword_matches >= 2:  # At least 2 keywords match
                problematic_areas.append(area)
        
        return problematic_areas
    
    def _generate_recommendation(self, common_issues: List, agent_performance: Dict) -> str:
        """Generate primary recommendation based on analysis"""
        if not self.iteration_reasons:
            return "No specific recommendation available"
        
        # Analyze patterns
        total_iterations = len(self.iteration_reasons)
        avg_quality_score = sum(r.quality_score for r in self.iteration_reasons) / total_iterations
        
        if total_iterations >= 8 and avg_quality_score < 0.4:
            return "Fundamental design issues detected. Consider starting over with simplified requirements."
        
        if total_iterations >= 6 and len(common_issues) <= 2:
            return "Progress is being made but slowly. Consider continuing with focused improvements."
        
        if len(common_issues) >= 3 and any(count >= 5 for _, count in common_issues[:3]):
            return "Recurring issues suggest knowledge gaps. Consider human expert consultation."
        
        # Check agent performance
        problematic_agents = [
            agent for agent, stats in agent_performance.items() 
            if stats["iterations_caused"] >= 4 and stats["avg_quality_score"] < 0.5
        ]
        
        if len(problematic_agents) >= 2:
            return "Multiple agents struggling. Consider breaking down requirements into smaller tasks."
        
        return "Continue with current approach but focus on most frequent issues."
    
    def _generate_user_options(self, summary: IterationSummary) -> List[Dict]:
        """Generate user decision options based on analysis"""
        base_options = [
            {
                "option": "continue_5_more",
                "title": "Continue for 5 more iterations",
                "description": "Extend the iteration limit by 5 to allow more refinement",
                "risk": "May indicate fundamental design issues if pattern continues",
                "recommended": summary.recommendation.startswith("Progress is being made")
            },
            {
                "option": "continue_3_more",
                "title": "Continue for 3 more iterations", 
                "description": "Short extension to address most critical issues",
                "risk": "Limited time to resolve complex problems",
                "recommended": len(summary.common_issues) <= 2
            },
            {
                "option": "accept_current",
                "title": "Accept current implementation",
                "description": "Use the code in its current state with known issues",
                "risk": "May have quality, security, or functionality issues",
                "recommended": False
            },
            {
                "option": "restart_simplified",
                "title": "Restart with simplified requirements",
                "description": "Start over with reduced scope and simpler requirements",
                "risk": "Additional development time and effort required",
                "recommended": summary.total_iterations >= 8 or len(summary.problematic_areas) >= 4
            },
            {
                "option": "break_into_subtasks",
                "title": "Break into smaller subtasks",
                "description": "Split the current task into smaller, manageable pieces",
                "risk": "May require more coordination between subtasks",
                "recommended": len(summary.problematic_areas) >= 3
            },
            {
                "option": "human_review",
                "title": "Request human expert review",
                "description": "Get human expert input on the implementation approach",
                "risk": "Delays implementation but may provide crucial insights",
                "recommended": summary.recommendation.startswith("Recurring issues")
            }
        ]
        
        # Sort by recommendation
        return sorted(base_options, key=lambda x: x["recommended"], reverse=True)
    
    def _get_primary_recommendation(self, summary: IterationSummary) -> str:
        """Get the primary recommendation for the user"""
        options = self._generate_user_options(summary)
        recommended_option = next((opt for opt in options if opt["recommended"]), options[0])
        
        return f"Recommended: {recommended_option['title']} - {recommended_option['description']}"

class UserInteractionHandler:
    """
    Handles user interactions when iteration limits are reached
    """
    
    def __init__(self):
        self.interaction_history = []
    
    async def prompt_user_decision(self, iteration_info: Dict, cli_interface=None) -> str:
        """
        Present iteration analysis and get user decision
        """
        summary = iteration_info["iteration_summary"]
        
        # Display comprehensive analysis
        self._display_iteration_analysis(summary, cli_interface)
        
        # Present options
        options = iteration_info["user_options"]
        choice = await self._get_user_choice(options, cli_interface)
        
        # Record interaction
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "choice": choice,
            "options_presented": len(options)
        })
        
        return choice
    
    def _display_iteration_analysis(self, summary: IterationSummary, cli_interface=None):
        """Display detailed analysis of iteration history"""
        
        analysis_text = f"""
🔄 **ITERATION LIMIT REACHED - ANALYSIS REQUIRED**

**Summary:**
- Total Iterations: {summary.total_iterations}
- Time Spent: {summary.time_spent:.1f} seconds
- Most Recent Quality Score: {summary.reasons[-1].quality_score:.1%} (if available)

**🚨 Most Common Issues:**
{self._format_common_issues(summary.common_issues)}

**📊 Agent Performance Analysis:**
{self._format_agent_performance(summary.agent_performance)}

**🎯 Problematic Areas Identified:**
{self._format_problematic_areas(summary.problematic_areas)}

**📈 Iteration Timeline:**
{self._format_iteration_timeline(summary.reasons)}

**🤖 AI Recommendation:**
{summary.recommendation}

---
"""
        
        if cli_interface:
            cli_interface.display_panel(analysis_text, title="🚨 Iteration Analysis")
        else:
            print(analysis_text)
    
    def _format_common_issues(self, common_issues: List[str]) -> str:
        """Format common issues for display"""
        if not common_issues:
            return "- No specific recurring issues identified"
        
        formatted = []
        for i, issue in enumerate(common_issues[:5], 1):
            formatted.append(f"{i}. {issue}")
        
        return "\n".join(formatted)
    
    def _format_agent_performance(self, agent_performance: Dict) -> str:
        """Format agent performance data"""
        if not agent_performance:
            return "- No agent performance data available"
        
        formatted = []
        for agent, stats in agent_performance.items():
            avg_score = stats["avg_quality_score"]
            iterations = stats["iterations_caused"]
            
            status = "🟢" if avg_score >= 0.7 else "🟡" if avg_score >= 0.4 else "🔴"
            
            formatted.append(
                f"{status} **{agent}**: {iterations} iterations, "
                f"Avg Quality: {avg_score:.1%}"
            )
        
        return "\n".join(formatted)
    
    def _format_problematic_areas(self, problematic_areas: List[str]) -> str:
        """Format problematic areas"""
        if not problematic_areas:
            return "- No specific problematic areas identified"
        
        return "\n".join([f"⚠️ {area}" for area in problematic_areas])
    
    def _format_iteration_timeline(self, reasons: List[IterationReason]) -> str:
        """Format iteration timeline"""
        if not reasons:
            return "- No iteration history available"
        
        formatted = []
        for reason in reasons[-5:]:  # Show last 5 iterations
            timestamp = reason.timestamp.split("T")[1][:8]  # Extract time
            quality_indicator = "🟢" if reason.quality_score >= 0.7 else "🟡" if reason.quality_score >= 0.4 else "🔴"
            
            formatted.append(
                f"{quality_indicator} Iteration {reason.iteration_number} ({timestamp}): "
                f"{reason.reason[:60]}{'...' if len(reason.reason) > 60 else ''}"
            )
        
        if len(reasons) > 5:
            formatted.insert(0, f"... (showing last 5 of {len(reasons)} iterations)")
        
        return "\n".join(formatted)
    
    async def _get_user_choice(self, options: List[Dict], cli_interface=None) -> str:
        """Get user choice from available options"""
        
        choice_text = "\n**Available Options:**\n\n"
        
        for i, option in enumerate(options, 1):
            recommended_text = " ⭐ **RECOMMENDED**" if option["recommended"] else ""
            choice_text += f"**{i}. {option['title']}**{recommended_text}\n"
            choice_text += f"   {option['description']}\n"
            choice_text += f"   Risk: {option['risk']}\n\n"
        
        choice_text += "Please enter your choice (1-{0}): ".format(len(options))
        
        if cli_interface:
            cli_interface.display_text(choice_text)
            choice_num = await cli_interface.get_user_input("Enter choice number: ")
        else:
            print(choice_text)
            choice_num = input("Enter choice number: ")
        
        try:
            choice_index = int(choice_num) - 1
            if 0 <= choice_index < len(options):
                return options[choice_index]["option"]
            else:
                print("Invalid choice, defaulting to first option")
                return options[0]["option"]
        except ValueError:
            print("Invalid input, defaulting to first option")
            return options[0]["option"]

class IterationDecisionExecutor:
    """
    Executes user decisions about iteration continuation
    """
    
    def __init__(self):
        self.decision_history = []
    
    async def execute_decision(self, decision: str, workflow_context: Dict) -> Dict:
        """
        Execute the user's decision about iteration continuation
        """
        execution_result = {
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "original_context": workflow_context
        }
        
        if decision == "continue_5_more":
            execution_result.update(await self._extend_iterations(5, workflow_context))
        
        elif decision == "continue_3_more":
            execution_result.update(await self._extend_iterations(3, workflow_context))
        
        elif decision == "accept_current":
            execution_result.update(await self._accept_current_state(workflow_context))
        
        elif decision == "restart_simplified":
            execution_result.update(await self._restart_simplified(workflow_context))
        
        elif decision == "break_into_subtasks":
            execution_result.update(await self._break_into_subtasks(workflow_context))
        
        elif decision == "human_review":
            execution_result.update(await self._request_human_review(workflow_context))
        
        else:
            execution_result.update({
                "action": "error",
                "message": f"Unknown decision: {decision}",
                "fallback": "accept_current"
            })
        
        # Record decision
        self.decision_history.append(execution_result)
        
        return execution_result
    
    async def _extend_iterations(self, additional_iterations: int, context: Dict) -> Dict:
        """Extend iteration limit"""
        return {
            "action": "extend_iterations",
            "additional_iterations": additional_iterations,
            "new_max_iterations": context.get("max_iterations", 10) + additional_iterations,
            "continue_workflow": True,
            "message": f"Iteration limit extended by {additional_iterations}"
        }
    
    async def _accept_current_state(self, context: Dict) -> Dict:
        """Accept current implementation state"""
        return {
            "action": "accept_current", 
            "continue_workflow": False,
            "finalize": True,
            "message": "Accepting current implementation with known issues",
            "warnings": ["Implementation may have unresolved quality issues"]
        }
    
    async def _restart_simplified(self, context: Dict) -> Dict:
        """Restart with simplified requirements"""
        return {
            "action": "restart_simplified",
            "continue_workflow": False,
            "restart": True,
            "message": "Restarting with simplified requirements",
            "simplification_suggestions": [
                "Reduce feature scope",
                "Focus on core functionality only",
                "Implement basic version first",
                "Add complexity incrementally"
            ]
        }
    
    async def _break_into_subtasks(self, context: Dict) -> Dict:
        """Break current task into smaller subtasks"""
        return {
            "action": "break_into_subtasks",
            "continue_workflow": False,
            "create_subtasks": True,
            "message": "Breaking task into smaller, manageable subtasks",
            "subtask_strategy": "Sequential implementation of smaller components"
        }
    
    async def _request_human_review(self, context: Dict) -> Dict:
        """Request human expert review"""
        return {
            "action": "human_review",
            "continue_workflow": False,
            "pause_for_human": True,
            "message": "Pausing workflow for human expert review",
            "review_focus": [
                "Implementation approach validation",
                "Architecture design review", 
                "Quality standards verification",
                "Requirement clarification"
            ]
        }

class IterationManager:
    """
    High-level manager that coordinates iteration control, user interaction, and decision execution
    """
    
    def __init__(self, max_iterations: int = 10):
        self.controller = IterationController(max_iterations)
        self.interaction_handler = UserInteractionHandler()
        self.decision_executor = IterationDecisionExecutor()
    
    async def handle_iteration_check(self, current_iteration: int, quality_result: Dict, cli_interface=None) -> Dict:
        """
        Main method to handle iteration checking and user decisions
        """
        # Check iteration limit
        iteration_check = await self.controller.check_iteration_limit(current_iteration, quality_result)
        
        if not iteration_check["limit_reached"]:
            return iteration_check
        
        # Limit reached - get user decision
        user_decision = await self.interaction_handler.prompt_user_decision(
            iteration_check, cli_interface
        )
        
        # Execute decision
        execution_result = await self.decision_executor.execute_decision(
            user_decision, {"max_iterations": self.controller.max_iterations}
        )
        
        # Update iteration controller if extending
        if execution_result["action"] == "extend_iterations":
            self.controller.max_iterations = execution_result["new_max_iterations"]
        
        return {
            "limit_reached": True,
            "user_decision": user_decision,
            "execution_result": execution_result,
            "iteration_analysis": iteration_check["iteration_summary"]
        }
    
    def get_iteration_statistics(self) -> Dict:
        """Get comprehensive iteration statistics"""
        return {
            "controller": {
                "max_iterations": self.controller.max_iterations,
                "recorded_reasons": len(self.controller.iteration_reasons),
                "start_time": self.controller.start_time.isoformat()
            },
            "interactions": {
                "total_user_interactions": len(self.interaction_handler.interaction_history)
            },
            "decisions": {
                "total_decisions_executed": len(self.decision_executor.decision_history),
                "decision_types": [d["decision"] for d in self.decision_executor.decision_history]
            }
        }