"""
Engine Parity Quality Gate
Quality validation for Live/Backtest engine parity requirements
"""

import re
import time
from typing import Dict, List, Any, Optional
from .base_quality_gate import BaseQualityGate, QualityCheck, QualityGateResult, QualityLevel


class EngineParityQualityGate(BaseQualityGate):
    """
    Quality gate for Live/Backtest engine parity validation
    Ensures identical logic between Live and Backtest modes
    """
    
    def __init__(self):
        super().__init__("Engine Parity Quality Gate")
    
    def get_default_thresholds(self) -> Dict[str, float]:
        """Return engine parity-specific thresholds"""
        return {
            "min_overall_score": 0.85,  # 85% minimum score for engine parity
            "critical_pass_rate": 1.0,  # 100% of critical checks must pass
            "future_leak_tolerance": 0.0  # Zero tolerance for future leaks
        }
    
    async def evaluate(self, code: str, context: Optional[Dict] = None) -> QualityGateResult:
        """Evaluate engine parity requirements"""
        start_time = time.time()
        checks = {}
        
        # Core Engine Parity Requirements
        checks.update(await self._check_unified_engine(code))
        checks.update(await self._check_future_leak_prevention(code))
        checks.update(await self._check_iterative_processing(code))
        checks.update(await self._check_engine_chart_decoupling(code))
        
        # Data Handling Consistency
        checks.update(await self._check_data_access_patterns(code))
        checks.update(await self._check_decision_timing(code))
        checks.update(await self._check_mode_switching(code))
        
        # Architecture Validation
        checks.update(await self._check_result_flow(code))
        checks.update(await self._check_timing_abstraction(code))
        
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
    
    async def _check_unified_engine(self, code: str) -> Dict[str, QualityCheck]:
        """Check for unified engine pattern"""
        check_result = self._analyze_unified_engine(code)
        
        return {
            "unified_engine": self.create_quality_check(
                name="Unified Engine Pattern",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="engine_architecture"
            )
        }
    
    async def _check_future_leak_prevention(self, code: str) -> Dict[str, QualityCheck]:
        """Check future leak prevention measures"""
        check_result = self._analyze_future_leak_prevention(code)
        
        return {
            "future_leak_prevention": self.create_quality_check(
                name="Future Leak Prevention",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="data_integrity"
            )
        }
    
    async def _check_iterative_processing(self, code: str) -> Dict[str, QualityCheck]:
        """Check iterative minute-by-minute processing"""
        check_result = self._analyze_iterative_processing(code)
        
        return {
            "iterative_processing": self.create_quality_check(
                name="Iterative Minute Processing",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.CRITICAL,
                category="processing_logic"
            )
        }
    
    async def _check_engine_chart_decoupling(self, code: str) -> Dict[str, QualityCheck]:
        """Check engine-chart decoupling"""
        check_result = self._analyze_engine_chart_decoupling(code)
        
        return {
            "engine_chart_decoupling": self.create_quality_check(
                name="Engine-Chart Decoupling",
                passed=check_result["passed"],
                score=check_result["score"],
                details=check_result["details"],
                recommendations=check_result["recommendations"],
                level=QualityLevel.HIGH,
                category="architecture_separation"
            )
        }
    
    async def _check_data_access_patterns(self, code: str) -> Dict[str, QualityCheck]:
        """Check consistent data access patterns"""
        patterns = [
            r'\.iloc\[:.*current_index\]|\.iloc\[:.*i\]',  # Proper slicing
            r'available.*data|current.*data|up.*to.*index',  # Data limiting
            r'def.*get.*data.*current|def.*get.*available'   # Data access methods
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.6
        
        return {
            "data_access_patterns": self.create_quality_check(
                name="Consistent Data Access Patterns",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} data access patterns",
                recommendations=["Implement consistent data access patterns"] if not passed else [],
                level=QualityLevel.HIGH,
                category="data_access"
            )
        }
    
    async def _check_decision_timing(self, code: str) -> Dict[str, QualityCheck]:
        """Check decision timing consistency"""
        patterns = [
            r'bar.*close|candle.*close|end.*of.*bar',      # Decision timing
            r'minute.*complete|bar.*complete',              # Bar completion
            r'decision.*point|trigger.*decision'            # Decision triggers
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.5
        
        return {
            "decision_timing": self.create_quality_check(
                name="Decision Timing Consistency",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} timing patterns",
                recommendations=["Implement consistent decision timing"] if not passed else [],
                level=QualityLevel.HIGH,
                category="timing_consistency"
            )
        }
    
    async def _check_mode_switching(self, code: str) -> Dict[str, QualityCheck]:
        """Check mode switching implementation"""
        patterns = [
            r'mode.*=.*(live|backtest)|is_live|is_backtest',   # Mode variables
            r'if.*live|if.*backtest|mode.*check',              # Mode conditionals
            r'class.*Engine.*mode|Engine.*live.*backtest'      # Engine mode support
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.6
        
        return {
            "mode_switching": self.create_quality_check(
                name="Mode Switching Implementation",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} mode switching patterns",
                recommendations=["Implement proper mode switching logic"] if not passed else [],
                level=QualityLevel.MEDIUM,
                category="engine_modes"
            )
        }
    
    async def _check_result_flow(self, code: str) -> Dict[str, QualityCheck]:
        """Check result flow architecture"""
        patterns = [
            r'return.*result|return.*signal|return.*trade',    # Result returns
            r'engine.*result|result.*engine',                   # Engine results
            r'format.*chart|chart.*annotation|chart.*data'     # Chart formatting
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.5
        
        return {
            "result_flow": self.create_quality_check(
                name="Result Flow Architecture",
                passed=passed,
                score=score,
                details=f"Found {found_patterns}/{len(patterns)} result flow patterns",
                recommendations=["Implement proper result flow architecture"] if not passed else [],
                level=QualityLevel.MEDIUM,
                category="result_architecture"
            )
        }
    
    async def _check_timing_abstraction(self, code: str) -> Dict[str, QualityCheck]:
        """Check timing abstraction layer"""
        patterns = [
            r'sleep|time\.sleep|delay',                         # Live timing
            r'fast.*as.*possible|no.*delay|instant',           # Backtest timing
            r'timing.*layer|time.*abstraction|speed.*control'  # Abstraction layer
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / 2, 1.0)  # Need at least 2 patterns
        passed = score >= 0.5
        
        return {
            "timing_abstraction": self.create_quality_check(
                name="Timing Abstraction Layer",
                passed=passed,
                score=score,
                details=f"Found {found_patterns} timing abstraction patterns",
                recommendations=["Implement timing abstraction layer"] if not passed else [],
                level=QualityLevel.MEDIUM,
                category="timing_architecture"
            )
        }
    
    # Individual analysis methods
    def _analyze_unified_engine(self, code: str) -> Dict:
        """Analyze unified engine pattern"""
        patterns = [
            r'class.*Engine|Engine.*class',
            r'mode.*=.*(live|backtest)|engine.*mode',
            r'def.*run.*engine|def.*execute.*engine|def.*start.*engine',
            r'unified.*engine|single.*engine|shared.*engine'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        recommendations = []
        if not passed:
            if not re.search(r'class.*Engine', code, re.IGNORECASE):
                recommendations.append("Create unified Engine class")
            if not re.search(r'mode.*=.*(live|backtest)', code, re.IGNORECASE):
                recommendations.append("Add mode parameter (live/backtest)")
            if not re.search(r'def.*run.*engine', code, re.IGNORECASE):
                recommendations.append("Implement engine execution method")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} unified engine patterns",
            "recommendations": recommendations
        }
    
    def _analyze_future_leak_prevention(self, code: str) -> Dict:
        """Analyze future leak prevention measures"""
        # Good patterns (prevent future leak)
        good_patterns = [
            r'\.iloc\[:.*current|\.iloc\[:.*i\]|\.iloc\[:.*index',
            r'available.*data|current.*data|up.*to.*current',
            r'range\(.*current|range\(.*i\)|range\(.*index'
        ]
        
        # Bad patterns (cause future leak)
        bad_patterns = [
            r'\.iloc\[.*:\]|\.iloc\[-\d+:\]',     # Full data access
            r'future|lookahead|forward',           # Future-looking terms
            r'shift\(-|lag\(-',                    # Future shifting
            r'\.iloc\[i\+1:\]|\.iloc\[.*\+.*:\]'  # Future indexing
        ]
        
        good_found = sum(1 for pattern in good_patterns if re.search(pattern, code, re.IGNORECASE))
        bad_found = sum(1 for pattern in bad_patterns if re.search(pattern, code, re.IGNORECASE))
        
        # Score: good patterns add, bad patterns subtract heavily
        score = (good_found / len(good_patterns)) - (bad_found * 0.5)
        score = max(0, min(1, score))  # Clamp to 0-1
        passed = score >= 0.7 and bad_found == 0
        
        recommendations = []
        if bad_found > 0:
            recommendations.append(f"Remove {bad_found} future leak patterns")
        if good_found < len(good_patterns):
            recommendations.append("Add more current data restrictions")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Good patterns: {good_found}, Bad patterns: {bad_found}",
            "recommendations": recommendations
        }
    
    def _analyze_iterative_processing(self, code: str) -> Dict:
        """Analyze iterative minute-by-minute processing"""
        patterns = [
            r'for.*minute|for.*bar|for.*i.*in.*range',
            r'minute.*by.*minute|bar.*by.*bar|iterative',
            r'range\(.*len\(.*data|range\(.*len\(.*df',
            r'process.*each.*minute|process.*each.*bar'
        ]
        
        found_patterns = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
        score = found_patterns / len(patterns)
        passed = score >= 0.75
        
        recommendations = []
        if not passed:
            if not re.search(r'for.*minute|for.*bar', code, re.IGNORECASE):
                recommendations.append("Implement minute-by-minute loop")
            if not re.search(r'range\(.*len\(', code, re.IGNORECASE):
                recommendations.append("Process data iteratively with range(len(data))")
            if not re.search(r'iterative|minute.*by.*minute', code, re.IGNORECASE):
                recommendations.append("Add iterative processing comments/documentation")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns}/{len(patterns)} iterative processing patterns",
            "recommendations": recommendations
        }
    
    def _analyze_engine_chart_decoupling(self, code: str) -> Dict:
        """Analyze engine-chart decoupling"""
        # Good patterns (decoupled)
        decoupling_patterns = [
            r'return.*result|return.*signal|return.*trade',
            r'engine.*result|result.*from.*engine',
            r'separate.*chart|decouple.*chart|chart.*layer'
        ]
        
        # Bad patterns (coupled)
        coupling_patterns = [
            r'plot|plt\.|matplotlib|chart\.show',
            r'display.*chart|render.*chart|show.*plot',
            r'streamlit.*chart|st\.plotly|st\.line_chart'
        ]
        
        decoupling_found = sum(1 for pattern in decoupling_patterns if re.search(pattern, code, re.IGNORECASE))
        coupling_found = sum(1 for pattern in coupling_patterns if re.search(pattern, code, re.IGNORECASE))
        
        # Score: decoupling patterns good, coupling patterns bad
        score = (decoupling_found / len(decoupling_patterns)) - (coupling_found * 0.3)
        score = max(0, min(1, score))
        passed = score >= 0.5 and coupling_found <= 1  # Allow minimal coupling
        
        recommendations = []
        if coupling_found > 1:
            recommendations.append(f"Remove {coupling_found} chart coupling patterns from engine")
        if decoupling_found < len(decoupling_patterns):
            recommendations.append("Add more result return patterns for decoupling")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Decoupling patterns: {decoupling_found}, Coupling patterns: {coupling_found}",
            "recommendations": recommendations
        }