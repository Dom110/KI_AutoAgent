from __future__ import annotations

"""
PerformanceBot - Performance analysis and optimization specialist
Profiles code, detects bottlenecks, suggests optimizations
"""

import cProfile
import io
import json
import logging
import os
import pstats
import shutil
import subprocess
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from utils.openai_service import OpenAIService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent

logger = logging.getLogger(__name__)


@dataclass
class PerformanceProfile:
    """Performance analysis results"""

    execution_time: float
    memory_usage: dict[str, float]
    cpu_profile: dict[str, Any]
    bottlenecks: list[dict[str, Any]]
    optimization_suggestions: list[str]
    complexity_analysis: dict[str, Any]


class PerformanceBot(ChatAgent):
    """
    Performance analysis and optimization specialist
    - Code profiling (CPU, Memory, I/O)
    - Bottleneck detection
    - Optimization recommendations
    - Benchmark comparisons
    - External software analysis
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="performance_bot",
            name="PerformanceBot",
            full_name="Performance Analysis Specialist",
            description="Expert in profiling, benchmarking, and optimizing code performance",
            model="gpt-4o-2024-11-20",
            capabilities=[AgentCapability.CODE_REVIEW, AgentCapability.BUG_FIXING],
            temperature=0.3,
            max_tokens=4000,
            icon="⚡",
            instructions_path=".ki_autoagent/instructions/performance-instructions.md",
        )
        super().__init__(config)
        self.openai = OpenAIService(model=self.config.model)

    @override
    async def execute(self, request: TaskRequest) -> TaskResult:
        """Execute performance analysis task"""
        start_time = datetime.now()

        try:
            prompt_lower = request.prompt.lower()

            # Determine task type using match/case
            match prompt_lower:
                case s if "profile" in s or "performance" in s:
                    result = await self.analyze_performance(request)
                case s if "benchmark" in s or "compare" in s:
                    result = await self.run_benchmarks(request)
                case s if "optimize" in s:
                    result = await self.suggest_optimizations(request)
                case s if "analyze" in s and "package" in s:
                    result = await self.analyze_external_package(request)
                case _:
                    # General performance consultation
                    result = await self.provide_performance_advice(request)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                agent=self.name,
                content=result,
                status="success",
                execution_time=execution_time,
            )

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                agent=self.name,
                content=f"Performance analysis failed: {str(e)}",
                status="error",
                execution_time=execution_time,
            )

    async def analyze_performance(self, request: TaskRequest) -> str:
        """Analyze code performance"""
        # Extract code from request or context
        code = request.context.get("code", "")
        if not code:
            return "Please provide code to analyze. You can include it in the context."

        # Determine language
        language = request.context.get("language", "python")

        if language == "python":
            profile = await self._profile_python(code)
        elif language in ["javascript", "typescript"]:
            profile = await self._profile_javascript(code)
        else:
            return f"Performance profiling not yet supported for {language}"

        # Format results
        return self._format_profile_results(profile)

    async def _profile_python(self, code: str) -> PerformanceProfile:
        """Profile Python code"""

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # CPU Profiling
            profiler = cProfile.Profile()

            # Memory tracking
            tracemalloc.start()
            memory_before = tracemalloc.get_traced_memory()[0]

            # Execute and profile
            start_time = time.time()
            profiler.enable()

            try:
                # Compile and execute the code
                with open(temp_file) as f:
                    compiled = compile(f.read(), temp_file, "exec")
                    exec(compiled, {"__name__": "__main__"})
            except Exception as e:
                logger.warning(f"Code execution error during profiling: {e}")

            profiler.disable()
            execution_time = time.time() - start_time

            # Get memory stats
            memory_after = tracemalloc.get_traced_memory()[0]
            memory_peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()

            # Analyze profile
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats("cumulative")
            stats.print_stats(20)

            # Extract bottlenecks
            bottlenecks = self._extract_bottlenecks(stats)

            # Analyze complexity
            complexity = await self._analyze_complexity(code)

            # Generate suggestions
            suggestions = await self._generate_suggestions(
                code, bottlenecks, complexity
            )

            return PerformanceProfile(
                execution_time=execution_time,
                memory_usage={
                    "used_bytes": memory_after - memory_before,
                    "peak_bytes": memory_peak,
                    "used_mb": (memory_after - memory_before) / 1_048_576,
                    "peak_mb": memory_peak / 1_048_576,
                },
                cpu_profile=self._parse_profile_stats(stream.getvalue()),
                bottlenecks=bottlenecks,
                optimization_suggestions=suggestions,
                complexity_analysis=complexity,
            )

        finally:
            os.unlink(temp_file)

    def _extract_bottlenecks(self, stats) -> list[dict[str, Any]]:
        """Extract performance bottlenecks from profiling stats"""
        bottlenecks = []

        # Get top time-consuming functions
        stats.sort_stats("time")
        for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:10]:
            if tt > 0.001:  # More than 1ms
                bottlenecks.append(
                    {
                        "type": "cpu_time",
                        "function": f"{func[0]}:{func[1]}:{func[2]}",
                        "total_time": round(tt, 4),
                        "call_count": nc,
                        "time_per_call": round(tt / nc if nc > 0 else 0, 6),
                        "severity": "high"
                        if tt > 0.1
                        else "medium"
                        if tt > 0.01
                        else "low",
                    }
                )

        # Identify high call count functions
        stats.sort_stats("calls")
        for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:5]:
            if nc > 1000:
                bottlenecks.append(
                    {
                        "type": "high_call_count",
                        "function": f"{func[0]}:{func[1]}:{func[2]}",
                        "call_count": nc,
                        "total_time": round(tt, 4),
                        "severity": "high" if nc > 10000 else "medium",
                    }
                )

        return bottlenecks

    async def _analyze_complexity(self, code: str) -> dict[str, Any]:
        """Analyze code complexity"""
        complexity = {
            "lines_of_code": len(code.splitlines()),
            "loops": code.count("for ") + code.count("while "),
            "conditionals": code.count("if ")
            + code.count("elif ")
            + code.count("else:"),
            "functions": code.count("def ") + code.count("lambda "),
            "classes": code.count("class "),
        }

        # Estimate Big-O complexity
        if "for " in code and "for " in code[code.index("for ") + 4 :]:
            complexity[
                "estimated_complexity"
            ] = "O(n²) or higher - nested loops detected"
        elif "for " in code or "while " in code:
            complexity["estimated_complexity"] = "O(n) - linear complexity"
        else:
            complexity["estimated_complexity"] = "O(1) - constant time"

        return complexity

    async def _generate_suggestions(
        self, code: str, bottlenecks: list[dict], complexity: dict
    ) -> list[str]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []

        # Analyze bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "high_call_count":
                suggestions.append(
                    f"⚡ Function {bottleneck['function']} called {bottleneck['call_count']} times - consider memoization or caching"
                )
            elif bottleneck["type"] == "cpu_time" and bottleneck["severity"] == "high":
                suggestions.append(
                    f"🔥 Function {bottleneck['function']} takes {bottleneck['total_time']}s - needs optimization"
                )

        # Common optimization patterns
        if "append" in code and any(b["call_count"] > 100 for b in bottlenecks):
            suggestions.append(
                "📊 Multiple appends detected - consider using list comprehension or pre-allocation"
            )

        if complexity.get("loops", 0) > 2:
            suggestions.append(
                "🔄 Multiple loops detected - consider vectorization with NumPy or combining loops"
            )

        if "sorted" in code or "sort" in code:
            if any(
                "for" in code[i : i + 50]
                for i in range(len(code))
                if "sort" in code[i : i + 10]
            ):
                suggestions.append(
                    "🎯 Sorting inside loop detected - move sort outside if possible"
                )

        if "+=" in code and "str" in code:
            suggestions.append(
                "📝 String concatenation with += detected - use join() for better performance"
            )

        if not suggestions:
            suggestions.append("✅ No major performance issues detected")

        return suggestions

    def _parse_profile_stats(self, stats_output: str) -> dict[str, Any]:
        """Parse profiler stats output into structured format"""
        lines = stats_output.splitlines()

        # Find the stats table
        stats = []
        for line in lines:
            if "function calls" in line or "ncalls" in line:
                continue
            parts = line.split()
            if len(parts) >= 6 and parts[0].replace(".", "").isdigit():
                stats.append(
                    {
                        "ncalls": parts[0],
                        "tottime": parts[1],
                        "percall": parts[2],
                        "cumtime": parts[3],
                        "function": " ".join(parts[5:]),
                    }
                )

        return {"top_functions": stats[:10]}

    def _format_profile_results(self, profile: PerformanceProfile) -> str:
        """Format profiling results for display"""
        results = []
        results.append("# ⚡ Performance Analysis Report\n")

        # Execution metrics
        results.append("## 📊 Execution Metrics")
        results.append(f"- **Execution Time**: {profile.execution_time:.4f} seconds")
        results.append(f"- **Memory Used**: {profile.memory_usage['used_mb']:.2f} MB")
        results.append(f"- **Peak Memory**: {profile.memory_usage['peak_mb']:.2f} MB\n")

        # Complexity analysis
        results.append("## 🧮 Complexity Analysis")
        for key, value in profile.complexity_analysis.items():
            results.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        results.append("")

        # Bottlenecks
        if profile.bottlenecks:
            results.append("## 🔥 Performance Bottlenecks")
            for i, bottleneck in enumerate(profile.bottlenecks[:5], 1):
                severity_emoji = (
                    "🔴"
                    if bottleneck["severity"] == "high"
                    else "🟡"
                    if bottleneck["severity"] == "medium"
                    else "🟢"
                )
                results.append(f"{i}. {severity_emoji} **{bottleneck['function']}**")
                results.append(f"   - Time: {bottleneck.get('total_time', 0)}s")
                results.append(f"   - Calls: {bottleneck.get('call_count', 0)}")
            results.append("")

        # Optimization suggestions
        results.append("## 💡 Optimization Suggestions")
        for i, suggestion in enumerate(profile.optimization_suggestions, 1):
            results.append(f"{i}. {suggestion}")

        return "\n".join(results)

    async def analyze_external_package(self, request: TaskRequest) -> str:
        """Download and analyze external software package"""
        package_name = request.context.get("package", "")
        if not package_name:
            # Try to extract from prompt
            import re

            match = re.search(r"analyze\s+(\S+)", request.prompt.lower())
            if match:
                package_name = match.group(1)
            else:
                return "Please specify a package name to analyze"

        logger.info(f"🔍 Analyzing external package: {package_name}")

        # Create virtual environment
        venv_path = tempfile.mkdtemp(prefix=f"analysis_{package_name}_")

        try:
            # Create venv
            result = subprocess.run(
                ["python3", "-m", "venv", venv_path], capture_output=True, text=True
            )
            if result.returncode != 0:
                return f"Failed to create virtual environment: {result.stderr}"

            # Install package
            pip_path = os.path.join(venv_path, "bin", "pip")
            result = subprocess.run(
                [pip_path, "install", package_name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                return f"Failed to install package: {result.stderr}"

            # Analyze installed package
            analysis = await self._analyze_package_structure(venv_path, package_name)

            return self._format_package_analysis(package_name, analysis)

        except Exception as e:
            logger.error(f"Package analysis failed: {e}")
            return f"Failed to analyze package: {str(e)}"
        finally:
            # Cleanup
            shutil.rmtree(venv_path, ignore_errors=True)

    async def _analyze_package_structure(
        self, venv_path: str, package_name: str
    ) -> dict[str, Any]:
        """Analyze the structure and characteristics of an installed package"""
        site_packages = os.path.join(venv_path, "lib", "python3.11", "site-packages")

        # Find package directory
        package_dir = None
        for item in os.listdir(site_packages):
            if package_name.replace("-", "_") in item.lower():
                package_dir = os.path.join(site_packages, item)
                break

        if not package_dir or not os.path.isdir(package_dir):
            return {"error": "Package directory not found"}

        analysis = {
            "file_count": 0,
            "total_lines": 0,
            "file_types": {},
            "imports": set(),
            "functions": [],
            "classes": [],
            "patterns": [],
        }

        # Analyze Python files
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    analysis["file_count"] += 1

                    try:
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            lines = content.splitlines()
                            analysis["total_lines"] += len(lines)

                            # Extract imports
                            for line in lines[:50]:  # Check first 50 lines
                                if line.startswith("import ") or line.startswith(
                                    "from "
                                ):
                                    analysis["imports"].add(line.strip())

                            # Count functions and classes
                            analysis["functions"].extend(
                                [
                                    line.strip()
                                    for line in lines
                                    if line.strip().startswith("def ")
                                ][:10]
                            )
                            analysis["classes"].extend(
                                [
                                    line.strip()
                                    for line in lines
                                    if line.strip().startswith("class ")
                                ][:10]
                            )
                    except:
                        pass

        # Convert set to list for JSON serialization
        analysis["imports"] = list(analysis["imports"])[:20]

        return analysis

    def _format_package_analysis(
        self, package_name: str, analysis: dict[str, Any]
    ) -> str:
        """Format package analysis results"""
        results = []
        results.append(f"# 📦 Package Analysis: {package_name}\n")

        if "error" in analysis:
            return f"Error: {analysis['error']}"

        results.append("## 📊 Package Statistics")
        results.append(f"- **Files**: {analysis['file_count']} Python files")
        results.append(f"- **Lines of Code**: {analysis['total_lines']:,}")
        results.append(f"- **Classes**: {len(analysis['classes'])}")
        results.append(f"- **Functions**: {len(analysis['functions'])}\n")

        if analysis["imports"]:
            results.append("## 📚 Key Dependencies")
            for imp in analysis["imports"][:10]:
                results.append(f"- `{imp}`")
            results.append("")

        if analysis["classes"]:
            results.append("## 🏗️ Main Classes")
            for cls in analysis["classes"][:5]:
                results.append(f"- `{cls}`")
            results.append("")

        results.append("## 💡 Analysis Summary")
        results.append(f"The package '{package_name}' appears to be a ")

        # Determine package type based on imports
        imports_str = " ".join(analysis["imports"])
        if "django" in imports_str or "flask" in imports_str:
            results.append("web framework or web-related library")
        elif "numpy" in imports_str or "pandas" in imports_str:
            results.append("data science or numerical computing library")
        elif "tensorflow" in imports_str or "torch" in imports_str:
            results.append("machine learning library")
        else:
            results.append("Python library")

        results.append(
            f" with {analysis['file_count']} files and {analysis['total_lines']:,} lines of code."
        )

        return "\n".join(results)

    async def _process_agent_request(self, prompt: str, context: dict[str, Any]) -> str:
        """
        Process agent request - implementation of abstract method from ChatAgent
        Routes performance-related requests to appropriate handler
        """
        # Create a TaskRequest object for internal routing
        request = TaskRequest(
            task_id=f"perf_{datetime.now().timestamp()}",
            agent_id=self.config.agent_id,
            prompt=prompt,
            context=context or {},
        )

        # Use the execute method to handle the request
        result = await self.execute(request)
        return (
            result.content if isinstance(result.content, str) else str(result.content)
        )

    async def provide_performance_advice(self, request: TaskRequest) -> str:
        """Provide general performance optimization advice"""
        prompt = f"""
        As a performance optimization expert, provide advice for:
        {request.prompt}

        Include:
        1. Common performance pitfalls
        2. Best practices
        3. Tools and techniques
        4. Specific optimizations

        Focus on practical, actionable advice.
        """

        response = await self.openai.complete(prompt, temperature=0.3)
        return response

    async def run_benchmarks(self, request: TaskRequest) -> str:
        """Run performance benchmarks"""
        implementations = request.context.get("implementations", [])

        if not implementations:
            return "Please provide code implementations to benchmark in the context"

        results = []
        results.append("# 🏁 Benchmark Results\n")

        for i, impl in enumerate(implementations, 1):
            profile = await self._profile_python(impl)
            results.append(f"## Implementation {i}")
            results.append(f"- **Execution Time**: {profile.execution_time:.6f}s")
            results.append(
                f"- **Memory Used**: {profile.memory_usage['used_mb']:.2f} MB"
            )
            results.append(
                f"- **Complexity**: {profile.complexity_analysis.get('estimated_complexity', 'Unknown')}"
            )
            results.append("")

        # Determine winner
        results.append("## 🏆 Winner")
        results.append(
            "Implementation 1 (add comparative analysis once multiple implementations are tested)"
        )

        return "\n".join(results)

    async def suggest_optimizations(self, request: TaskRequest) -> str:
        """Suggest specific code optimizations"""
        code = request.context.get("code", "")

        if not code:
            return "Please provide code to optimize"

        # Profile the code first
        profile = await self._profile_python(code)

        # Generate optimized version using AI
        optimization_prompt = f"""
        Optimize this Python code for better performance:

        ```python
        {code}
        ```

        Current bottlenecks:
        {json.dumps(profile.bottlenecks[:3], indent=2)}

        Provide an optimized version with explanations for each change.
        """

        optimized = await self.openai.complete(optimization_prompt, temperature=0.2)

        return f"{self._format_profile_results(profile)}\n\n## 🚀 Optimized Version\n\n{optimized}"
