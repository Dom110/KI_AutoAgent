#!/usr/bin/env python3
"""
🎬 Video Analysis Demo - Gemini 2.5 Pro
Minimal working example for video understanding

Requirements:
    pip install google-generativeai

Usage:
    export GOOGLE_GEMINI_API_KEY="your_api_key"
    python video_analysis_demo.py path/to/video.mp4
"""

import os
import sys
import time
import google.generativeai as genai
from pathlib import Path

def analyze_video(video_path: str, query: str = None):
    """
    Analyze video using Gemini 2.5 Pro native video understanding

    Args:
        video_path: Path to video file (mp4, mov, avi, webm)
        query: What to analyze (optional)

    Returns:
        dict: Analysis results
    """

    # Configure Gemini API
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)

    print(f"🎬 Analyzing video: {video_path}")
    print("━" * 80)

    # Check file exists
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Upload video to Gemini
    print("📤 Uploading video to Gemini API...")
    video_file = genai.upload_file(path=video_path)
    print(f"✅ Video uploaded: {video_file.name}")

    # Wait for processing
    print("⏳ Processing video...")
    while video_file.state.name == "PROCESSING":
        time.sleep(1)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"Video processing failed: {video_file.state}")

    print("✅ Video ready for analysis")

    # Default query if none provided
    if query is None:
        query = """
        Analyze this video and provide:
        1. Summary of what's happening
        2. Key moments or events (with timestamps if possible)
        3. Main topics or themes
        4. Any notable visual or audio elements

        Be specific and detailed.
        """

    # Analyze with Gemini 2.5 Pro
    print("\n🤖 Gemini 2.5 Pro analyzing...")
    print("━" * 80)

    model = genai.GenerativeModel("gemini-2.5-pro-latest")
    response = model.generate_content([query, video_file])

    print("\n📊 ANALYSIS RESULTS:")
    print("━" * 80)
    print(response.text)
    print("━" * 80)

    # Cleanup (optional - files auto-expire after 48 hours)
    # genai.delete_file(video_file.name)

    return {
        "video_path": video_path,
        "video_uri": video_file.uri,
        "duration": video_file.video_metadata.duration if hasattr(video_file, 'video_metadata') else None,
        "query": query,
        "analysis": response.text,
        "model": "gemini-2.5-pro-latest"
    }


def demo_bug_report():
    """Demo: Analyze a bug report screen recording"""

    query = """
    This is a screen recording of a software bug.

    Please analyze:
    1. What steps does the user take?
    2. At what point does the bug occur?
    3. What is the expected behavior vs actual behavior?
    4. Any error messages or visual indicators?
    5. Suggestions for debugging or fixing?
    """

    # Example with a hypothetical bug report video
    video_path = sys.argv[1] if len(sys.argv) > 1 else "bug_report.mp4"

    result = analyze_video(video_path, query)
    return result


def demo_code_walkthrough():
    """Demo: Analyze a code walkthrough video"""

    query = """
    This is a code walkthrough or tutorial video.

    Please extract:
    1. What programming language/framework is being used?
    2. Main concepts or patterns demonstrated
    3. Key code snippets or functions explained
    4. Learning objectives
    5. Step-by-step flow of the tutorial
    """

    video_path = sys.argv[1] if len(sys.argv) > 1 else "tutorial.mp4"

    result = analyze_video(video_path, query)
    return result


def demo_meeting_summary():
    """Demo: Summarize a meeting recording"""

    query = """
    This is a meeting or discussion recording.

    Please provide:
    1. List of participants (if identifiable by voice/name)
    2. Main topics discussed
    3. Key decisions made
    4. Action items assigned
    5. Timeline: When were different topics discussed?
    """

    video_path = sys.argv[1] if len(sys.argv) > 1 else "meeting.mp4"

    result = analyze_video(video_path, query)
    return result


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🎬 VIDEO ANALYSIS DEMO - Gemini 2.5 Pro")
    print("=" * 80 + "\n")

    if len(sys.argv) < 2:
        print("❌ Usage: python video_analysis_demo.py <path_to_video.mp4>")
        print("\nExamples:")
        print("  python video_analysis_demo.py bug_report.mp4")
        print("  python video_analysis_demo.py tutorial.mov")
        print("  python video_analysis_demo.py meeting.webm")
        sys.exit(1)

    # Run general analysis
    try:
        result = analyze_video(sys.argv[1])

        print("\n✅ Analysis complete!")
        print(f"📊 Results saved to: analysis_results.txt")

        # Save to file
        with open("analysis_results.txt", "w") as f:
            f.write(f"Video: {result['video_path']}\n")
            f.write(f"Model: {result['model']}\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['analysis'])

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
