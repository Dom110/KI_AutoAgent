# Build Validation System Guide

**Extracted from:** CLAUDE.md
**Date:** 2025-10-13
**Version:** v6.0+

---

## 🏗️ BUILD VALIDATION SYSTEM (v6.0+)

### **Comprehensive Multi-Language Build Validation**

**Implemented:** 2025-10-12 (v6.0.0)

The build validation system automatically runs appropriate build/lint checks after code generation to ensure generated code actually compiles/runs.

---

## 📋 Supported Validation Types

### 1. TypeScript Compilation Check (Quality Threshold: 0.90)
- **Tool:** `tsc --noEmit`
- **Detects:** `.ts`, `.tsx` files
- **Requirements:** `tsconfig.json` and `package.json` in workspace
- **Timeout:** 60 seconds
- **Errors → Quality Score:** 0.50 (forces iteration)

**Example Output:**
```
📘 Project Type: TypeScript
   Quality Threshold: 0.90 (highest)
🔬 Running TypeScript compilation check (tsc --noEmit)...
✅ TypeScript compilation passed! (0.8s)
✅ Build validation PASSED
```

### 2. Python Type Checking (Quality Threshold: 0.85)
- **Tool:** `python3 -m mypy`
- **Detects:** `.py` files
- **Flags:** `--ignore-missing-imports`, `--no-strict-optional`
- **Timeout:** 60 seconds
- **Graceful Degradation:** Warns if mypy not installed

**Example Output:**
```
🐍 Project Type: Python
   Quality Threshold: 0.85
🔬 Running Python mypy type check (5 files)...
✅ Python mypy type check passed!
✅ Build validation PASSED
```

### 3. JavaScript Linting (Quality Threshold: 0.75)
- **Tool:** `npx eslint`
- **Detects:** `.js`, `.jsx` files (excluding `.ts`/`.tsx`)
- **Timeout:** 60 seconds
- **Return Codes:** 0 = success, 1 = lint errors, 2 = fatal error
- **Graceful Degradation:** Continues on configuration issues

**Example Output:**
```
📙 Project Type: JavaScript
   Quality Threshold: 0.75
🔬 Running JavaScript ESLint check (3 files)...
✅ JavaScript ESLint check passed!
✅ Build validation PASSED
```

---

## 🎯 Polyglot Project Support

**NEW in v6.0.0:** Multiple validation checks run for mixed-language projects!

Changed from `elif` to `if` to support projects with multiple languages:

```python
# ✅ NOW: Multiple checks for polyglot projects
if has_typescript:
    # TypeScript check runs
if has_python:
    # Python check ALSO runs (if .py files exist)
if has_javascript:
    # JavaScript check ALSO runs (if .js files exist)
```

**Example:** TypeScript frontend + Python backend → BOTH checks run!

---

## 📊 Quality Score Management

When build validation **FAILS:**

1. **Original Quality Score Preserved** - Logged for debugging
2. **Quality Score Reduced to 0.50** - Forces another ReviewFix iteration
3. **Build Errors Appended to Feedback** - Fixer knows what to fix

**Example:**
```
⚠️  Build validation FAILED - reducing quality score to 0.50
   Original quality score: 0.82
   New quality score: 0.50

## BUILD VALIDATION ERRORS

**typescript_compilation:**
```
src/app.tsx(15,7): error TS2322: Type 'string' is not assignable to type 'number'.
src/utils.ts(23,12): error TS2304: Cannot find name 'process'.
```
```

---

## 🔧 Implementation Location

**File:** `backend/subgraphs/reviewfix_subgraph_v6_1.py`

Build validation runs **AFTER** GPT-4o-mini code review, **BEFORE** storing review in memory.

```python
async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
    # 1. Read generated files
    # 2. GPT-4o-mini review (quality score)
    # 3. BUILD VALIDATION (this is where it runs)
    # 4. Adjust quality score if build fails
    # 5. Store review in memory
    # 6. Return state
```

---

## 🛡️ Error Handling

All validation checks handle errors gracefully:

```python
try:
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        cwd=workspace_path,
        capture_output=True,
        text=True,
        timeout=60
    )
    # Check result...
except subprocess.TimeoutExpired:
    logger.error("❌ TypeScript compilation timeout (60s)")
    build_validation_passed = False
except FileNotFoundError:
    logger.warning("⚠️  Tool not installed - skipping check")
except Exception as e:
    logger.error(f"❌ Check failed: {e}")
    build_validation_passed = False
```

---

## 📦 Installation Requirements

### TypeScript Projects:
```bash
npm install -D typescript  # tsc must be available
```

### Python Projects:
```bash
pip install mypy  # Optional but recommended
```

### JavaScript Projects:
```bash
npm install -D eslint  # Optional but recommended
```

---

## ⚙️ Configuration

No configuration needed! System automatically:
1. Detects project type from generated files
2. Checks for required tools (tsconfig.json, mypy, eslint)
3. Runs appropriate validation
4. Skips validation if tool not available (with warning)

---

## ⚡ Performance

- **TypeScript Check:** 0.8s (fast!)
- **Python Check:** 1-2s (depending on file count)
- **JavaScript Check:** 1-2s (depending on file count)
- **Total Overhead:** 1-5s (minimal impact on overall workflow)

---

## 🔮 Future Enhancements

Potential improvements (not yet implemented):

1. **True Parallel Execution** - Run all checks with `asyncio.gather()`
2. **Go Validation** - `go build` or `go vet`
3. **Rust Validation** - `cargo check`
4. **Java Validation** - `javac` or Maven/Gradle
5. **Custom Validation** - User-defined validation scripts

Currently uses sequential execution but supports multiple checks for polyglot projects.

See: `V6.1_ROADMAP.md` for planned enhancements.

---

## 🐛 Debugging Build Validation

### Check if validation ran:
```bash
grep "Running.*compilation check" /tmp/v6_server.log
```

### Check validation results:
```bash
grep "Build validation" /tmp/v6_server.log
```

### Check project type detection:
```bash
grep "Project Type:" /tmp/v6_server.log
```

### View build errors:
```bash
grep -A 10 "BUILD VALIDATION ERRORS" /tmp/v6_server.log
```

---

## ⚠️ Known Issues

- **Python mypy validation** - ✅ IMPLEMENTED (v6.0.0)
- **JavaScript ESLint validation** - ✅ IMPLEMENTED (v6.0.0)
- **Parallel validation** - ⏳ Polyglot support added, true async TBD
- **Go/Rust/Java validation** - ⏳ Planned (see V6.1_ROADMAP.md)

---

## ✅ Best Practices

1. **Always install build tools** - TypeScript projects need `tsconfig.json`
2. **Check logs for validation results** - Build validation runs silently
3. **Quality score 0.50** - Indicates build failure, fixer will iterate
4. **Graceful degradation** - Missing tools warn but don't fail workflow

### Example Workflow:

```
Codesmith generates files → ReviewFix reviewer analyzes code
                         ↓
                    Quality score: 0.85
                         ↓
                 BUILD VALIDATION RUNS
                         ↓
            TypeScript: tsc --noEmit
                         ↓
                 ❌ 3 compilation errors!
                         ↓
        Quality score reduced to 0.50
                         ↓
           Build errors appended to feedback
                         ↓
    Fixer iterates with compilation errors
                         ↓
            Files fixed, validation passes
                         ↓
                 ✅ Quality maintained: 0.85
```

---

## 📊 Validation Quality Thresholds

| Language | Threshold | Reason |
|----------|-----------|--------|
| TypeScript | 0.90 | Highest - type safety critical |
| Python | 0.85 | High - type hints important |
| JavaScript | 0.75 | Medium - linting for style |
| Go | 0.85 | High - compilation critical |
| Rust | 0.85 | High - compilation critical |
| Java | 0.80 | High - compilation critical |

**If build fails:** Quality score → 0.50 (forces iteration regardless of original score)

---

## 🎯 Integration with Review-Fix Loop

Build validation is part of the Review-Fix iteration loop:

```
Iteration 1: Code generated, quality 0.75, BUILD PASS → Store in memory
Iteration 2: Code improved, quality 0.88, BUILD FAIL → Reduce to 0.50, iterate
Iteration 3: Errors fixed, quality 0.82, BUILD PASS → Store in memory ✅
```

Maximum iterations: 3 (controlled by ReviewFix system)

---

**Last Updated:** 2025-10-13
**See Also:** CLAUDE_CLI_INTEGRATION.md, E2E_TESTING_GUIDE.md
**Reference:** V6.1_ROADMAP.md (Extended Language Support)
