"""
KI AutoAgent Backend Version Information

Version 4.0.21 - Fail-Fast Architecture & No Fallbacks
"""

__version__ = "4.0.21"
__version_info__ = (4, 0, 21)
__release_date__ = "2025-09-24"
__author__ = "KI AutoAgent Team"
__description__ = "Cognitive AI Development Platform with Self-Understanding Capabilities"

def get_version():
    """Return the current version as a string"""
    return __version__

def get_version_tuple():
    """Return the current version as a tuple of integers"""
    return __version_info__

def is_compatible(required_version):
    """Check if current version is compatible with required version"""
    if isinstance(required_version, str):
        required = tuple(map(int, required_version.split('.')))
    else:
        required = required_version

    # Major version must match for compatibility
    return __version_info__[0] == required[0]