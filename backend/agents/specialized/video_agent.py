"""
VideoAgent - Video Understanding and Analysis Specialist
Uses Google Gemini 2.0 Flash for native video comprehension (audio + visual)
Supports batch processing with custom instructions
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Fix import paths
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from agents.base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                                    TaskResult)
from agents.base.chat_agent import ChatAgent
from services.gemini_video_service import GeminiVideoService

# Import Settings for configuration
try:
    from config.settings import settings

    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    logging.warning("Settings not available - using hardcoded defaults")

# Try to import GPT-4o service for custom instruction execution
try:
    from utils.openai_service import OpenAIService

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI service not available - custom instructions limited")

logger = logging.getLogger(__name__)


class VideoAgent(ChatAgent):
    """
    Video Understanding and Analysis Expert

    Features:
    - Native video comprehension (audio + visual + temporal reasoning)
    - Transcript extraction with timestamps
    - Visual scene analysis
    - Custom instruction execution on video content
    - Batch processing (N videos → N outputs)
    - Dual output (JSON for agents + Markdown for humans)
    - Multi-language support

    Supported Workflows:
    1. Predefined Tasks: transcript, summary, analysis
    2. Custom Instructions: "Erstelle eine Trading Strategie aus diesem Video"
    3. Batch Processing: 20 videos + custom instruction → 20 MD files
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize VideoAgent

        Args:
            workspace_path: Current workspace path (for workspace-aware operations)
        """
        # Get configuration from Settings or use defaults
        if SETTINGS_AVAILABLE:
            model = settings.VIDEOAGENT_MODEL
            temperature = settings.VIDEOAGENT_TEMPERATURE
            max_tokens = settings.VIDEOAGENT_MAX_TOKENS
            output_dir = Path(
                settings.VIDEOAGENT_OUTPUT_DIR.replace("~", str(Path.home()))
            )
            logger.info(f"✅ VideoAgent using Settings configuration: {model}")
        else:
            # Fallback to hardcoded defaults
            model = "gemini-2.0-flash-exp"
            temperature = 0.7
            max_tokens = 8000
            output_dir = Path.home() / ".ki_autoagent" / "data" / "video_output"
            logger.warning(
                "⚠️  VideoAgent using hardcoded defaults (Settings not available)"
            )

        config = AgentConfig(
            agent_id="video",
            name="VideoAgent",
            full_name="Video Understanding Specialist",
            description="Specialized in video comprehension, analysis, and content extraction",
            model=model,
            capabilities=[
                AgentCapability.WEB_RESEARCH,  # For video content research
                AgentCapability.DOCUMENTATION,  # For generating documentation
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            icon="🎥",
            instructions_path="$HOME/.ki_autoagent/config/instructions/video-instructions.md",
        )
        super().__init__(config)

        # Initialize Gemini Video Service
        try:
            self.gemini_service = GeminiVideoService()
            logger.info(f"✅ VideoAgent initialized with {model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini Video Service: {e}")
            raise

        # Initialize GPT-4o for custom instruction execution
        if OPENAI_AVAILABLE:
            try:
                self.openai_service = OpenAIService(model="gpt-4o")
                logger.info("✅ GPT-4o service initialized for custom instructions")
            except Exception as e:
                logger.warning(f"⚠️  GPT-4o service not available: {e}")
                self.openai_service = None
        else:
            self.openai_service = None

        # Output directory (from Settings or default)
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Workspace path
        self.workspace_path = workspace_path or os.getcwd()

        # Token tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute video analysis task

        Supports 3 modes:
        1. Predefined Task: request.context["task"] = "transcript" | "summary" | "analysis"
        2. Custom Instruction: request.context["custom_instruction"] = "..."
        3. Batch Processing: request.context["videos"] = [{path, instruction, output_name}, ...]

        Args:
            request: Task request with video path(s) and instructions

        Returns:
            TaskResult with analysis results
        """
        start_time = datetime.now()
        self._current_request = request

        logger.info("🎥 VideoAgent starting execution")

        try:
            # MODE 3: Batch Processing
            if "videos" in request.context:
                return await self._execute_batch(request, start_time)

            # MODE 2: Custom Instruction
            elif "custom_instruction" in request.context:
                return await self._execute_custom(request, start_time)

            # MODE 1: Predefined Task
            elif "task" in request.context:
                return await self._execute_predefined(request, start_time)

            else:
                # Default: Basic analysis
                return await self._execute_predefined(request, start_time)

        except Exception as e:
            logger.error(f"❌ VideoAgent execution failed: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                status="error",
                content=f"Video analysis failed: {str(e)}",
                agent=self.config.agent_id,
                metadata={"error": str(e), "execution_time": execution_time},
                execution_time=execution_time,
                tokens_used=0,
            )

    async def _execute_predefined(
        self, request: TaskRequest, start_time: datetime
    ) -> TaskResult:
        """
        Execute predefined task (transcript, summary, analysis)
        """
        video_path = request.context.get("video_path")
        task = request.context.get("task", "analysis")
        output_name = request.context.get("output_name", f"video_{task}")

        if not video_path:
            raise ValueError("video_path is required in request.context")

        logger.info(f"🎬 Executing predefined task: {task} on {video_path}")

        # Basic video analysis
        video_data = await self._analyze_video_basic(video_path)

        # Generate result based on task
        if task == "transcript":
            result = video_data["transcript"]
        elif task == "summary":
            result = video_data.get("summary", "Summary not available")
        else:  # analysis
            result = self._format_analysis_result(video_data)

        # Generate dual output
        await self._generate_dual_output(
            video_data=video_data,
            result=result,
            video_path=video_path,
            output_name=output_name,
            instruction=f"Predefined task: {task}",
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        return TaskResult(
            status="success",
            content=result,
            agent=self.config.agent_id,
            metadata={
                "video_path": video_path,
                "task": task,
                "output_files": [
                    str(self.output_dir / f"{output_name}.json"),
                    str(self.output_dir / f"{output_name}.md"),
                ],
                "tokens_used": self.total_tokens_used,
                "cost_usd": self.total_cost,
            },
            execution_time=execution_time,
            tokens_used=self.total_tokens_used,
        )

    async def _execute_custom(
        self, request: TaskRequest, start_time: datetime
    ) -> TaskResult:
        """
        Execute custom instruction on video
        Example: "Erstelle eine Trading Strategie aus diesem Video"
        """
        video_path = request.context.get("video_path")
        custom_instruction = request.context["custom_instruction"]
        output_name = request.context.get("output_name", "video_custom")

        if not video_path:
            raise ValueError("video_path is required in request.context")

        logger.info(f"🎯 Executing custom instruction on {video_path}")
        logger.info(f"📝 Instruction: {custom_instruction[:100]}...")

        # Basic video analysis
        video_data = await self._analyze_video_basic(video_path)

        # Execute custom instruction using GPT-4o
        result = await self._apply_custom_instruction(
            video_data, custom_instruction, video_path
        )

        # Generate dual output
        await self._generate_dual_output(
            video_data=video_data,
            result=result,
            video_path=video_path,
            output_name=output_name,
            instruction=custom_instruction,
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        return TaskResult(
            status="success",
            content=result,
            agent=self.config.agent_id,
            metadata={
                "video_path": video_path,
                "custom_instruction": custom_instruction,
                "output_files": [
                    str(self.output_dir / f"{output_name}.json"),
                    str(self.output_dir / f"{output_name}.md"),
                ],
                "tokens_used": self.total_tokens_used,
                "cost_usd": self.total_cost,
            },
            execution_time=execution_time,
            tokens_used=self.total_tokens_used,
        )

    async def _execute_batch(
        self, request: TaskRequest, start_time: datetime
    ) -> TaskResult:
        """
        Batch process multiple videos with custom instructions

        request.context["videos"] = [
            {
                "path": "/path/to/video1.mp4",
                "instruction": "Create trading strategy...",
                "output_name": "strategy_01"
            },
            ...
        ]
        """
        videos = request.context["videos"]
        logger.info(f"📦 Batch processing {len(videos)} videos")

        results = []
        failed = []

        for i, video_spec in enumerate(videos, 1):
            try:
                logger.info(
                    f"🎬 Processing video {i}/{len(videos)}: {video_spec['path']}"
                )

                # Analyze video
                video_data = await self._analyze_video_basic(video_spec["path"])

                # Apply custom instruction
                result = await self._apply_custom_instruction(
                    video_data, video_spec["instruction"], video_spec["path"]
                )

                # Generate dual output
                await self._generate_dual_output(
                    video_data=video_data,
                    result=result,
                    video_path=video_spec["path"],
                    output_name=video_spec["output_name"],
                    instruction=video_spec["instruction"],
                )

                results.append(
                    {
                        "video": video_spec["path"],
                        "output_name": video_spec["output_name"],
                        "status": "success",
                    }
                )

            except Exception as e:
                logger.error(f"❌ Failed to process {video_spec['path']}: {e}")
                failed.append({"video": video_spec["path"], "error": str(e)})

        execution_time = (datetime.now() - start_time).total_seconds()

        # Summary
        summary = f"""Batch Processing Complete:
✅ Successful: {len(results)}
❌ Failed: {len(failed)}
📁 Output: {self.output_dir}

Total Tokens: {self.total_tokens_used:,}
Total Cost: ${self.total_cost:.4f}
"""

        return TaskResult(
            status="success" if len(failed) == 0 else "partial_success",
            content=summary,
            agent=self.config.agent_id,
            metadata={
                "total_videos": len(videos),
                "successful": len(results),
                "failed": len(failed),
                "results": results,
                "failures": failed,
                "output_dir": str(self.output_dir),
                "tokens_used": self.total_tokens_used,
                "cost_usd": self.total_cost,
            },
            execution_time=execution_time,
            tokens_used=self.total_tokens_used,
        )

    async def _analyze_video_basic(self, video_path: str) -> dict[str, Any]:
        """
        Extract basic video data using Gemini:
        - Transcript with timestamps
        - Visual analysis (scenes, objects, actions)
        - Timeline/structure
        - Summary

        Args:
            video_path: Path to video file

        Returns:
            Dict with video analysis data
        """
        logger.info(f"🔍 Analyzing video: {video_path}")

        # Transcript Extraction
        transcript_prompt = """Provide a complete transcript of this video with timestamps.

Format:
[00:00] Speaker: Text content
[00:15] Speaker: More text
...

Include all spoken words accurately."""

        transcript = await self.gemini_service.analyze_complete(
            video_path=video_path,
            prompt=transcript_prompt,
            cleanup_after=False,  # Keep video for additional analysis
        )

        # Visual Analysis
        visual_prompt = """Analyze the visual content of this video:

1. Key scenes and their timestamps
2. Important objects, people, or elements shown
3. Visual transitions and structure
4. On-screen text or graphics
5. Overall visual style and quality

Provide a structured analysis."""

        visual_analysis = await self.gemini_service.analyze_complete(
            video_path=video_path, prompt=visual_prompt, cleanup_after=False
        )

        # Summary
        summary_prompt = """Provide a comprehensive summary of this video:

1. Main topic/subject
2. Key points discussed
3. Important takeaways
4. Target audience
5. Overall purpose

Keep it concise but informative (3-5 paragraphs)."""

        summary = await self.gemini_service.analyze_complete(
            video_path=video_path,
            prompt=summary_prompt,
            cleanup_after=True,  # Final analysis, cleanup now
        )

        video_data = {
            "video_path": video_path,
            "transcript": transcript,
            "visual_analysis": visual_analysis,
            "summary": summary,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info("✅ Video analysis complete")
        return video_data

    async def _apply_custom_instruction(
        self, video_data: dict[str, Any], instruction: str, video_path: str
    ) -> str:
        """
        Apply custom instruction to video data using GPT-4o

        Args:
            video_data: Analyzed video data from _analyze_video_basic()
            instruction: Custom user instruction
            video_path: Original video path

        Returns:
            Result of applying the instruction
        """
        logger.info(f"🎯 Applying custom instruction: {instruction[:100]}...")

        # Detect instruction language (for multi-language support)
        language = self._detect_language(instruction)

        # Build prompt for GPT-4o
        prompt = f"""You are a video content analyst. You have analyzed a video and extracted the following data:

VIDEO DATA:
{json.dumps(video_data, indent=2, ensure_ascii=False)}

USER INSTRUCTION:
{instruction}

Execute this instruction based on the video data. Provide a complete, well-structured response in {language}.
The response should be ready to use (e.g., if instruction asks for trading strategy, provide the complete strategy).
"""

        # Use GPT-4o if available, otherwise fallback to Gemini
        if self.openai_service:
            result = await self.openai_service.complete(prompt)
        else:
            # Fallback to Gemini for text generation
            result = await self.gemini_service.generate_text(prompt)

        logger.info("✅ Custom instruction applied")
        return result

    async def _generate_dual_output(
        self,
        video_data: dict[str, Any],
        result: str,
        video_path: str,
        output_name: str,
        instruction: str,
    ) -> None:
        """
        Generate BOTH JSON (for agents) and Markdown (for humans)

        Args:
            video_data: Analyzed video data
            result: Processing result
            video_path: Original video path
            output_name: Base filename (without extension)
            instruction: Instruction that was executed
        """
        logger.info(f"📄 Generating dual output: {output_name}")

        # JSON Output (for agent-to-agent communication)
        json_output = {
            "video_path": video_path,
            "instruction": instruction,
            "result": result,
            "video_data": {
                "transcript": video_data.get("transcript", ""),
                "visual_analysis": video_data.get("visual_analysis", ""),
                "summary": video_data.get("summary", ""),
            },
            "metadata": {
                "analyzed_at": video_data.get("analyzed_at"),
                "generated_at": datetime.utcnow().isoformat(),
                "agent": self.config.agent_id,
            },
        }

        json_path = self.output_dir / f"{output_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ JSON saved: {json_path}")

        # Markdown Output (for human readability)
        md_content = f"""# Video Analysis: {output_name}

**Video:** `{video_path}`
**Analyzed:** {video_data.get('analyzed_at', 'N/A')}
**Generated:** {datetime.utcnow().isoformat()}

---

## 📝 Instruction

{instruction}

---

## ✅ Result

{result}

---

## 📊 Video Data

### 🎤 Transcript

{video_data.get('transcript', 'N/A')}

### 👁️ Visual Analysis

{video_data.get('visual_analysis', 'N/A')}

### 📄 Summary

{video_data.get('summary', 'N/A')}

---

*Generated by VideoAgent 🎥*
"""

        md_path = self.output_dir / f"{output_name}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"✅ Markdown saved: {md_path}")

    def _format_analysis_result(self, video_data: dict[str, Any]) -> str:
        """Format complete analysis result"""
        return f"""Video Analysis Complete

Summary:
{video_data.get('summary', 'N/A')}

Transcript Available: {len(video_data.get('transcript', ''))} characters
Visual Analysis Available: {len(video_data.get('visual_analysis', ''))} characters

See output files for complete details.
"""

    def _detect_language(self, text: str) -> str:
        """
        Detect language of instruction text
        Simple heuristic - can be improved with langdetect library
        """
        # German keywords
        german_keywords = [
            "erstelle",
            "baue",
            "analysiere",
            "video",
            "strategie",
            "aus",
            "diesem",
        ]
        german_count = sum(1 for word in german_keywords if word in text.lower())

        if german_count >= 2:
            return "German"
        else:
            return "English"

    async def _process_agent_request(self, message: Any) -> Any:
        """
        Process request from another agent (required by BaseAgent)

        VideoAgent can receive requests from other agents to analyze videos
        and return structured results.

        Args:
            message: AgentMessage with video analysis request

        Returns:
            Analysis result (dict or string)
        """
        from agents.base.base_agent import AgentMessage

        if not isinstance(message, AgentMessage):
            logger.warning(f"VideoAgent received non-AgentMessage: {type(message)}")
            return {"error": "Invalid message type"}

        try:
            # Extract video analysis request from message content
            content = message.content

            # Create TaskRequest from agent message
            if isinstance(content, dict):
                task_request = TaskRequest(
                    prompt=content.get("prompt", "Analyze video"),
                    context=content.get("context", {}),
                )
            else:
                task_request = TaskRequest(prompt=str(content), context={})

            # Execute video analysis
            result = await self.execute(task_request)

            # Return structured result
            return {
                "status": result.status,
                "content": result.content,
                "metadata": result.metadata,
                "from_agent": "video",
                "to_agent": message.from_agent,
            }

        except Exception as e:
            logger.error(f"VideoAgent failed to process agent request: {e}")
            return {
                "error": str(e),
                "from_agent": "video",
                "to_agent": message.from_agent,
            }
