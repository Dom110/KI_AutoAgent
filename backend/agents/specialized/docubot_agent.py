"""
DocuBot Agent - Technical Documentation Specialist
Generates documentation, API specs, and user guides
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class DocuBotAgent(ChatAgent):
    """
    Technical Documentation Specialist
    - API documentation generation
    - Code documentation
    - User guides and tutorials
    - README files
    - Architecture documentation
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="docubot",
            name="DocuBot",
            full_name="Technical Documentation Expert",
            description="Specialized in creating comprehensive documentation",
            model="gpt-4o-2024-11-20",
            capabilities=[
                AgentCapability.DOCUMENTATION
            ],
            temperature=0.7,
            max_tokens=4000,
            icon="📝",
            instructions_path=".ki_autoagent/instructions/docubot-instructions.md"
        )
        super().__init__(config)
        self.ai_service = OpenAIService(model=self.config.model)

    async def _get_architect_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Get Architect's system analysis from shared_context (v5.8.2)
        Returns system_knowledge with diagrams, code_index, etc.
        """
        if not self.shared_context:
            logger.warning("⚠️ DocuBot: shared_context not available")
            return None

        try:
            analysis = self.shared_context.get('architect:system_knowledge')
            if analysis:
                logger.info("✅ DocuBot: Got Architect analysis from shared_context")
                return analysis
            else:
                logger.info("ℹ️ DocuBot: No Architect analysis available yet")
                return None
        except Exception as e:
            logger.error(f"❌ DocuBot: Failed to get Architect analysis: {e}")
            return None

    async def _generate_architecture_docs(self, architect_analysis: Dict[str, Any]) -> str:
        """
        Generate comprehensive ARCHITECTURE.md from Architect's analysis

        Includes:
        - System overview
        - Mermaid diagrams (container, component, dependency)
        - API endpoints
        - Tech stack
        - Code statistics
        - Quality metrics
        """
        docs = []

        # Header
        docs.append("# 🏗️ System Architecture Documentation\n")
        docs.append(f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        # System Overview
        code_index = architect_analysis.get('code_index', {})
        stats = code_index.get('statistics', {})

        docs.append("## 📊 System Overview\n")
        docs.append(f"- **Total Files**: {stats.get('total_files', 0)}")
        docs.append(f"- **Functions**: {stats.get('total_functions', 0)}")
        docs.append(f"- **Classes**: {stats.get('total_classes', 0)}")
        docs.append(f"- **API Endpoints**: {stats.get('total_api_endpoints', 0)}")
        docs.append(f"- **Lines of Code**: {stats.get('lines_of_code', 0):,}\n")

        # Quality Metrics
        metrics = architect_analysis.get('metrics', {})
        metrics_summary = metrics.get('summary', {})

        docs.append("## 📈 Quality Metrics\n")
        docs.append(f"- **Quality Score**: {metrics_summary.get('quality_score', 0):.1f}/100")
        docs.append(f"- **Average Complexity**: {metrics_summary.get('average_complexity', 0):.1f}")
        docs.append(f"- **Maintainability Index**: {metrics_summary.get('average_maintainability', 0):.1f}\n")

        # Architecture Diagrams
        diagrams = architect_analysis.get('diagrams', {})

        if diagrams.get('container'):
            docs.append("## 🏗️ Container Architecture\n")
            docs.append("```mermaid")
            docs.append(diagrams['container'])
            docs.append("```\n")

        if diagrams.get('component'):
            docs.append("## 🧩 Component Diagram\n")
            docs.append("```mermaid")
            docs.append(diagrams['component'])
            docs.append("```\n")

        if diagrams.get('dependency_graph'):
            docs.append("## 📊 Dependency Graph\n")
            docs.append("```mermaid")
            docs.append(diagrams['dependency_graph'])
            docs.append("```\n")

        # API Endpoints
        api_endpoints = code_index.get('api_endpoints', [])
        if api_endpoints:
            docs.append("## 🌐 API Endpoints\n")
            for endpoint in api_endpoints:
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                handler = endpoint.get('handler', 'unknown')
                docs.append(f"- **{method}** `{path}` → `{handler}`")
            docs.append("")

        # Tech Stack
        tech_stack = code_index.get('tech_stack', {})
        if tech_stack:
            docs.append("## 🛠️ Technology Stack\n")
            for category, technologies in tech_stack.items():
                if technologies:
                    docs.append(f"### {category.title()}")
                    for tech in technologies:
                        docs.append(f"- {tech}")
                    docs.append("")

        # Security Summary
        security = architect_analysis.get('security', {})
        security_summary = security.get('summary', {})
        if security_summary:
            docs.append("## 🔒 Security Overview\n")
            docs.append(f"- **Critical Issues**: {security_summary.get('critical', 0)}")
            docs.append(f"- **High Risk**: {security_summary.get('high', 0)}")
            docs.append(f"- **Medium Risk**: {security_summary.get('medium', 0)}\n")

        # Dead Code Summary
        dead_code = architect_analysis.get('dead_code', {})
        dead_code_summary = dead_code.get('summary', {})
        total_dead = dead_code_summary.get('total_dead_code', 0)
        if total_dead > 0:
            docs.append("## 🧹 Code Cleanup Opportunities\n")
            docs.append(f"- **Unused Items**: {total_dead}")
            docs.append(f"  - Functions: {dead_code_summary.get('functions', 0)}")
            docs.append(f"  - Classes: {dead_code_summary.get('classes', 0)}")
            docs.append(f"  - Variables: {dead_code_summary.get('variables', 0)}\n")

        # Footer
        docs.append("---")
        docs.append("*Generated by DocuBot using Architect's system analysis*")

        return "\n".join(docs)

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute documentation task

        v5.8.2: Auto-generates ARCHITECTURE.md if Architect analysis is available
        """
        try:
            # v5.8.2: Check if this is an architecture documentation request
            prompt_lower = request.prompt.lower()
            is_architecture_request = any(keyword in prompt_lower for keyword in [
                'architecture', 'system', 'overview', 'structure', 'diagram'
            ])

            # Try to get Architect's analysis
            architect_analysis = await self._get_architect_analysis()

            # If architecture docs requested AND analysis available, generate ARCHITECTURE.md
            if is_architecture_request and architect_analysis:
                logger.info("📐 Generating ARCHITECTURE.md from Architect analysis...")

                architecture_docs = await self._generate_architecture_docs(architect_analysis)

                # Save to file if workspace available
                workspace_path = request.context.get('workspace_path') if request.context else None
                if workspace_path:
                    import os
                    arch_file_path = os.path.join(workspace_path, 'ARCHITECTURE.md')
                    try:
                        with open(arch_file_path, 'w', encoding='utf-8') as f:
                            f.write(architecture_docs)
                        logger.info(f"✅ ARCHITECTURE.md written to {arch_file_path}")

                        return TaskResult(
                            status="success",
                            content=f"""✅ Architecture documentation generated successfully!

**File created**: `ARCHITECTURE.md`

Preview:
{architecture_docs[:500]}...

Full documentation has been saved to the workspace.""",
                            agent=self.config.agent_id,
                            metadata={
                                "model": self.config.model,
                                "timestamp": datetime.now().isoformat(),
                                "file_created": arch_file_path,
                                "source": "architect_analysis"
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to write ARCHITECTURE.md: {e}")
                        # Fall through to return docs as content

                # If can't save to file, return docs as content
                return TaskResult(
                    status="success",
                    content=architecture_docs,
                    agent=self.config.agent_id,
                    metadata={
                        "model": self.config.model,
                        "timestamp": datetime.now().isoformat(),
                        "source": "architect_analysis"
                    }
                )

            # Standard documentation generation with AI
            # v5.8.2: Include Architect context if available
            context_info = ""
            if architect_analysis:
                code_index = architect_analysis.get('code_index', {})
                stats = code_index.get('statistics', {})
                context_info = f"""
AVAILABLE SYSTEM INFORMATION:
- Total Files: {stats.get('total_files', 0)}
- Functions: {stats.get('total_functions', 0)}
- API Endpoints: {stats.get('total_api_endpoints', 0)}

Use this information to enhance documentation accuracy.
"""

            system_prompt = f"""
            You are DocuBot, a technical documentation expert. Generate clear,
            comprehensive documentation based on the user's request. Include:
            - Clear structure with headers
            - Code examples where relevant
            - API specifications if applicable
            - Usage instructions
            - Best practices

            {context_info}
            """

            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=request.prompt,
                temperature=0.7
            )

            # ASIMOV RULE 1: NO FALLBACK WITHOUT DOCUMENTED REASON
            if "error" in response.lower() and "api" in response.lower():
                raise Exception(f"API error - no fallback allowed per Asimov Rule 1: {response}")

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"DocuBot execution error: {e}")
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            return TaskResult(
                status="error",
                content=f"DOCUMENTATION FAILED: {str(e)}\n\nNo fallback allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id
            )

    # REMOVED: _generate_fallback_documentation method
    # ASIMOV RULE 1: No fallbacks without documented user reason
    # All errors must fail fast with clear error messages

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
