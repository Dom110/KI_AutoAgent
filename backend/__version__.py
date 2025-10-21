from __future__ import annotations

"""
KI AutoAgent Backend Version Information

Version 7.0.0-alpha - Supervisor Pattern Migration
"""

# Version numbers - Single source of truth
__version__ = "7.0.0-alpha"
__version_info__ = (7, 0, 0)
__release_tag__ = "v7.0.0-alpha-supervisor"
__release_date__ = "2025-10-20"
__author__ = "KI AutoAgent Team"
__description__ = (
    "Supervisor Pattern Architecture with Central Orchestration"
)

# Version string with 'v' prefix for display
__version_display__ = f"v{__version__}"


def get_version():
    """Return the current version as a string"""
    return __version__


def get_version_tuple():
    """Return the current version as a tuple of integers"""
    return __version_info__


def is_compatible(required_version):
    """Check if current version is compatible with required version"""
    if isinstance(required_version, str):
        required = tuple(map(int, required_version.split(".")))
    else:
        required = required_version

    # Major version must match for compatibility
    return __version_info__[0] == required[0]
