"""
🚨 KI AutoAgent Deprecation Management System

Manages deprecated modules, features, and provides clear migration paths.
This system ensures:
- ✅ Obsolete modules are clearly marked
- ✅ Startup is BLOCKED if deprecated code is loaded
- ✅ Developers see VISUAL warnings
- ✅ Clear migration guides are provided

Usage:
    from backend.deprecation import DeprecationValidator, get_registry
    
    validator = DeprecationValidator()
    validator.validate_imports()  # Checks all loaded modules
    
    registry = get_registry()
    summary = registry.get_summary()
    print(f"Critical: {summary['critical']}, Error: {summary['error']}")

CLI Usage:
    python -m backend.deprecation report          # Show full report
    python -m backend.deprecation check            # Check startup
    python -m backend.deprecation list             # List all deprecated
    python -m backend.deprecation migrate <key>   # Show migration guide
"""

from .registry import (
    DeprecatedModule,
    DeprecationRegistry,
    DeprecationSeverity,
    get_registry,
)
from .validator import (
    DeprecationValidator,
    ImportBlocker,
    get_validator,
    validate_startup,
)
from .warnings import (
    DeprecationWarning,
    print_deprecation_banner,
    print_migration_guide,
    print_critical_deprecation_error,
    Colors,
)
from .migration_guides import get_migration_guide, get_all_migration_guides

__all__ = [
    # Registry
    'DeprecatedModule',
    'DeprecationRegistry',
    'DeprecationSeverity',
    'get_registry',
    
    # Validator
    'DeprecationValidator',
    'ImportBlocker',
    'get_validator',
    'validate_startup',
    
    # Warnings
    'DeprecationWarning',
    'print_deprecation_banner',
    'print_migration_guide',
    'print_critical_deprecation_error',
    'Colors',
    
    # Migration Guides
    'get_migration_guide',
    'get_all_migration_guides',
]

__version__ = '1.0.0'
__author__ = 'KI AutoAgent Team'
__license__ = 'MIT'