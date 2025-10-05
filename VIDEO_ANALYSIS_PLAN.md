# 🎬 Video Analysis Integration Plan - KI_AutoAgent v5.9.0

## 📊 Overview

Add video understanding capabilities to KI_AutoAgent using multiple backends.

## 🎯 Goals

1. Enable agents to analyze screen recordings (bug reports)
2. Understand code walkthrough videos
3. Extract insights from meeting recordings
4. Index tutorial videos for knowledge base

## 🏗️ Architecture

### Components

```
backend/
├── agents/specialized/
│   └── video_agent.py          # New: VideoAnalyzerAgent
├── services/
│   ├── gemini_video_service.py # Gemini 2.5 Pro integration
│   ├── whisper_service.py      # Audio transcription
│   └── frame_extractor.py      # OpenCV frame extraction
├── config/
│   └── video_config.yaml       # Video processing settings
└── utils/
    └── video_utils.py          # Helper functions
```

## 📦 Dependencies

```python
# requirements.txt additions
google-generativeai>=0.4.0    # Gemini API
openai-whisper>=20231117      # Audio transcription
opencv-python>=4.9.0          # Frame extraction
ffmpeg-python>=0.2.0          # Video processing
```

## 🔧 Implementation Phases

### Phase 1: Gemini 2.5 Native Video (Primary)

**Files to create:**
- `backend/services/gemini_video_service.py`
- `backend/agents/specialized/video_agent.py`

**Features:**
- Upload video to Gemini API
- Native video analysis (up to 2 hours)
- Temporal reasoning
- Moment retrieval

**Example Usage:**
```python
video_agent = VideoAnalyzerAgent()
result = await video_agent.analyze_video(
    video_path="bug_report.mp4",
    query="What steps lead to the error? When does it occur?",
    mode="gemini"
)
```

### Phase 2: Hybrid Mode (Fallback)

**Files to create:**
- `backend/services/whisper_service.py`
- `backend/utils/frame_extractor.py`

**Features:**
- Audio transcription with Whisper
- Key frame extraction (every 5 seconds)
- Combined analysis with Claude/GPT-4o

**Use when:**
- Video > 2 hours
- Audio is primary content
- Gemini API unavailable

### Phase 3: VS Code Extension Integration

**Files to modify:**
- `vscode-extension/src/commands/analyzeVideo.ts`
- `vscode-extension/src/ui/VideoAnalysisPanel.ts`

**Features:**
- Upload video from workspace
- Show analysis results
- Link timestamps to code locations

### Phase 4: Knowledge Base Integration

**Files to modify:**
- `backend/agents/specialized/research_agent.py`
- `backend/data/knowledge_base/video_index.json`

**Features:**
- Index analyzed videos
- Search by content
- Retrieve relevant video segments

## 💰 Cost Analysis

| Backend | 1 min video | 1 hour video | Use Case |
|---------|-------------|--------------|----------|
| Gemini Native | $0.10 | $6.00 | Primary (bugs, tutorials) |
| Hybrid | $0.25 | $15.00 | Fallback (long meetings) |
| GPT-4o Frames | $1.80 | $108.00 | Not recommended |

## 🎯 Use Cases Priority

### High Priority
1. **Bug Report Videos** - Screen recordings with steps to reproduce
2. **Code Walkthrough** - Understand code flow from videos
3. **Tutorial Indexing** - Extract key concepts from tutorials

### Medium Priority
4. **Meeting Summaries** - Action items from team meetings
5. **UI/UX Review** - Analyze user interaction videos

### Low Priority
6. **Live Streaming** - Real-time video analysis (future: Gemini Multimodal Live API)

## 🚀 Quick Start Implementation

### Step 1: Add Gemini API Key

```bash
# ~/.ki_autoagent/config/.env
GOOGLE_GEMINI_API_KEY=your_api_key_here
```

### Step 2: Install Dependencies

```bash
pip install google-generativeai openai-whisper opencv-python ffmpeg-python
```

### Step 3: Create VideoAgent

```python
# backend/agents/specialized/video_agent.py
from agents.base.base_agent import BaseAgent
import google.generativeai as genai

class VideoAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro-latest")
```

### Step 4: Register Agent

```python
# backend/langgraph_system/workflow.py
from agents.specialized.video_agent import VideoAnalyzerAgent

# In __init__:
self.video_agent = VideoAnalyzerAgent()
```

### Step 5: Add to Orchestrator

```yaml
# backend/config/agent_capabilities.yaml
agents:
  VideoAnalyzerAgent:
    capabilities:
      video_analysis: true
      max_video_duration: 7200  # 2 hours
      supported_formats:
        - mp4
        - mov
        - avi
        - webm
    description: "Analyzes video content using Gemini 2.5 Pro native video understanding"
```

## 📝 Testing Plan

### Unit Tests
- [ ] Video upload to Gemini
- [ ] Frame extraction
- [ ] Audio transcription
- [ ] Hybrid analysis

### Integration Tests
- [ ] Bug report analysis (30s video)
- [ ] Code walkthrough (5min video)
- [ ] Meeting summary (1hr video)

### E2E Tests
- [ ] VS Code extension → VideoAgent
- [ ] Result display in UI
- [ ] Knowledge base indexing

## 🔒 Security Considerations

1. **Video Storage**: Videos uploaded to Gemini API (ephemeral)
2. **Privacy**: Don't upload sensitive videos
3. **File Size Limits**: Max 2GB per video
4. **Rate Limiting**: Gemini API quotas

## 📊 Success Metrics

- **Accuracy**: 90%+ for bug identification
- **Cost**: < $10 per hour of video
- **Speed**: < 30 seconds for 1-minute video
- **User Satisfaction**: 4.5+ stars

## 🗓️ Timeline

- **Week 1-2**: Phase 1 (Gemini Native) - Core implementation
- **Week 3**: Phase 2 (Hybrid Mode) - Fallback system
- **Week 4**: Phase 3 (VS Code Integration) - UI
- **Week 5**: Phase 4 (Knowledge Base) - Indexing
- **Week 6**: Testing & Polish

## 🎓 Learning Resources

- [Gemini Video Understanding Docs](https://ai.google.dev/gemini-api/docs/video-understanding)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [OpenCV Python Tutorial](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

---

**Status**: 📝 Planning Phase
**Version**: 5.9.0
**Owner**: CodeSmith v5.8.2
**Last Updated**: 2025-10-04
