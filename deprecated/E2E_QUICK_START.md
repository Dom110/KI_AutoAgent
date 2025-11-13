# ⚡ E2E Test Generator - Quick Start (5 Minutes)

**Status:** Ready to use  
**Platform:** Python 3.13+ / Playwright  
**Time Estimate:** 5 minutes  

---

## 🚀 QUICK START IN 5 STEPS

### Step 1: Verify Installation (1 min)

```bash
# Check Python
python --version  # Should be 3.13+

# Go to project root
cd /Users/dominikfoert/git/KI_AutoAgent

# Install E2E dependencies
pip install playwright
npx playwright install
```

### Step 2: Create Sample React App (1 min)

```bash
# Create a test app
npx create-react-app test-app
cd test-app

# Add data-testid to components
# (Important for E2E testing!)
```

### Step 3: Analyze App (1 min)

```python
from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer

analyzer = ReactComponentAnalyzer("/path/to/test-app")
analysis = analyzer.analyze_app()

print(f"Found {analysis['total_components']} components")
```

### Step 4: Generate Tests (1 min)

```python
from backend.e2e_testing.test_generator import E2ETestGenerator

generator = E2ETestGenerator("/path/to/test-app")
result = generator.analyze_and_generate()

print(f"Generated {result['scenarios']} test scenarios")

# Write tests to disk
generator.write_test_files("/path/to/test-app/tests/e2e")
```

### Step 5: Run Tests (1 min)

```python
import asyncio
from backend.e2e_testing.test_executor import PlaywrightTestExecutor

async def run():
    executor = PlaywrightTestExecutor("/path/to/test-app/tests/e2e")
    result = await executor.run_all_tests()
    print(f"Tests passed: {result['passed_tests']}/{result['total_tests']}")

asyncio.run(run())
```

---

## ✅ QUICK VALIDATION

### Check 1: Can I import the modules?

```python
from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer
from backend.e2e_testing.test_generator import E2ETestGenerator
from backend.e2e_testing.browser_engine import BrowserEngine
from backend.e2e_testing.test_executor import PlaywrightTestExecutor
print("✅ All imports successful")
```

### Check 2: Can I analyze a React app?

```python
analyzer = ReactComponentAnalyzer("./test-app")
analysis = analyzer.analyze_app()
if analysis['total_components'] > 0:
    print(f"✅ Found {analysis['total_components']} components")
else:
    print("⚠️  No components found - check app structure")
```

### Check 3: Can I generate tests?

```python
generator = E2ETestGenerator("./test-app")
result = generator.analyze_and_generate()
if result['scenarios'] > 0:
    print(f"✅ Generated {result['scenarios']} tests")
else:
    print("⚠️  No tests generated - check components")
```

---

## 📊 ONE-LINER EXAMPLES

### Analyze React App

```python
from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer; analyzer = ReactComponentAnalyzer("./app"); print(analyzer.analyze_app())
```

### Generate and Export Tests

```python
from backend.e2e_testing.test_generator import E2ETestGenerator; gen = E2ETestGenerator("./app"); gen.analyze_and_generate(); gen.write_test_files("./tests/e2e")
```

### Get Statistics

```python
from backend.e2e_testing.test_generator import E2ETestGenerator; gen = E2ETestGenerator("./app"); gen.analyze_and_generate(); print(gen.get_statistics())
```

---

## 🎯 COMMON TASKS

### Find Components with Forms

```python
analyzer = ReactComponentAnalyzer("./app")
analyzer.analyze_app()

form_components = analyzer.get_components_with_forms()
for comp in form_components:
    print(f"✓ {comp.name}: {len(comp.form_fields)} form fields")
```

### Find Components with API Calls

```python
analyzer = ReactComponentAnalyzer("./app")
analyzer.analyze_app()

api_components = analyzer.get_components_with_api_calls()
for comp in api_components:
    print(f"✓ {comp.name}: {len(comp.api_calls)} API calls")
```

### Get Test Scenarios by Type

```python
gen = E2ETestGenerator("./app")
gen.analyze_and_generate()

happy_path = [s for s in gen.scenarios if s.scenario_type == 'happy_path']
error_cases = [s for s in gen.scenarios if s.scenario_type == 'error_case']
edge_cases = [s for s in gen.scenarios if s.scenario_type == 'edge_case']

print(f"Happy Path: {len(happy_path)}")
print(f"Error Cases: {len(error_cases)}")
print(f"Edge Cases: {len(edge_cases)}")
```

### Export Test Scenarios to JSON

```python
gen = E2ETestGenerator("./app")
gen.analyze_and_generate()
gen.export_scenarios("./scenarios.json")
```

---

## 🔧 TROUBLESHOOTING QUICK FIXES

| Problem | Quick Fix |
|---------|-----------|
| "No components found" | Add React imports to your files: `import React from 'react'` |
| "No test IDs found" | Add `data-testid` to your components: `<input data-testid="name" />` |
| "Module not found" | Install: `pip install playwright` |
| "Playwright not found" | Install browsers: `npx playwright install` |
| "Tests timeout" | Increase timeout: `PlaywrightTestExecutor(..., config={'timeout': 60000})` |

---

## 🧪 MINIMAL TEST EXAMPLE

**File: test_minimal.py**

```python
#!/usr/bin/env python3
"""Minimal E2E test generator example"""

import asyncio
from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer
from backend.e2e_testing.test_generator import E2ETestGenerator

async def main():
    app_path = "./test-app"  # Change to your app path
    
    print("📊 Analyzing React app...")
    analyzer = ReactComponentAnalyzer(app_path)
    analysis = analyzer.analyze_app()
    print(f"✅ Found {analysis['total_components']} components")
    
    print("\n📝 Generating tests...")
    generator = E2ETestGenerator(app_path)
    result = generator.analyze_and_generate()
    print(f"✅ Generated {result['scenarios']} test scenarios")
    
    print("\n📂 Writing test files...")
    generator.write_test_files(f"{app_path}/tests/e2e")
    print(f"✅ Wrote {len(result['test_files'])} test files")
    
    print("\n📊 Statistics:")
    stats = generator.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**

```bash
python test_minimal.py
```

---

## 📋 REVIEWFIX INTEGRATION QUICK TEST

```python
import asyncio
from backend.agents.reviewfix_e2e_agent import ReviewFixE2EAgent

async def test_reviewfix():
    agent = ReviewFixE2EAgent("/path/to/workspace")
    
    result = await agent.review_generated_code(
        generated_files=[],
        app_type='react'
    )
    
    summary = agent.get_review_summary()
    print(f"Status: {summary['status']}")
    print(f"Severity: {summary['severity']}")
    
    if summary['recommendations']:
        print("\nRecommendations:")
        for rec in summary['recommendations']:
            print(f"  • {rec}")

asyncio.run(test_reviewfix())
```

---

## 🎯 NEXT STEPS

1. **Add data-testid to React components** - Essential for E2E testing
2. **Run on your app** - Test with your own React project
3. **Integrate with ReviewFix** - Use in the full workflow
4. **Monitor results** - Track test success rates

---

## 📞 HELP

### View Component Analysis

```python
analyzer = ReactComponentAnalyzer("./app")
analyzer.analyze_app()

for name, comp in analyzer.components.items():
    print(f"\n{name}:")
    print(f"  Type: {comp.type}")
    print(f"  Props: {comp.props}")
    print(f"  State: {comp.state_vars}")
    print(f"  Hooks: {comp.hooks}")
    print(f"  Test IDs: {comp.test_ids}")
```

### View Generated Test Code

```python
gen = E2ETestGenerator("./app")
gen.analyze_and_generate()

for filename, code in gen.test_files.items():
    print(f"\n=== {filename} ===")
    print(code[:500])  # First 500 chars
    print("...")
```

### View Test Scenarios

```python
gen = E2ETestGenerator("./app")
gen.analyze_and_generate()

for scenario in gen.scenarios[:5]:  # First 5
    print(f"\n{scenario.title}")
    print(f"  Type: {scenario.scenario_type}")
    print(f"  Component: {scenario.component_name}")
```

---

## ✨ YOU'RE ALL SET!

Everything is installed and ready. Now:

1. **Pick your React app** → Change app_path in examples
2. **Add data-testid** → To interactive elements  
3. **Run the generator** → Generate tests
4. **Check results** → Review generated test files
5. **Integrate with ReviewFix** → Use in workflow

---

**Ready to go! 🚀**

For full documentation, see: `E2E_TEST_GENERATOR_COMPLETE_GUIDE.md`