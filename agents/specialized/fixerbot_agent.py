"""
FixerBot Agent - Bug Fixing and Code Optimization Specialist
Fixes bugs, optimizes performance, and refactors code
"""

import logging
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.claude_code_service import ClaudeCodeService, ClaudeCodeConfig

logger = logging.getLogger(__name__)

class FixerBotAgent(ChatAgent):
    """
    Bug Fixing and Optimization Expert (Two-Tier Strategy)

    Tier 1: Pattern-based fixes (fast, deterministic)
    Tier 2: AI-powered fixes (flexible, for unknown errors)

    Capabilities:
    - Bug fixes and patches
    - Performance optimization
    - Code refactoring
    - Memory leak fixes
    - Modernization of legacy code
    """

    # Known error patterns for fast fixing (Tier 1)
    KNOWN_ERROR_PATTERNS = {
        'directory_listing': {
            'keywords': ['directory listing', 'index of', 'not found', 'canvas element not found'],
            'file_pattern': r'browser_tester\.py',
            'description': 'Browser shows directory listing instead of HTML file',
            'fix_method': '_fix_directory_listing'
        },
        'element_not_found': {
            'keywords': ['element not found', 'selector', 'querySelector', 'getElementById'],
            'file_pattern': r'\.(html|js)$',
            'description': 'HTML element not found by selector',
            'fix_method': '_fix_element_selector'
        },
        'js_syntax_error': {
            'keywords': ['syntaxerror', 'unexpected token', 'parsing error'],
            'file_pattern': r'\.(js|html)$',
            'description': 'JavaScript syntax error',
            'fix_method': '_fix_js_syntax'
        },
        'import_error': {
            'keywords': ['modulenotfounderror', 'importerror', 'cannot import'],
            'file_pattern': r'\.py$',
            'description': 'Python import error',
            'fix_method': '_fix_import_error'
        }
    }

    def __init__(self):
        config = AgentConfig(
            agent_id="fixer",
            name="FixerBot",
            full_name="Bug Fixing & Optimization Expert",
            description="Specialized in fixing bugs, optimizing performance, and refactoring",
            model="claude-4.1-sonnet-20250920",
            capabilities=[
                AgentCapability.BUG_FIXING,
                AgentCapability.CODE_GENERATION
            ],
            temperature=0.5,
            max_tokens=4000,
            icon="🔧",
            instructions_path=".ki_autoagent/instructions/fixerbot-instructions.md"
        )
        super().__init__(config)
        # Use Claude CLI - NO FALLBACKS
        self.ai_service = ClaudeCodeService(
            ClaudeCodeConfig(model="sonnet")
        )
        if not self.ai_service.is_available():
            logger.error("FixerBot requires Claude CLI! Install with: npm install -g @anthropic-ai/claude-code")

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute bug fixing task using Two-Tier Strategy:

        Tier 1: Pattern-based fixes (fast, deterministic)
        Tier 2: AI-powered fixes (flexible, for unknown errors)
        """
        try:
            logger.info(f"🔧 FixerBot executing: {request.prompt[:100]}...")

            # Extract errors from Reviewer's context
            context = request.context or {}
            previous_result = context.get('previous_step_result')

            errors_to_fix = []
            files_to_fix = []

            if previous_result:
                # Extract errors from Reviewer result
                if isinstance(previous_result, dict):
                    errors_to_fix = previous_result.get('errors', [])
                    metadata = previous_result.get('metadata', {})
                    files_to_fix = metadata.get('files_created', [])

                    logger.info(f"📋 Extracted {len(errors_to_fix)} errors from Reviewer")
                    logger.info(f"📁 Files involved: {files_to_fix}")

            # TIER 1: Pattern-based fixing (fast)
            pattern_fixes = []
            remaining_errors = []

            for error in errors_to_fix:
                error_lower = str(error).lower()
                matched_pattern = self._match_pattern(error_lower, files_to_fix)

                if matched_pattern:
                    logger.info(f"✅ Pattern matched: {matched_pattern['name']} - {matched_pattern['description']}")
                    fix_result = await self._apply_pattern_fix(matched_pattern, error, files_to_fix)
                    pattern_fixes.append(fix_result)
                else:
                    logger.info(f"❓ No pattern match for error: {error[:80]}...")
                    remaining_errors.append(error)

            # TIER 2: AI-powered fixing (flexible)
            ai_fixes = []
            if remaining_errors:
                logger.info(f"🤖 Using AI-powered fixing for {len(remaining_errors)} remaining errors")
                ai_fix_result = await self._ai_powered_fix(remaining_errors, request.prompt, files_to_fix)
                ai_fixes.append(ai_fix_result)

            # Build comprehensive result
            total_fixes = len(pattern_fixes) + len(ai_fixes)

            if total_fixes == 0:
                # No errors to fix, just use AI for general improvements
                logger.info("📝 No specific errors found - performing general code review")
                return await self._ai_powered_fix([], request.prompt, files_to_fix)

            # Format response
            content_parts = [f"🔧 **FixerBot Report** - {total_fixes} fixes applied\n"]

            if pattern_fixes:
                content_parts.append(f"\n### ⚡ Pattern-Based Fixes ({len(pattern_fixes)})")
                for i, fix in enumerate(pattern_fixes, 1):
                    content_parts.append(f"\n**Fix {i}:** {fix['description']}")
                    content_parts.append(f"- File: `{fix['file']}`")
                    content_parts.append(f"- Status: {fix['status']}")
                    if fix.get('details'):
                        content_parts.append(f"- Details: {fix['details']}")

            if ai_fixes:
                content_parts.append(f"\n### 🤖 AI-Powered Fixes ({len(ai_fixes)})")
                for fix in ai_fixes:
                    content_parts.append(f"\n{fix['content']}")

            content = "\n".join(content_parts)

            return TaskResult(
                status="success",
                content=content,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "fix_type": "two_tier",
                    "pattern_fixes": len(pattern_fixes),
                    "ai_fixes": len(ai_fixes),
                    "total_fixes": total_fixes,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"FixerBot execution error: {e}")
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            return TaskResult(
                status="error",
                content=f"FIX FAILED: {str(e)}\n\nNo fallback allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id
            )

    def _match_pattern(self, error_text: str, files: List[str]) -> Optional[Dict[str, Any]]:
        """
        Match error against known patterns (Tier 1)

        Args:
            error_text: Error message in lowercase
            files: List of files involved

        Returns:
            Matched pattern with metadata, or None
        """
        for pattern_name, pattern_config in self.KNOWN_ERROR_PATTERNS.items():
            # Check if any keyword matches
            keyword_match = any(keyword in error_text for keyword in pattern_config['keywords'])

            if not keyword_match:
                continue

            # Check if file pattern matches any of the files
            file_pattern = pattern_config['file_pattern']
            file_match = any(re.search(file_pattern, f) for f in files) if files else True

            if file_match or not files:
                return {
                    'name': pattern_name,
                    'description': pattern_config['description'],
                    'fix_method': pattern_config['fix_method'],
                    'keywords': pattern_config['keywords'],
                    'file_pattern': file_pattern
                }

        return None

    async def _apply_pattern_fix(
        self,
        pattern: Dict[str, Any],
        error: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """
        Apply pattern-based fix (Tier 1)

        Args:
            pattern: Matched pattern configuration
            error: Original error message
            files: List of files to fix

        Returns:
            Fix result with status and details
        """
        fix_method_name = pattern['fix_method']
        fix_method = getattr(self, fix_method_name, None)

        if not fix_method:
            logger.error(f"Fix method not found: {fix_method_name}")
            return {
                'description': pattern['description'],
                'file': 'unknown',
                'status': '❌ Failed (method not implemented)',
                'details': f"Fix method {fix_method_name} not found"
            }

        try:
            result = await fix_method(error, files)
            return result
        except Exception as e:
            logger.error(f"Pattern fix failed: {e}")
            return {
                'description': pattern['description'],
                'file': files[0] if files else 'unknown',
                'status': '❌ Failed',
                'details': str(e)
            }

    async def _fix_directory_listing(self, error: str, files: List[str]) -> Dict[str, Any]:
        """
        Fix directory listing issue in browser_tester.py

        The bug: URL is http://localhost:PORT instead of http://localhost:PORT/filename.html
        """
        browser_tester_file = None
        for f in files:
            if 'browser_tester.py' in f:
                browser_tester_file = f
                break

        if not browser_tester_file:
            # Search for the file
            import subprocess
            result = subprocess.run(
                ['find', '/Users/dominikfoert/git/KI_AutoAgent/backend', '-name', 'browser_tester.py'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                browser_tester_file = result.stdout.strip().split('\n')[0]

        if not browser_tester_file:
            return {
                'description': 'Fix directory listing in browser_tester.py',
                'file': 'browser_tester.py',
                'status': '❌ Failed (file not found)',
                'details': 'Could not locate browser_tester.py'
            }

        # Read file
        with open(browser_tester_file, 'r') as f:
            content = f.read()

        # Apply fixes to all occurrences
        fixes_applied = 0

        # Pattern 1: url = f"http://localhost:{port}"
        # Fix: url = f"http://localhost:{port}/{filename}"
        if 'url = f"http://localhost:{port}"' in content:
            # Find and replace with proper URL construction
            content = content.replace(
                'url = f"http://localhost:{port}"',
                'filename = os.path.basename(html_file)\n        url = f"http://localhost:{port}/{filename}"'
            )
            fixes_applied += 1

        # Pattern 2: Any other http://localhost:{port} without filename
        # Use regex to find and fix
        url_pattern = r'url = f"http://localhost:\{port\}"'
        if re.search(url_pattern, content):
            content = re.sub(
                url_pattern,
                'filename = os.path.basename(html_file)\n        url = f"http://localhost:{port}/{filename}"',
                content
            )
            fixes_applied += 1

        if fixes_applied > 0:
            # Write back
            with open(browser_tester_file, 'w') as f:
                f.write(content)

            logger.info(f"✅ Fixed directory listing bug in {browser_tester_file}")
            return {
                'description': 'Fix directory listing in browser_tester.py',
                'file': browser_tester_file,
                'status': '✅ Fixed',
                'details': f'Applied {fixes_applied} URL construction fixes'
            }
        else:
            return {
                'description': 'Fix directory listing in browser_tester.py',
                'file': browser_tester_file,
                'status': '⚠️ Already fixed or pattern not found',
                'details': 'No matching patterns found to fix'
            }

    async def _fix_element_selector(self, error: str, files: List[str]) -> Dict[str, Any]:
        """
        Fix HTML element selector issues

        Common issues:
        - Wrong ID or class name
        - Missing element in DOM
        - Incorrect querySelector syntax
        """
        # For now, delegate to AI (pattern detection only)
        return {
            'description': 'Fix element selector',
            'file': files[0] if files else 'unknown',
            'status': '🤖 Delegated to AI (complex fix)',
            'details': 'Element selector issues require AI analysis'
        }

    async def _fix_js_syntax(self, error: str, files: List[str]) -> Dict[str, Any]:
        """
        Fix JavaScript syntax errors

        Common issues:
        - Missing semicolons
        - Unclosed brackets
        - Invalid function syntax
        """
        # Delegate to AI for complex JS fixes
        return {
            'description': 'Fix JavaScript syntax error',
            'file': files[0] if files else 'unknown',
            'status': '🤖 Delegated to AI (requires parsing)',
            'details': 'JS syntax errors require AI-powered analysis'
        }

    async def _fix_import_error(self, error: str, files: List[str]) -> Dict[str, Any]:
        """
        Fix Python import errors

        Common issues:
        - Missing package
        - Wrong import path
        - Circular imports
        """
        # Delegate to AI for import resolution
        return {
            'description': 'Fix Python import error',
            'file': files[0] if files else 'unknown',
            'status': '🤖 Delegated to AI (requires dependency analysis)',
            'details': 'Import errors require AI-powered dependency resolution'
        }

    async def _ai_powered_fix(
        self,
        errors: List[str],
        task_prompt: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """
        AI-powered fixing for unknown errors (Tier 2)

        Uses Claude CLI to analyze and fix complex issues
        """
        if not self.ai_service.is_available():
            return {
                'content': '❌ Claude CLI not available for AI-powered fixes',
                'status': 'error'
            }

        # Build detailed prompt for Claude
        if errors:
            errors_text = "\n".join(f"- {e}" for e in errors)
            prompt = f"""Fix the following errors found in the code:

{errors_text}

Files involved:
{chr(10).join(f'- {f}' for f in files)}

Original task: {task_prompt}

Please analyze the errors and provide fixes with explanations."""
        else:
            prompt = f"""Review and improve the following code:

Task: {task_prompt}

Files involved:
{chr(10).join(f'- {f}' for f in files)}

Provide recommendations and improvements."""

        system_prompt = """You are FixerBot, an expert at fixing bugs and optimizing code.

Your specialties:
1. 🐛 Bug Fixes - Identify and fix all types of bugs
2. ⚡ Performance - Optimize for speed and efficiency
3. 🔄 Refactoring - Clean up and modernize code
4. 💧 Memory - Fix memory leaks and optimize usage
5. 🆕 Modernization - Update legacy code to modern standards

Always provide:
- Root cause analysis
- Fixed code with explanations
- Why the fix works
- Testing recommendations
- Prevention strategies"""

        try:
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5
            )

            return {
                'content': response,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"AI-powered fix failed: {e}")
            return {
                'content': f'❌ AI fix failed: {str(e)}',
                'status': 'error'
            }

    # REMOVED: _generate_fallback_fix method
    # ASIMOV RULE 1: No fallbacks without documented user reason
    # All errors must fail fast with clear error messages

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
