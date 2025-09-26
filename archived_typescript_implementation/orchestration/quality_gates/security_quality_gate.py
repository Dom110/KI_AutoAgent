"""
Security Quality Gate
Security validation for web applications and financial systems
"""

import re
import time
from typing import Dict, List, Any, Optional
from .base_quality_gate import BaseQualityGate, QualityCheck, QualityGateResult, QualityLevel


class SecurityQualityGate(BaseQualityGate):
    """
    Security quality gate based on OWASP Top 10 and common security best practices
    Applicable to web applications, APIs, and financial systems
    """
    
    def __init__(self):
        super().__init__("Security Quality Gate")
    
    def get_default_thresholds(self) -> Dict[str, float]:
        """Return security-specific thresholds"""
        return {
            "min_overall_score": 0.8,  # 80% minimum score
            "critical_security_rate": 1.0,  # 100% of critical security checks must pass
            "vulnerability_tolerance": 0.1  # Max 10% minor vulnerabilities
        }
    
    async def evaluate(self, code: str, context: Optional[Dict] = None) -> QualityGateResult:
        """Evaluate security requirements"""
        start_time = time.time()
        checks = {}
        
        # OWASP Top 10 Security Checks
        checks.update(await self._check_injection_vulnerabilities(code))
        checks.update(await self._check_authentication_security(code))
        checks.update(await self._check_sensitive_data_exposure(code))
        checks.update(await self._check_xml_external_entities(code))
        checks.update(await self._check_broken_access_control(code))
        checks.update(await self._check_security_misconfiguration(code))
        checks.update(await self._check_xss_vulnerabilities(code))
        checks.update(await self._check_insecure_deserialization(code))
        checks.update(await self._check_vulnerable_components(code))
        checks.update(await self._check_insufficient_logging(code))
        
        # Additional Security Checks
        checks.update(await self._check_csrf_protection(code))
        checks.update(await self._check_input_validation(code))
        checks.update(await self._check_output_encoding(code))
        checks.update(await self._check_secure_communication(code))
        checks.update(await self._check_secrets_management(code))
        
        # Financial System Specific Security
        if context and context.get("domain") == "Financial Trading Systems":
            checks.update(await self._check_financial_security(code))
        
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
    
    async def _check_injection_vulnerabilities(self, code: str) -> Dict[str, QualityCheck]:
        """Check for SQL injection and other injection vulnerabilities"""
        # SQL Injection patterns
        sql_injection_patterns = [
            r'execute\([^)]*\+[^)]*\)|query\([^)]*\+[^)]*\)',  # String concatenation in SQL
            r'f".*SELECT|f\'.*SELECT|".*SELECT.*".*\+|\'.*SELECT.*\'.*\+',  # F-string/concat SQL
            r'cursor\.execute\([^)]*%|\.execute\([^)]*format',  # Unsafe parameterization
        ]
        
        # Good patterns (parameterized queries)
        safe_sql_patterns = [
            r'execute\([^)]*,\s*\([^)]*\)|\.execute\([^)]*,\s*params',  # Parameterized queries
            r'prepared.*statement|bind.*parameter',  # Prepared statements
            r'sqlalchemy|ORM|\.filter\(',  # ORM usage
        ]
        
        vulnerabilities = sum(1 for pattern in sql_injection_patterns if re.search(pattern, code, re.IGNORECASE))
        safe_practices = sum(1 for pattern in safe_sql_patterns if re.search(pattern, code, re.IGNORECASE))
        
        # Command injection patterns
        command_injection_patterns = [
            r'os\.system\([^)]*\+|subprocess\.[^(]*\([^)]*\+',  # Command concatenation
            r'shell=True.*\+|exec\([^)]*\+',  # Shell injection
        ]
        
        command_vulnerabilities = sum(1 for pattern in command_injection_patterns if re.search(pattern, code, re.IGNORECASE))
        
        total_vulnerabilities = vulnerabilities + command_vulnerabilities
        score = max(0, 1.0 - (total_vulnerabilities * 0.3) + (safe_practices * 0.1))
        passed = total_vulnerabilities == 0
        
        recommendations = []
        if vulnerabilities > 0:
            recommendations.append("Use parameterized queries instead of string concatenation")
        if command_vulnerabilities > 0:
            recommendations.append("Avoid shell=True and command string concatenation")
        if safe_practices == 0 and (vulnerabilities > 0 or "sql" in code.lower()):
            recommendations.append("Implement ORM or prepared statements")
        
        return {
            "injection_vulnerabilities": self.create_quality_check(
                name="Injection Vulnerabilities",
                passed=passed,
                score=score,
                details=f"SQL injection risks: {vulnerabilities}, Command injection risks: {command_vulnerabilities}, Safe practices: {safe_practices}",
                recommendations=recommendations,
                level=QualityLevel.CRITICAL,
                category="owasp_injection"
            )
        }
    
    async def _check_authentication_security(self, code: str) -> Dict[str, QualityCheck]:
        """Check authentication and session management security"""
        # Authentication patterns
        auth_patterns = [
            r'password.*hash|hash.*password|bcrypt|scrypt|argon2',  # Password hashing
            r'jwt.*token|session.*token|auth.*token',  # Token-based auth
            r'login.*attempt|failed.*login|account.*lockout',  # Brute force protection
        ]
        
        # Insecure patterns
        insecure_auth_patterns = [
            r'password.*plain|plain.*password|password.*=.*input',  # Plain text passwords
            r'md5\(.*password|sha1\(.*password',  # Weak hashing
            r'session.*cookie.*secure.*false|httponly.*false',  # Insecure cookies
        ]
        
        secure_practices = sum(1 for pattern in auth_patterns if re.search(pattern, code, re.IGNORECASE))
        insecure_practices = sum(1 for pattern in insecure_auth_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, min(1, (secure_practices / 3) - (insecure_practices * 0.5)))
        passed = insecure_practices == 0 and (secure_practices > 0 or "auth" not in code.lower())
        
        recommendations = []
        if insecure_practices > 0:
            recommendations.append("Fix insecure authentication practices")
        if secure_practices == 0 and "auth" in code.lower():
            recommendations.append("Implement secure authentication mechanisms")
        
        return {
            "authentication_security": self.create_quality_check(
                name="Authentication Security",
                passed=passed,
                score=score,
                details=f"Secure practices: {secure_practices}, Insecure practices: {insecure_practices}",
                recommendations=recommendations,
                level=QualityLevel.CRITICAL,
                category="owasp_auth"
            )
        }
    
    async def _check_sensitive_data_exposure(self, code: str) -> Dict[str, QualityCheck]:
        """Check for sensitive data exposure"""
        # Sensitive data patterns in code
        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']',  # Hardcoded secrets
            r'secret\s*=\s*["\'][^"\']+["\']|token\s*=\s*["\'][^"\']+["\']',
            r'print.*password|print.*secret|print.*api_key|log.*password',  # Logging secrets
            r'credit.*card|ssn|social.*security|bank.*account',  # PII patterns
        ]
        
        # Secure patterns
        secure_patterns = [
            r'os\.environ|getenv|env\.|config\.',  # Environment variables
            r'encrypt|decrypt|cipher|keystore',  # Encryption
            r'mask|redact|sanitize|hash',  # Data protection
        ]
        
        exposures = sum(1 for pattern in sensitive_patterns if re.search(pattern, code, re.IGNORECASE))
        protections = sum(1 for pattern in secure_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, 1.0 - (exposures * 0.4) + (protections * 0.1))
        passed = exposures == 0
        
        recommendations = []
        if exposures > 0:
            recommendations.append("Remove hardcoded secrets and sensitive data logging")
            recommendations.append("Use environment variables for sensitive configuration")
        if protections == 0 and ("password" in code.lower() or "secret" in code.lower()):
            recommendations.append("Implement data encryption and masking")
        
        return {
            "sensitive_data_exposure": self.create_quality_check(
                name="Sensitive Data Exposure",
                passed=passed,
                score=score,
                details=f"Data exposures: {exposures}, Protection measures: {protections}",
                recommendations=recommendations,
                level=QualityLevel.CRITICAL,
                category="owasp_data_exposure"
            )
        }
    
    async def _check_xml_external_entities(self, code: str) -> Dict[str, QualityCheck]:
        """Check for XML External Entity (XXE) vulnerabilities"""
        # XXE vulnerability patterns
        xxe_patterns = [
            r'xml\.etree.*parse\(|lxml.*parse\(|xmltodict\.parse',  # XML parsing
            r'resolve_entities\s*=\s*True|external_entities\s*=\s*True',  # Unsafe XML config
        ]
        
        # Secure XML patterns
        secure_xml_patterns = [
            r'resolve_entities\s*=\s*False|external_entities\s*=\s*False',  # Safe XML config
            r'defuse.*xml|safe.*xml.*parser',  # Safe XML libraries
        ]
        
        vulnerabilities = sum(1 for pattern in xxe_patterns if re.search(pattern, code, re.IGNORECASE))
        safe_practices = sum(1 for pattern in secure_xml_patterns if re.search(pattern, code, re.IGNORECASE))
        
        # If no XML processing, pass by default
        has_xml = "xml" in code.lower() or "etree" in code.lower()
        if not has_xml:
            score = 1.0
            passed = True
        else:
            score = max(0, 1.0 - (vulnerabilities * 0.5) + (safe_practices * 0.3))
            passed = vulnerabilities == 0
        
        recommendations = []
        if vulnerabilities > 0:
            recommendations.append("Disable XML external entities in parsers")
            recommendations.append("Use secure XML parsing libraries")
        
        return {
            "xml_external_entities": self.create_quality_check(
                name="XML External Entities (XXE)",
                passed=passed,
                score=score,
                details=f"XXE vulnerabilities: {vulnerabilities}, Safe practices: {safe_practices}",
                recommendations=recommendations,
                level=QualityLevel.HIGH if has_xml else QualityLevel.LOW,
                category="owasp_xxe"
            )
        }
    
    async def _check_broken_access_control(self, code: str) -> Dict[str, QualityCheck]:
        """Check for broken access control"""
        # Access control patterns
        access_control_patterns = [
            r'@login_required|@require_auth|@permission_required',  # Decorators
            r'if.*user\.is_authenticated|if.*user\.has_permission',  # Manual checks
            r'role.*check|permission.*check|authorize|can_access',  # Authorization logic
        ]
        
        # Insecure patterns
        insecure_patterns = [
            r'admin.*=.*True|is_admin.*=.*True',  # Hardcoded admin
            r'bypass.*auth|skip.*auth|no.*auth.*required',  # Auth bypasses
        ]
        
        access_controls = sum(1 for pattern in access_control_patterns if re.search(pattern, code, re.IGNORECASE))
        insecure_practices = sum(1 for pattern in insecure_patterns if re.search(pattern, code, re.IGNORECASE))
        
        # Check for route/endpoint definitions
        has_routes = bool(re.search(r'@app\.route|@api\.route|def.*view|class.*View', code, re.IGNORECASE))
        
        if not has_routes:
            score = 1.0
            passed = True
        else:
            score = max(0, (access_controls / 2) - (insecure_practices * 0.5))
            passed = insecure_practices == 0 and access_controls > 0
        
        recommendations = []
        if insecure_practices > 0:
            recommendations.append("Remove hardcoded admin privileges and auth bypasses")
        if has_routes and access_controls == 0:
            recommendations.append("Implement proper access control for routes")
        
        return {
            "broken_access_control": self.create_quality_check(
                name="Broken Access Control",
                passed=passed,
                score=score,
                details=f"Access controls: {access_controls}, Insecure practices: {insecure_practices}",
                recommendations=recommendations,
                level=QualityLevel.CRITICAL if has_routes else QualityLevel.MEDIUM,
                category="owasp_access_control"
            )
        }
    
    async def _check_security_misconfiguration(self, code: str) -> Dict[str, QualityCheck]:
        """Check for security misconfiguration"""
        # Secure configuration patterns
        secure_config_patterns = [
            r'DEBUG\s*=\s*False|debug\s*=\s*false',  # Production debug setting
            r'HTTPS|SSL|TLS|secure\s*=\s*True',  # Secure communication
            r'ALLOWED_HOSTS|CORS_ALLOW|security.*header',  # Security headers
        ]
        
        # Insecure configuration patterns
        insecure_config_patterns = [
            r'DEBUG\s*=\s*True|debug\s*=\s*true',  # Debug in production
            r'CORS_ALLOW_ALL\s*=\s*True|CORS.*\*',  # Open CORS
            r'verify\s*=\s*False|ssl.*verify.*false',  # SSL verification disabled
        ]
        
        secure_configs = sum(1 for pattern in secure_config_patterns if re.search(pattern, code, re.IGNORECASE))
        insecure_configs = sum(1 for pattern in insecure_config_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, min(1, (secure_configs / 3) - (insecure_configs * 0.5)))
        passed = insecure_configs == 0
        
        recommendations = []
        if insecure_configs > 0:
            recommendations.append("Fix insecure configuration settings")
        if secure_configs == 0:
            recommendations.append("Implement security configuration best practices")
        
        return {
            "security_misconfiguration": self.create_quality_check(
                name="Security Misconfiguration",
                passed=passed,
                score=score,
                details=f"Secure configs: {secure_configs}, Insecure configs: {insecure_configs}",
                recommendations=recommendations,
                level=QualityLevel.HIGH,
                category="owasp_misconfig"
            )
        }
    
    async def _check_xss_vulnerabilities(self, code: str) -> Dict[str, QualityCheck]:
        """Check for Cross-Site Scripting (XSS) vulnerabilities"""
        # XSS vulnerability patterns
        xss_patterns = [
            r'\.innerHTML\s*=|outerHTML\s*=',  # Direct DOM manipulation
            r'render_template_string\([^)]*\+|render\([^)]*\+',  # Template injection
            r'safe\s*\||mark_safe\(|Markup\(',  # Unsafe HTML marking
        ]
        
        # XSS protection patterns
        protection_patterns = [
            r'escape\(|html\.escape|cgi\.escape',  # HTML escaping
            r'CSP|Content-Security-Policy',  # Content Security Policy
            r'sanitize|bleach\.clean|html.*filter',  # HTML sanitization
        ]
        
        vulnerabilities = sum(1 for pattern in xss_patterns if re.search(pattern, code, re.IGNORECASE))
        protections = sum(1 for pattern in protection_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, 1.0 - (vulnerabilities * 0.4) + (protections * 0.2))
        passed = vulnerabilities == 0
        
        recommendations = []
        if vulnerabilities > 0:
            recommendations.append("Use HTML escaping and avoid innerHTML assignments")
            recommendations.append("Implement Content Security Policy")
        if protections == 0 and "html" in code.lower():
            recommendations.append("Add HTML sanitization and escaping")
        
        return {
            "xss_vulnerabilities": self.create_quality_check(
                name="Cross-Site Scripting (XSS)",
                passed=passed,
                score=score,
                details=f"XSS vulnerabilities: {vulnerabilities}, Protection measures: {protections}",
                recommendations=recommendations,
                level=QualityLevel.HIGH,
                category="owasp_xss"
            )
        }
    
    async def _check_insecure_deserialization(self, code: str) -> Dict[str, QualityCheck]:
        """Check for insecure deserialization"""
        # Insecure deserialization patterns
        insecure_patterns = [
            r'pickle\.loads|pickle\.load|cPickle\.loads',  # Unsafe pickle
            r'yaml\.load\(|yaml\.unsafe_load',  # Unsafe YAML
            r'eval\(|exec\(',  # Code execution
        ]
        
        # Secure patterns
        secure_patterns = [
            r'json\.loads|json\.load',  # Safe JSON
            r'yaml\.safe_load|yaml\.SafeLoader',  # Safe YAML
            r'ast\.literal_eval',  # Safe evaluation
        ]
        
        vulnerabilities = sum(1 for pattern in insecure_patterns if re.search(pattern, code, re.IGNORECASE))
        safe_practices = sum(1 for pattern in secure_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, 1.0 - (vulnerabilities * 0.5) + (safe_practices * 0.1))
        passed = vulnerabilities == 0
        
        recommendations = []
        if vulnerabilities > 0:
            recommendations.append("Avoid pickle and unsafe deserialization")
            recommendations.append("Use JSON or safe YAML loading")
        
        return {
            "insecure_deserialization": self.create_quality_check(
                name="Insecure Deserialization",
                passed=passed,
                score=score,
                details=f"Vulnerabilities: {vulnerabilities}, Safe practices: {safe_practices}",
                recommendations=recommendations,
                level=QualityLevel.HIGH,
                category="owasp_deserialization"
            )
        }
    
    async def _check_vulnerable_components(self, code: str) -> Dict[str, QualityCheck]:
        """Check for use of vulnerable components"""
        # This is a basic check - in practice, you'd integrate with tools like Safety or Snyk
        imports = re.findall(r'import\s+(\w+)|from\s+(\w+)', code)
        all_imports = [imp[0] or imp[1] for imp in imports]
        
        # Known vulnerable patterns (examples)
        known_vulnerable = ['pickle', 'yaml']  # Simplified example
        found_vulnerable = [imp for imp in all_imports if imp in known_vulnerable]
        
        score = 1.0 - (len(found_vulnerable) * 0.2)
        passed = len(found_vulnerable) == 0
        
        recommendations = []
        if found_vulnerable:
            recommendations.append(f"Review usage of potentially vulnerable components: {found_vulnerable}")
            recommendations.append("Use dependency scanning tools like Safety or Snyk")
        
        return {
            "vulnerable_components": self.create_quality_check(
                name="Vulnerable Components",
                passed=passed,
                score=score,
                details=f"Potentially vulnerable imports: {found_vulnerable}",
                recommendations=recommendations,
                level=QualityLevel.MEDIUM,
                category="owasp_components"
            )
        }
    
    async def _check_insufficient_logging(self, code: str) -> Dict[str, QualityCheck]:
        """Check for insufficient logging and monitoring"""
        # Logging patterns
        logging_patterns = [
            r'import logging|from logging|logger\.',  # Logging imports
            r'log\.|logging\.|audit\.|security\.log',  # Logging usage
            r'exception|error|warning|critical',  # Log levels
        ]
        
        # Security event logging
        security_logging_patterns = [
            r'login.*log|auth.*log|access.*log',  # Authentication logging
            r'failed.*attempt|security.*event|audit.*trail',  # Security events
        ]
        
        basic_logging = sum(1 for pattern in logging_patterns if re.search(pattern, code, re.IGNORECASE))
        security_logging = sum(1 for pattern in security_logging_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = min(1, (basic_logging * 0.1) + (security_logging * 0.3))
        passed = basic_logging > 0
        
        recommendations = []
        if basic_logging == 0:
            recommendations.append("Implement comprehensive logging")
        if security_logging == 0 and "auth" in code.lower():
            recommendations.append("Add security event logging")
        
        return {
            "insufficient_logging": self.create_quality_check(
                name="Insufficient Logging & Monitoring",
                passed=passed,
                score=score,
                details=f"Basic logging: {basic_logging}, Security logging: {security_logging}",
                recommendations=recommendations,
                level=QualityLevel.MEDIUM,
                category="owasp_logging"
            )
        }
    
    async def _check_csrf_protection(self, code: str) -> Dict[str, QualityCheck]:
        """Check for CSRF protection"""
        csrf_patterns = [
            r'csrf_token|CSRFProtect|csrf_exempt',  # CSRF tokens
            r'@csrf_protect|csrf_verify',  # CSRF protection
        ]
        
        has_forms = bool(re.search(r'<form|request\.POST|request\.form', code, re.IGNORECASE))
        csrf_protection = sum(1 for pattern in csrf_patterns if re.search(pattern, code, re.IGNORECASE))
        
        if not has_forms:
            score = 1.0
            passed = True
        else:
            score = min(1, csrf_protection / 2)
            passed = csrf_protection > 0
        
        recommendations = []
        if has_forms and csrf_protection == 0:
            recommendations.append("Implement CSRF protection for forms")
        
        return {
            "csrf_protection": self.create_quality_check(
                name="CSRF Protection",
                passed=passed,
                score=score,
                details=f"Forms detected: {has_forms}, CSRF protection: {csrf_protection}",
                recommendations=recommendations,
                level=QualityLevel.HIGH if has_forms else QualityLevel.LOW,
                category="csrf"
            )
        }
    
    async def _check_input_validation(self, code: str) -> Dict[str, QualityCheck]:
        """Check for input validation"""
        validation_patterns = [
            r'validate|validator|schema|marshmallow',  # Validation libraries
            r'isinstance\(|type\(.*\)==|len\(',  # Type/length checks
            r'regex|re\.|pattern|match',  # Regex validation
        ]
        
        found_validation = sum(1 for pattern in validation_patterns if re.search(pattern, code, re.IGNORECASE))
        has_inputs = bool(re.search(r'input\(|request\.|args\.|form\.|json\.|params', code, re.IGNORECASE))
        
        if not has_inputs:
            score = 1.0
            passed = True
        else:
            score = min(1, found_validation / 3)
            passed = found_validation > 0
        
        recommendations = []
        if has_inputs and found_validation == 0:
            recommendations.append("Implement comprehensive input validation")
        
        return {
            "input_validation": self.create_quality_check(
                name="Input Validation",
                passed=passed,
                score=score,
                details=f"Input handling: {has_inputs}, Validation patterns: {found_validation}",
                recommendations=recommendations,
                level=QualityLevel.HIGH if has_inputs else QualityLevel.LOW,
                category="input_validation"
            )
        }
    
    async def _check_output_encoding(self, code: str) -> Dict[str, QualityCheck]:
        """Check for output encoding"""
        encoding_patterns = [
            r'escape|html\.escape|urllib\.quote',  # HTML/URL encoding
            r'encode\(|decode\(|charset|utf-8',  # Character encoding
        ]
        
        found_encoding = sum(1 for pattern in encoding_patterns if re.search(pattern, code, re.IGNORECASE))
        has_output = bool(re.search(r'print\(|return.*html|render|response', code, re.IGNORECASE))
        
        if not has_output:
            score = 1.0
            passed = True
        else:
            score = min(1, found_encoding / 2)
            passed = found_encoding > 0 or not re.search(r'html|render', code, re.IGNORECASE)
        
        recommendations = []
        if has_output and found_encoding == 0 and "html" in code.lower():
            recommendations.append("Implement proper output encoding for HTML content")
        
        return {
            "output_encoding": self.create_quality_check(
                name="Output Encoding",
                passed=passed,
                score=score,
                details=f"Output handling: {has_output}, Encoding patterns: {found_encoding}",
                recommendations=recommendations,
                level=QualityLevel.MEDIUM,
                category="output_encoding"
            )
        }
    
    async def _check_secure_communication(self, code: str) -> Dict[str, QualityCheck]:
        """Check for secure communication"""
        secure_patterns = [
            r'https://|ssl|tls|secure=True',  # Secure protocols
            r'verify=True|cert_reqs=ssl\.CERT_REQUIRED',  # Certificate verification
        ]
        
        insecure_patterns = [
            r'http://|verify=False|ssl.*verify.*false',  # Insecure protocols
        ]
        
        secure_comm = sum(1 for pattern in secure_patterns if re.search(pattern, code, re.IGNORECASE))
        insecure_comm = sum(1 for pattern in insecure_patterns if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, 1.0 - (insecure_comm * 0.5) + (secure_comm * 0.2))
        passed = insecure_comm == 0
        
        recommendations = []
        if insecure_comm > 0:
            recommendations.append("Use HTTPS and enable certificate verification")
        
        return {
            "secure_communication": self.create_quality_check(
                name="Secure Communication",
                passed=passed,
                score=score,
                details=f"Secure patterns: {secure_comm}, Insecure patterns: {insecure_comm}",
                recommendations=recommendations,
                level=QualityLevel.HIGH,
                category="secure_communication"
            )
        }
    
    async def _check_secrets_management(self, code: str) -> Dict[str, QualityCheck]:
        """Check for proper secrets management"""
        return await self._check_sensitive_data_exposure(code)  # Already implemented above
    
    async def _check_financial_security(self, code: str) -> Dict[str, QualityCheck]:
        """Check financial system-specific security"""
        financial_security_patterns = [
            r'decimal\.Decimal|Decimal\(',  # Precise calculations
            r'encrypt.*transaction|encrypt.*trade',  # Transaction encryption
            r'audit.*trail|compliance.*log',  # Compliance logging
        ]
        
        financial_risks = [
            r'float.*price|float.*amount|float.*money',  # Floating point money
            r'print.*balance|print.*account|log.*balance',  # Balance logging
        ]
        
        secure_practices = sum(1 for pattern in financial_security_patterns if re.search(pattern, code, re.IGNORECASE))
        risk_patterns = sum(1 for pattern in financial_risks if re.search(pattern, code, re.IGNORECASE))
        
        score = max(0, (secure_practices / 3) - (risk_patterns * 0.5))
        passed = risk_patterns == 0 and secure_practices > 0
        
        recommendations = []
        if risk_patterns > 0:
            recommendations.append("Fix financial data handling risks")
        if secure_practices == 0:
            recommendations.append("Implement financial-grade security practices")
        
        return {
            "financial_security": self.create_quality_check(
                name="Financial System Security",
                passed=passed,
                score=score,
                details=f"Secure practices: {secure_practices}, Risk patterns: {risk_patterns}",
                recommendations=recommendations,
                level=QualityLevel.CRITICAL,
                category="financial_security"
            )
        }