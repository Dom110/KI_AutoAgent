"""
Trading Quality Gates System
Comprehensive quality validation for trading systems with RON strategy specific checks
"""

import re
import time
from typing import Dict, List, Any, Optional, Union
from .base_quality_gate import BaseQualityGate, QualityCheck, QualityGateResult, QualityLevel


class TradingSystemQualityGate(BaseQualityGate):
    """
    Comprehensive quality gate for trading systems
    Based on research findings for financial/trading systems
    """
    
    def __init__(self):
        super().__init__("Trading System Quality Gate")
    
    def get_default_thresholds(self) -> Dict[str, float]:
        """Return trading-specific thresholds"""
        return {
            "min_overall_score": 0.8,  # 80% minimum score
            "financial_compliance_rate": 0.9,  # 90% of financial checks must pass
            "risk_management_rate": 0.9,  # 90% of risk management checks must pass
            "max_function_lines": 50  # Max lines per function
        }
    
    async def evaluate(self, code: str, context: Optional[Dict] = None) -> QualityGateResult:
        """
        Comprehensive evaluation of trading system code
        """
        start_time = time.time()
        checks = {}
        
        # Financial System Specific Checks
        checks.update(await self._check_financial_calculations(code))
        checks.update(await self._check_risk_management(code))
        checks.update(await self._check_trading_compliance(code))
        
        # General Code Quality Checks
        checks.update(await self._check_code_structure(code))
        checks.update(await self._check_error_handling(code))
        checks.update(await self._check_documentation(code))
        
        # Stock Analyser Specific Checks
        if context and context.get("project_type") == "stock_analyser":
            checks.update(await self._check_stock_analyser_compliance(code, context))
        
        # Calculate results
        overall_score = self.calculate_overall_score(checks)
        passed = self.determine_pass_status(overall_score, checks)
        
        # Count statistics
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks.values() if c.passed)
        failed_checks = total_checks - passed_checks
        critical_failures = sum(1 for c in checks.values() 
                               if c.level == QualityLevel.CRITICAL and not c.passed)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        result = QualityGateResult(
            gate_name=self.gate_name,
            overall_score=overall_score,
            passed=passed,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            critical_failures=critical_failures,
            checks=checks,
            summary=self.generate_summary(None),  # Will be set below
            recommendations=self.generate_recommendations(checks),
            execution_time_ms=execution_time
        )
        
        result.summary = self.generate_summary(result)
        return result
    
    async def _check_financial_calculations(self, code: str) -> Dict[str, QualityCheck]:
        """Check financial calculation accuracy requirements"""
        checks = {}
        
        # Check for Decimal usage
        decimal_usage = self._check_decimal_precision(code)
        checks["decimal_precision"] = self.create_quality_check(
            name="Decimal Precision",
            passed=decimal_usage["passed"],
            score=decimal_usage["score"],
            details=decimal_usage["details"],
            recommendations=decimal_usage["recommendations"],
            level=QualityLevel.CRITICAL,
            category="financial"
        )
        
        # Check P&L calculation patterns
        pnl_check = self._check_pnl_calculations(code)
        checks["pnl_calculation"] = self.create_quality_check(
            name="P&L Calculation",
            passed=pnl_check["passed"],
            score=pnl_check["score"], 
            details=pnl_check["details"],
            recommendations=pnl_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="financial"
        )
        
        # Check CRV calculations
        crv_check = self._check_crv_calculations(code)
        checks["crv_calculation"] = self.create_quality_check(
            name="CRV Calculation",
            passed=crv_check["passed"],
            score=crv_check["score"],
            details=crv_check["details"], 
            recommendations=crv_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="financial"
        )
        
        return checks
    
    async def _check_risk_management(self, code: str) -> Dict[str, QualityCheck]:
        """Check risk management requirements"""
        checks = {}
        
        # Position size validation
        position_check = self._check_position_validation(code)
        checks["position_validation"] = self.create_quality_check(
            name="Position Size Validation",
            passed=position_check["passed"],
            score=position_check["score"],
            details=position_check["details"],
            recommendations=position_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="risk_management"
        )
        
        # Stop loss implementation
        stop_loss_check = self._check_stop_loss_logic(code)
        checks["stop_loss_logic"] = self.create_quality_check(
            name="Stop Loss Implementation",
            passed=stop_loss_check["passed"],
            score=stop_loss_check["score"],
            details=stop_loss_check["details"],
            recommendations=stop_loss_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="risk_management"
        )
        
        # Maximum exposure limits
        exposure_check = self._check_exposure_limits(code)
        checks["exposure_limits"] = self.create_quality_check(
            name="Exposure Limits",
            passed=exposure_check["passed"], 
            score=exposure_check["score"],
            details=exposure_check["details"],
            recommendations=exposure_check["recommendations"],
            level=QualityLevel.MEDIUM,
            category="risk_management"
        )
        
        return checks
    
    async def _check_trading_compliance(self, code: str) -> Dict[str, QualityCheck]:
        """Check trading system compliance requirements"""
        checks = {}
        
        # Market hours validation
        hours_check = self._check_market_hours(code)
        checks["market_hours"] = self.create_quality_check(
            name="Market Hours Validation",
            passed=hours_check["passed"],
            score=hours_check["score"],
            details=hours_check["details"],
            recommendations=hours_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="compliance"
        )
        
        # Audit trail logging
        audit_check = self._check_audit_trail(code)
        checks["audit_trail"] = self.create_quality_check(
            name="Audit Trail Logging",
            passed=audit_check["passed"],
            score=audit_check["score"],
            details=audit_check["details"],
            recommendations=audit_check["recommendations"],
            level=QualityLevel.MEDIUM,
            category="compliance"
        )
        
        return checks
    
    async def _check_code_structure(self, code: str) -> Dict[str, QualityCheck]:
        """Check code structure and quality"""
        checks = {}
        
        # Function size check (using base class method)
        function_size_check = self.check_function_complexity(code, self.thresholds["max_function_lines"])
        checks["function_size"] = function_size_check
        
        # Type annotations
        type_check = self._check_type_annotations(code)
        checks["type_annotations"] = self.create_quality_check(
            name="Type Annotations",
            passed=type_check["passed"],
            score=type_check["score"],
            details=type_check["details"],
            recommendations=type_check["recommendations"],
            level=QualityLevel.MEDIUM,
            category="code_quality"
        )
        
        return checks
    
    async def _check_error_handling(self, code: str) -> Dict[str, QualityCheck]:
        """Check error handling patterns"""
        checks = {}
        
        # Exception handling
        exception_check = self._check_exception_patterns(code)
        checks["exception_handling"] = self.create_quality_check(
            name="Exception Handling",
            passed=exception_check["passed"],
            score=exception_check["score"],
            details=exception_check["details"],
            recommendations=exception_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="error_handling"
        )
        
        # Graceful degradation
        degradation_check = self._check_graceful_degradation(code)
        checks["graceful_degradation"] = self.create_quality_check(
            name="Graceful Degradation",
            passed=degradation_check["passed"],
            score=degradation_check["score"],
            details=degradation_check["details"],
            recommendations=degradation_check["recommendations"],
            level=QualityLevel.MEDIUM,
            category="error_handling"
        )
        
        return checks
    
    async def _check_documentation(self, code: str) -> Dict[str, QualityCheck]:
        """Check documentation requirements"""
        checks = {}
        
        # Docstring coverage
        docstring_check = self._check_docstring_coverage(code)
        checks["docstring_coverage"] = self.create_quality_check(
            name="Docstring Coverage",
            passed=docstring_check["passed"],
            score=docstring_check["score"],
            details=docstring_check["details"],
            recommendations=docstring_check["recommendations"],
            level=QualityLevel.MEDIUM,
            category="documentation"
        )
        
        return checks
    
    async def _check_stock_analyser_compliance(self, code: str, context: Dict) -> Dict[str, QualityCheck]:
        """Check stock_analyser specific requirements"""
        checks = {}
        
        # Fallback policy compliance
        fallback_check = self._check_fallback_policy(code)
        checks["fallback_policy"] = self.create_quality_check(
            name="Fallback Policy Compliance",
            passed=fallback_check["passed"],
            score=fallback_check["score"],
            details=fallback_check["details"],
            recommendations=fallback_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="stock_analyser"
        )
        
        # Live data policy
        live_data_check = self._check_live_data_policy(code)
        checks["live_data_policy"] = self.create_quality_check(
            name="Live Data Policy",
            passed=live_data_check["passed"],
            score=live_data_check["score"],
            details=live_data_check["details"],
            recommendations=live_data_check["recommendations"],
            level=QualityLevel.CRITICAL,
            category="stock_analyser"
        )
        
        return checks
    
    # Individual check implementations
    def _check_decimal_precision(self, code: str) -> Dict:
        """Check for proper decimal usage in financial calculations"""
        decimal_imports = len(re.findall(r'from decimal import Decimal|import decimal', code))
        float_financial = len(re.findall(r'float\([^)]*price|float\([^)]*amount|float\([^)]*cost|float\([^)]*pnl', code, re.IGNORECASE))
        
        score = 1.0 if decimal_imports > 0 and float_financial == 0 else 0.0
        passed = score >= 0.8
        
        recommendations = []
        if decimal_imports == 0:
            recommendations.append("Import and use Decimal for financial calculations")
        if float_financial > 0:
            recommendations.append("Replace float() with Decimal() for financial values")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Decimal imports: {decimal_imports}, Float financial ops: {float_financial}",
            "recommendations": recommendations
        }
    
    def _check_pnl_calculations(self, code: str) -> Dict:
        """Check P&L calculation patterns"""
        pnl_patterns = [
            r'profit.*=.*entry.*exit|pnl.*=.*entry.*exit',
            r'entry_price.*exit_price',
            r'calculate.*pnl|calculate.*profit'
        ]
        
        found_patterns = sum(1 for pattern in pnl_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / len(pnl_patterns), 1.0)
        passed = score >= 0.6
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} P&L calculation patterns",
            "recommendations": ["Implement proper P&L calculation methods"] if not passed else []
        }
    
    def _check_crv_calculations(self, code: str) -> Dict:
        """Check CRV (Cost-Risk-Value) calculation patterns"""
        crv_patterns = [
            r'crv|reward.*risk|risk.*reward',
            r'stop.*loss.*distance',
            r'target.*distance',
            r'1:1|1\.0.*ratio'
        ]
        
        found_patterns = sum(1 for pattern in crv_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / len(crv_patterns), 1.0)
        passed = score >= 0.5
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} CRV calculation patterns",
            "recommendations": ["Implement proper CRV calculation methods"] if not passed else []
        }
    
    def _check_position_validation(self, code: str) -> Dict:
        """Check position size validation"""
        validation_patterns = [
            r'if.*position.*size|if.*amount',
            r'validate.*position|check.*position',
            r'max.*position|maximum.*position',
            r'assert.*position|assert.*amount'
        ]
        
        found_patterns = sum(1 for pattern in validation_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / 2, 1.0)  # At least 2 patterns expected
        passed = score >= 0.5
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} position validation patterns",
            "recommendations": ["Add position size validation logic"] if not passed else []
        }
    
    def _check_stop_loss_logic(self, code: str) -> Dict:
        """Check stop loss implementation"""
        stop_loss_patterns = [
            r'stop.*loss|sl.*price',
            r'exit.*condition|close.*position',
            r'risk.*management'
        ]
        
        found_patterns = sum(1 for pattern in stop_loss_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / len(stop_loss_patterns), 1.0)
        passed = score >= 0.6
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} stop loss patterns",
            "recommendations": ["Implement comprehensive stop loss logic"] if not passed else []
        }
    
    def _check_exposure_limits(self, code: str) -> Dict:
        """Check exposure limit controls"""
        exposure_patterns = [
            r'max.*exposure|maximum.*risk',
            r'portfolio.*limit|total.*exposure',
            r'drawdown.*limit'
        ]
        
        found_patterns = sum(1 for pattern in exposure_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / len(exposure_patterns), 1.0)
        passed = score >= 0.3
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} exposure limit patterns",
            "recommendations": ["Add exposure limit controls"] if not passed else []
        }
    
    def _check_market_hours(self, code: str) -> Dict:
        """Check market hours validation"""
        hours_patterns = [
            r'16:00|16\.00|20:00|20\.00',
            r'trading.*hours|market.*hours',
            r'time.*check|hour.*validation'
        ]
        
        found_patterns = sum(1 for pattern in hours_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / 2, 1.0)  # At least 2 patterns expected
        passed = score >= 0.5
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} market hours patterns",
            "recommendations": ["Add market hours validation (16:00-20:00)"] if not passed else []
        }
    
    def _check_audit_trail(self, code: str) -> Dict:
        """Check audit trail logging"""
        logging_patterns = [
            r'log|logger|logging',
            r'timestamp|datetime\.now',
            r'record|audit|trace'
        ]
        
        found_patterns = sum(1 for pattern in logging_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / len(logging_patterns), 1.0)
        passed = score >= 0.6
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} logging patterns",
            "recommendations": ["Add comprehensive audit trail logging"] if not passed else []
        }
    
    def _check_type_annotations(self, code: str) -> Dict:
        """Check type annotations coverage"""
        function_defs = len(re.findall(r'def\s+\w+', code))
        typed_functions = len(re.findall(r'def\s+\w+.*?:\s*\w+', code))
        
        score = typed_functions / max(function_defs, 1) if function_defs > 0 else 1.0
        passed = score >= 0.8
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Typed functions: {typed_functions}/{function_defs}",
            "recommendations": ["Add type annotations to functions"] if not passed else []
        }
    
    def _check_exception_patterns(self, code: str) -> Dict:
        """Check exception handling patterns"""
        try_blocks = len(re.findall(r'try:', code))
        except_blocks = len(re.findall(r'except', code))
        bare_excepts = len(re.findall(r'except:', code))
        
        score = 1.0
        if try_blocks == 0:
            score = 0.0
        elif bare_excepts > 0:
            score = 0.5  # Penalize bare except clauses
        elif except_blocks < try_blocks:
            score = 0.7
        
        passed = score >= 0.7
        
        recommendations = []
        if try_blocks == 0:
            recommendations.append("Add try/except blocks for error handling")
        if bare_excepts > 0:
            recommendations.append("Replace bare except: with specific exceptions")
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Try blocks: {try_blocks}, Except blocks: {except_blocks}, Bare excepts: {bare_excepts}",
            "recommendations": recommendations
        }
    
    def _check_graceful_degradation(self, code: str) -> Dict:
        """Check graceful degradation patterns"""
        degradation_patterns = [
            r'fallback|backup|alternative',
            r'retry|attempt.*again',
            r'default.*value|default.*behavior'
        ]
        
        found_patterns = sum(1 for pattern in degradation_patterns if re.search(pattern, code, re.IGNORECASE))
        score = min(found_patterns / 2, 1.0)  # At least 2 patterns expected
        passed = score >= 0.3
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Found {found_patterns} degradation patterns",
            "recommendations": ["Add graceful degradation mechanisms"] if not passed else []
        }
    
    def _check_docstring_coverage(self, code: str) -> Dict:
        """Check docstring coverage"""
        functions = len(re.findall(r'def\s+\w+', code))
        docstrings = len(re.findall(r'def\s+\w+.*?""".*?"""', code, re.DOTALL))
        
        score = docstrings / max(functions, 1) if functions > 0 else 1.0
        passed = score >= 0.7
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Documented functions: {docstrings}/{functions}",
            "recommendations": ["Add docstrings to functions"] if not passed else []
        }
    
    def _check_fallback_policy(self, code: str) -> Dict:
        """Check compliance with stock_analyser fallback policy"""
        forbidden_patterns = [
            (r'return\s+None', "Forbidden: return None"),
            (r'return\s+pd\.DataFrame\(\)', "Forbidden: return empty DataFrame"),
            (r'except:\s*pass', "Forbidden: silent failures"),
            (r'yfinance|yf\.', "Forbidden: yfinance usage"),
            (r'skip.*symbol|continue.*symbol', "Forbidden: skip failed symbols")
        ]
        
        violations = []
        for pattern, message in forbidden_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(message)
        
        score = 1.0 - (len(violations) / len(forbidden_patterns))
        passed = len(violations) == 0
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Violations: {violations}" if violations else "Fallback policy compliant",
            "recommendations": ["Fix fallback policy violations"] if violations else []
        }
    
    def _check_live_data_policy(self, code: str) -> Dict:
        """Check live data policy compliance (no future data)"""
        future_leak_patterns = [
            r'future|lookahead|forward',
            r'shift\(-\d+\)|shift\(.*-.*\)',
            r'\[\s*-?\d+\s*:\s*\].*future'
        ]
        
        violations = sum(1 for pattern in future_leak_patterns if re.search(pattern, code, re.IGNORECASE))
        score = 1.0 - min(violations / 3, 1.0)
        passed = violations == 0
        
        return {
            "passed": passed,
            "score": score,
            "details": f"Potential future leaks: {violations}",
            "recommendations": ["Remove future data leak patterns"] if violations > 0 else []
        }