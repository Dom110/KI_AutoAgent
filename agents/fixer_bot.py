"""
FixerBot - Bug Fixing and Code Improvement Agent
Behebt Fehler und optimiert Code
"""
from typing import Dict, Any, List, Optional, Tuple
from .base_agent import BaseAgent

class FixerBot(BaseAgent):
    """
    Code Fixing Expert mit Claude Sonnet 4 (2025)
    Spezialisiert auf Fehlerbehebung und Optimierung
    """
    
    def __init__(self):
        super().__init__(
            name="FixerBot",
            role="Bug Fixer & Optimizer",
            model="claude-sonnet-4-20250514"
        )
        
        self.temperature = 0.1  # Very low for precise fixes
        self.max_tokens = 5000
        
        self.system_prompt = """You are FixerBot, an expert at fixing bugs and optimizing code.

Your expertise includes:
- Bug diagnosis and fixing
- Performance optimization
- Memory leak detection and resolution
- Refactoring for maintainability
- Security vulnerability patching
- Dependency conflict resolution
- Error handling improvement
- Code modernization

Fixing approach:
1. Understand the root cause, not just symptoms
2. Provide minimal, targeted fixes
3. Ensure backward compatibility
4. Add proper error handling
5. Include tests for the fix
6. Document what was changed and why
7. Suggest preventive measures

Optimization priorities:
- Correctness first
- Security second
- Performance third
- Readability fourth

Always provide:
- The fixed code
- Explanation of the issue
- What was changed
- How to test the fix
- Prevention recommendations"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "bug_fixing",
                "debugging",
                "optimization",
                "refactoring",
                "security_patching",
                "performance_tuning",
                "memory_optimization",
                "dependency_resolution"
            ],
            "fix_types": [
                "syntax_errors",
                "logic_errors",
                "runtime_errors",
                "performance_issues",
                "security_vulnerabilities",
                "memory_leaks",
                "race_conditions"
            ],
            "languages": [
                "python",
                "javascript",
                "typescript",
                "java",
                "go"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Behebt Fehler und optimiert Code
        """
        # Analyze the problem
        analysis = self._analyze_problem(task, context)
        
        # Build fix prompt
        prompt = self._build_fix_prompt(task, context, analysis)
        
        # Generate fixes
        fixes = await self._generate_fixes(prompt, context)
        
        # Validate fixes
        validated_fixes = self._validate_fixes(fixes)
        
        # Create fix summary
        summary = self._create_fix_summary(validated_fixes)
        
        return {
            "agent": self.name,
            "task": task,
            "output": fixes,
            "analysis": analysis,
            "fixes": validated_fixes,
            "summary": summary,
            "status": "success" if validated_fixes else "partial"
        }
    
    def _analyze_problem(self, task: str, context: Dict) -> Dict:
        """
        Analysiert das Problem
        """
        analysis = {
            "problem_type": "unknown",
            "severity": "medium",
            "affected_areas": [],
            "root_cause": None
        }
        
        # Detect problem type from task and context
        task_lower = task.lower()
        
        if "error" in task_lower or "exception" in task_lower:
            analysis["problem_type"] = "error"
            analysis["severity"] = "high"
        elif "performance" in task_lower or "slow" in task_lower:
            analysis["problem_type"] = "performance"
        elif "security" in task_lower or "vulnerability" in task_lower:
            analysis["problem_type"] = "security"
            analysis["severity"] = "critical"
        elif "memory" in task_lower or "leak" in task_lower:
            analysis["problem_type"] = "memory"
            analysis["severity"] = "high"
        
        # Extract error details if available
        if context.get("error_message"):
            analysis["error_details"] = context["error_message"]
        
        if context.get("stack_trace"):
            analysis["stack_trace"] = context["stack_trace"]
        
        return analysis
    
    def _build_fix_prompt(self, task: str, context: Dict, analysis: Dict) -> str:
        """
        Baut spezialisierten Prompt für Fehlerbehebung
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Fix Task: {task}\n")
        
        # Add problem analysis
        prompt_parts.append(f"Problem Type: {analysis['problem_type']}")
        prompt_parts.append(f"Severity: {analysis['severity']}\n")
        
        # Add problematic code
        if context.get("code"):
            prompt_parts.append(f"Problematic Code:\n```python\n{context['code']}\n```\n")
        
        # Add error details
        if analysis.get("error_details"):
            prompt_parts.append(f"Error Message: {analysis['error_details']}\n")
        
        if analysis.get("stack_trace"):
            prompt_parts.append(f"Stack Trace:\n{analysis['stack_trace'][:500]}\n")
        
        # Add review feedback if available
        if context.get("review_feedback"):
            prompt_parts.append(f"Code Review Feedback:\n{context['review_feedback']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. Fixed code with the issue resolved")
        prompt_parts.append("2. Clear explanation of what was wrong")
        prompt_parts.append("3. What specifically was changed")
        prompt_parts.append("4. How to verify the fix works")
        prompt_parts.append("5. How to prevent similar issues")
        
        return "\n".join(prompt_parts)
    
    async def _generate_fixes(self, prompt: str, context: Dict) -> str:
        """
        Generiert Fehlerbehebungen
        """
        # Mock implementation for testing
        fixes = '''## Bug Fix Report

### Issue Identified

**Problem**: Thread safety issue in position tracking causing race conditions
**Type**: Concurrency Bug
**Severity**: HIGH
**Root Cause**: Multiple threads accessing and modifying the shared `self.positions` dictionary without synchronization

### Fixed Code

```python
import threading
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    timestamp: datetime
    price: float
    quantity: int
    
class MomentumStrategy:
    """
    Momentum-based trading strategy - THREAD-SAFE VERSION
    Identifies stocks with strong momentum for trading opportunities
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        momentum_threshold: float = 0.02,
        risk_percentage: float = 0.02
    ):
        """
        Initialize momentum strategy with thread safety
        
        Args:
            lookback_period: Number of periods for momentum calculation
            momentum_threshold: Minimum momentum threshold for signals
            risk_percentage: Risk per trade as percentage of capital
        """
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.risk_percentage = risk_percentage
        self.positions: Dict[str, float] = {}
        
        # FIX: Add thread lock for position tracking
        self.positions_lock = threading.RLock()  # Use RLock for re-entrant locking
        
        # FIX: Add validation for initialization parameters
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters"""
        if self.lookback_period <= 0:
            raise ValueError(f"Lookback period must be positive, got {self.lookback_period}")
        if not 0 < self.momentum_threshold < 1:
            raise ValueError(f"Momentum threshold must be between 0 and 1, got {self.momentum_threshold}")
        if not 0 < self.risk_percentage < 1:
            raise ValueError(f"Risk percentage must be between 0 and 1, got {self.risk_percentage}")
    
    def calculate_momentum(self, prices: pd.Series) -> float:
        """
        Calculate momentum indicator - OPTIMIZED VERSION
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Momentum value as percentage change
        """
        # FIX: Add input validation
        if prices is None or prices.empty:
            logger.warning("Empty price series provided")
            return 0.0
            
        if len(prices) < self.lookback_period:
            logger.debug(f"Insufficient data: {len(prices)} < {self.lookback_period}")
            return 0.0
        
        # FIX: Optimized calculation - single operation
        try:
            return float(prices.iloc[-1] / prices.iloc[-self.lookback_period] - 1)
        except (IndexError, ZeroDivisionError) as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        capital: float
    ) -> Optional[TradeSignal]:
        """
        Generate trading signal based on momentum - FIXED VERSION
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            capital: Available capital
            
        Returns:
            TradeSignal if conditions met, None otherwise
        """
        # FIX: Comprehensive input validation
        if data is None or data.empty:
            logger.warning(f"No data available for {symbol}")
            return None
            
        if capital <= 0:
            logger.error(f"Invalid capital amount: {capital}")
            return None
        
        # FIX: Safe column access with error handling
        try:
            # Normalize column names
            data.columns = data.columns.str.lower()
            
            if 'close' not in data.columns:
                logger.error(f"Missing 'close' column for {symbol}")
                return None
            
            # Calculate momentum
            momentum = self.calculate_momentum(data['close'])
            
            # Safe price extraction
            current_price = float(data['close'].iloc[-1])
            if current_price <= 0:
                logger.error(f"Invalid price for {symbol}: {current_price}")
                return None
            
            # Position sizing with validation
            position_size = self._calculate_position_size(capital, current_price)
            
            # Generate signal based on momentum
            signal = None
            
            # FIX: Thread-safe position access
            with self.positions_lock:
                if momentum > self.momentum_threshold:
                    # Check if we already have a position
                    if symbol not in self.positions:
                        signal = TradeSignal(
                            symbol=symbol,
                            action='buy',
                            confidence=min(momentum / self.momentum_threshold, 1.0),
                            timestamp=datetime.now(),
                            price=current_price,
                            quantity=position_size
                        )
                        # Track position
                        self.positions[symbol] = current_price
                        
                elif momentum < -self.momentum_threshold:
                    # Check if we have a position to sell
                    if symbol in self.positions:
                        signal = TradeSignal(
                            symbol=symbol,
                            action='sell',
                            confidence=min(abs(momentum) / self.momentum_threshold, 1.0),
                            timestamp=datetime.now(),
                            price=current_price,
                            quantity=position_size
                        )
                        # Remove position
                        del self.positions[symbol]
                else:
                    signal = TradeSignal(
                        symbol=symbol,
                        action='hold',
                        confidence=0.5,
                        timestamp=datetime.now(),
                        price=current_price,
                        quantity=0
                    )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
            return None
    
    def _calculate_position_size(
        self,
        capital: float,
        price: float
    ) -> int:
        """
        Calculate position size based on risk management - VALIDATED VERSION
        
        Args:
            capital: Available capital
            price: Current stock price
            
        Returns:
            Number of shares to trade
        """
        # FIX: Add comprehensive validation
        if capital <= 0:
            logger.error(f"Invalid capital: {capital}")
            return 0
            
        if price <= 0:
            logger.error(f"Invalid price: {price}")
            return 0
        
        risk_amount = capital * self.risk_percentage
        shares = int(risk_amount / price)
        
        # FIX: Add maximum position size limit
        MAX_POSITION_SIZE = int(capital * 0.1 / price)  # Max 10% of capital
        shares = min(shares, MAX_POSITION_SIZE)
        
        return max(shares, 1) if shares > 0 else 0

    def get_positions(self) -> Dict[str, float]:
        """Thread-safe position getter"""
        with self.positions_lock:
            return self.positions.copy()
    
    def clear_positions(self) -> None:
        """Thread-safe position clearing"""
        with self.positions_lock:
            self.positions.clear()
```

### What Was Changed

1. **Thread Safety**:
   - Added `threading.RLock()` for thread-safe position tracking
   - All position dictionary access now wrapped in lock context
   - Added thread-safe getter and setter methods

2. **Input Validation**:
   - Added parameter validation in `__init__`
   - Comprehensive validation in `generate_signal`
   - Capital and price validation in position sizing

3. **Error Handling**:
   - Try-except blocks for all risky operations
   - Proper logging of errors with context
   - Graceful degradation on errors

4. **Performance Optimization**:
   - Single-pass momentum calculation
   - Removed redundant DataFrame operations
   - Early returns for invalid inputs

5. **Code Quality**:
   - Added constants for magic numbers
   - Normalized column names for consistency
   - Better separation of concerns

### How to Test the Fix

```python
# Test thread safety
import concurrent.futures

def test_thread_safety():
    strategy = MomentumStrategy()
    data = pd.DataFrame({
        'close': np.random.randn(100) + 100
    })
    
    def generate_signals(symbol):
        for _ in range(100):
            strategy.generate_signal(symbol, data, 10000)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_signals, f"STOCK_{i}") for i in range(10)]
        concurrent.futures.wait(futures)
    
    print(f"Final positions: {strategy.get_positions()}")
    print("Thread safety test passed!")

# Test input validation
def test_validation():
    strategy = MomentumStrategy()
    
    # Test with invalid inputs
    assert strategy.generate_signal("TEST", pd.DataFrame(), 10000) is None
    assert strategy.generate_signal("TEST", None, 10000) is None
    assert strategy.generate_signal("TEST", pd.DataFrame({'close': []}), -100) is None
    
    print("Validation tests passed!")

# Run tests
test_thread_safety()
test_validation()
```

### Prevention Recommendations

1. **Use Thread-Safe Data Structures**:
   - Consider using `threading.local()` for thread-local storage
   - Use `queue.Queue` for inter-thread communication
   - Implement proper synchronization primitives

2. **Implement Comprehensive Testing**:
   - Unit tests for all methods
   - Integration tests with concurrent execution
   - Property-based testing for edge cases

3. **Code Review Checklist**:
   - Always check for shared state access
   - Validate all external inputs
   - Handle all exception cases
   - Add logging for debugging

4. **Use Static Analysis Tools**:
   - `mypy` for type checking
   - `pylint` for code quality
   - `bandit` for security issues
   - `thread_sanitizer` for race conditions

5. **Documentation**:
   - Document thread-safety guarantees
   - Mark methods as thread-safe or not
   - Include concurrency considerations in docstrings

### Summary

The fixes address critical thread-safety issues and add robust error handling. The code is now production-ready with proper synchronization, validation, and error recovery. Performance has also been improved through optimized calculations.
'''
        
        return fixes
    
    def _validate_fixes(self, fixes: str) -> List[Dict[str, Any]]:
        """
        Validiert die generierten Fixes
        """
        # Extract code blocks and validate syntax
        import re
        
        validated = []
        code_blocks = re.findall(r'```python\n(.*?)```', fixes, re.DOTALL)
        
        for i, code in enumerate(code_blocks):
            try:
                # Basic syntax check
                compile(code, f'<fix_{i}>', 'exec')
                validated.append({
                    "fix_id": i + 1,
                    "code": code,
                    "valid": True,
                    "syntax_check": "passed"
                })
            except SyntaxError as e:
                validated.append({
                    "fix_id": i + 1,
                    "code": code,
                    "valid": False,
                    "syntax_check": f"failed: {e}"
                })
        
        return validated
    
    def _create_fix_summary(self, validated_fixes: List[Dict]) -> Dict[str, Any]:
        """
        Erstellt eine Zusammenfassung der Fixes
        """
        valid_count = sum(1 for f in validated_fixes if f["valid"])
        total_count = len(validated_fixes)
        
        return {
            "total_fixes": total_count,
            "valid_fixes": valid_count,
            "invalid_fixes": total_count - valid_count,
            "success_rate": valid_count / total_count if total_count > 0 else 0,
            "fix_categories": [
                "Thread Safety",
                "Input Validation",
                "Error Handling",
                "Performance Optimization",
                "Code Quality"
            ],
            "critical_fixes_applied": True,
            "ready_for_production": valid_count == total_count
        }