"""
🎨 Deprecation Warnings - Visual warning system with colored output

Provides clear, actionable deprecation warnings that developers can't miss
"""

from typing import Optional
from .registry import DeprecatedModule, DeprecationSeverity


class Colors:
    """ANSI color codes"""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class DeprecationWarning:
    """Represents a deprecation warning"""
    
    def __init__(self, module: DeprecatedModule):
        self.module = module
    
    def __str__(self) -> str:
        return self.format()
    
    def format(self) -> str:
        """Format the warning message"""
        if self.module.severity == DeprecationSeverity.CRITICAL:
            return self._format_critical()
        elif self.module.severity == DeprecationSeverity.ERROR:
            return self._format_error()
        else:
            return self._format_warning()
    
    def _format_critical(self) -> str:
        """Format CRITICAL severity warning"""
        lines = [
            "\n" + "=" * 90,
            f"{Colors.RED}{Colors.BOLD}🚫 CRITICAL DEPRECATION - STARTUP BLOCKED{Colors.END}",
            "=" * 90,
            f"\n{Colors.BOLD}Module:{Colors.END} {self.module.module_path}",
            f"{Colors.BOLD}File:{Colors.END} {self.module.file_path}",
            f"{Colors.BOLD}Deprecated Since:{Colors.END} {self.module.deprecated_since}",
            f"\n{Colors.BOLD}Reason:{Colors.END}\n  {self.module.reason}",
            f"\n{Colors.BOLD}Replacement:{Colors.END}\n  {self.module.replacement}",
        ]
        
        if self.module.features_missing:
            lines.append(f"\n{Colors.BOLD}Features NOT in v7:{Colors.END}")
            for feature in self.module.features_missing:
                lines.append(f"  ❌ {feature}")
        
        lines.extend([
            f"\n{Colors.BOLD}Migration Effort:{Colors.END} {self.module.migration_effort}",
            f"{Colors.BOLD}Contact:{Colors.END} {self.module.contact}",
            "\n" + "=" * 90 + "\n",
        ])
        
        return "\n".join(lines)
    
    def _format_error(self) -> str:
        """Format ERROR severity warning"""
        lines = [
            "\n" + "-" * 90,
            f"{Colors.YELLOW}{Colors.BOLD}⚠️  ERROR-LEVEL DEPRECATION{Colors.END}",
            "-" * 90,
            f"\n{Colors.BOLD}Module:{Colors.END} {self.module.module_path}",
            f"{Colors.BOLD}File:{Colors.END} {self.module.file_path}",
            f"\n{Colors.BOLD}Reason:{Colors.END}\n  {self.module.reason}",
            f"\n{Colors.BOLD}Replacement:{Colors.END}\n  {self.module.replacement}",
            f"\n{Colors.BOLD}Migration Effort:{Colors.END} {self.module.migration_effort}",
            "\n" + "-" * 90 + "\n",
        ]
        
        return "\n".join(lines)
    
    def _format_warning(self) -> str:
        """Format WARNING severity warning"""
        lines = [
            f"\n{Colors.CYAN}ℹ️  {self.module.module_path}",
            f"   {self.module.reason}",
            f"   → Use: {self.module.replacement}{Colors.END}\n",
        ]
        
        return "\n".join(lines)


def print_deprecation_banner():
    """Print the deprecation check banner"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔍 DEPRECATION VALIDATION{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 90}{Colors.END}")


def print_critical_deprecation_error(module: DeprecatedModule):
    """Print a critical deprecation error"""
    warning = DeprecationWarning(module)
    print(warning.format())


def print_deprecation_warning(module: DeprecatedModule):
    """Print a deprecation warning"""
    warning = DeprecationWarning(module)
    print(warning.format())


def print_migration_guide(migration_key: str):
    """Print migration guide (stub - will be expanded)"""
    from .migration_guides import get_migration_guide
    
    guide = get_migration_guide(migration_key)
    if guide:
        print(f"\n{Colors.GREEN}{Colors.BOLD}📖 Migration Guide{Colors.END}")
        print(f"{Colors.GREEN}{'=' * 90}{Colors.END}")
        print(guide)
        print(f"{Colors.GREEN}{'=' * 90}{Colors.END}\n")


def print_startup_deprecation_report(validator):
    """Print a startup deprecation report"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 90}")
    print("📋 STARTUP DEPRECATION CHECK")
    print(f"{'=' * 90}{Colors.END}\n")
    
    is_valid, error_msg = validator.check_startup_compatibility()
    
    if is_valid:
        print(f"{Colors.GREEN}✅ All deprecation checks passed{Colors.END}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}{error_msg}{Colors.END}\n")
        return False
    
    return True


def print_critical_modules_blocking_startup(modules: list):
    """Print critical modules that are blocking startup"""
    if not modules:
        return
    
    print(f"\n{Colors.RED}{Colors.BOLD}{'=' * 90}")
    print("🚫 CRITICAL MODULES BLOCKING STARTUP")
    print(f"{'=' * 90}{Colors.END}\n")
    
    for module_name in modules:
        print(f"{Colors.RED}  • {module_name}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Fix: Remove usage of these modules and migrate to v7 APIs{Colors.END}\n")


def format_feature_comparison(deprecated_features: list, replacements: list) -> str:
    """Format a comparison between old and new features"""
    output = ["\n" + "=" * 90]
    output.append(f"{Colors.BOLD}Feature Comparison{Colors.END}\n")
    
    max_len = max(len(f) for f in deprecated_features + replacements)
    
    output.append(f"{Colors.RED}❌ v6 (DEPRECATED){Colors.END:<{max_len + 20}} {Colors.GREEN}✅ v7 (NEW){Colors.END}")
    output.append("-" * 90)
    
    max_features = max(len(deprecated_features), len(replacements))
    for i in range(max_features):
        old_feature = deprecated_features[i] if i < len(deprecated_features) else ""
        new_feature = replacements[i] if i < len(replacements) else ""
        output.append(f"{Colors.RED}{old_feature:<40}{Colors.END} → {Colors.GREEN}{new_feature}{Colors.END}")
    
    output.append("=" * 90 + "\n")
    return "\n".join(output)