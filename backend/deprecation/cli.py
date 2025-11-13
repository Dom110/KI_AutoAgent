"""
🛠️  Deprecation System CLI Tool

Usage:
    python -m backend.deprecation report          # Show full deprecation report
    python -m backend.deprecation check            # Check startup compatibility
    python -m backend.deprecation migrate <key>   # Show migration guide
    python -m backend.deprecation list             # List all deprecated modules
    python -m backend.deprecation watch            # Watch for deprecated imports
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .registry import get_registry, DeprecationSeverity
from .validator import get_validator
from .warnings import print_deprecation_banner, Colors, format_feature_comparison
from .migration_guides import get_migration_guide, get_all_migration_guides


def cmd_report():
    """Show comprehensive deprecation report"""
    validator = get_validator()
    validator.print_deprecation_report()


def cmd_check():
    """Check startup compatibility"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔍 CHECKING STARTUP COMPATIBILITY{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 90}{Colors.END}\n")
    
    validator = get_validator()
    is_valid, error_msg = validator.check_startup_compatibility()
    
    if is_valid:
        print(f"{Colors.GREEN}✅ All deprecation checks passed{Colors.END}")
        print(f"{Colors.GREEN}   Server can start successfully{Colors.END}\n")
    else:
        print(f"{Colors.RED}❌ Startup compatibility check failed{Colors.END}")
        print(f"{Colors.RED}{error_msg}{Colors.END}\n")
        return 1
    
    return 0


def cmd_migrate(guide_key: Optional[str] = None):
    """Show migration guide"""
    if not guide_key:
        # List all available guides
        print(f"\n{Colors.CYAN}{Colors.BOLD}📖 AVAILABLE MIGRATION GUIDES{Colors.END}")
        print(f"{Colors.CYAN}{'=' * 90}{Colors.END}\n")
        
        guides = get_all_migration_guides()
        for key, content in guides.items():
            first_line = content.split('\n')[0]
            print(f"  • {Colors.BOLD}{key}{Colors.END}")
            print(f"    {first_line}\n")
        
        print(f"Usage: python -m backend.deprecation migrate <key>\n")
        return 0
    
    print(f"\n{Colors.BOLD}{'=' * 90}")
    print(f"📖 MIGRATION GUIDE: {guide_key}")
    print(f"{'=' * 90}{Colors.END}\n")
    
    guide = get_migration_guide(guide_key)
    if guide:
        print(guide)
        return 0
    else:
        print(f"{Colors.RED}❌ Migration guide not found: {guide_key}{Colors.END}")
        print(f"\nAvailable guides:")
        guides = get_all_migration_guides()
        for key in guides.keys():
            print(f"  • {key}")
        print()
        return 1


def cmd_list():
    """List all deprecated modules"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}📋 DEPRECATED MODULES REGISTRY{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 90}{Colors.END}\n")
    
    registry = get_registry()
    summary = registry.get_summary()
    
    print(f"Total deprecated: {summary['total_deprecated']}")
    print(f"  • CRITICAL: {summary['critical']}")
    print(f"  • ERROR:    {summary['error']}")
    print(f"  • WARNING:  {summary['warning']}\n")
    
    # Group by severity
    print(f"{Colors.RED}{Colors.BOLD}🚫 CRITICAL (Blocks Startup){Colors.END}")
    print(f"{Colors.RED}{'=' * 90}{Colors.END}")
    critical = registry.get_all_by_severity(DeprecationSeverity.CRITICAL)
    if critical:
        for module in critical:
            print(f"  {module.module_path}")
            print(f"    → {module.reason}")
            print(f"    → Replace: {module.replacement}")
            print()
    else:
        print(f"  {Colors.GREEN}None{Colors.END}\n")
    
    print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  ERROR (Warns Loudly){Colors.END}")
    print(f"{Colors.YELLOW}{'=' * 90}{Colors.END}")
    errors = registry.get_all_by_severity(DeprecationSeverity.ERROR)
    if errors:
        for module in errors:
            print(f"  {module.module_path}")
            print(f"    → {module.reason}")
            print()
    else:
        print(f"  {Colors.GREEN}None{Colors.END}\n")
    
    print(f"{Colors.CYAN}{Colors.BOLD}ℹ️  WARNING (Informational){Colors.END}")
    print(f"{Colors.CYAN}{'=' * 90}{Colors.END}")
    warnings = registry.get_all_by_severity(DeprecationSeverity.WARNING)
    if warnings:
        for module in warnings:
            print(f"  {module.module_path}")
            print(f"    → {module.reason}")
            print()
    else:
        print(f"  {Colors.GREEN}None{Colors.END}\n")


def cmd_watch():
    """Watch for deprecated imports (running server)"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}👀 WATCHING FOR DEPRECATED IMPORTS{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 90}{Colors.END}\n")
    
    print(f"This command monitors Python imports during server execution.")
    print(f"Start your server and this will report any deprecated modules.\n")
    
    print(f"📌 To use this feature:")
    print(f"  1. Add deprecation monitoring to your application")
    print(f"  2. The import blocker will intercept deprecated imports")
    print(f"  3. Check logs for deprecation warnings\n")
    
    print(f"🔍 Alternative: Use Python's warnings module:")
    print(f"  python -W all backend/api/server_v7_mcp.py\n")


def cmd_info():
    """Show information about deprecation system"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 90}")
    print(f"KI AutoAgent Deprecation Management System")
    print(f"{'=' * 90}{Colors.END}\n")
    
    print(f"Version: 1.0.0")
    print(f"Status: ✅ Active\n")
    
    print(f"{Colors.BOLD}Purpose:{Colors.END}")
    print(f"  Manages deprecated modules and guides developers through migrations\n")
    
    print(f"{Colors.BOLD}How it works:{Colors.END}")
    print(f"  1. Registry: Tracks all deprecated modules")
    print(f"  2. Validator: Checks imports at runtime")
    print(f"  3. Warnings: Shows clear, actionable warnings")
    print(f"  4. Guides: Provides migration documentation\n")
    
    print(f"{Colors.BOLD}Severity Levels:{Colors.END}")
    print(f"  🚫 CRITICAL  - Blocks startup if loaded")
    print(f"  ⚠️  ERROR     - Warns loudly but allows startup")
    print(f"  ℹ️  WARNING   - Informational warnings\n")
    
    print(f"{Colors.BOLD}Available Commands:{Colors.END}")
    print(f"  report              - Show comprehensive report")
    print(f"  check               - Check startup compatibility")
    print(f"  migrate [key]       - Show migration guide")
    print(f"  list                - List all deprecated modules")
    print(f"  watch               - Watch for deprecated imports")
    print(f"  info                - Show this information\n")
    
    print(f"{Colors.BOLD}Learn More:{Colors.END}")
    print(f"  cat backend/deprecation/DEPRECATION_SYSTEM.md\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="KI AutoAgent Deprecation Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.deprecation report
  python -m backend.deprecation check
  python -m backend.deprecation migrate v6_to_v7_workflow
  python -m backend.deprecation list
  python -m backend.deprecation info
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # report command
    subparsers.add_parser("report", help="Show comprehensive deprecation report")
    
    # check command
    subparsers.add_parser("check", help="Check startup compatibility")
    
    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Show migration guide")
    migrate_parser.add_argument("key", nargs="?", default=None, help="Migration guide key")
    
    # list command
    subparsers.add_parser("list", help="List all deprecated modules")
    
    # watch command
    subparsers.add_parser("watch", help="Watch for deprecated imports")
    
    # info command
    subparsers.add_parser("info", help="Show deprecation system information")
    
    args = parser.parse_args()
    
    # Route to command handler
    if args.command == "report":
        cmd_report()
        return 0
    elif args.command == "check":
        return cmd_check()
    elif args.command == "migrate":
        return cmd_migrate(args.key if hasattr(args, 'key') else None)
    elif args.command == "list":
        cmd_list()
        return 0
    elif args.command == "watch":
        cmd_watch()
        return 0
    elif args.command == "info":
        cmd_info()
        return 0
    else:
        cmd_info()
        return 0


if __name__ == "__main__":
    sys.exit(main())