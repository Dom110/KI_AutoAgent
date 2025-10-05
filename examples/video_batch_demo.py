"""
Video Analysis Demo - KI AutoAgent v5.8.2

Demonstrates VideoAgent capabilities:
1. Single video analysis (transcript, summary)
2. Custom instructions on video content
3. Batch processing with flexible instructions

Example Use Case: 20 Trading Videos → 20 Trading Strategy Markdown Files

Requirements:
- GEMINI_API_KEY environment variable
- google-generativeai package: pip install google-generativeai
- Video files (MP4, MOV, AVI, etc.)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agents.specialized.video_agent import VideoAgent
from agents.base.base_agent import TaskRequest


async def demo_single_video():
    """
    Demo 1: Single Video Analysis
    Extract transcript, visual analysis, and summary
    """
    print("\n" + "="*80)
    print("DEMO 1: Single Video Analysis (Predefined Task)")
    print("="*80 + "\n")

    # Initialize VideoAgent
    agent = VideoAgent(workspace_path=".")

    # Example video path (replace with your video)
    video_path = "/path/to/your/video.mp4"

    # Check if file exists
    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        print("Please update video_path with an actual video file")
        return

    # Task: Get transcript
    request = TaskRequest(
        prompt="Extract transcript from video",
        context={
            "video_path": video_path,
            "task": "transcript",  # Options: "transcript", "summary", "analysis"
            "output_name": "demo_transcript"
        }
    )

    print(f"📹 Analyzing video: {video_path}")
    print("🎯 Task: Extract transcript\n")

    result = await agent.execute(request)

    if result.status == "success":
        print("✅ Analysis complete!")
        print(f"📊 Result preview (first 500 chars):\n")
        print(result.content[:500] + "...\n")
        print(f"📁 Output files:")
        for file in result.metadata.get("output_files", []):
            print(f"   - {file}")
        print(f"\n💰 Cost: ${result.metadata.get('cost_usd', 0):.4f}")
        print(f"⏱️  Time: {result.execution_time:.2f}s")
    else:
        print(f"❌ Analysis failed: {result.content}")


async def demo_custom_instruction():
    """
    Demo 2: Custom Instruction
    Apply user-defined transformation to video content
    """
    print("\n" + "="*80)
    print("DEMO 2: Custom Instruction on Video")
    print("="*80 + "\n")

    agent = VideoAgent(workspace_path=".")

    # Example video (replace with your video)
    video_path = "/path/to/trading_tutorial.mp4"

    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        print("Please update video_path with an actual video file")
        return

    # Custom instruction in German (multi-language support)
    custom_instruction = """
    Analysiere dieses Trading-Video und erstelle eine detaillierte Trading-Strategie.

    Extrahiere folgende Informationen:

    1. **Entry-Kriterien**: Wann sollte der Trade eröffnet werden?
    2. **Exit-Kriterien**: Wann sollte der Trade geschlossen werden?
    3. **Stop-Loss**: Wo wird der Stop-Loss platziert?
    4. **Take-Profit**: Wo sind die Profit-Ziele?
    5. **Risk Management**: Wie viel Risiko pro Trade?
    6. **Indikatoren**: Welche technischen Indikatoren werden verwendet?
    7. **Timeframe**: Auf welchem Zeitrahmen funktioniert die Strategie?

    Gib die Strategie in einem strukturierten Format aus, das direkt als
    Anleitung für einen Trading-Bot verwendet werden kann.
    """

    request = TaskRequest(
        prompt="Apply custom instruction to video",
        context={
            "video_path": video_path,
            "custom_instruction": custom_instruction,
            "output_name": "trading_strategy_from_video"
        }
    )

    print(f"📹 Analyzing video: {video_path}")
    print(f"🎯 Custom instruction: {custom_instruction[:100]}...\n")

    result = await agent.execute(request)

    if result.status == "success":
        print("✅ Strategy extraction complete!")
        print(f"📊 Result preview (first 800 chars):\n")
        print(result.content[:800] + "...\n")
        print(f"📁 Output files:")
        for file in result.metadata.get("output_files", []):
            print(f"   - {file}")
        print(f"\n💰 Cost: ${result.metadata.get('cost_usd', 0):.4f}")
        print(f"⏱️  Time: {result.execution_time:.2f}s")
    else:
        print(f"❌ Analysis failed: {result.content}")


async def demo_batch_processing():
    """
    Demo 3: Batch Processing
    Process 20 trading videos → 20 trading strategy files
    """
    print("\n" + "="*80)
    print("DEMO 3: Batch Processing - 20 Videos → 20 Strategy Files")
    print("="*80 + "\n")

    agent = VideoAgent(workspace_path=".")

    # Base instruction template
    base_instruction = """
    Analysiere dieses Trading-Video und erstelle eine Trading-Strategie.

    Extrahiere:
    1. Entry-Kriterien
    2. Exit-Kriterien
    3. Stop-Loss Platzierung
    4. Take-Profit Ziele
    5. Risk Management Regeln
    6. Verwendete Indikatoren
    7. Zeitrahmen (Timeframe)

    Format: Strukturierte Anleitung für Trading-Bot
    """

    # Example: 20 video files
    # In real use, replace with actual video paths
    video_dir = Path("/path/to/trading_videos")

    # Create video specs for batch processing
    videos = []
    for i in range(1, 21):
        video_file = video_dir / f"strategy_{i:02d}.mp4"

        # Customize instruction per video if needed
        # Here we use the same instruction for all, but you can vary it
        custom_instruction = base_instruction + f"\n\n**Video {i}/20**"

        videos.append({
            "path": str(video_file),
            "instruction": custom_instruction,
            "output_name": f"trading_strategy_{i:02d}"
        })

    # Check if directory exists
    if not video_dir.exists():
        print(f"⚠️  Video directory not found: {video_dir}")
        print("This is a demo - showing what the batch request would look like:\n")

        print(f"📦 Batch Configuration:")
        print(f"   Total videos: {len(videos)}")
        print(f"   Video directory: {video_dir}")
        print(f"   Output naming: trading_strategy_01.md ... trading_strategy_20.md")
        print(f"\nExample video spec:")
        print(f"   {videos[0]}\n")

        print("To run this demo:")
        print("1. Create video directory with MP4 files")
        print("2. Update video_dir path in this script")
        print("3. Set GEMINI_API_KEY environment variable")
        print("4. Run: python examples/video_batch_demo.py")
        return

    # Create batch request
    request = TaskRequest(
        prompt="Batch process trading videos",
        context={
            "videos": videos  # List of {path, instruction, output_name}
        }
    )

    print(f"📦 Starting batch processing...")
    print(f"📹 Videos: {len(videos)}")
    print(f"📁 Output: ~/.ki_autoagent/data/video_output/\n")

    result = await agent.execute(request)

    if result.status in ["success", "partial_success"]:
        print("✅ Batch processing complete!\n")
        print(result.content)

        # Show metadata
        metadata = result.metadata
        print(f"\n📊 Batch Statistics:")
        print(f"   Total videos: {metadata['total_videos']}")
        print(f"   ✅ Successful: {metadata['successful']}")
        print(f"   ❌ Failed: {metadata['failed']}")
        print(f"   📁 Output directory: {metadata['output_dir']}")
        print(f"   💰 Total cost: ${metadata['cost_usd']:.4f}")
        print(f"   ⏱️  Total time: {result.execution_time:.2f}s")

        if metadata['failed'] > 0:
            print(f"\n⚠️  Failures:")
            for failure in metadata['failures']:
                print(f"   - {failure['video']}: {failure['error']}")
    else:
        print(f"❌ Batch processing failed: {result.content}")


async def main():
    """
    Run all demos
    """
    print("\n" + "="*80)
    print("KI AutoAgent v5.8.2 - VideoAgent Demonstrations")
    print("="*80)

    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ ERROR: GEMINI_API_KEY environment variable not set")
        print("\nTo run these demos:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("3. Run this script again\n")
        return

    # Run demos
    try:
        await demo_single_video()
        await demo_custom_instruction()
        await demo_batch_processing()

        print("\n" + "="*80)
        print("All demos complete!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
