"""
RON Strategy Quality Gate
Specialized quality validation for RON strategy implementation
"""

import re
import time
from typing import Dict, List, Any, Optional
from .base_quality_gate import BaseQualityGate, QualityCheck, QualityGateResult, QualityLevel


class RONStrategyQualityGate(BaseQualityGate):
    """
    Specialized quality gate for RON strategy implementation
    Validates precise RON strategy rules and mathematical accuracy
    """
    
    def __init__(self):
        super().__init__("RON Strategy Quality Gate")
    
    def get_default_thresholds(self) -> Dict[str, float]:
        """Return RON strategy-specific thresholds"""
        return {
            "min_overall_score": 0.9,  # 90% minimum score for trading strategy
            "critical_pass_rate": 1.0,  # 100% of critical checks must pass
            "strategy_accuracy_threshold": 0.8  # 80% strategy pattern accuracy
        }
    
    async def evaluate(self, code: str, context: Optional[Dict] = None) -> QualityGateResult:
        """Evaluate RON strategy specific requirements"""
        start_time = time.time()
        checks = {}
        
        # Core RON Strategy Requirements
        checks.update(await self._check_vwap_fibonacci_condition(code))
        checks.update(await self._check_ema9_logic(code))
        checks.update(await self._check_new_high_logic(code))
        checks.update(await self._check_crv_requirement(code))
        checks.update(await self._check_space_to_382(code))
        checks.update(await self._check_ron_trading_hours(code))
        
        # RON Entry Logic Validation
        checks.update(await self._check_entry_conditions(code))
        checks.update(await self._check_exit_conditions(code))
        checks.update(await self._check_timing_precision(code))
        
        # Mathematical Accuracy
        checks.update(await self._check_fibonacci_calculation(code))
        checks.update(await self._check_vwap_calculation(code))
        checks.update(await self._check_ema9_calculation(code))
        
        # Calculate results
        overall_score = self.calculate_overall_score(checks)
        passed = self.determine_pass_status(overall_score, checks)
        
        # Count statistics
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks.values() if c.passed)
        failed_checks = total_checks - passed_checks
        critical_failures = sum(1 for c in checks.values() 
                               if c.level == QualityLevel.CRITICAL and not c.passed)
        
        execution_time = (time.time() - start_time) * 1000
        
        result = QualityGateResult(
            gate_name=self.gate_name,
            overall_score=overall_score,
            passed=passed,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            critical_failures=critical_failures,
            checks=checks,
            summary=self.generate_summary(None),
            recommendations=self.generate_recommendations(checks),
            execution_time_ms=execution_time
        )
        
        result.summary = self.generate_summary(result)
        return result
    
    async def _check_vwap_fibonacci_condition(self, code: str) -> Dict[str, QualityCheck]:
        """Check VWAP > 50% Fibonacci condition implementation"""
        check_result = self._analyze_vwap_fibonacci_condition(code)
        
        return {
            "vwap_fibonacci": self.create_quality_check(
                name="VWAP > 50% Fibonacci Condition",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_core"
            )
        }
    
    async def _check_ema9_logic(self, code: str) -> Dict[str, QualityCheck]:
        """Check EMA9 confirmation logic"""
        check_result = self._analyze_ema9_logic(code)
        
        return {
            "ema9_confirmation": self.create_quality_check(
                name="EMA9 Confirmation Logic",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_core"
            )
        }
    
    async def _check_new_high_logic(self, code: str) -> Dict[str, QualityCheck]:
        """Check new high confirmation logic"""
        check_result = self._analyze_new_high_logic(code)
        
        return {
            "new_high_logic": self.create_quality_check(
                name="New High Confirmation",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_core"
            )
        }
    
    async def _check_crv_requirement(self, code: str) -> Dict[str, QualityCheck]:
        """Check CRV >= 1:1 requirement"""
        check_result = self._analyze_crv_requirement(code)
        
        return {
            "crv_requirement": self.create_quality_check(
                name="CRV >= 1:1 Requirement",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_core"
            )
        }
    
    async def _check_space_to_382(self, code: str) -> Dict[str, QualityCheck]:
        """Check space to 38.2% Fibonacci level validation"""
        check_result = self._analyze_space_to_382(code)
        
        return {
            "space_to_382": self.create_quality_check(
                name="Space to 38.2% Validation",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_core"
            )
        }
    
    async def _check_ron_trading_hours(self, code: str) -> Dict[str, QualityCheck]:
        """Check RON trading hours implementation"""
        check_result = self._analyze_ron_trading_hours(code)
        
        return {
            "trading_hours": self.create_quality_check(
                name="RON Trading Hours (16:00-20:00)",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_timing"
            )
        }
    
    async def _check_entry_conditions(self, code: str) -> Dict[str, QualityCheck]:
        """Check complete entry condition logic"""
        patterns = [
            r'time.*between.*16.*20|16:00.*20:00',  # Time window
            r'vwap.*>.*50|vwap.*>.*0\.5',           # VWAP condition
            r'close.*>.*ema|price.*>.*ema',         # EMA condition
            r'new.*high|next.*bar.*high'            # New high condition
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75  # Need at least 75% of entry conditions
        
        return {
            "entry_conditions": self.create_quality_check(
                name="Complete Entry Conditions",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} entry condition patterns",
                recommendations=["Implement all required entry conditions"] if not passed else [],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_logic"
            )
        }
    
    async def _check_exit_conditions(self, code: str) -> Dict[str, QualityCheck]:
        """Check exit condition logic"""
        patterns = [
            r'50.*fibonacci|50.*fib|0\.5.*fib',     # TP at 50% Fibonacci
            r'vwap.*target|target.*vwap',           # TP at VWAP
            r'stop.*loss|sl.*price',                # Stop loss
            r'21:59|21\.59|close.*all.*positions'   # Forced exit
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75  # Need at least 75% of exit conditions
        
        return {
            "exit_conditions": self.create_quality_check(
                name="Complete Exit Conditions",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} exit condition patterns",
                recommendations=["Implement all required exit conditions"] if not passed else [],
                level=QualityLevel.CRITICAL,
                category="ron_strategy_logic"
            )
        }
    
    async def _check_timing_precision(self, code: str) -> Dict[str, QualityCheck]:
        """Check timing precision requirements"""
        patterns = [
            r'1.*minute|1min|60.*second',           # 1-minute bars
            r'close.*bar|end.*bar|bar.*complete',   # Decision at bar close
            r'next.*bar|following.*bar'             # Execution next bar
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.6  # Need timing precision
        
        return {
            "timing_precision": self.create_quality_check(
                name="Timing Precision",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} timing precision patterns",
                recommendations=["Implement precise timing requirements"] if not passed else [],
                level=QualityLevel.HIGH,
                category="ron_strategy_timing"
            )
        }
    
    async def _check_fibonacci_calculation(self, code: str) -> Dict[str, QualityCheck]:
        """Check Fibonacci calculation accuracy"""
        patterns = [
            r'high.*low|session.*high.*low',        # High-Low calculation
            r'23\.6|38\.2|50\.0|61\.8|78\.6',       # Fibonacci levels
            r'fibonacci|fib.*level|retracement'      # Fibonacci terminology
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.8  # High accuracy required for calculations
        
        return {
            "fibonacci_calculation": self.create_quality_check(
                name="Fibonacci Calculation Accuracy",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} Fibonacci calculation patterns",
                recommendations=["Implement accurate Fibonacci calculations"] if not passed else [],
                level=QualityLevel.HIGH,
                category="ron_strategy_calculations"
            )
        }
    
    async def _check_vwap_calculation(self, code: str) -> Dict[str, QualityCheck]:
        """Check VWAP calculation accuracy"""
        patterns = [
            r'volume.*weighted|vwap',               # VWAP terminology
            r'volume.*price|price.*volume',         # Volume-price calculation
            r'cumulative.*volume|cum.*volume'       # Cumulative volume
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.8  # High accuracy required
        
        return {
            "vwap_calculation": self.create_quality_check(
                name="VWAP Calculation Accuracy",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} VWAP calculation patterns",
                recommendations=["Implement accurate VWAP calculations"] if not passed else [],
                level=QualityLevel.HIGH,
                category="ron_strategy_calculations"
            )
        }
    
    async def _check_ema9_calculation(self, code: str) -> Dict[str, QualityCheck]:
        """Check EMA9 calculation accuracy"""
        patterns = [
            r'ema.*9|exponential.*9|ema9',          # EMA9 terminology
            r'smoothing|alpha|decay',               # EMA calculation terms
            r'period.*9|window.*9'                  # 9-period specification
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.6  # Moderate accuracy required
        
        return {
            "ema9_calculation": self.create_quality_check(
                name="EMA9 Calculation Accuracy",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} EMA9 calculation patterns",
                recommendations=["Implement accurate EMA9 calculations"] if not passed else [],
                level=QualityLevel.MEDIUM,
                category="ron_strategy_calculations"
            )
        }
    
    # Individual analysis methods
    def _analyze_vwap_fibonacci_condition(self, code: str) -> Dict:
        """Analyze VWAP > 50% Fibonacci condition implementation"""
        patterns = [
            r'vwap.*>.*50|vwap.*>.*0\.5',
            r'fibonacci.*50|fib.*50|50.*percent',
            r'vwap.*fibonacci|fibonacci.*vwap',
            r'long.*condition|entry.*condition'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        recommendations = []
        if not passed:
            if not re.search(r'vwap.*>.*50|vwap.*>.*0\.5', code, re.IGNORECASE):
                recommendations.append("Implement VWAP > 50% condition check")
            if not re.search(r'fibonacci|fib', code, re.IGNORECASE):
                recommendations.append("Add Fibonacci retracement calculation")
            if not re.search(r'long.*condition', code, re.IGNORECASE):
                recommendations.append("Apply condition specifically to long trades")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} VWAP-Fibonacci patterns",
            "recommendations": recommendations
        }
    
    def _analyze_ema9_logic(self, code: str) -> Dict:
        """Analyze EMA9 crossover logic"""
        patterns = [
            r'ema.*9|ema9|exponential.*9',
            r'price.*>.*ema|close.*>.*ema|above.*ema',
            r'current.*bar|1.*minute.*bar',
            r'crossover|cross.*above'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} EMA9 crossover patterns",
            "recommendations": ["Implement complete EMA9 crossover logic"] if not passed else []
        }
    
    def _analyze_new_high_logic(self, code: str) -> Dict:
        """Analyze new high confirmation logic"""
        patterns = [
            r'new.*high|higher.*high|next.*high',
            r'previous.*bar|previous.*candle|last.*bar',
            r'high.*>.*high|high\[.*\].*>.*high',
            r'confirmation|confirm.*entry'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} new high confirmation patterns",
            "recommendations": ["Implement new high confirmation logic"] if not passed else []
        }
    
    def _analyze_crv_requirement(self, code: str) -> Dict:
        """Analyze CRV >= 1:1 requirement"""
        patterns = [
            r'crv.*>=.*1|crv.*>.*1|crv.*1\.0',
            r'reward.*risk|risk.*reward|target.*stop',
            r'distance.*target|distance.*stop',
            r'1:1|one.*to.*one|minimum.*crv'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.5  # At least half the patterns
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} CRV requirement patterns",
            "recommendations": ["Implement CRV >= 1:1 validation"] if not passed else []
        }
    
    def _analyze_space_to_382(self, code: str) -> Dict:
        """Analyze space to 38.2% Fibonacci level validation"""
        patterns = [
            r'38\.2|382|thirty.*eight',
            r'space.*to|distance.*to|room.*to',
            r'fibonacci.*level|fib.*level',
            r'sufficient.*space|enough.*space'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} space to 38.2% patterns",
            "recommendations": ["Implement space to 38.2% level validation"] if not passed else []
        }
    
    def _analyze_ron_trading_hours(self, code: str) -> Dict:
        """Analyze RON trading hours implementation"""
        patterns = [
            r'16:00|16\.00|4.*pm|sixteen.*hundred',
            r'20:00|20\.00|8.*pm|twenty.*hundred',
            r'trading.*hours|market.*hours|session.*hours',
            r'after.*hours|extended.*hours'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        recommendations = []
        if not passed:
            if not re.search(r'16:00|16\.00', code, re.IGNORECASE):
                recommendations.append("Add 16:00 start time validation")
            if not re.search(r'20:00|20\.00', code, re.IGNORECASE):
                recommendations.append("Add 20:00 end time validation")
            if not re.search(r'trading.*hours', code, re.IGNORECASE):
                recommendations.append("Implement trading hours validation")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} trading hours patterns",
            "recommendations": recommendations
        }