#!/usr/bin/env python3
"""
Create/Update version.json for KI AutoAgent installation
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import argparse


def get_version_from_file():
    """Read version from __version__.py"""
    # Try multiple possible paths
    possible_paths = [
        Path(__file__).parent.parent / "backend" / "__version__.py",
        Path.cwd() / "backend" / "__version__.py",
        Path.cwd() / "__version__.py",
    ]

    for version_file in possible_paths:
        if version_file.exists():
            with open(version_file) as f:
                for line in f:
                    if line.startswith("__version__"):
                        version = line.split("=")[1].strip().strip('"').strip("'")
                        return version

    return "unknown"


def create_version_info(install_dir: str, is_update: bool = False):
    """Create or update version.json"""
    install_path = Path(install_dir)
    version_file = install_path / "version.json"

    current_version = get_version_from_file()

    if version_file.exists() and is_update:
        # Update existing
        with open(version_file) as f:
            data = json.load(f)

        # Save previous version
        data["previous_version"] = data.get("installed_version", "unknown")
        data["installed_version"] = current_version
        data["update_date"] = datetime.now().isoformat()
        data["last_update_check"] = datetime.now().isoformat()

        # Preserve other fields
        if "instructions_version" not in data:
            data["instructions_version"] = current_version

    else:
        # Create new
        data = {
            "installed_version": current_version,
            "installation_date": datetime.now().isoformat(),
            "instructions_version": current_version,
            "last_update_check": datetime.now().isoformat()
        }

    # Write version.json
    with open(version_file, 'w') as f:
        json.dump(data, f, indent=2)

    action = "updated" if is_update else "created"
    print(f"   ✓ Version info {action}: {current_version}")


def main():
    parser = argparse.ArgumentParser(description='Create/update KI AutoAgent version info')
    parser.add_argument('--install-dir', required=True, help='Installation directory')
    parser.add_argument('--update', action='store_true', help='Update existing version.json')

    args = parser.parse_args()

    # Check if install directory exists
    if not Path(args.install_dir).exists():
        print(f"❌ Installation directory not found: {args.install_dir}")
        sys.exit(1)

    try:
        create_version_info(args.install_dir, args.update)
    except Exception as e:
        print(f"❌ Error creating version info: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
