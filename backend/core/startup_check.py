"""
Startup dependency checker for KI AutoAgent
Validates all required dependencies at application startup
Fails fast with detailed, actionable error messages
"""

import sys
import os
import importlib
import traceback
from typing import List, Dict, Any
import logging

from .exceptions import DependencyError

logger = logging.getLogger(__name__)


class StartupChecker:
    """
    Validates all required dependencies at startup
    Fails fast with detailed error messages
    """

    @staticmethod
    async def check_all_dependencies() -> None:
        """
        Check all required dependencies at application startup
        Raises DependencyError with detailed information if any dependency is missing
        """
        errors = []

        # 1. Check Redis availability
        errors.extend(StartupChecker._check_redis())

        # 2. Check required Python packages
        errors.extend(StartupChecker._check_python_packages())

        # 3. Check file system permissions
        errors.extend(StartupChecker._check_file_permissions())

        # 4. Check required environment variables
        errors.extend(StartupChecker._check_environment())

        # If any errors found, raise DependencyError with all details
        if errors:
            raise DependencyError(errors)

        logger.info("✅ All system dependencies verified successfully")

    @staticmethod
    def _check_redis() -> List[Dict[str, Any]]:
        """Check Redis availability - both client and server"""
        errors = []

        # Check Redis Python client
        try:
            import redis
        except ImportError as e:
            errors.append({
                'component': 'Redis Python Client',
                'error': 'Redis package not installed',
                'solution': 'pip install redis',
                'file': __file__,
                'line': sys._getframe().f_lineno,
                'traceback': traceback.format_exc()
            })
            return errors  # Can't check server without client

        # Check Redis server connection
        try:
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
            r.ping()
            logger.info("✅ Redis server is running and accessible")
        except redis.ConnectionError as e:
            errors.append({
                'component': 'Redis Server',
                'error': f'Cannot connect to Redis server: {str(e)}',
                'solution': (
                    'Start Redis server:\n'
                    '   - Docker: docker run -d -p 6379:6379 redis:7-alpine\n'
                    '   - macOS:  brew services start redis\n'
                    '   - Linux:  sudo systemctl start redis\n'
                    '   - Test:   redis-cli ping'
                ),
                'file': __file__,
                'line': sys._getframe().f_lineno,
                'traceback': traceback.format_exc()
            })
        except Exception as e:
            errors.append({
                'component': 'Redis Server',
                'error': f'Unexpected Redis error: {str(e)}',
                'solution': 'Check Redis installation and configuration',
                'file': __file__,
                'line': sys._getframe().f_lineno,
                'traceback': traceback.format_exc()
            })

        return errors

    @staticmethod
    def _check_python_packages() -> List[Dict[str, Any]]:
        """Check required Python packages are installed"""
        errors = []

        required_packages = [
            ('tree_sitter', 'tree-sitter', 'Code parsing and AST analysis'),
            ('tree_sitter_python', 'tree-sitter-python', 'Python code parsing'),
            ('tree_sitter_javascript', 'tree-sitter-javascript', 'JavaScript code parsing'),
            ('tree_sitter_typescript', 'tree-sitter-typescript', 'TypeScript code parsing'),
            ('msgpack', 'msgpack', 'Binary serialization for cache'),
            ('watchdog', 'watchdog', 'File system monitoring'),
            ('fastapi', 'fastapi', 'Web framework'),
            ('websockets', 'websockets', 'WebSocket support'),
        ]

        for import_name, pip_name, description in required_packages:
            try:
                importlib.import_module(import_name)
                logger.debug(f"✅ {import_name} ({description}) is installed")
            except ImportError:
                errors.append({
                    'component': f'{pip_name} ({description})',
                    'error': f'Package {import_name} not found',
                    'solution': f'pip install {pip_name}',
                    'file': __file__,
                    'line': sys._getframe().f_lineno
                })

        # Optional but recommended packages (log warnings but don't fail)
        optional_packages = [
            ('semgrep', 'semgrep', 'Security analysis'),
            ('radon', 'radon', 'Code metrics'),
            ('vulture', 'vulture', 'Dead code detection'),
        ]

        for import_name, pip_name, description in optional_packages:
            try:
                importlib.import_module(import_name)
                logger.debug(f"✅ {import_name} ({description}) is installed")
            except ImportError:
                logger.warning(f"⚠️ Optional package {pip_name} ({description}) not installed. "
                             f"Install with: pip install {pip_name}")

        return errors

    @staticmethod
    def _check_file_permissions() -> List[Dict[str, Any]]:
        """Check required directories exist and are writable"""
        errors = []

        # Check home directory for .ki_autoagent
        home_dir = os.path.expanduser('~')
        ki_dir = os.path.join(home_dir, '.ki_autoagent')

        try:
            # Create directory if it doesn't exist
            os.makedirs(ki_dir, exist_ok=True)

            # Test write permissions
            test_file = os.path.join(ki_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)

            logger.info(f"✅ Cache directory {ki_dir} is writable")
        except PermissionError as e:
            errors.append({
                'component': 'File System Permissions',
                'error': f'Cannot write to {ki_dir}',
                'solution': f'Grant write permissions: chmod 755 {ki_dir}',
                'file': __file__,
                'line': sys._getframe().f_lineno,
                'traceback': traceback.format_exc()
            })
        except Exception as e:
            errors.append({
                'component': 'File System',
                'error': f'Unexpected error accessing {ki_dir}: {str(e)}',
                'solution': f'Check directory permissions and disk space',
                'file': __file__,
                'line': sys._getframe().f_lineno,
                'traceback': traceback.format_exc()
            })

        return errors

    @staticmethod
    def _check_environment() -> List[Dict[str, Any]]:
        """Check required environment variables"""
        errors = []

        # Import ConfigManager for proper API key checking
        try:
            from core.config_manager import ConfigManager
        except ImportError:
            # If ConfigManager not available, use env vars directly
            ConfigManager = None

        # Check for API keys (FAIL FAST if not configured)
        api_keys = [
            ('OPENAI_API_KEY', 'OpenAI GPT Modelle'),
            ('PERPLEXITY_API_KEY', 'Research Agent'),
        ]

        # Check for Anthropic API key OR Claude CLI
        # Claude CLI is an alternative authentication method, not a fallback
        has_claude_cli = False
        try:
            import subprocess
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                has_claude_cli = True
                logger.info("✅ Claude CLI verfügbar als Alternative zu ANTHROPIC_API_KEY")
        except:
            pass

        if not has_claude_cli:
            api_keys.append(('ANTHROPIC_API_KEY', 'Claude Modelle'))

        for env_var, description in api_keys:
            if ConfigManager:
                try:
                    # Try to get key through ConfigManager (checks all sources)
                    value = ConfigManager.get_api_key(env_var)
                    logger.info(f"✅ {env_var} verfügbar für {description}")
                except Exception as e:
                    errors.append({
                        'component': f'API Key: {env_var}',
                        'error': f'{env_var} nicht konfiguriert',
                        'solution': (
                            f'Konfigurieren Sie {env_var}:\n'
                            f'   1. export {env_var}="your-api-key"\n'
                            f'   2. backend/config/api_keys.yaml\n'
                            f'   3. .env Datei im Projekt-Root'
                        ),
                        'file': __file__,
                        'line': sys._getframe().f_lineno,
                        'traceback': None
                    })
            else:
                # Fallback to env var check
                if not os.environ.get(env_var):
                    errors.append({
                        'component': f'API Key: {env_var}',
                        'error': f'{env_var} nicht als Environment Variable gesetzt',
                        'solution': f'export {env_var}="your-api-key"',
                        'file': __file__,
                        'line': sys._getframe().f_lineno,
                        'traceback': None
                    })

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            errors.append({
                'component': 'Python Version',
                'error': f'Python {python_version.major}.{python_version.minor} is too old',
                'solution': 'Upgrade to Python 3.8 or newer',
                'file': __file__,
                'line': sys._getframe().f_lineno
            })

        return errors

    @staticmethod
    async def quick_health_check() -> Dict[str, Any]:
        """
        Perform a quick health check, returning status without raising exceptions
        Used for health endpoints and monitoring
        """
        health = {
            'healthy': True,
            'checks': {},
            'errors': []
        }

        # Redis check
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
            r.ping()
            health['checks']['redis'] = 'OK'
        except Exception as e:
            health['healthy'] = False
            health['checks']['redis'] = f'FAILED: {str(e)}'
            health['errors'].append('Redis not available')

        # Basic package check
        critical_packages = ['tree_sitter', 'fastapi', 'msgpack']
        for package in critical_packages:
            try:
                importlib.import_module(package)
                health['checks'][package] = 'OK'
            except ImportError:
                health['healthy'] = False
                health['checks'][package] = 'NOT INSTALLED'
                health['errors'].append(f'{package} not installed')

        return health