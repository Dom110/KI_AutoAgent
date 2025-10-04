#!/usr/bin/env python3
"""
Instructions Update Manager for KI AutoAgent
Handles base instructions updates with user control
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import difflib
import argparse
import sys


class InstructionsUpdater:
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.backup_dir = Path(target_dir).parent / "instructions_updates" / "backups"
        self.staging_dir = Path(target_dir).parent / "instructions_updates"

        # Create target dir if it doesn't exist
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def find_changes(self) -> Dict[str, str]:
        """
        Compare source and target instructions.
        Returns: {filename: status}
        Status: 'new', 'changed', 'unchanged', 'deleted'
        """
        changes = {}

        # Check source files
        for source_file in self.source_dir.glob("*.md"):
            target_file = self.target_dir / source_file.name

            if not target_file.exists():
                changes[source_file.name] = 'new'
            else:
                source_hash = self.get_file_hash(source_file)
                target_hash = self.get_file_hash(target_file)

                if source_hash != target_hash:
                    changes[source_file.name] = 'changed'
                else:
                    changes[source_file.name] = 'unchanged'

        # Check for deleted files
        for target_file in self.target_dir.glob("*.md"):
            if not (self.source_dir / target_file.name).exists():
                changes[target_file.name] = 'deleted'

        return changes

    def show_diff(self, filename: str, context_lines: int = 3) -> str:
        """Show diff between source and target file"""
        source_file = self.source_dir / filename
        target_file = self.target_dir / filename

        with open(source_file) as f:
            source_lines = f.readlines()

        with open(target_file) as f:
            target_lines = f.readlines()

        diff = difflib.unified_diff(
            target_lines,
            source_lines,
            fromfile=f'current/{filename}',
            tofile=f'new/{filename}',
            lineterm='',
            n=context_lines
        )

        return '\n'.join(diff)

    def show_summary_diff(self, filename: str) -> str:
        """Show summary of changes"""
        source_file = self.source_dir / filename
        target_file = self.target_dir / filename

        with open(source_file) as f:
            source_lines = f.readlines()

        with open(target_file) as f:
            target_lines = f.readlines()

        # Count added/removed lines
        diff = list(difflib.unified_diff(target_lines, source_lines, lineterm=''))
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return f"+{added} lines, -{removed} lines"

    def update_interactive(self):
        """Interactive update mode"""
        changes = self.find_changes()

        print("\n📊 Instructions Update Summary:")
        print("=" * 60)

        new_files = [f for f, s in changes.items() if s == 'new']
        changed_files = [f for f, s in changes.items() if s == 'changed']
        deleted_files = [f for f, s in changes.items() if s == 'deleted']
        unchanged_files = [f for f, s in changes.items() if s == 'unchanged']

        if new_files:
            print(f"\n🆕 New files ({len(new_files)}):")
            for f in new_files:
                print(f"  + {f}")

        if changed_files:
            print(f"\n✏️  Changed files ({len(changed_files)}):")
            for f in changed_files:
                summary = self.show_summary_diff(f)
                print(f"  ~ {f} ({summary})")

        if deleted_files:
            print(f"\n🗑️  Deleted files ({len(deleted_files)}):")
            for f in deleted_files:
                print(f"  - {f}")

        if unchanged_files:
            print(f"\n✅ Unchanged files ({len(unchanged_files)}):")
            for f in unchanged_files[:3]:  # Show first 3
                print(f"  = {f}")
            if len(unchanged_files) > 3:
                print(f"  ... and {len(unchanged_files) - 3} more")

        if not (new_files or changed_files or deleted_files):
            print("\n✅ No changes detected. All instructions are up to date.")
            return

        print("\n" + "=" * 60)

        # Handle each changed file
        for filename in changed_files:
            print(f"\n📝 {filename}")
            print("-" * 60)

            while True:
                choice = input(
                    "[1] Update (overwrite)\n"
                    "[2] Keep current\n"
                    "[3] Save new as .new (manual merge)\n"
                    "[4] Show diff\n"
                    "Your choice: "
                )

                if choice == '1':
                    self._backup_and_update(filename)
                    print(f"✅ Updated {filename}")
                    break

                elif choice == '2':
                    print(f"⏭️  Kept current {filename}")
                    break

                elif choice == '3':
                    self._save_as_new(filename)
                    print(f"💾 Saved new version as {filename}.new")
                    break

                elif choice == '4':
                    diff = self.show_diff(filename)
                    print("\n" + "─" * 60)
                    print(diff)
                    print("─" * 60 + "\n")
                    # Continue loop to ask again

                else:
                    print("Invalid choice. Please select 1-4.")

        # Handle new files
        if new_files:
            print("\n🆕 New Files")
            print("-" * 60)

        for filename in new_files:
            print(f"\n📄 {filename}")
            choice = input("Install? [Y/n]: ")
            if choice.lower() != 'n':
                shutil.copy(self.source_dir / filename, self.target_dir / filename)
                print(f"✅ Installed {filename}")
            else:
                print(f"⏭️  Skipped {filename}")

    def _backup_and_update(self, filename: str):
        """Backup current and update with new"""
        # Create backup
        backup_path = self.backup_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path.mkdir(parents=True, exist_ok=True)

        target_file = self.target_dir / filename
        if target_file.exists():
            shutil.copy(target_file, backup_path / filename)

        # Update
        shutil.copy(self.source_dir / filename, target_file)

    def _save_as_new(self, filename: str):
        """Save new version as .new file"""
        source_file = self.source_dir / filename
        target_file = self.target_dir / f"{filename}.new"
        shutil.copy(source_file, target_file)

    def update_overwrite(self):
        """Overwrite all (for automated updates)"""
        # Backup all current
        backup_path = self.backup_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path.mkdir(parents=True, exist_ok=True)

        for file in self.target_dir.glob("*.md"):
            shutil.copy(file, backup_path / file.name)

        # Copy all new
        for file in self.source_dir.glob("*.md"):
            shutil.copy(file, self.target_dir / file.name)

        print(f"✅ All instructions updated (backup: {backup_path})")

    def update_preserve(self):
        """Preserve current, only install new files"""
        changes = self.find_changes()
        new_files = [f for f, s in changes.items() if s == 'new']

        if new_files:
            for filename in new_files:
                shutil.copy(self.source_dir / filename, self.target_dir / filename)
                print(f"✅ Installed new file: {filename}")

        changed_count = len([f for f in changes if changes[f] == 'changed'])
        if changed_count > 0:
            print(f"⏭️  Preserved {changed_count} existing file(s)")

        print("✅ Update complete (preserve mode)")

    def update_backup(self):
        """Copy new to staging area for manual merge"""
        # Get version from backend
        version = self._get_version()
        staging_path = self.staging_dir / version
        staging_path.mkdir(parents=True, exist_ok=True)

        changes = self.find_changes()

        # Copy all files to staging
        for filename in self.source_dir.glob("*.md"):
            shutil.copy(filename, staging_path / filename.name)

        # Create CHANGES.md
        with open(staging_path / "CHANGES.md", 'w') as f:
            f.write(f"# Instructions Changes for v{version}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            for status in ['new', 'changed', 'deleted', 'unchanged']:
                files = [f for f, s in changes.items() if s == status]
                if files:
                    f.write(f"- **{status.capitalize()}**: {len(files)} file(s)\n")

            f.write("\n## File Details\n\n")
            for filename, status in sorted(changes.items()):
                f.write(f"### {filename}\n")
                f.write(f"**Status**: {status}\n\n")

                if status == 'changed':
                    summary = self.show_summary_diff(filename)
                    f.write(f"**Changes**: {summary}\n\n")

        print(f"💾 New instructions saved to: {staging_path}")
        print(f"📝 Review {staging_path}/CHANGES.md for details")
        print(f"📂 Merge manually from staging area when ready")

    def _get_version(self) -> str:
        """Get version from backend __version__.py"""
        # Try to find __version__.py
        possible_paths = [
            Path(__file__).parent.parent / "backend" / "__version__.py",
            Path(self.source_dir).parent / "__version__.py",
        ]

        for path in possible_paths:
            if path.exists():
                with open(path) as f:
                    for line in f:
                        if line.startswith("__version__"):
                            version = line.split("=")[1].strip().strip('"').strip("'")
                            return version

        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description='Update KI AutoAgent base instructions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive update (default)
  %(prog)s --source backend/.kiautoagent/instructions --target ~/.ki_autoagent/config/instructions

  # Automated update (overwrite all)
  %(prog)s --source ... --target ... --mode overwrite --no-prompt

  # Keep all existing (only add new files)
  %(prog)s --source ... --target ... --mode preserve

  # Save new to staging area for manual merge
  %(prog)s --source ... --target ... --mode backup
        """
    )

    parser.add_argument('--source', required=True, help='Source instructions directory')
    parser.add_argument('--target', required=True, help='Target instructions directory')
    parser.add_argument('--mode',
                       choices=['install', 'interactive', 'overwrite', 'preserve', 'backup'],
                       default='interactive',
                       help='Update mode (default: interactive)')
    parser.add_argument('--no-prompt', action='store_true',
                       help='Skip all prompts (auto-accept)')

    args = parser.parse_args()

    # Check if source directory exists
    if not Path(args.source).exists():
        print(f"❌ Source directory not found: {args.source}")
        sys.exit(1)

    updater = InstructionsUpdater(args.source, args.target)

    try:
        if args.mode == 'install':
            # First installation - just copy
            print("📝 Installing base instructions...")
            for file in Path(args.source).glob("*.md"):
                shutil.copy(file, Path(args.target) / file.name)
                print(f"   ✓ {file.name}")
            print("✅ Instructions installed")

        elif args.mode == 'interactive' and not args.no_prompt:
            updater.update_interactive()

        elif args.mode == 'overwrite':
            updater.update_overwrite()

        elif args.mode == 'preserve':
            updater.update_preserve()

        elif args.mode == 'backup':
            updater.update_backup()

        else:
            print("❌ Invalid mode or missing --no-prompt for non-interactive mode")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⏸️  Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
