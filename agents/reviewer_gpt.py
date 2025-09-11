"""
ReviewerGPT - Code Review and Quality Assurance Agent
Analysiert Code-Qualität und findet Verbesserungen
"""
from typing import Dict, Any, List, Tuple
from .base_agent import BaseAgent

class ReviewerGPT(BaseAgent):
    """
    Code Review Expert mit GPT-4o
    Findet Bugs, Security Issues und Optimierungsmöglichkeiten
    """
    
    def __init__(self):
        super().__init__(
            name="ReviewerGPT",
            role="Code Reviewer",
            model="gpt-4o-mini"  # Efficient for code analysis
        )
        
        self.temperature = 0.1  # Very low for precise analysis
        self.max_tokens = 3000
        
        self.system_prompt = """You are ReviewerGPT, an expert code reviewer and quality assurance specialist.

Your expertise includes:
- Code quality analysis and best practices
- Security vulnerability detection
- Performance optimization
- Design pattern recognition
- Testing coverage assessment
- Dependency analysis
- Code smell detection
- Refactoring suggestions

Review criteria:
1. Correctness: Does the code work as intended?
2. Security: Are there vulnerabilities or risks?
3. Performance: Are there optimization opportunities?
4. Readability: Is the code clear and maintainable?
5. Best Practices: Does it follow language conventions?
6. Testing: Is there adequate test coverage?
7. Documentation: Are comments and docs sufficient?

Provide actionable feedback with:
- Severity levels (Critical, High, Medium, Low)
- Specific line numbers when applicable
- Concrete improvement suggestions
- Example fixes for issues found"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "code_review",
                "bug_detection",
                "security_analysis",
                "performance_review",
                "refactoring",
                "test_coverage",
                "dependency_check"
            ],
            "languages": [
                "python",
                "javascript",
                "typescript",
                "java",
                "go",
                "rust"
            ],
            "review_types": [
                "security",
                "performance",
                "style",
                "architecture",
                "testing"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Führt Code Review durch
        """
        # Build review prompt
        prompt = self._build_review_prompt(task, context)
        
        # Perform review
        review_result = await self._perform_review(prompt, context)
        
        # Analyze and categorize issues
        issues = self._categorize_issues(review_result)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        return {
            "agent": self.name,
            "task": task,
            "output": review_result,
            "issues": issues,
            "recommendations": recommendations,
            "quality_score": self._calculate_quality_score(issues),
            "status": "success"
        }
    
    def _build_review_prompt(self, task: str, context: Dict) -> str:
        """
        Baut spezialisierten Prompt für Code Review
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Review Task: {task}\n")
        
        # Add code to review
        if context.get("code"):
            prompt_parts.append(f"Code to review:\n```python\n{context['code']}\n```\n")
        
        # Add specific review focus
        if context.get("review_focus"):
            prompt_parts.append(f"Focus areas: {context['review_focus']}\n")
        
        # Add context about the project
        if context.get("project_type"):
            prompt_parts.append(f"Project type: {context['project_type']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide a detailed review including:")
        prompt_parts.append("1. Critical issues that must be fixed")
        prompt_parts.append("2. Security vulnerabilities")
        prompt_parts.append("3. Performance improvements")
        prompt_parts.append("4. Code quality suggestions")
        prompt_parts.append("5. Overall assessment and score")
        
        return "\n".join(prompt_parts)
    
    async def _perform_review(self, prompt: str, context: Dict) -> str:
        """
        Führt den Code Review durch
        """
        # Mock implementation for testing
        review = '''## Code Review Report

### Overall Assessment
**Quality Score: 7.5/10**

The code implements a functional momentum trading strategy with good structure and documentation. However, there are several areas for improvement regarding error handling, performance optimization, and security.

### Critical Issues (Must Fix)

#### 1. Insufficient Error Handling in Data Fetching
**Severity: HIGH**
**Location: Lines 241-285**

The `generate_signal` method lacks proper error handling for edge cases:

```python
# Current code
momentum = self.calculate_momentum(data['close'])
current_price = data['close'].iloc[-1]  # Can throw IndexError

# Recommended fix
try:
    if data.empty or 'close' not in data.columns:
        logger.error(f"Invalid data for {symbol}")
        return None
    
    momentum = self.calculate_momentum(data['close'])
    if len(data) == 0:
        return None
    current_price = data['close'].iloc[-1]
except (IndexError, KeyError) as e:
    logger.error(f"Data access error for {symbol}: {e}")
    return None
```

#### 2. Race Condition in Position Tracking
**Severity: HIGH**
**Location: Line 206**

The `self.positions` dictionary is not thread-safe:

```python
# Add thread safety
import threading
self.positions_lock = threading.Lock()

# When accessing positions
with self.positions_lock:
    self.positions[symbol] = new_position
```

### Security Vulnerabilities

#### 1. Unvalidated Input in Position Sizing
**Severity: MEDIUM**
**Location: Lines 287-304**

No validation of capital parameter could lead to negative position sizes:

```python
# Add validation
if capital <= 0:
    raise ValueError(f"Invalid capital amount: {capital}")
if price <= 0:
    raise ValueError(f"Invalid price: {price}")
```

### Performance Optimizations

#### 1. Redundant DataFrame Operations
**Severity: LOW**
**Location: Lines 218-222**

```python
# Current: Multiple passes over data
recent_prices = prices.tail(self.lookback_period)
return (recent_prices.iloc[-1] / recent_prices.iloc[0] - 1)

# Optimized: Single operation
if len(prices) >= self.lookback_period:
    return prices.iloc[-1] / prices.iloc[-self.lookback_period] - 1
return 0.0
```

#### 2. Inefficient Backtest Loop
**Severity: MEDIUM**
**Location: Lines 324-339**

Using DataFrame slicing in loop is inefficient:

```python
# Use vectorized operations where possible
momentum_series = data['close'].rolling(self.lookback_period).apply(
    lambda x: x.iloc[-1] / x.iloc[0] - 1 if len(x) == self.lookback_period else 0
)
```

### Code Quality Improvements

#### 1. Magic Numbers
**Severity: LOW**

Hardcoded values should be constants:

```python
# Define at class level
DEFAULT_LOOKBACK = 20
DEFAULT_THRESHOLD = 0.02
MAX_POSITION_SIZE = 10000
MIN_SHARES = 1
```

#### 2. Incomplete Type Hints
**Severity: LOW**

Some methods lack complete type annotations:

```python
# Add return type hints
def calculate_momentum(self, prices: pd.Series) -> float:
def _calculate_position_size(self, capital: float, price: float) -> int:
```

### Testing Recommendations

1. **Add Unit Tests**: No test coverage detected
   - Test edge cases (empty data, single row)
   - Test momentum calculation accuracy
   - Test position sizing logic

2. **Integration Tests**: Test with real market data
   - Historical data validation
   - Broker connection mocking

3. **Performance Tests**: Benchmark with large datasets

### Best Practices

✅ Good use of dataclasses for TradeSignal
✅ Proper async/await implementation
✅ Clear method separation
✅ Comprehensive docstrings

❌ Missing logging configuration
❌ No configuration validation
❌ Limited exception types
❌ No retry mechanisms

### Recommendations Priority

1. **Immediate**: Fix error handling and thread safety
2. **Short-term**: Add input validation and tests
3. **Long-term**: Optimize performance, add monitoring

### Summary

The code is well-structured but needs critical improvements in error handling and thread safety before production use. The momentum strategy implementation is sound, but robustness and defensive programming practices need enhancement.
'''
        
        return review
    
    def _categorize_issues(self, review_result: str) -> Dict[str, List[Dict]]:
        """
        Kategorisiert gefundene Issues nach Severity
        """
        # Mock categorization
        return {
            "critical": [
                {
                    "title": "Insufficient Error Handling",
                    "severity": "HIGH",
                    "location": "Lines 241-285",
                    "description": "Missing error handling for edge cases"
                },
                {
                    "title": "Race Condition in Position Tracking",
                    "severity": "HIGH",
                    "location": "Line 206",
                    "description": "Thread safety issue with positions dictionary"
                }
            ],
            "security": [
                {
                    "title": "Unvalidated Input",
                    "severity": "MEDIUM",
                    "location": "Lines 287-304",
                    "description": "No validation of capital parameter"
                }
            ],
            "performance": [
                {
                    "title": "Redundant DataFrame Operations",
                    "severity": "LOW",
                    "location": "Lines 218-222",
                    "description": "Multiple passes over data"
                },
                {
                    "title": "Inefficient Backtest Loop",
                    "severity": "MEDIUM",
                    "location": "Lines 324-339",
                    "description": "DataFrame slicing in loop"
                }
            ],
            "quality": [
                {
                    "title": "Magic Numbers",
                    "severity": "LOW",
                    "location": "Multiple",
                    "description": "Hardcoded values should be constants"
                },
                {
                    "title": "Incomplete Type Hints",
                    "severity": "LOW",
                    "location": "Multiple methods",
                    "description": "Missing return type annotations"
                }
            ]
        }
    
    def _generate_recommendations(self, issues: Dict) -> List[str]:
        """
        Generiert priorisierte Empfehlungen
        """
        recommendations = []
        
        # Critical issues first
        if issues.get("critical"):
            recommendations.append("1. IMMEDIATE: Fix critical issues before deployment")
            for issue in issues["critical"]:
                recommendations.append(f"   - {issue['title']}")
        
        # Security next
        if issues.get("security"):
            recommendations.append("2. HIGH PRIORITY: Address security vulnerabilities")
            for issue in issues["security"]:
                recommendations.append(f"   - {issue['title']}")
        
        # Performance
        if issues.get("performance"):
            recommendations.append("3. MEDIUM PRIORITY: Optimize performance")
            for issue in issues["performance"]:
                recommendations.append(f"   - {issue['title']}")
        
        # Quality
        if issues.get("quality"):
            recommendations.append("4. LOW PRIORITY: Improve code quality")
            for issue in issues["quality"]:
                recommendations.append(f"   - {issue['title']}")
        
        return recommendations
    
    def _calculate_quality_score(self, issues: Dict) -> float:
        """
        Berechnet Quality Score basierend auf Issues
        """
        base_score = 10.0
        
        # Deduct points based on severity
        deductions = {
            "critical": 1.0,
            "security": 0.7,
            "performance": 0.3,
            "quality": 0.1
        }
        
        for category, issue_list in issues.items():
            if category in deductions:
                base_score -= len(issue_list) * deductions[category]
        
        return max(0, min(10, base_score))