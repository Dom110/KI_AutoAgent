"""
Base Quality Gate System for KI_AutoAgent

This module provides the abstract base classes for quality gates that can be
extended for different domains (trading, web apps, APIs, etc.).
"""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
from enum import Enum


class QualityLevel(Enum):
    """Quality check severity levels"""
    CRITICAL = "critical"      # Must pass - system failure if not
    HIGH = "high"             # Important - significant impact
    MEDIUM = "medium"         # Moderate - quality improvement
    LOW = "low"               # Minor - nice to have
    INFO = "info"             # Informational - no action needed


@dataclass
class QualityCheck:
    """Individual quality check result"""
    name: str
    passed: bool
    score: float  # 0.0 - 1.0
    details: str
    recommendations: List[str]
    level: QualityLevel = QualityLevel.MEDIUM
    category: str = "general"
    file_path: Optional[str] = None
    line_numbers: Optional[List[int]] = None


@dataclass 
class QualityGateResult:
    """Complete quality gate evaluation result"""
    gate_name: str
    overall_score: float  # 0.0 - 1.0
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    checks: Dict[str, QualityCheck]
    summary: str
    recommendations: List[str]
    execution_time_ms: float


class BaseQualityGate(ABC):
    """
    Abstract base class for all quality gates.
    
    Each domain (trading, web apps, etc.) should extend this class
    to implement domain-specific quality checks.
    """
    
    def __init__(self, gate_name: str):
        self.gate_name = gate_name
        self.thresholds = self.get_default_thresholds()
    
    @abstractmethod
    def get_default_thresholds(self) -> Dict[str, float]:
        """Return default quality thresholds for this gate"""
        pass
    
    @abstractmethod
    async def evaluate(self, code: str, context: Optional[Dict] = None) -> QualityGateResult:
        """
        Evaluate code quality and return comprehensive results.
        
        Args:
            code: Source code to evaluate
            context: Optional context with project specifics, agent outputs, etc.
            
        Returns:
            QualityGateResult: Complete evaluation results
        """
        pass
    
    def create_quality_check(
        self,
        name: str,
        passed: bool,
        score: float,
        details: str,
        recommendations: List[str],
        level: QualityLevel = QualityLevel.MEDIUM,
        category: str = "general",
        file_path: Optional[str] = None,
        line_numbers: Optional[List[int]] = None
    ) -> QualityCheck:
        """Helper to create quality check objects"""
        return QualityCheck(
            name=name,
            passed=passed,
            score=max(0.0, min(1.0, score)),  # Clamp to 0-1
            details=details,
            recommendations=recommendations,
            level=level,
            category=category,
            file_path=file_path,
            line_numbers=line_numbers
        )
    
    def calculate_overall_score(self, checks: Dict[str, QualityCheck]) -> float:
        """Calculate weighted overall score from individual checks"""
        if not checks:
            return 0.0
            
        # Weight by quality level
        level_weights = {
            QualityLevel.CRITICAL: 5.0,
            QualityLevel.HIGH: 3.0,
            QualityLevel.MEDIUM: 2.0,
            QualityLevel.LOW: 1.0,
            QualityLevel.INFO: 0.5
        }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for check in checks.values():
            weight = level_weights.get(check.level, 1.0)
            total_weighted_score += check.score * weight
            total_weight += weight
            
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def determine_pass_status(
        self, 
        overall_score: float, 
        checks: Dict[str, QualityCheck]
    ) -> bool:
        """Determine if quality gate passes based on score and critical failures"""
        # Any critical failure = automatic fail
        critical_failures = [c for c in checks.values() 
                           if c.level == QualityLevel.CRITICAL and not c.passed]
        if critical_failures:
            return False
            
        # Check overall score threshold
        min_score = self.thresholds.get("min_overall_score", 0.8)
        return overall_score >= min_score
    
    def generate_summary(self, result: QualityGateResult) -> str:
        """Generate human-readable summary"""
        status = "PASSED" if result.passed else "FAILED"
        return f"""
Quality Gate: {result.gate_name} - {status}
Overall Score: {result.overall_score:.2f}/1.00
Checks: {result.passed_checks}/{result.total_checks} passed
Critical Failures: {result.critical_failures}
Execution Time: {result.execution_time_ms:.1f}ms
"""
    
    def generate_recommendations(self, checks: Dict[str, QualityCheck]) -> List[str]:
        """Generate prioritized recommendations from failed checks"""
        recommendations = []
        
        # Sort by priority (critical first, then by score)
        failed_checks = [c for c in checks.values() if not c.passed]
        failed_checks.sort(key=lambda c: (
            c.level == QualityLevel.CRITICAL,
            c.level == QualityLevel.HIGH,
            1.0 - c.score
        ), reverse=True)
        
        for check in failed_checks[:10]:  # Top 10 recommendations
            for rec in check.recommendations:
                if rec not in recommendations:
                    recommendations.append(rec)
                    
        return recommendations
    
    # Common utility methods for pattern matching
    def find_pattern_matches(
        self, 
        code: str, 
        patterns: List[str], 
        ignore_comments: bool = True
    ) -> List[Dict[str, Any]]:
        """Find pattern matches in code with line numbers"""
        if ignore_comments:
            # Remove comments (simplified - handles # and /* */ comments)
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            
        matches = []
        lines = code.split('\n')
        
        for pattern in patterns:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append({
                        'pattern': pattern,
                        'line': line_num,
                        'content': line.strip(),
                        'match': re.search(pattern, line, re.IGNORECASE).group()
                    })
                    
        return matches
    
    def check_imports(self, code: str, required: List[str] = None, 
                     forbidden: List[str] = None) -> QualityCheck:
        """Check for required and forbidden imports"""
        import_lines = re.findall(r'^(?:from\s+\S+\s+)?import\s+.+$', 
                                 code, re.MULTILINE)
        all_imports = ' '.join(import_lines)
        
        issues = []
        score = 1.0
        
        # Check required imports
        if required:
            missing = [imp for imp in required if imp not in all_imports]
            if missing:
                issues.append(f"Missing required imports: {missing}")
                score -= 0.2 * len(missing)
                
        # Check forbidden imports  
        if forbidden:
            found = [imp for imp in forbidden if imp in all_imports]
            if found:
                issues.append(f"Forbidden imports found: {found}")
                score -= 0.3 * len(found)
                
        return self.create_quality_check(
            name="Import Validation",
            passed=len(issues) == 0,
            score=max(0.0, score),
            details=f"Import analysis: {'; '.join(issues) if issues else 'All imports valid'}",
            recommendations=[f"Fix import issues: {issue}" for issue in issues],
            category="imports"
        )
    
    def check_function_complexity(self, code: str, max_lines: int = 50) -> QualityCheck:
        """Check function complexity by line count"""
        functions = re.findall(r'def\s+(\w+)\(.*?\):(.*?)(?=\ndef|\Z)', 
                              code, re.DOTALL)
        
        complex_functions = []
        total_functions = len(functions)
        
        for func_name, func_body in functions:
            line_count = len([line for line in func_body.split('\n') 
                            if line.strip() and not line.strip().startswith('#')])
            if line_count > max_lines:
                complex_functions.append((func_name, line_count))
                
        score = 1.0 - (len(complex_functions) / max(total_functions, 1)) * 0.5
        
        return self.create_quality_check(
            name="Function Complexity",
            passed=len(complex_functions) == 0,
            score=score,
            details=f"Found {len(complex_functions)} complex functions (>{max_lines} lines)",
            recommendations=[f"Refactor {name} ({lines} lines)" 
                           for name, lines in complex_functions],
            category="complexity"
        )