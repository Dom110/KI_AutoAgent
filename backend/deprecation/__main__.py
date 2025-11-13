"""
Entry point for running deprecation CLI as a module

Usage:
    python -m backend.deprecation report
    python -m backend.deprecation check
    python -m backend.deprecation list
    python -m backend.deprecation migrate <key>
    python -m backend.deprecation info
"""

from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())