"""
📖 Migration Guides - Clear instructions for updating deprecated code

Provides specific, actionable migration paths for each deprecated feature
"""

from typing import Optional


def get_migration_guide(key: str) -> Optional[str]:
    """Get migration guide by key"""
    guides = {
        "v6_to_v7_workflow": _guide_v6_to_v7_workflow(),
        "query_classifier_migration": _guide_query_classifier(),
        "curiosity_system_migration": _guide_curiosity_system(),
        "predictive_system_migration": _guide_predictive_system(),
        "learning_system_migration": _guide_learning_system(),
        "neurosymbolic_reasoner_migration": _guide_neurosymbolic_reasoner(),
        "self_diagnosis_migration": _guide_self_diagnosis(),
        "tool_registry_migration": _guide_tool_registry(),
        "approval_manager_migration": _guide_approval_manager(),
        "hitl_manager_migration": _guide_hitl_manager(),
        "workflow_adapter_migration": _guide_workflow_adapter(),
        "asimov_rules_migration": _guide_asimov_rules(),
    }
    return guides.get(key)


def _guide_v6_to_v7_workflow() -> str:
    """Migration guide: v6 workflow to v7 MCP workflow"""
    return """
🔄 MIGRATION: workflow_v6_integrated.py → workflow_v7_mcp.py

OVERVIEW:
The v6 workflow has been replaced with a Pure MCP Architecture.
This is a BREAKING CHANGE but provides better modularity and scalability.

KEY CHANGES:
✅ v6: Monolithic workflow with 9 cognitive systems
✅ v7: Distributed MCP servers with clear responsibilities

MIGRATION STEPS:

1. REPLACE WORKFLOW INITIALIZATION
   ❌ OLD (v6):
      from backend.workflow_v6_integrated import WorkflowV6Integrated
      workflow = WorkflowV6Integrated(workspace_path="...")
   
   ✅ NEW (v7):
      from backend.workflow_v7_mcp import WorkflowV7MCP
      from backend.utils.mcp_manager import MCPManager
      mcp_manager = MCPManager()
      workflow = WorkflowV7MCP(mcp_manager=mcp_manager)

2. REPLACE QUERY EXECUTION
   ❌ OLD (v6):
      result = await workflow.run(user_query="...", session_id="...")
   
   ✅ NEW (v7):
      response = await workflow.route_query(
          query="...",
          session_id="...",
          user_context={}
      )

3. COGNITIVE SYSTEMS MIGRATION
   • QueryClassifierV6 → SupervisorMCP (automatic routing)
   • CuriositySystemV6 → Interactive MCP Agents
   • PredictiveSystemV6 → MCP Metrics Collection
   • LearningSystemV6 → MCP Memory Server
   • NeurosymbolicReasonerV6 → Distributed MCP Reasoning
   • SelfDiagnosisV6 → MCP Error Handlers
   • WorkflowAdapterV6 → MCP Agent Adaptation
   • ApprovalManagerV6 → v7 Approval Handler
   • AsimovRulesV6 → v7 Security Module

4. TESTING YOUR MIGRATION
   ✅ Run: pytest backend/tests/test_v7_complete_workflow.py
   ✅ Test WebSocket: ws://localhost:8002/ws/chat
   ✅ Verify MCP Servers: http://localhost:8002/diagnostics

MIGRATION EFFORT: 🔴 HARD (involves architectural changes)
TIME ESTIMATE: 2-4 hours for full migration
DOCUMENTATION: See MIGRATION_GUIDE_v7.0.md

NEED HELP? Contact: team@ki-autoagent.dev
"""


def _guide_query_classifier() -> str:
    """Migration guide: QueryClassifierV6"""
    return """
🔄 MIGRATION: QueryClassifierV6 → SupervisorMCP

The query classification system has been completely redesigned.
Instead of a separate classifier, routing is now handled by SupervisorMCP.

OLD APPROACH (v6):
1. Query enters QueryClassifierV6
2. Classifier analyzes query type (BUILD, EXPLAIN, ANALYZE, EXTEND, etc.)
3. Classifier routes to appropriate agent

NEW APPROACH (v7):
1. Query enters SupervisorMCP
2. SupervisorMCP analyzes query context directly
3. SupervisorMCP routes to appropriate MCP server via JSON-RPC

MIGRATION CODE:
❌ OLD:
    classifier = QueryClassifierV6()
    query_type, confidence = classifier.classify(user_query)
    
✅ NEW:
    # Routing is automatic in SupervisorMCP
    # Access routing decisions via MCP memory:
    routing_decision = await mcp_manager.call_tool(
        server="memory",
        tool="get_routing_decision",
        args={"query": user_query}
    )

FEATURE MAPPING:
• Query Type Detection → SupervisorMCP context analysis
• Confidence Scoring → MCP decision metrics
• Route Determination → SupervisorMCP agent selection
"""


def _guide_curiosity_system() -> str:
    """Migration guide: CuriositySystemV6"""
    return """
🔄 MIGRATION: CuriositySystemV6 → Interactive MCP Agents

The curiosity system (knowledge gap identification) is now handled by individual MCP agents.

OLD APPROACH (v6):
1. Centralized curiosity system asks clarifying questions
2. System stores knowledge gaps
3. System suggests additional queries

NEW APPROACH (v7):
1. Each MCP agent asks clarifying questions as needed
2. MCP Memory Server stores knowledge gaps
3. Agents collaborate via MCP protocol

MIGRATION CODE:
❌ OLD:
    curiosity = CuriositySystemV6()
    clarifying_questions = curiosity.identify_gaps(user_query)
    answers = await collect_user_input(clarifying_questions)
    
✅ NEW:
    # Agents ask questions internally via MCP
    # Access knowledge gaps via MCP memory:
    gaps = await mcp_manager.call_tool(
        server="memory",
        tool="get_knowledge_gaps",
        args={"query": user_query}
    )
    # Retrieve clarifying questions from agents
    questions = await supervisor.get_clarifying_questions(user_query)

MIGRATION BENEFITS:
• Queries are handled by specialist MCP agents
• Questions are context-specific (not generic)
• Better integration with actual workflow execution
"""


def _guide_predictive_system() -> str:
    """Migration guide: PredictiveSystemV6"""
    return """
🔄 MIGRATION: PredictiveSystemV6 → MCP Metrics

The predictive system (workflow duration, risk assessment) now uses MCP metrics.

OLD APPROACH (v6):
1. Centralized predictive system estimates duration and risks
2. System provides pre-execution analysis
3. System stored historical patterns

NEW APPROACH (v7):
1. MCP Memory Server stores execution metrics
2. Agents provide real-time predictions
3. Historical data is queried from MCP Memory

MIGRATION CODE:
❌ OLD:
    predictor = PredictiveSystemV6()
    duration_estimate = predictor.estimate_duration(user_query)
    risk_factors = predictor.identify_risks(user_query)
    
✅ NEW:
    # Get metrics from MCP Memory Server
    metrics = await mcp_manager.call_tool(
        server="memory",
        tool="get_workflow_metrics",
        args={"query": user_query}
    )
    duration_estimate = metrics.get("avg_duration")
    risk_factors = metrics.get("risk_factors")

MIGRATION BENEFITS:
• Predictions based on actual execution data
• More accurate over time (machine learning)
• Integrated with MCP workflow execution
"""


def _guide_learning_system() -> str:
    """Migration guide: LearningSystemV6 → MCP Memory Server"""
    return """
🔄 MIGRATION: LearningSystemV6 → MCP Memory Server

Post-execution learning is now handled by the MCP Memory Server.

OLD APPROACH (v6):
1. Workflow execution completes
2. LearningSystemV6 records metrics (time, agents used, errors, etc.)
3. System adapts future workflows based on learning

NEW APPROACH (v7):
1. Workflow execution completes
2. MCP agents report metrics to Memory Server
3. Memory Server stores and aggregates learning

MIGRATION CODE:
❌ OLD:
    learning = LearningSystemV6()
    learning.record_execution(
        query=user_query,
        result=result,
        execution_time=elapsed_time,
        agents_used=agents,
        error_count=errors
    )
    
✅ NEW:
    # MCP agents automatically report metrics
    await mcp_manager.call_tool(
        server="memory",
        tool="store_workflow_execution",
        args={
            "query": user_query,
            "result": result,
            "execution_time": elapsed_time,
            "agents_used": agents,
            "error_count": errors
        }
    )

MIGRATION BENEFITS:
• Decentralized learning (each agent contributes)
• Better integration with MCP architecture
• Memory is persistent and queryable
"""


def _guide_neurosymbolic_reasoner() -> str:
    """Migration guide: NeurosymbolicReasonerV6"""
    return """
🔄 MIGRATION: NeurosymbolicReasonerV6 → Distributed MCP Reasoning

Neurosymbolic reasoning is now distributed across MCP agents.

OLD APPROACH (v6):
1. Before execution: Validate decisions with hybrid reasoning
2. Centralized validation logic
3. System provides yes/no decision

NEW APPROACH (v7):
1. Each agent validates its own decisions
2. SupervisorMCP coordinates reasoning across agents
3. Memory Server stores reasoning traces

MIGRATION CODE:
❌ OLD:
    reasoner = NeurosymbolicReasonerV6()
    validation = reasoner.validate_decision(
        query=user_query,
        proposed_action=action,
        context=workflow_context
    )
    if not validation.approved:
        # Handle rejection
    
✅ NEW:
    # Reasoning is distributed
    # Access validation via MCP:
    decision = await mcp_manager.call_tool(
        server="supervisor",
        tool="validate_decision",
        args={
            "query": user_query,
            "action": action,
            "context": workflow_context
        }
    )

MIGRATION BENEFITS:
• Reasoning is domain-specific (per agent)
• Better scalability
• Transparent decision-making via MCP
"""


def _guide_self_diagnosis() -> str:
    """Migration guide: SelfDiagnosisV6"""
    return """
🔄 MIGRATION: SelfDiagnosisV6 → MCP Error Handlers

Error diagnosis and healing is now in MCP error handlers.

OLD APPROACH (v6):
1. Error occurs
2. SelfDiagnosisV6 analyzes root cause
3. System attempts auto-healing
4. If healing fails, escalates to HITL

NEW APPROACH (v7):
1. Error occurs
2. Agent-specific error handler analyzes
3. Handler attempts auto-healing
4. If fails, escalates via MCP to HITL

MIGRATION CODE:
❌ OLD:
    diagnosis = SelfDiagnosisV6()
    diagnosis_result = diagnosis.diagnose(error=exception)
    if diagnosis_result.can_heal:
        await diagnosis_result.heal()
    else:
        await hitl_manager.escalate(error=exception)
    
✅ NEW:
    # Error handling is in MCP agents
    error_response = await agent.handle_error(error=exception)
    if error_response.healable:
        await agent.heal_error(error=exception)
    else:
        await hitl_handler.escalate(error=exception)

MIGRATION BENEFITS:
• Errors are handled by domain experts (agents)
• Better error context preservation
• Cleaner integration with MCP
"""


def _guide_tool_registry() -> str:
    """Migration guide: tool_registry_v6.py"""
    return """
🔄 MIGRATION: ToolRegistryV6 → MCP Server Native Tools

Tool management is now handled by MCP servers themselves.

OLD APPROACH (v6):
1. Centralized tool registry
2. Agents query registry for available tools
3. Registry dynamically assigns tools to agents

NEW APPROACH (v7):
1. Each MCP server exposes its own tools
2. Tools are defined in MCP server metadata
3. Agents discover tools via MCP protocol

MIGRATION CODE:
❌ OLD:
    registry = ToolRegistryV6()
    tools_for_agent = registry.get_tools_for_agent(agent_name="codesmith")
    
✅ NEW:
    # Tools are part of MCP server definition
    tools = await mcp_manager.get_server_resources(
        server_name="codesmith"
    )

MIGRATION BENEFITS:
• Tools are owned by their servers
• Better tool discoverability
• Simpler architecture
"""


def _guide_approval_manager() -> str:
    """Migration guide: ApprovalManagerV6"""
    return """
🔄 MIGRATION: ApprovalManagerV6 → v7 Approval Handler

Approval manager has been partially migrated. Update to v7 version.

OLD APPROACH (v6):
    from backend.workflow.approval_manager_v6 import ApprovalManagerV6
    
✅ NEW (v7):
    from backend.api.handlers.approval_handler import ApprovalHandler

KEY CHANGES:
• Approval workflow is now async MCP-based
• HITL (Human-in-the-loop) is the primary approval mechanism
• Approvals are stored in MCP Memory Server
"""


def _guide_hitl_manager() -> str:
    """Migration guide: hitl_manager_v6.py"""
    return """
🔄 MIGRATION: HITLManagerV6 → v7 HITL Handler

HITL manager has been partially migrated to v7.

OLD APPROACH (v6):
    from backend.workflow.hitl_manager_v6 import HITLManagerV6
    
✅ NEW (v7):
    from backend.api.handlers.hitl_handler import HITLHandler

FEATURES RETAINED:
✅ Human approval workflows
✅ Context capture and decision recording
✅ Integration with workflow execution

FEATURES REMOVED:
❌ Old logging format (use MCP Memory instead)
❌ Legacy decision storage (use MCP Memory instead)
"""


def _guide_workflow_adapter() -> str:
    """Migration guide: WorkflowAdapterV6"""
    return """
🔄 MIGRATION: WorkflowAdapterV6 → MCP Agent Adaptation

Workflow adaptation is now handled by MCP agents directly.

OLD APPROACH (v6):
    adapter = WorkflowAdapterV6()
    adapter.adapt_on_error(error=exception)
    adapter.adapt_on_success(success_metrics=metrics)
    
✅ NEW (v7):
    # Agents adapt internally
    # No central adapter needed
    # Adaptations are stored in MCP Memory

MIGRATION BENEFITS:
• Agents are self-adaptive
• No centralized adaptation logic
• Better integration with MCP
"""


def _guide_asimov_rules() -> str:
    """Migration guide: Asimov Rules"""
    return """
🔄 MIGRATION: AsimovRulesV6 → v7 Security Module

Asimov Rules have been partially migrated to v7.

OLD APPROACH (v6):
    • Rule 1: Don't harm human code
    • Rule 2: Code safety validation
    • Rule 3: Architecture documentation checks

NEW APPROACH (v7):
    • Rule 1: HITL for risky operations ✅
    • Rule 2: MCP security module (todo)
    • Rule 3: MCP validator (todo)

CURRENTLY IMPLEMENTED:
✅ HITL integration for approval workflows
❌ Code safety validation (planned)
❌ Architecture documentation checks (planned)

MIGRATION CODE:
❌ OLD:
    asimov = AsimovRules()
    asimov.validate_code_safety(code=generated_code)
    asimov.check_architecture(codebase=project_root)
    
✅ NEW (for HITL):
    approval_handler = ApprovalHandler()
    approval = await approval_handler.request_approval(
        action="code_generation",
        context=workflow_context,
        reason="Critical code generation"
    )

NEXT STEPS:
1. Implement MCP security server for code safety
2. Implement MCP validator server for architecture checks
3. Integrate with HITL workflow
"""


def get_all_migration_guides() -> dict[str, str]:
    """Get all migration guides"""
    return {
        "v6_to_v7_workflow": _guide_v6_to_v7_workflow(),
        "query_classifier_migration": _guide_query_classifier(),
        "curiosity_system_migration": _guide_curiosity_system(),
        "predictive_system_migration": _guide_predictive_system(),
        "learning_system_migration": _guide_learning_system(),
        "neurosymbolic_reasoner_migration": _guide_neurosymbolic_reasoner(),
        "self_diagnosis_migration": _guide_self_diagnosis(),
        "tool_registry_migration": _guide_tool_registry(),
        "approval_manager_migration": _guide_approval_manager(),
        "hitl_manager_migration": _guide_hitl_manager(),
        "workflow_adapter_migration": _guide_workflow_adapter(),
        "asimov_rules_migration": _guide_asimov_rules(),
    }