#!/usr/bin/env python3
"""
Analyze KI_AutoAgent v5.8.3 Architecture
Generate comprehensive system diagrams and documentation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, os.path.expanduser("~/.ki_autoagent"))
sys.path.insert(0, os.path.expanduser("~/.ki_autoagent/backend"))

async def analyze_system_architecture():
    """Use Architect agent to analyze and document the v5.8.3 system"""

    try:
        from backend.agents.specialized.architect_agent import ArchitectAgent
        from backend.agents.base.base_agent import TaskRequest

        # Initialize Architect
        workspace_path = "/Users/dominikfoert/git/KI_AutoAgent"
        architect = ArchitectAgent()

        # Task: Analyze the complete v5.8.3 architecture
        task_request = TaskRequest(
            prompt="""
            ANALYZE AND DOCUMENT KI_AutoAgent v5.8.3 Architecture:

            Create a comprehensive system architecture analysis including:

            1. **LangGraph Workflow System** (backend/langgraph_system/):
               - State management with immutability (state.py with reducer pattern)
               - Workflow orchestration (workflow.py with 0 mutations)
               - Extensions (supervisor.py, agentic_rag.py)
               - Checkpointing and Store integration

            2. **Agent System** (backend/agents/specialized/):
               - Agent hierarchy and responsibilities
               - Communication patterns
               - Memory and learning systems

            3. **v5.8.3 Key Improvements**:
               - State immutability with custom reducer
               - LangGraph Store for cross-session learning
               - Supervisor Pattern for orchestration
               - Agentic RAG for intelligent search

            4. **Integration Points**:
               - WebSocket multi-client protocol
               - Workspace isolation
               - Instructions system (base + project)

            Generate:
            - Architecture diagrams (C4 model: Context, Container, Component)
            - Data flow diagrams showing state updates
            - Agent interaction sequence diagrams
            - Technology stack visualization

            Focus on v5.8.3 best practices implementation.
            """,
            global_context=f"Workspace: {workspace_path}",
            context={
                "version": "5.8.3",
                "focus": "LangGraph best practices",
                "key_files": [
                    "backend/langgraph_system/workflow.py",
                    "backend/langgraph_system/state.py",
                    "backend/langgraph_system/extensions/supervisor.py",
                    "backend/langgraph_system/extensions/agentic_rag.py"
                ]
            }
        )

        logger.info("🏗️ Starting architecture analysis...")
        result = await architect.execute(task_request)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"architecture_analysis_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Save main result
        with open(f"{output_dir}/analysis.md", "w") as f:
            f.write("# KI_AutoAgent v5.8.3 Architecture Analysis\n\n")
            f.write(result.content)

        # Save any generated artifacts
        if hasattr(result, 'metadata') and result.metadata and "artifacts" in result.metadata:
            for artifact_name, artifact_content in result.metadata["artifacts"].items():
                with open(f"{output_dir}/{artifact_name}", "w") as f:
                    f.write(artifact_content)

        logger.info(f"✅ Analysis complete! Results saved to {output_dir}/")

        return result

    except Exception as e:
        logger.error(f"❌ Architecture analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main execution"""
    logger.info("="*60)
    logger.info("KI_AutoAgent v5.8.3 Architecture Analysis")
    logger.info("="*60)

    result = await analyze_system_architecture()

    if result:
        logger.info("\n📊 Architecture Analysis Summary:")
        logger.info("-" * 40)
        print(result.content[:2000])  # Print first 2000 chars
        if len(result.content) > 2000:
            logger.info(f"\n... (truncated, full analysis in output directory)")

if __name__ == "__main__":
    asyncio.run(main())