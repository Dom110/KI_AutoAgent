"""
CodeSmithAgent - Code generation and implementation specialist
Uses Claude 4.1 Sonnet for superior code generation
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.claude_code_service import ClaudeCodeService, ClaudeCodeConfig

# Import new analysis tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.indexing.tree_sitter_indexer import TreeSitterIndexer
from core.indexing.code_indexer import CodeIndexer
from core.analysis.vulture_analyzer import VultureAnalyzer
from core.analysis.radon_metrics import RadonMetrics
from services.diagram_service import DiagramService

logger = logging.getLogger(__name__)

@dataclass
class CodeImplementation:
    """Code implementation details"""
    language: str
    filename: str
    code: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    dependencies: List[str] = None
    complexity: str = "medium"  # simple, medium, complex

class CodeSmithAgent(ChatAgent):
    """
    Code Generation and Implementation Specialist
    - Code generation in multiple languages
    - Test creation
    - Code refactoring
    - Bug fixing
    - Documentation generation
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="codesmith",
            name="CodeSmithAgent",
            full_name="Code Implementation Specialist",
            description="Expert in code generation, implementation, and optimization using Claude",
            model="claude-4.1-sonnet-20250920",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.BUG_FIXING
            ],
            temperature=0.6,  # Lower for more consistent code
            max_tokens=4000,
            icon="💻"
        )
        super().__init__(config)

        # Initialize Claude Code CLI service (NO FALLBACKS)
        self.claude_cli = ClaudeCodeService(
            ClaudeCodeConfig(model="sonnet")  # Use Sonnet model via CLI
        )

        # Check if CLI is available
        if not self.claude_cli.is_available():
            error_msg = (
                "CodeSmithAgent requires Claude Code CLI!\n"
                "Install with: npm install -g @anthropic-ai/claude-code\n"
                "Or configure a different agent/model for code tasks."
            )
            logger.error(error_msg)
            # Don't raise here, but log the error

        # Initialize code analysis tools
        self.tree_sitter = TreeSitterIndexer()
        self.code_indexer = CodeIndexer()
        self.vulture = VultureAnalyzer()
        self.metrics = RadonMetrics()
        self.diagram_service = DiagramService()

        # Code intelligence cache
        self.code_knowledge = None

        # Code patterns and templates
        self.code_patterns = self._load_code_patterns()

        # Language-specific configurations
        self.language_configs = self._load_language_configs()

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute code generation task
        """
        start_time = datetime.now()

        try:
            # Analyze code request
            code_spec = await self.analyze_code_request(request.prompt)

            # Generate implementation
            implementation = await self.generate_implementation(code_spec)

            # Generate tests if requested
            if code_spec.get("include_tests", True):
                implementation.tests = await self.generate_tests(implementation)

            # Generate documentation
            if code_spec.get("include_docs", True):
                implementation.documentation = await self.generate_documentation(implementation)

            # Format output
            output = self.format_implementation(implementation)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                status="success",
                content=output,
                agent=self.config.agent_id,
                metadata={
                    "language": implementation.language,
                    "filename": implementation.filename,
                    "complexity": implementation.complexity,
                    "has_tests": bool(implementation.tests),
                    "has_docs": bool(implementation.documentation),
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return TaskResult(
                status="error",
                content=f"Failed to generate code: {str(e)}",
                agent=self.config.agent_id
            )

    async def analyze_code_request(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze code generation request
        """
        # Detect programming language
        language = self._detect_language(prompt)

        # Extract specifications
        system_prompt = """
        You are a senior software engineer.
        Analyze the code request and identify:
        1. Main functionality required
        2. Input/output specifications
        3. Performance requirements
        4. Error handling needs
        5. Testing requirements
        6. Documentation needs

        Be thorough and specific.
        """

        analysis_prompt = f"""
        Request: {prompt}

        Analyze and provide specifications:
        - Main functionality
        - Language: {language}
        - Complexity level
        - Special requirements
        - Include tests: yes/no
        - Include documentation: yes/no
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code analysis")

        response = await self.claude_cli.complete(analysis_prompt, system_prompt)

        return {
            "prompt": prompt,
            "language": language,
            "functionality": self._extract_functionality(response),
            "include_tests": "test" in prompt.lower() or "testing" in prompt.lower(),
            "include_docs": "document" in prompt.lower() or "doc" in prompt.lower(),
            "complexity": self._assess_complexity(prompt)
        }

    async def generate_implementation(
        self,
        spec: Dict[str, Any]
    ) -> CodeImplementation:
        """
        Generate code implementation
        """
        language = spec["language"]
        lang_config = self.language_configs.get(language, {})

        system_prompt = f"""
        You are Claude, an expert {language} programmer.
        Generate production-ready, clean, efficient code.
        Follow {language} best practices and conventions.
        Include comprehensive error handling.
        Make the code maintainable and well-structured.
        """

        implementation_prompt = f"""
        Language: {language}

        Requirements:
        {spec['prompt']}

        Generate complete, production-ready implementation with:
        1. Clear function/class structure
        2. Type hints (if applicable)
        3. Error handling
        4. Input validation
        5. Inline comments for complex logic

        Code should be ready to use without modifications.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code generation")

        code = await self.claude_cli.generate_code(
            specification=spec['prompt'],
            language=language,
            context=str(spec.get('functionality', ''))
        )

        # Extract filename
        filename = self._generate_filename(spec['prompt'], language)

        # Extract dependencies
        dependencies = self._extract_dependencies(code, language)

        return CodeImplementation(
            language=language,
            filename=filename,
            code=code,
            dependencies=dependencies,
            complexity=spec.get('complexity', 'medium')
        )

    async def generate_tests(self, implementation: CodeImplementation) -> str:
        """
        Generate tests for the implementation
        """
        language = implementation.language
        test_framework = self._get_test_framework(language)

        system_prompt = f"""
        You are a test engineer expert in {language}.
        Generate comprehensive tests using {test_framework}.
        Cover edge cases, error conditions, and normal operation.
        Make tests clear, maintainable, and thorough.
        """

        test_prompt = f"""
        Generate comprehensive tests for this {language} code:

        ```{language}
        {implementation.code}
        ```

        Use {test_framework} framework.
        Include:
        1. Unit tests for all functions/methods
        2. Edge case testing
        3. Error condition testing
        4. Integration tests if applicable

        Make tests production-ready.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for test generation")

        tests = await self.claude_cli.complete(test_prompt, system_prompt)

        return tests

    async def generate_documentation(self, implementation: CodeImplementation) -> str:
        """
        Generate documentation for the implementation
        """
        system_prompt = """
        You are a technical writer.
        Generate clear, comprehensive documentation.
        Include usage examples and API reference.
        """

        doc_prompt = f"""
        Generate documentation for this {implementation.language} code:

        ```{implementation.language}
        {implementation.code}
        ```

        Include:
        1. Overview and purpose
        2. Installation/setup (if needed)
        3. API reference
        4. Usage examples
        5. Parameters and return values
        6. Error handling notes

        Use markdown format.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for documentation generation")

        documentation = await self.claude_cli.complete(doc_prompt, system_prompt)

        return documentation

    async def refactor_code(
        self,
        code: str,
        language: str,
        improvements: List[str] = None
    ) -> str:
        """
        Refactor existing code for improvements
        """
        system_prompt = f"""
        You are a senior {language} developer specializing in code refactoring.
        Improve code quality, performance, and maintainability.
        Follow {language} best practices and modern patterns.
        """

        refactor_prompt = f"""
        Refactor this {language} code:

        ```{language}
        {code}
        ```

        Improvements to make:
        {chr(10).join('- ' + imp for imp in improvements) if improvements else '- General improvements'}

        Focus on:
        1. Code clarity and readability
        2. Performance optimization
        3. Better error handling
        4. Reduced complexity
        5. Modern {language} patterns

        Provide the refactored code with comments explaining major changes.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code refactoring")

        refactored = await self.claude_cli.complete(refactor_prompt, system_prompt)

        return refactored

    async def fix_bugs(self, code: str, error_description: str, language: str) -> str:
        """
        Fix bugs in code
        """
        system_prompt = f"""
        You are a debugging expert in {language}.
        Identify and fix bugs efficiently.
        Ensure the fix is robust and doesn't introduce new issues.
        """

        fix_prompt = f"""
        Fix the bug in this {language} code:

        Code:
        ```{language}
        {code}
        ```

        Error/Bug Description:
        {error_description}

        Provide:
        1. Fixed code
        2. Explanation of the bug
        3. How the fix works
        4. Any additional improvements

        Make sure the fix is complete and tested.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for bug fixing")

        fixed_code = await self.claude_cli.complete(fix_prompt, system_prompt)

        return fixed_code

    def format_implementation(self, implementation: CodeImplementation) -> str:
        """
        Format implementation for output
        """
        output = []
        output.append(f"# 💻 Code Implementation\n")
        output.append(f"**Language**: {implementation.language}")
        output.append(f"**Filename**: `{implementation.filename}`")
        output.append(f"**Complexity**: {implementation.complexity}\n")

        if implementation.dependencies:
            output.append("## 📦 Dependencies")
            for dep in implementation.dependencies:
                output.append(f"- {dep}")
            output.append("")

        output.append("## 📄 Code")
        output.append(f"```{implementation.language}")
        output.append(implementation.code)
        output.append("```\n")

        if implementation.tests:
            output.append("## 🧪 Tests")
            output.append(f"```{implementation.language}")
            output.append(implementation.tests)
            output.append("```\n")

        if implementation.documentation:
            output.append("## 📚 Documentation")
            output.append(implementation.documentation)

        output.append("\n---")
        output.append("*Generated by CodeSmithAgent (Claude 4.1 Sonnet)*")

        return "\n".join(output)

    def _detect_language(self, prompt: str) -> str:
        """
        Detect programming language from prompt
        """
        prompt_lower = prompt.lower()

        language_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue"],
            "typescript": ["typescript", "ts", "angular"],
            "java": ["java", "spring", "junit"],
            "go": ["go", "golang"],
            "rust": ["rust", "cargo"],
            "cpp": ["c++", "cpp"],
            "csharp": ["c#", "csharp", "dotnet"],
            "ruby": ["ruby", "rails"],
            "php": ["php", "laravel"],
        }

        for lang, keywords in language_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return lang

        # Default to Python if no language detected
        return "python"

    def _extract_functionality(self, response: str) -> str:
        """
        Extract main functionality from analysis
        """
        # Simple extraction - could be enhanced
        lines = response.split('\n')
        for line in lines:
            if "functionality" in line.lower():
                return line.strip()

        return "General implementation"

    def _assess_complexity(self, prompt: str) -> str:
        """
        Assess code complexity from prompt
        """
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["simple", "basic", "hello world"]):
            return "simple"
        elif any(word in prompt_lower for word in ["complex", "advanced", "sophisticated"]):
            return "complex"
        else:
            return "medium"

    def _generate_filename(self, prompt: str, language: str) -> str:
        """
        Generate appropriate filename
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "rust": ".rs",
            "cpp": ".cpp",
            "csharp": ".cs",
            "ruby": ".rb",
            "php": ".php",
        }

        # Extract main concept from prompt
        words = prompt.lower().split()[:5]
        name = "_".join(w for w in words if len(w) > 2)[:30]

        if not name:
            name = "implementation"

        return name + extensions.get(language, ".txt")

    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """
        Extract dependencies from code
        """
        dependencies = []

        if language == "python":
            # Extract import statements
            import_pattern = r'^(?:import|from)\s+(\S+)'
            matches = re.findall(import_pattern, code, re.MULTILINE)
            dependencies = [m.split('.')[0] for m in matches]

        elif language in ["javascript", "typescript"]:
            # Extract require/import statements
            import_pattern = r'(?:import|require)\s*\(?[\'"]([^\'")]+)[\'"]\)?'
            matches = re.findall(import_pattern, code)
            dependencies = matches

        # Filter out standard library modules
        dependencies = list(set(d for d in dependencies if not d.startswith('_')))

        return dependencies[:10]  # Limit to 10 dependencies

    def _get_test_framework(self, language: str) -> str:
        """
        Get appropriate test framework for language
        """
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "JUnit",
            "go": "testing",
            "rust": "cargo test",
            "cpp": "gtest",
            "csharp": "xUnit",
            "ruby": "RSpec",
            "php": "PHPUnit",
        }

        return frameworks.get(language, "unit test")

    def _load_code_patterns(self) -> List[Dict[str, Any]]:
        """
        Load code patterns library
        """
        return [
            {
                "pattern": "singleton",
                "languages": ["python", "java", "csharp"],
                "use_case": "Ensure single instance of a class"
            },
            {
                "pattern": "factory",
                "languages": ["python", "java", "typescript"],
                "use_case": "Create objects without specifying exact class"
            },
            {
                "pattern": "observer",
                "languages": ["javascript", "typescript", "python"],
                "use_case": "Event-driven programming"
            }
        ]

    def _load_language_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load language-specific configurations
        """
        return {
            "python": {
                "style_guide": "PEP 8",
                "type_hints": True,
                "docstring_format": "Google",
            },
            "javascript": {
                "style_guide": "Airbnb",
                "es_version": "ES6+",
                "module_system": "ESM",
            },
            "typescript": {
                "style_guide": "Airbnb",
                "strict_mode": True,
                "target": "ES2022",
            }
        }

    async def analyze_codebase(self, root_path: str = '.') -> Dict[str, Any]:
        """
        Perform deep code analysis for intelligent code generation

        Uses Tree-sitter AST and metrics to understand:
        - Existing code patterns
        - Coding style
        - Common abstractions
        - Performance hotspots
        """
        logger.info("Analyzing codebase for pattern extraction...")

        # Build complete code index
        self.code_knowledge = await self.code_indexer.build_full_index(root_path)

        # Extract code patterns for reuse
        patterns = self.code_knowledge.get('patterns', {})

        # Find dead code that can be removed
        dead_code = await self.vulture.find_dead_code(root_path)

        # Calculate code metrics
        metrics = await self.metrics.calculate_all_metrics(root_path)

        self.code_knowledge['dead_code'] = dead_code
        self.code_knowledge['metrics'] = metrics

        return self.code_knowledge

    async def implement_with_patterns(self, spec: str) -> str:
        """
        Implement feature using existing code patterns from the codebase

        This ensures new code matches existing style and patterns
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        # Extract relevant patterns
        patterns = self.code_knowledge.get('patterns', {})
        architecture = self.code_knowledge.get('architecture', {})

        # Build context-aware prompt
        context_prompt = f"""
        Implement the following feature using these existing patterns:

        Architecture Style: {architecture.get('style', 'Unknown')}
        Design Patterns Found: {', '.join(patterns.get('design_patterns', []))}

        Feature Specification:
        {spec}

        Follow the existing code style and patterns exactly.
        """

        # Generate implementation
        response = await self.claude_cli.process_message(context_prompt)
        return response

    async def refactor_complex_code(self, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Identify and refactor complex code sections

        Uses Radon metrics to find complex functions and suggest refactoring
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        metrics = self.code_knowledge.get('metrics', {})

        # Find refactoring candidates
        candidates = await self.metrics.identify_refactoring_candidates(metrics)

        refactorings = []
        for candidate in candidates[:3]:  # Limit to top 3
            if candidate['type'] == 'function':
                # Generate refactoring suggestion
                prompt = f"""
                Refactor this complex function:
                File: {candidate['file']}
                Function: {candidate['name']}
                Complexity: {candidate['complexity']}

                Suggestion: {candidate['suggestion']}

                Provide refactored code that reduces complexity.
                """

                refactored_code = await self.claude_cli.process_message(prompt)

                refactorings.append({
                    'original': candidate,
                    'refactored_code': refactored_code,
                    'improvement': 'Reduced complexity'
                })

        return refactorings

    async def optimize_performance_hotspots(self) -> List[Dict[str, str]]:
        """
        Find and optimize performance bottlenecks in the code

        Uses pattern analysis to identify inefficient code
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        patterns = self.code_knowledge.get('patterns', {})
        perf_issues = patterns.get('performance_issues', [])

        optimizations = []

        for issue in perf_issues[:5]:  # Top 5 issues
            optimization_prompt = f"""
            Optimize this performance issue:
            Type: {issue.get('type')}
            File: {issue.get('file')}
            Line: {issue.get('line')}

            Current code causing issue:
            {issue.get('code', 'N/A')}

            Provide optimized version.
            """

            optimized = await self.claude_cli.process_message(optimization_prompt)

            optimizations.append({
                'issue': issue,
                'optimized_code': optimized,
                'expected_improvement': 'Significant performance gain'
            })

        return optimizations

    async def generate_missing_tests(self) -> str:
        """
        Identify untested code and generate comprehensive tests

        Uses code index to find functions without tests
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        # Find functions without tests
        all_functions = self.code_knowledge.get('ast', {}).get('functions', {})

        # Simple heuristic: functions without 'test_' prefix likely need tests
        untested = []
        for func_key, func_info in all_functions.items():
            func_name = func_info.get('name', '')
            if not func_name.startswith('test_') and not func_name.startswith('_'):
                untested.append(func_info)

        if not untested:
            return "All functions appear to have tests!"

        # Generate tests for top untested functions
        test_prompt = f"""
        Generate comprehensive unit tests for these functions:

        {json.dumps(untested[:5], indent=2)}

        Use pytest framework with proper fixtures and assertions.
        """

        tests = await self.claude_cli.process_message(test_prompt)
        return tests

    async def cleanup_dead_code(self) -> str:
        """
        Generate script to remove dead code safely

        Uses Vulture analysis to identify unused code
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        dead_code = self.code_knowledge.get('dead_code', {})

        if not dead_code.get('summary', {}).get('total_dead_code'):
            return "No dead code found!"

        # Generate cleanup script
        cleanup_script = await self.vulture.generate_cleanup_script(dead_code)

        return f"""
## Dead Code Cleanup Report

### Summary
- **{dead_code['summary']['total_dead_code']}** items of dead code found
- **{dead_code['summary']['estimated_lines_to_remove']}** lines can be removed
- **Priority**: {dead_code['summary']['cleanup_priority']}

### Cleanup Script
```python
{cleanup_script}
```

Run this script to safely comment out dead code for review.
"""

    async def _process_agent_request(self, message) -> Any:
        """
        Process request from another agent
        Implementation of abstract method from BaseAgent
        """
        # Handle code generation requests from other agents
        if message.content.get("requesting_code"):
            task = message.content.get("task", "")
            result = await self.execute(TaskRequest(prompt=task))
            return {"code_result": result.content}

        return {"message": "CodeSmith received request"}
