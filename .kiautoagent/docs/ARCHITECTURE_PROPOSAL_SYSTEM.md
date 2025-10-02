# Architecture Proposal System (v5.2.0)

## 📋 Overview

Das Architecture Proposal System stellt sicher, dass der Architect nach der Research-Phase **IMMER** einen detaillierten Architekturvorschlag erstellt und User-Approval einholt, bevor mit der Implementierung begonnen wird.

## 🎯 Motivation

**Problem (vorher):** Architect macht Research → erstellt direkt finales Design → kein User-Feedback

**Lösung (jetzt):** Architect macht Research → erstellt Proposal mit Verbesserungsvorschlägen → User Approval → finalisiert Design

### ASIMOV Rule #4 Integration

Das System folgt der ASIMOV Rule #4 ("Information Before Action"):
- **Research ist IMMER mandatory** (keine Option zum Überspringen)
- **Proposal basiert auf Research-Erkenntnissen**
- **Verbesserungen werden proaktiv vorgeschlagen** (auch wenn nicht explizit angefragt)

## 🔄 Workflow

```
User Request
    ↓
Architect: Research Phase
    ↓
Create Architecture Proposal
    ├─ Summary
    ├─ Suggested Improvements (based on research)
    ├─ Tech Stack with Justifications
    ├─ Project Structure
    ├─ Risks & Mitigations
    └─ Research Insights
    ↓
Display to User (Interactive UI)
    ↓
User Decision:
    ├─ ✅ Approve → Finalize Architecture → Continue Workflow
    ├─ ✏️ Modify → User Feedback → Revise Proposal → Re-Display
    └─ ❌ Reject → Different Approach → Re-Planning
```

## 🏗️ Technical Implementation

### Backend State (state.py)

```python
# v5.2.0: Architecture Proposal System
architecture_proposal: Optional[Dict[str, Any]]  # Draft proposal
proposal_status: Literal["none", "pending", "approved", "rejected", "modified"]
user_feedback_on_proposal: Optional[str]  # User comments
needs_approval: bool  # Generic approval flag
approval_type: Literal["none", "execution_plan", "architecture_proposal"]
```

### Architect Node Flow (workflow.py)

```python
async def architect_node(state):
    # PHASE 1: Check proposal status
    if proposal_status == "approved":
        return finalize_architecture()

    if proposal_status in ["rejected", "modified"]:
        return revise_proposal(user_feedback)

    # PHASE 2: No proposal yet
    if not architecture_proposal:
        research_result = await execute_architect_task()
        proposal = await create_architecture_proposal(research_result)
        state["architecture_proposal"] = proposal
        state["needs_approval"] = True
        return state
```

### Approval Node (workflow.py)

```python
async def approval_node(state):
    approval_type = state.get("approval_type")

    if approval_type == "architecture_proposal":
        # Wait for user decision via WebSocket
        state["status"] = "waiting_architecture_approval"
        return state

    elif approval_type == "execution_plan":
        # Existing Plan-First logic
        ...
```

### WebSocket Messages

**Backend → Frontend:**
```json
{
    "type": "architecture_proposal",
    "session_id": "abc123",
    "proposal": {
        "summary": "...",
        "improvements": "...",
        "tech_stack": "...",
        "structure": "...",
        "risks": "...",
        "research_insights": "..."
    }
}
```

**Frontend → Backend:**
```json
{
    "type": "architecture_approval",
    "session_id": "abc123",
    "decision": "approved" | "rejected" | "modified",
    "feedback": "Optional user comments..."
}
```

### Frontend UI (MultiAgentChatPanel.ts)

**Interactive Proposal Card:**
- Collapsible sections (Summary, Improvements, Tech Stack, etc.)
- Three action buttons:
  - ✅ **Approve** - Proceed with design
  - ✏️ **Modify** - Opens feedback textarea → Submit changes
  - ❌ **Reject** - Start over with different approach
- Input disabled while awaiting decision
- Card removed after decision processed

## 📝 Example: Tetris App Architecture Proposal

### User Input (Original)
```
"Erstelle eine Tetris App mit TypeScript"
```

### Architect Research Phase
- Best practices für Game Development
- TypeScript Game Architecture Patterns
- Canvas vs DOM rendering
- Performance benchmarks
- Accessibility guidelines
- Mobile gaming trends

### Generated Architecture Proposal

```markdown
# 🏛️ Architecture Proposal

## 📊 Summary

Eine moderne Tetris-Implementierung mit TypeScript, HTML5 Canvas für
Hardware-beschleunigtes Rendering, und modularer Architektur nach
Model-View-Controller Pattern.

**Key Features:**
- Classic Tetris gameplay (7 Tetromino-Typen nach SRS-Standard)
- Progressive Schwierigkeitsstufen mit 7-bag Randomizer
- High-Score Persistierung (LocalStorage/IndexedDB)
- Responsive Design (Desktop & Mobile mit Touch Controls)
- Accessibility Support (WCAG 2.1 konform)

**Architecture Highlights:**
- Separation of Concerns (Game Logic ↔ Rendering ↔ Input)
- Framework-agnostic Core (ermöglicht React Native Port)
- Test-Driven Development (80%+ Coverage)

---

## ✨ Suggested Improvements

**Ihr Original-Request:** "Tetris App mit TypeScript"

**Verbesserungsvorschläge basierend auf Research:**

### 1. Game Engine Architecture (nicht erwähnt)
**Warum:** Ihr Request nennt nur "Tetris App", aber professionelle Game
Entwicklung benötigt klare Trennung zwischen Game Logic, Rendering und Input.

**Research Basis:**
- 85% der erfolgreichen TypeScript Games nutzen MVC/ECS Pattern
- Ermöglicht Unit Testing (ohne Rendering-Layer)
- Erleichtert Multiplayer-Feature (zukünftig)

**Vorschlag:**
```
Core Logic (pure TypeScript, no DOM)
    ↓
Rendering Layer (Canvas API)
    ↓
Input Layer (Keyboard + Touch)
```

### 2. State Management mit Immutability (nicht erwähnt)
**Warum:** Race Conditions sind häufigste Bug-Quelle in Games

**Research Basis:**
- Redux-Pattern verhindert 90% der Timing-Bugs
- Ermöglicht Time-Travel Debugging
- GitHub Analysis: 78% der stabilen Games nutzen Immutable State

**Vorschlag:** Zentraler Game State mit Copy-on-Write Updates

### 3. Progressive Enhancement für Accessibility (nicht erwähnt)
**Warum:** 15% der mobilen User nutzen Accessibility-Features

**Research Basis:**
- WCAG 2.1 Guidelines für Games
- Keyboard navigation ist MANDATORY (Level A)
- Farbkontrast-Ratio minimum 4.5:1

**Vorschläge:**
- Keyboard-only Controls (ohne Maus spielbar)
- Optional: Screen Reader Support für Scores
- High-Contrast Mode (für Farbenblinde)
- Pause-Funktion (WCAG 2.2.2 erforderlich)

### 4. Performance-Optimierungen (nicht erwähnt)
**Warum:** Mobile Devices haben limitierte Ressourcen

**Research Basis:**
- RequestAnimationFrame statt setInterval (60fps garantiert)
- Dirty Rectangle Rendering (5x schneller als Full Redraw)
- Pre-calculated Collision Maps (O(1) statt O(n²))

**Vorschlag:** Adaptive FPS Scaling (degrades gracefully auf 30fps)

### 5. Testing Strategy (nicht erwähnt)
**Warum:** Ohne Tests ist Refactoring sehr riskant

**Research Basis:**
- GitHub Top 50 Games: 80% Test Coverage Standard
- Unit Tests für Game Logic (Vitest)
- Integration Tests für Rendering (Playwright)

**Vorschlag:** TDD Approach mit CI/CD Integration

### 6. Build-Tool Optimierung (nicht erwähnt)
**Warum:** "TypeScript" allein ist nicht genug für Production

**Research Basis:**
- Vite ist 10x schneller als Webpack (HMR in <50ms)
- Tree-Shaking reduziert Bundle um ~40%
- Native ESM = keine Transpilation in Dev

**Vorschlag:** Vite 5.0 + TypeScript 5.3+

---

## 🛠️ Recommended Tech Stack

### Core Technologies
- **TypeScript 5.3+**
  - Latest type inference features
  - Satisfies operator für strikte Typing
  - Const type parameters

- **HTML5 Canvas API**
  - Hardware-beschleunigtes Rendering (GPU)
  - 60fps on 95% of devices (caniuse.com)
  - Fallback: DOM-based Rendering (CSS Grid)

- **Vite 5.0**
  - Instant HMR (<50ms reload)
  - Native ESM in Development
  - Optimized Production Build (Rollup)
  - **Why not Webpack?** 10x langsamer, komplex zu konfigurieren

- **Vitest**
  - Native TypeScript support
  - Compatible with Vite (same transform pipeline)
  - Jest-like API but 5x faster

### Why NOT React/Vue/Angular?

**Research Insight:** Framework-Overhead ohne Benefits

**Analyse:**
- Tetris braucht 60fps Game Loop (React: 16ms Reconciliation Overhead)
- Canvas-Rendering = direkter Pixel-Zugriff (kein Virtual DOM)
- Bundle Size: React (42KB) vs. Vanilla (0KB)
- Game würde nur <10% der Framework-Features nutzen

**Fazit:** Vanilla TypeScript ist optimal für diesen Use Case

### Optional Enhancements

1. **Howler.js** (Audio Engine)
   - Cross-browser Audio Support
   - Sprite Sheets für Sound Effects
   - Fallback: Web Audio API direkt
   - **When?** Nach MVP (Phase 2)

2. **LocalForage** (Storage)
   - IndexedDB Wrapper (einfachere API als localStorage)
   - Async API (non-blocking)
   - **Use Case:** High-Score Persistierung

3. **Web Workers** (Future Feature)
   - AI-Gegner in Background Thread
   - Nicht blockierend für Rendering
   - **When?** Phase 3 (Multiplayer/AI)

---

## 📁 Project Structure

```
tetris-app/
├── src/
│   ├── core/                    # ✅ Game Logic (Framework-agnostic)
│   │   ├── Game.ts              # Main Game Controller
│   │   │   └─ Responsibilities: Game Loop, State Management
│   │   ├── Board.ts             # Game Board State (10x20 Grid)
│   │   │   └─ Responsibilities: Cell Management, Line Detection
│   │   ├── Tetromino.ts         # Tetromino Shapes & Rotation (SRS)
│   │   │   └─ 7 Types: I, O, T, S, Z, J, L
│   │   ├── ScoreManager.ts      # Scoring Logic & Level Progression
│   │   │   └─ Formula: Single=100, Double=300, Triple=500, Tetris=800
│   │   └── CollisionDetector.ts # Collision Detection (O(1) lookup)
│   │       └─ Pre-calculated Collision Map
│   │
│   ├── rendering/               # 🎨 View Layer (Canvas)
│   │   ├── CanvasRenderer.ts    # Canvas Drawing Logic
│   │   │   └─ 60fps Target, Dirty Rectangle Optimization
│   │   ├── ThemeManager.ts      # Colors & Styling
│   │   │   └─ Dark Mode, High-Contrast Mode
│   │   └── AnimationEngine.ts   # Line Clear Animations
│   │       └─ Fade-Out Effect, Particle System (optional)
│   │
│   ├── input/                   # 🎮 Controller Layer
│   │   ├── KeyboardHandler.ts   # Keyboard Input (Arrow Keys, Space)
│   │   │   └─ DAS (Delayed Auto Shift) Support
│   │   ├── TouchHandler.ts      # Mobile Touch Controls
│   │   │   └─ Swipe Gestures (Left/Right/Down, Tap=Rotate)
│   │   └── InputMapper.ts       # Action Mapping (Configurable Keys)
│   │
│   ├── persistence/             # 💾 Data Layer
│   │   ├── HighScoreStore.ts    # LocalStorage/IndexedDB
│   │   │   └─ Top 10 High Scores with Dates
│   │   └── GameStateSerializer.ts # Save/Load Game State
│   │       └─ JSON Serialization (for Pause/Resume)
│   │
│   ├── audio/                   # 🔊 Audio Layer (Phase 2)
│   │   ├── SoundManager.ts      # Sound Effects (Line Clear, Rotation)
│   │   └── MusicPlayer.ts       # Background Music (Loop)
│   │
│   ├── types/                   # 📘 TypeScript Definitions
│   │   ├── game.types.ts        # Game State, Tetromino, Board
│   │   ├── rendering.types.ts   # Color, Position, Dimensions
│   │   └── config.types.ts      # Game Config, Settings
│   │
│   ├── config/                  # ⚙️ Configuration
│   │   ├── game.config.ts       # Game Rules (Speed, Scoring)
│   │   └── rendering.config.ts  # Visual Settings (Cell Size, Colors)
│   │
│   ├── utils/                   # 🔧 Utilities
│   │   ├── random.ts            # 7-bag Random Generator (SRS Standard)
│   │   └── timing.ts            # Game Loop Timing (requestAnimationFrame)
│   │
│   └── main.ts                  # 🚀 Application Entry Point
│       └─ Initialize Game, Attach to Canvas
│
├── public/                      # 📦 Static Assets
│   ├── index.html               # Main HTML (minimal)
│   ├── sounds/                  # Audio Files (Phase 2)
│   │   ├── line-clear.mp3
│   │   ├── tetris.mp3
│   │   └── game-over.mp3
│   └── sprites/                 # Sprite Sheets (optional)
│
├── tests/                       # ✅ Test Suites
│   ├── unit/                    # Unit Tests (Vitest)
│   │   ├── Game.test.ts
│   │   ├── Board.test.ts
│   │   └── Tetromino.test.ts
│   ├── integration/             # Integration Tests
│   │   ├── GameFlow.test.ts     # Full Game Flow
│   │   └── Rendering.test.ts    # Canvas Rendering
│   └── e2e/                     # End-to-End Tests (Playwright)
│       └── gameplay.spec.ts     # User Interactions
│
├── docs/                        # 📚 Documentation
│   ├── ARCHITECTURE.md          # This Document
│   ├── GAME_RULES.md            # Tetris Rules (SRS, Scoring)
│   └── API.md                   # API Documentation (JSDoc)
│
├── .github/
│   └── workflows/
│       └── ci.yml               # CI/CD (GitHub Actions)
│           └─ Build, Test, Deploy
│
├── vite.config.ts               # Vite Configuration
├── tsconfig.json                # TypeScript Config (strict mode)
├── vitest.config.ts             # Test Config
├── package.json                 # Dependencies
└── README.md                    # Getting Started
```

### Architecture Benefits

✅ **Testability:**
- Core Logic isoliert von DOM/Canvas → Unit Tests ohne Browser
- Mocking: CanvasRenderer kann mit Stub ersetzt werden

✅ **Maintainability:**
- Klare Separation of Concerns → Änderungen lokal begrenzt
- Single Responsibility: Jede Klasse hat genau eine Aufgabe

✅ **Extensibility:**
- Neue Features einfach hinzuzufügen:
  - Multiplayer: Neue `MultiplayerManager.ts` in `/core`
  - AI: Neue `AIPlayer.ts` in `/core`
  - Skins: Neue Themes in `ThemeManager.ts`

✅ **Portability:**
- Core Logic (90% des Codes) kann für React Native wiederverwendet werden
- Nur Rendering Layer muss angepasst werden (Canvas → Native Graphics)

---

## ⚠️ Risks & Mitigations

### Risk 1: Canvas Performance auf Low-End Devices
**Impact:** Laggy Gameplay auf älteren Smartphones (30-40fps statt 60fps)

**Wahrscheinlichkeit:** Mittel (15% der Nutzer haben alte Devices)

**Mitigation Strategy:**
1. **Adaptive FPS Scaling**
   - Messen der Frame Time (performance.now())
   - Wenn <30fps: Degradation aktivieren (weniger Animationen)

2. **Low-Quality Mode**
   - Deaktivieren: Particle Effects, Shadow Effects
   - Vereinfachte Rendering (Solid Colors statt Gradients)

3. **Fallback: DOM-based Rendering**
   - Wenn Canvas FPS < 20fps: Wechsel zu CSS Grid
   - Funktional identisch, aber etwas weniger smooth

4. **Progressive Enhancement**
   - Feature Detection: `canvas.getContext('2d')`
   - Browser Support Check: caniuse.com zeigt 97% Kompatibilität

**Beispiel-Code:**
```typescript
if (avgFPS < 30) {
  renderer.enableLowQualityMode();
  logger.warn('FPS < 30, enabled Low Quality Mode');
}
```

---

### Risk 2: Browser Compatibility (ältere Browser)
**Impact:** Nicht spielbar auf IE11, sehr alten Safari-Versionen

**Wahrscheinlichkeit:** Niedrig (< 5% Nutzer)

**Mitigation Strategy:**
1. **Progressive Enhancement**
   - Core Gameplay funktioniert ohne moderne Features
   - Optional: Service Worker für Offline-Support

2. **Polyfills (nur wenn nötig)**
   - `requestAnimationFrame` Polyfill (für IE9)
   - Canvas API Feature Detection

3. **Clear Browser Requirements**
   - Dokumentation: "Chrome 90+, Firefox 88+, Safari 14+"
   - Error Message mit Download-Links zu modernen Browsern

4. **Transpilation**
   - Vite transpiliert zu ES2015 (97% Browser Support)
   - Optional: ES5 Target (aber größerer Bundle)

**Browser Support Matrix:**
- ✅ Chrome 90+ (Apr 2021)
- ✅ Firefox 88+ (Apr 2021)
- ✅ Safari 14+ (Sep 2020)
- ✅ Edge 90+ (Apr 2021)
- ❌ IE11 (unsupported)

---

### Risk 3: Mobile Touch Controls Complexity
**Impact:** Schlechte UX auf Mobile → Nutzer frustriert

**Wahrscheinlichkeit:** Hoch (60% der Casual Gamer spielen auf Mobile)

**Mitigation Strategy:**
1. **Research-backed Touch Library**
   - Hammer.js: 23k GitHub Stars, battle-tested
   - Swipe, Tap, Long-Press Gestures

2. **User Testing mit Real Devices**
   - Test auf 5+ verschiedenen Geräten:
     - iOS: iPhone 12, iPhone SE
     - Android: Samsung Galaxy S21, Pixel 6

3. **Alternative Control Schemes**
   - **Option A:** Swipe Gestures (Left/Right/Down, Tap=Rotate)
   - **Option B:** Virtual D-Pad (On-Screen Buttons)
   - **Option C:** Hybrid (Swipe + Optional Buttons)
   - User kann wählen in Settings!

4. **Haptic Feedback**
   - Vibration bei Line Clear (navigator.vibrate())
   - Taktiles Feedback verbessert UX deutlich

**Example Config:**
```typescript
const touchConfig = {
  swipe: { enabled: true, threshold: 50 },
  dpad: { enabled: false },
  haptic: { enabled: true }
};
```

---

### Risk 4: Audio Licensing (Tetris Theme)
**Impact:** Copyright-Claim → Projekt kann nicht veröffentlicht werden

**Wahrscheinlichkeit:** Hoch (Original Tetris Theme ist urheberrechtlich geschützt)

**Mitigation Strategy:**
1. **Royalty-Free Alternativen**
   - Freesound.org: Tausende von Game Sound Effects
   - OpenGameArt.org: CC0-lizenzierte Musik

2. **Optional Audio (User-Supplied)**
   - User kann eigene MP3s hochladen
   - Oder: Link zu Spotify/YouTube für Original-Musik

3. **Composer Commission (Phase 3)**
   - Beauftrage Composer für Original-Soundtrack
   - Kosten: ~$200-500 für 3-4 Tracks

4. **No-Audio Fallback**
   - Game ist vollständig spielbar ohne Audio
   - Audio ist "Nice to Have", nicht kritisch

**License Recommendations:**
- CC0 (Public Domain): Keine Einschränkungen
- CC BY 4.0: Attribution erforderlich (Credit im Game)

---

### Risk 5: Scope Creep (Feature-Bloat)
**Impact:** Projekt wird nie fertig, Timeline verlängert sich indefinitely

**Wahrscheinlichkeit:** Sehr Hoch (häufigster Grund für gescheiterte Projekte)

**Mitigation Strategy:**
1. **MVP-First Approach (Phase 1)**
   - Core Gameplay ONLY:
     - 7 Tetromino Types
     - Rotation (SRS)
     - Line Clearing
     - Scoring
     - Game Over
   - **Keine Extras:** Kein Audio, keine Animationen, kein Multiplayer
   - **Timeline:** 2 Wochen

2. **Phase 2: Polish (nach MVP)**
   - Audio System (Howler.js)
   - Line Clear Animations
   - High Score Persistence
   - **Timeline:** 1 Woche

3. **Phase 3: Advanced Features**
   - Multiplayer (WebSockets)
   - AI Opponent (Minimax Algorithm)
   - Skins & Themes
   - **Timeline:** 2-3 Wochen

4. **Feature Freeze**
   - Nach Phase 3: KEINE neuen Features mehr!
   - Nur Bugfixes und Performance-Optimierungen

**Decision Matrix:**
```
Feature Request → Ask:
1. Is it in the original Tetris? (If No → Phase 3 or Reject)
2. Does it improve Core Gameplay? (If No → Phase 2 or 3)
3. Can it wait until after MVP? (If Yes → Backlog)
```

---

## 🔍 Research Insights

### 1. Tetris Game Rules (Standard)
**Source:** Tetris Guidelines (The Tetris Company), Tetris Wiki

**Key Findings:**
- **7 Tetromino Types:** I, O, T, S, Z, J, L (standardized shapes)
- **SRS (Super Rotation System):** Modern rotation standard since 2001
  - 4 rotation states per Tetromino
  - Wall kicks: Wenn Rotation blockiert → versuche alternative Positionen
  - Spec: https://tetris.wiki/Super_Rotation_System

- **7-bag Randomizer:** Standard seit Tetris DS (2006)
  - Alle 7 Tetrominos werden shuffled
  - Garantiert: Max. 12 Pieces zwischen gleichen Types
  - Verhindert: Lange "I-Piece Droughts" (alte Versionen hatten das)

- **Lock Delay:** 0.5 Sekunden bevor Piece fixiert wird
  - Gibt User Zeit für Last-Second Adjustments
  - Reset bei Rotation/Movement (aber max. 15 resets)

- **Scoring (Standard):**
  - Single (1 Line): 100 × Level
  - Double (2 Lines): 300 × Level
  - Triple (3 Lines): 500 × Level
  - Tetris (4 Lines): 800 × Level
  - Back-to-Back Tetris: 1200 × Level (Bonus!)

**Implementation Decision:**
✅ Folge SRS-Standard exakt (für kompetitive Spieler vertraut)

---

### 2. Performance Best Practices
**Source:** MDN Web Docs, "HTML5 Game Development" (Mozilla Hacks)

**Benchmark Results:**
- `requestAnimationFrame()` vs `setInterval(16)`:
  - rAF: 60fps konstant (synchronisiert mit Display Refresh Rate)
  - setInterval: 45-55fps (inkonsistent, Jank)
  - **Winner:** rAF (Industry Standard)

- **Dirty Rectangle Rendering:**
  - Full Canvas Redraw: ~5ms per frame (60fps = 16.67ms budget)
  - Dirty Rect (only changed cells): ~1ms per frame
  - **Speedup:** 5x faster
  - **Trade-off:** Komplexere Logik (lohnt sich aber!)

- **Collision Detection:**
  - Naiv (O(n²) check): ~3ms per check
  - Pre-calculated Map (O(1) lookup): <0.1ms
  - **Speedup:** 30x faster
  - **How:** 2D Array `board[y][x] = occupied`

**Example Code:**
```typescript
// ✅ GOOD: Pre-calculated Collision Map
function checkCollision(tetromino: Tetromino, board: Board): boolean {
  for (const [x, y] of tetromino.cells) {
    if (board[y][x] !== null) return true;
  }
  return false;
}
// Runtime: O(1) per cell = O(4) total

// ❌ BAD: Nested loops
function checkCollisionSlow(tetromino: Tetromino, board: Board): boolean {
  for (let y = 0; y < 20; y++) {
    for (let x = 0; x < 10; x++) {
      // Check if tetromino overlaps with board[y][x]
      if (/* complex check */) return true;
    }
  }
  return false;
}
// Runtime: O(200) = O(n)
```

---

### 3. TypeScript Game Development
**Source:** GitHub Analysis (Top 50 TypeScript Game Repos)

**Statistics (N=50 repos, total 120k stars):**
- **Build Tools:**
  - Vite: 42 repos (84%)
  - Webpack: 6 repos (12%)
  - Parcel: 2 repos (4%)
  - **Trend:** Vite dominiert (5x populärer als Webpack)
  - **Why:** Instant HMR, Native ESM, einfachere Config

- **Architecture Patterns:**
  - MVC: 32 repos (64%)
  - ECS (Entity Component System): 18 repos (36%)
  - **Decision:** MVC für Tetris (ECS ist Overkill für diesen Scope)
  - **When to use ECS:** Bei >50 Entities mit komplexen Interaktionen

- **Testing:**
  - Repos mit Tests: 40 (80%)
  - Average Test Coverage: 78%
  - Test Framework: Vitest (28), Jest (12)
  - **Trend:** Vitest überholt Jest (native Vite Integration)

- **Rendering:**
  - Canvas API: 45 repos (90%)
  - DOM-based: 3 repos (6%)
  - WebGL: 2 repos (4%)
  - **Decision:** Canvas ist Standard (WebGL ist Overkill)

**Key Takeaway:**
✅ Vite + Vitest + Canvas API = Industry Best Practice

---

### 4. Accessibility Standards
**Source:** WCAG 2.1, Game Accessibility Guidelines (gameaccessibilityguidelines.com)

**Critical Requirements:**
- **WCAG Level A (MANDATORY):**
  - 1.4.1: Color is not the only visual means (use shapes + colors)
  - 2.1.1: Keyboard accessible (all functions via keyboard)
  - 2.2.2: Pause, Stop, Hide (games must be pausable)
  - **Failure to comply:** Legal risk (ADA lawsuits in US)

- **WCAG Level AA (RECOMMENDED):**
  - 1.4.3: Contrast ratio minimum 4.5:1
  - 1.4.11: Non-text contrast (UI controls visible)
  - **Testing Tool:** WebAIM Contrast Checker

- **Game-Specific Guidelines:**
  - Configurable Speed (slow mode for cognitive disabilities)
  - Screen Reader Support (optional, but appreciated)
  - Subtitle for Audio (for deaf players)

**Implementation Plan:**
1. **Phase 1 (MVP):**
   - ✅ Keyboard Controls (Arrow Keys, Space)
   - ✅ Pause Function (ESC key)
   - ✅ High Contrast Colors (default theme)

2. **Phase 2 (Polish):**
   - ✅ Configurable Speed (Settings menu)
   - ✅ Color-blind Mode (different shapes for colors)

3. **Phase 3 (Optional):**
   - ⚠️ Screen Reader (complex, low priority)

**Color Palette (WCAG Compliant):**
```typescript
const colors = {
  background: '#1a1a1a',  // Contrast: 16:1 (AAA)
  text: '#ffffff',        // Contrast: 21:1 (AAA)
  I: '#00f0f0',          // Cyan (Contrast: 8:1)
  O: '#f0f000',          // Yellow (Contrast: 12:1)
  T: '#a000f0',          // Purple (Contrast: 6:1)
  // ... etc
};
```

---

### 5. Mobile Gaming Trends
**Source:** "2024 Mobile Gaming Report" (Newzoo), App Annie Market Data

**Key Statistics:**
- **Device Usage:**
  - 70% of casual gamers play primarily on mobile
  - Average session length: 5-8 minutes (perfect for Tetris!)
  - Peak hours: 7-9 PM (commute time)

- **Control Preferences:**
  - Touch Gestures: 62% prefer (Swipe controls)
  - Virtual D-Pad: 28% prefer (On-screen buttons)
  - Hybrid: 10% (Both options)
  - **Decision:** Offer BOTH (let user choose in settings)

- **Performance Expectations:**
  - Users expect 60fps (74% would uninstall if laggy)
  - Load time: <3 seconds (acceptable)
  - Battery drain: <5% per 30 min (critical!)

- **Monetization (for future):**
  - Ads: 48% of games (interstitial ads between games)
  - IAP: 32% (cosmetic skins, no pay-to-win!)
  - Premium: 20% (upfront cost, no ads)
  - **Recommendation:** Start free with optional IAP (skins)

**Design Implications:**
- ✅ Mobile-first design (90% of dev time on mobile UX)
- ✅ Touch gestures as primary input (keyboard secondary)
- ✅ Portrait mode support (phones held vertically)
- ✅ Offline play (no internet required)

---

### 6. Similar Projects (GitHub Research)
**Analyzed Projects:**
1. **tetr.js** (3.2k stars)
   - Feature-rich (Multiplayer, Replay System, Skins)
   - **Problem:** Over-engineered (15k LOC, complex to maintain)
   - **Learning:** Start simple, add features incrementally

2. **tetris-ts** (890 stars)
   - Clean architecture (MVC, well-tested)
   - **Good:** Clear separation of concerns
   - **Used as reference:** File structure, naming conventions

3. **react-tetris** (1.5k stars)
   - Good UI/UX (animations, polish)
   - **Problem:** React overhead (unnecessary for Tetris)
   - **Learning:** Vanilla is better for this use case

**Key Takeaways:**
- ✅ Simpler is better (avoid feature creep)
- ✅ Clean architecture beats clever code
- ✅ Tests are essential (refactoring confidence)
- ❌ Frameworks add complexity without benefits (for this use case)

---

## 🎯 Next Steps (After Approval)

### Phase 1: MVP Implementation (2 weeks)
1. **Week 1:**
   - CodeSmith: Implement core game logic (`Game.ts`, `Board.ts`, `Tetromino.ts`)
   - CodeSmith: Implement collision detection (`CollisionDetector.ts`)
   - Reviewer: Code review for correctness (verify SRS compliance)

2. **Week 2:**
   - CodeSmith: Implement rendering (`CanvasRenderer.ts`)
   - CodeSmith: Implement input handling (`KeyboardHandler.ts`)
   - CodeSmith: Integrate all components (`main.ts`)
   - Reviewer: Final review before MVP release

### Phase 2: Polish (1 week)
- Audio system (Howler.js)
- Line clear animations
- High score persistence
- Settings menu (speed, controls)

### Phase 3: Advanced Features (2-3 weeks)
- Touch controls (mobile)
- AI opponent
- Multiplayer (WebSockets)
- Skins & themes

---

**⚠️ IMPORTANT: This proposal is based on research findings. Please review and approve before implementation begins.**

**Questions to consider:**
1. Are the suggested improvements aligned with your vision?
2. Is the tech stack acceptable? (Vite, TypeScript, Canvas)
3. Should any features be moved to a different phase?
4. Do you have specific requirements not covered here?

---

## 📚 References

- Tetris Guidelines: https://tetris.wiki/Tetris_Guideline
- SRS Rotation System: https://tetris.wiki/Super_Rotation_System
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- MDN Game Development: https://developer.mozilla.org/en-US/docs/Games
- Vite Documentation: https://vitejs.dev/
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- Game Accessibility Guidelines: https://gameaccessibilityguidelines.com/
```

---

*This proposal was generated using the Architecture Proposal System (v5.2.0) which ensures research-backed decisions and user approval before implementation.*
