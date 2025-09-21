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
from utils.anthropic_service import AnthropicService

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

        # Initialize Anthropic service
        self.anthropic = AnthropicService()

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

        response = await self.anthropic.complete(analysis_prompt, system_prompt)

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

        code = await self.anthropic.generate_code(
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

        tests = await self.anthropic.complete(test_prompt, system_prompt)

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

        documentation = await self.anthropic.complete(doc_prompt, system_prompt)

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

        refactored = await self.anthropic.complete(refactor_prompt, system_prompt)

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

        fixed_code = await self.anthropic.complete(fix_prompt, system_prompt)

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
