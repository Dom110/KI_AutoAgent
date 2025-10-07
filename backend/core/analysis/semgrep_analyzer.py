"""
Semgrep Analyzer - Security vulnerability detection
Real implementation using semgrep CLI
"""

import json
import logging
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class SemgrepAnalyzer:
    """
    Security analysis using Semgrep
    Detects security vulnerabilities, code smells, and best practice violations
    """

    def __init__(self):
        self.semgrep_available = shutil.which("semgrep") is not None
        if self.semgrep_available:
            logger.info("✅ Semgrep CLI found")
        else:
            logger.warning(
                "⚠️ Semgrep CLI not found - install with: pip install semgrep"
            )

    async def run_analysis(
        self, root_path: str, progress_callback: Callable | None = None
    ) -> dict[str, Any]:
        """
        Run security analysis on codebase using Semgrep

        Args:
            root_path: Root directory to analyze
            progress_callback: Optional callback for progress updates

        Returns:
            {
                'findings': [
                    {
                        'check_id': 'python.lang.security.dangerous-eval',
                        'path': 'app.py',
                        'line': 42,
                        'severity': 'ERROR',
                        'message': 'Detected eval() usage...',
                        'fix': 'Use ast.literal_eval()...'
                    }
                ],
                'summary': {
                    'critical': 2,
                    'high': 5,
                    'medium': 12,
                    'low': 8
                }
            }
        """
        if progress_callback:
            await progress_callback("🔒 Running Semgrep security analysis...")

        if not self.semgrep_available:
            logger.warning("Semgrep CLI not available - returning stub results")
            return {
                "findings": [],
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "note": "Semgrep CLI not installed - install with: pip install semgrep",
            }

        try:
            # v5.8.1: Use specific ruleset to avoid metrics conflict
            # --json: JSON output
            # --config=p/security-audit: Security-focused ruleset
            # --metrics=off: Don't send metrics to semgrep
            cmd = [
                "semgrep",
                "--config=p/security-audit",
                "--json",
                "--metrics=off",
                root_path,
            ]

            logger.info(f"🔍 Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            if result.returncode != 0 and result.returncode != 1:
                # returncode 1 means findings were found (not an error)
                logger.error(f"Semgrep error: {result.stderr}")
                return {
                    "findings": [],
                    "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    "error": result.stderr,
                }

            # Parse JSON output
            output = json.loads(result.stdout)
            findings = []
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

            for result_item in output.get("results", []):
                severity = (
                    result_item.get("extra", {}).get("severity", "UNKNOWN").upper()
                )

                # Map semgrep severity to our severity levels
                if severity in ["ERROR", "CRITICAL"]:
                    severity_key = "critical"
                elif severity == "WARNING":
                    severity_key = "high"
                elif severity == "INFO":
                    severity_key = "medium"
                else:
                    severity_key = "low"

                severity_counts[severity_key] += 1

                finding = {
                    "check_id": result_item.get("check_id", "unknown"),
                    "path": result_item.get("path", ""),
                    "line": result_item.get("start", {}).get("line", 0),
                    "end_line": result_item.get("end", {}).get("line", 0),
                    "severity": severity,
                    "message": result_item.get("extra", {}).get("message", ""),
                    "code": result_item.get("extra", {}).get("lines", ""),
                    "fix": result_item.get("extra", {}).get("fix", ""),
                    "metadata": result_item.get("extra", {}).get("metadata", {}),
                }
                findings.append(finding)

            if progress_callback:
                total = sum(severity_counts.values())
                await progress_callback(
                    f"🔒 Security analysis complete: {total} findings"
                )

            logger.info(f"✅ Semgrep analysis complete: {len(findings)} findings")

            return {
                "findings": findings,
                "summary": severity_counts,
                "total_findings": len(findings),
            }

        except subprocess.TimeoutExpired:
            logger.error("Semgrep analysis timed out after 5 minutes")
            return {
                "findings": [],
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "error": "Analysis timed out (>5 minutes)",
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep output: {e}")
            return {
                "findings": [],
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "error": f"Failed to parse output: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Semgrep analysis failed: {e}")
            return {
                "findings": [],
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "error": str(e),
            }
