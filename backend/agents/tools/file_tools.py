"""
File System Tools for AI Agents
Provides safe file operations with validation and audit logging
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class FileOperation:
    """Record of a file operation"""
    timestamp: str
    agent_name: str
    operation: str  # create, write, modify, delete
    file_path: str
    success: bool
    error: Optional[str] = None
    backup_path: Optional[str] = None


class FileSystemTools:
    """
    Secure file system operations for AI agents
    Includes validation, backup, and audit logging
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize file system tools

        Args:
            workspace_path: Base workspace path for operations
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.audit_log: List[FileOperation] = []
        self.backup_dir = os.path.join(self.workspace_path, '.ki_autoagent', 'backups')

        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

        # System paths that should never be modified
        self.protected_paths = {
            '/etc', '/usr', '/bin', '/sbin', '/lib', '/boot',
            '/System', '/Windows', 'C:\\Windows', 'C:\\Program Files'
        }

    def _validate_path(self, file_path: str, agent_name: str, allowed_paths: List[str] = None) -> tuple[bool, str]:
        """
        Validate if the path is safe to write to

        Args:
            file_path: Path to validate
            agent_name: Name of the agent requesting access
            allowed_paths: List of allowed path patterns for this agent

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Convert to absolute path
        abs_path = os.path.abspath(os.path.join(self.workspace_path, file_path))

        # Check if path is within workspace
        try:
            Path(abs_path).relative_to(self.workspace_path)
        except ValueError:
            return False, f"Path {file_path} is outside workspace"

        # Check against protected system paths
        for protected in self.protected_paths:
            if abs_path.startswith(protected):
                return False, f"Path {file_path} is in protected system directory"

        # Check against agent's allowed paths if specified
        if allowed_paths:
            path_allowed = False
            for pattern in allowed_paths:
                # Convert glob pattern to check
                if '*' in pattern:
                    # Simple glob matching
                    pattern_base = pattern.replace('**/', '').replace('*', '')
                    if pattern_base in abs_path:
                        path_allowed = True
                        break
                else:
                    # Exact directory match
                    if abs_path.startswith(os.path.abspath(os.path.join(self.workspace_path, pattern))):
                        path_allowed = True
                        break

            if not path_allowed:
                return False, f"Path {file_path} not in allowed paths for agent {agent_name}"

        return True, ""

    def _create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of existing file

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file or None if file doesn't exist
        """
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(file_path)}.{timestamp}.backup"
        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"✅ Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return None

    def _log_operation(self, operation: FileOperation):
        """Log file operation to audit log"""
        self.audit_log.append(operation)

        # Also log to file
        audit_file = os.path.join(self.workspace_path, '.ki_autoagent', 'file_operations.log')
        os.makedirs(os.path.dirname(audit_file), exist_ok=True)

        with open(audit_file, 'a') as f:
            f.write(json.dumps(asdict(operation)) + '\n')

        # Log to logger
        if operation.success:
            logger.info(f"✅ {operation.agent_name} {operation.operation} {operation.file_path}")
        else:
            logger.error(f"❌ {operation.agent_name} failed to {operation.operation} {operation.file_path}: {operation.error}")

    async def write_file(
        self,
        path: str,
        content: str,
        agent_name: str,
        allowed_paths: List[str] = None,
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to a file

        Args:
            path: File path (relative to workspace)
            content: Content to write
            agent_name: Name of agent performing operation
            allowed_paths: List of allowed paths for this agent
            create_dirs: Create parent directories if they don't exist

        Returns:
            Dict with status and details
        """
        # Validate path
        is_valid, error = self._validate_path(path, agent_name, allowed_paths)
        if not is_valid:
            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="write",
                file_path=path,
                success=False,
                error=error
            )
            self._log_operation(operation)
            return {
                "status": "error",
                "error": error,
                "agent": agent_name,
                "path": path
            }

        abs_path = os.path.abspath(os.path.join(self.workspace_path, path))

        # Create parent directories if needed
        if create_dirs:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Create backup if file exists
        backup_path = None
        if os.path.exists(abs_path):
            backup_path = self._create_backup(abs_path)

        # Write the file
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)

            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="write",
                file_path=path,
                success=True,
                backup_path=backup_path
            )
            self._log_operation(operation)

            return {
                "status": "success",
                "path": path,
                "absolute_path": abs_path,
                "agent": agent_name,
                "backup": backup_path,
                "size": len(content)
            }

        except Exception as e:
            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="write",
                file_path=path,
                success=False,
                error=str(e)
            )
            self._log_operation(operation)

            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name,
                "path": path
            }

    async def create_file(
        self,
        path: str,
        content: str,
        agent_name: str,
        allowed_paths: List[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new file

        Args:
            path: File path (relative to workspace)
            content: Content to write
            agent_name: Name of agent performing operation
            allowed_paths: List of allowed paths for this agent
            overwrite: Allow overwriting existing file

        Returns:
            Dict with status and details
        """
        abs_path = os.path.abspath(os.path.join(self.workspace_path, path))

        # Check if file exists
        if os.path.exists(abs_path) and not overwrite:
            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="create",
                file_path=path,
                success=False,
                error="File already exists"
            )
            self._log_operation(operation)

            return {
                "status": "error",
                "error": "File already exists",
                "agent": agent_name,
                "path": path
            }

        # Use write_file for the actual creation
        return await self.write_file(path, content, agent_name, allowed_paths)

    async def modify_file(
        self,
        path: str,
        modifications: List[Dict[str, Any]],
        agent_name: str,
        allowed_paths: List[str] = None
    ) -> Dict[str, Any]:
        """
        Modify an existing file with line-by-line changes

        Args:
            path: File path (relative to workspace)
            modifications: List of modifications with line numbers and content
            agent_name: Name of agent performing operation
            allowed_paths: List of allowed paths for this agent

        Returns:
            Dict with status and details
        """
        abs_path = os.path.abspath(os.path.join(self.workspace_path, path))

        # Check if file exists
        if not os.path.exists(abs_path):
            return {
                "status": "error",
                "error": "File does not exist",
                "agent": agent_name,
                "path": path
            }

        # Validate path
        is_valid, error = self._validate_path(path, agent_name, allowed_paths)
        if not is_valid:
            return {
                "status": "error",
                "error": error,
                "agent": agent_name,
                "path": path
            }

        # Create backup
        backup_path = self._create_backup(abs_path)

        try:
            # Read current content
            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Apply modifications
            for mod in modifications:
                line_num = mod.get('line', -1)
                action = mod.get('action', 'replace')
                content = mod.get('content', '')

                if action == 'replace' and 0 <= line_num < len(lines):
                    lines[line_num] = content + '\n'
                elif action == 'insert' and 0 <= line_num <= len(lines):
                    lines.insert(line_num, content + '\n')
                elif action == 'delete' and 0 <= line_num < len(lines):
                    del lines[line_num]

            # Write modified content
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="modify",
                file_path=path,
                success=True,
                backup_path=backup_path
            )
            self._log_operation(operation)

            return {
                "status": "success",
                "path": path,
                "agent": agent_name,
                "backup": backup_path,
                "modifications": len(modifications)
            }

        except Exception as e:
            operation = FileOperation(
                timestamp=datetime.now().isoformat(),
                agent_name=agent_name,
                operation="modify",
                file_path=path,
                success=False,
                error=str(e)
            )
            self._log_operation(operation)

            # Restore backup if operation failed
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, abs_path)
                logger.info(f"✅ Restored from backup after failed modification")

            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name,
                "path": path
            }

    async def read_file(
        self,
        path: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Read a file (for completeness, agents already have read access)

        Args:
            path: File path (relative to workspace)
            agent_name: Name of agent performing operation

        Returns:
            Dict with status and content
        """
        abs_path = os.path.abspath(os.path.join(self.workspace_path, path))

        if not os.path.exists(abs_path):
            return {
                "status": "error",
                "error": "File does not exist",
                "agent": agent_name,
                "path": path
            }

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "status": "success",
                "path": path,
                "content": content,
                "agent": agent_name,
                "size": len(content)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name,
                "path": path
            }

    def get_audit_log(self, agent_name: Optional[str] = None) -> List[Dict]:
        """
        Get audit log of file operations

        Args:
            agent_name: Filter by agent name (optional)

        Returns:
            List of file operations
        """
        if agent_name:
            return [asdict(op) for op in self.audit_log if op.agent_name == agent_name]
        return [asdict(op) for op in self.audit_log]