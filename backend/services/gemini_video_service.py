"""
Gemini Video Service
Handles video upload, analysis, and processing using Google Gemini 2.0 Flash API
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)


class GeminiVideoService:
    """
    Service for video analysis using Google Gemini 2.0 Flash
    Supports native video understanding (audio + visual) up to 2 hours
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Video Service

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)

        Raises:
            ImportError: If google-generativeai is not installed
            ValueError: If API key is not provided
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Set environment variable or pass api_key parameter."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Use Gemini 2.0 Flash Experimental (native video support)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

        logger.info("🎥 GeminiVideoService initialized with gemini-2.0-flash-exp")

    async def upload_video(self, video_path: str) -> Any:
        """
        Upload video to Gemini Files API and wait for processing

        Args:
            video_path: Path to video file

        Returns:
            Video file object from Gemini API

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If video processing fails
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"📤 Uploading video: {video_path_obj.name}")

        # Upload file (synchronous, run in executor)
        loop = asyncio.get_event_loop()
        video_file = await loop.run_in_executor(
            None,
            genai.upload_file,
            str(video_path_obj)
        )

        logger.info(f"⏳ Processing video: {video_file.name}")

        # Wait for processing (ACTIVE state)
        max_wait = 300  # 5 minutes timeout
        elapsed = 0
        poll_interval = 10  # Check every 10 seconds

        while video_file.state.name == "PROCESSING":
            if elapsed >= max_wait:
                raise RuntimeError(
                    f"Video processing timeout after {max_wait}s: {video_file.name}"
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # Refresh file state
            video_file = await loop.run_in_executor(
                None,
                genai.get_file,
                video_file.name
            )

            logger.debug(f"⏳ Processing... ({elapsed}s elapsed)")

        # Check final state
        if video_file.state.name == "FAILED":
            raise RuntimeError(
                f"Video processing failed: {video_file.name} - {video_file.error}"
            )

        logger.info(f"✅ Video ready: {video_file.name} ({video_file.state.name})")
        return video_file

    async def analyze_video(
        self,
        video_file: Any,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Analyze video with custom prompt using Gemini

        Args:
            video_file: Video file object from upload_video()
            prompt: Analysis prompt/question
            temperature: Model temperature (0.0-1.0)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If generation fails
        """
        logger.info(f"🔍 Analyzing video with prompt: {prompt[:100]}...")

        try:
            # Generate content (synchronous, run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                [video_file, prompt]
            )

            result = response.text
            logger.info(f"✅ Analysis complete ({len(result)} chars)")
            return result

        except Exception as e:
            logger.error(f"❌ Video analysis failed: {e}")
            raise RuntimeError(f"Gemini video analysis failed: {e}")

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text without video (for instruction transformation)

        Args:
            prompt: Text prompt
            temperature: Model temperature (0.0-1.0)

        Returns:
            Generated text response
        """
        logger.debug(f"💬 Generating text with prompt: {prompt[:100]}...")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )

            return response.text

        except Exception as e:
            logger.error(f"❌ Text generation failed: {e}")
            raise RuntimeError(f"Gemini text generation failed: {e}")

    async def cleanup(self, video_file: Any) -> None:
        """
        Delete video file from Gemini API

        Args:
            video_file: Video file object to delete
        """
        try:
            logger.info(f"🗑️  Deleting video: {video_file.name}")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                genai.delete_file,
                video_file.name
            )
            logger.info("✅ Video deleted")
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete video: {e}")

    async def analyze_complete(
        self,
        video_path: str,
        prompt: str,
        cleanup_after: bool = True
    ) -> str:
        """
        Complete workflow: Upload → Analyze → Cleanup

        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            cleanup_after: Delete video after analysis (default: True)

        Returns:
            Analysis result text
        """
        video_file = None
        try:
            # Upload and wait for processing
            video_file = await self.upload_video(video_path)

            # Analyze
            result = await self.analyze_video(video_file, prompt)

            return result

        finally:
            # Cleanup
            if video_file and cleanup_after:
                await self.cleanup(video_file)
