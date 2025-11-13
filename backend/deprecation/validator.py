"""
🔍 Deprecation Validator - Enforces deprecation policies at runtime

This validator:
- Scans loaded modules for deprecated code
- BLOCKS startup if critical deprecated code is imported
- Provides detailed warnings for non-critical deprecations
- Hooks into Python's import system to intercept deprecated modules
"""

import sys
import importlib.abc
import importlib.machinery
from pathlib import Path
from typing import Optional, List
import logging

from .registry import get_registry, DeprecationSeverity
from .warnings import (
    print_deprecation_banner,
    print_critical_deprecation_error,
    print_deprecation_warning,
)

logger = logging.getLogger(__name__)


class ImportBlocker(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """
    Meta path finder that intercepts imports of deprecated modules
    and blocks them or warns about them
    """
    
    def __init__(self):
        self.registry = get_registry()
        self.blocked_imports: List[str] = []
        self.warned_imports: List[str] = []
    
    def find_module(self, fullname: str, path=None):
        """Called when Python tries to import a module"""
        # Convert module name to path-like format
        # e.g., "backend.workflow_v6_integrated" -> "backend/workflow_v6_integrated.py"
        
        if self.registry.is_deprecated(fullname):
            deprecated = self.registry.get(fullname)
            
            if deprecated.severity == DeprecationSeverity.CRITICAL:
                self.blocked_imports.append(fullname)
                raise ImportError(
                    f"\n{'='*90}\n"
                    f"🚫 DEPRECATED MODULE BLOCKED: {fullname}\n"
                    f"{'='*90}\n"
                    f"This module is CRITICAL deprecated as of {deprecated.deprecated_since}\n"
                    f"\nReason: {deprecated.reason}\n"
                    f"Replacement: {deprecated.replacement}\n"
                    f"\n❌ Cannot start server while using deprecated critical modules\n"
                    f"{'='*90}\n"
                )
            elif deprecated.severity == DeprecationSeverity.ERROR:
                self.warned_imports.append(fullname)
                logger.warning(
                    f"⚠️  ERROR-level deprecated module imported: {fullname}\n"
                    f"   Reason: {deprecated.reason}\n"
                    f"   Replacement: {deprecated.replacement}"
                )
        
        return None  # Let normal import machinery handle it


class DeprecationValidator:
    """Main validation orchestrator"""
    
    def __init__(self):
        self.registry = get_registry()
        self.blocker = ImportBlocker()
        self.import_errors: List[str] = []
        self.warnings: List[str] = []
    
    def install_import_hook(self):
        """Install the import blocker into Python's import system"""
        if self.blocker not in sys.meta_path:
            sys.meta_path.insert(0, self.blocker)
            logger.info("✅ Import deprecation hook installed")
    
    def uninstall_import_hook(self):
        """Remove the import blocker"""
        if self.blocker in sys.meta_path:
            sys.meta_path.remove(self.blocker)
            logger.info("ℹ️  Import deprecation hook removed")
    
    def validate_imports(self) -> bool:
        """
        Scan currently loaded modules for deprecated code
        
        Returns:
            True if no critical deprecations found
            False if critical deprecations are being used
        """
        print_deprecation_banner()
        
        deprecated_loaded = []
        
        for module_name, module in sys.modules.items():
            if self.registry.is_deprecated(module_name):
                deprecated = self.registry.get(module_name)
                deprecated_loaded.append(deprecated)
        
        if not deprecated_loaded:
            print("   ✅ No deprecated modules currently loaded\n")
            return True
        
        # Separate by severity
        critical = [m for m in deprecated_loaded if m.severity == DeprecationSeverity.CRITICAL]
        errors = [m for m in deprecated_loaded if m.severity == DeprecationSeverity.ERROR]
        warnings = [m for m in deprecated_loaded if m.severity == DeprecationSeverity.WARNING]
        
        # Show what's loaded
        if warnings:
            print(f"   ⚠️  {len(warnings)} WARNING-level deprecated module(s):")
            for module in warnings:
                print(f"      • {module.module_path}")
            print()
        
        if errors:
            print(f"   ⚠️  {len(errors)} ERROR-level deprecated module(s):")
            for module in errors:
                print(f"      • {module.module_path}")
            print()
        
        if critical:
            print(f"   🚫 {len(critical)} CRITICAL deprecated module(s):")
            for module in critical:
                print(f"      • {module.module_path}")
                print(f"        Reason: {module.reason}")
                print(f"        Replace with: {module.replacement}")
            print()
            return False
        
        return True
    
    def validate_file_access(self, file_path: str) -> bool:
        """
        Check if a file access is trying to load a deprecated module
        
        Args:
            file_path: File path being imported
        
        Returns:
            True if allowed, False if blocked
            
        Raises:
            ImportError if critical deprecation
        """
        # Convert file path to module path
        # e.g., "backend/workflow_v6_integrated.py" -> "backend.workflow_v6_integrated"
        
        path = Path(file_path)
        module_name = str(path).replace("/", ".").replace("\\", ".").replace(".py", "")
        
        if self.registry.is_deprecated(module_name):
            deprecated = self.registry.get(module_name)
            
            if deprecated.severity == DeprecationSeverity.CRITICAL:
                print_critical_deprecation_error(deprecated)
                self.import_errors.append(module_name)
                return False
            else:
                print_deprecation_warning(deprecated)
                self.warnings.append(module_name)
        
        return True
    
    def check_startup_compatibility(self) -> tuple[bool, str]:
        """
        Comprehensive startup check
        
        Returns:
            (is_valid, error_message)
        """
        summary = self.registry.get_summary()
        
        # Check for critical deprecated modules that are loaded
        critical_loaded = []
        for module_name in sys.modules.keys():
            if self.registry.is_critical(module_name):
                critical_loaded.append(module_name)
        
        if critical_loaded:
            return False, (
                f"❌ Cannot start server with CRITICAL deprecated modules loaded:\n"
                f"   {', '.join(critical_loaded)}\n"
                f"Please update your code to use v7 APIs"
            )
        
        # Warn about error-level deprecations
        if summary["error"] > 0:
            logger.warning(
                f"⚠️  {summary['error']} ERROR-level deprecated module(s) exist in codebase. "
                f"Consider updating to v7 APIs."
            )
        
        return True, ""
    
    def print_deprecation_report(self):
        """Print a detailed deprecation report"""
        print("\n" + "=" * 90)
        print("📊 DEPRECATION REPORT")
        print("=" * 90 + "\n")
        
        summary = self.registry.get_summary()
        
        print(f"Total deprecated modules in registry: {summary['total_deprecated']}")
        print(f"  • CRITICAL: {summary['critical']}")
        print(f"  • ERROR:    {summary['error']}")
        print(f"  • WARNING:  {summary['warning']}\n")
        
        if summary['critical'] > 0:
            print("🚫 CRITICAL DEPRECATIONS (Block startup):")
            for module in self.registry.get_all_by_severity(DeprecationSeverity.CRITICAL):
                print(f"   • {module.module_path}")
                print(f"     Reason: {module.reason}")
                print(f"     Replace: {module.replacement}\n")
        
        if summary['error'] > 0:
            print("⚠️  ERROR-LEVEL DEPRECATIONS (Warn loudly):")
            for module in self.registry.get_all_by_severity(DeprecationSeverity.ERROR):
                print(f"   • {module.module_path}")
                print(f"     Reason: {module.reason}\n")
        
        if summary['warning'] > 0:
            print("ℹ️  WARNING-LEVEL DEPRECATIONS (Inform):")
            for module in self.registry.get_all_by_severity(DeprecationSeverity.WARNING):
                print(f"   • {module.module_path}")
                print(f"     Reason: {module.reason}\n")
        
        print("=" * 90 + "\n")


# Global validator instance
_validator = None


def get_validator() -> DeprecationValidator:
    """Get or create the global validator"""
    global _validator
    if _validator is None:
        _validator = DeprecationValidator()
    return _validator


def validate_startup() -> bool:
    """
    Perform startup deprecation validation
    
    Returns:
        True if startup should proceed, False to block
    """
    validator = get_validator()
    return validator.validate_imports()