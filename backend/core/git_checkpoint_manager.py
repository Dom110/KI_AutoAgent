"""
Git Checkpoint Manager for v6 Workflow System

Manages git-based checkpoints for workflow state with automatic commits and rollback.

Features:
- Automatic git commits at checkpoints
- Branch creation for experiments
- Rollback support
- Diff viewing
- Commit history tracking

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitCheckpointManager:
    """
    Manages git-based checkpoints for workflow state.

    Features:
    - Automatic git commits for checkpoints
    - Branch creation and switching
    - Rollback to previous checkpoints
    - View diffs between checkpoints
    - List commit history

    Usage:
        manager = GitCheckpointManager(workspace_path="/path/to/workspace")

        # Create checkpoint (auto-commit)
        checkpoint_id = await manager.create_checkpoint(
            name="after_architecture",
            message="Completed architecture design"
        )

        # Create experimental branch
        branch_id = await manager.create_branch("experiment_1")

        # Rollback to checkpoint
        await manager.rollback_to_checkpoint(checkpoint_id)

        # View diff
        diff = await manager.get_diff(checkpoint_id)
    """

    def __init__(
        self,
        workspace_path: str,
        auto_init: bool = True
    ):
        """
        Initialize Git Checkpoint Manager.

        Args:
            workspace_path: Path to workspace (git repository)
            auto_init: Auto-initialize git repo if not exists
        """
        self.workspace_path = Path(workspace_path)

        # Checkpoints (checkpoint_id -> metadata)
        self._checkpoints: dict[str, dict[str, Any]] = {}

        # Branches (branch_id -> metadata)
        self._branches: dict[str, dict[str, Any]] = {}

        logger.info("✅ GitCheckpointManager initialized")
        logger.info(f"   Workspace: {self.workspace_path}")

        # Initialize git if needed
        if auto_init:
            asyncio.create_task(self._ensure_git_repo())

    async def _ensure_git_repo(self):
        """Ensure git repository exists."""
        try:
            # Check if .git exists
            git_dir = self.workspace_path / ".git"

            if not git_dir.exists():
                logger.info("🔧 Initializing git repository...")

                result = await asyncio.create_subprocess_exec(
                    "git", "init",
                    cwd=str(self.workspace_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                await result.wait()

                if result.returncode == 0:
                    logger.info("✅ Git repository initialized")
                else:
                    logger.error("❌ Failed to initialize git repository")

        except Exception as e:
            logger.error(f"❌ Git initialization failed: {e}")

    async def create_checkpoint(
        self,
        name: str,
        message: str | None = None,
        auto_commit: bool = True,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Create checkpoint (git commit).

        Args:
            name: Checkpoint name
            message: Commit message (default: auto-generated)
            auto_commit: Auto-commit changes (default: True)
            metadata: Additional metadata

        Returns:
            Checkpoint ID (git commit hash)

        Raises:
            RuntimeError: If git commit fails
        """
        try:
            # Generate checkpoint ID
            checkpoint_id = f"checkpoint_{datetime.now().timestamp()}"

            # Auto-generate message if not provided
            if message is None:
                message = f"Checkpoint: {name}"

            # Add all changes
            if auto_commit:
                add_result = await asyncio.create_subprocess_exec(
                    "git", "add", ".",
                    cwd=str(self.workspace_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                await add_result.wait()

            # Create commit
            commit_result = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await commit_result.communicate()

            if commit_result.returncode == 0:
                # Get commit hash
                hash_result = await asyncio.create_subprocess_exec(
                    "git", "rev-parse", "HEAD",
                    cwd=str(self.workspace_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                hash_stdout, _ = await hash_result.communicate()
                commit_hash = hash_stdout.decode().strip()

                # Store checkpoint metadata
                self._checkpoints[checkpoint_id] = {
                    "checkpoint_id": checkpoint_id,
                    "name": name,
                    "message": message,
                    "commit_hash": commit_hash,
                    "created_at": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }

                logger.info(f"📍 Checkpoint created: {name}")
                logger.info(f"   Commit: {commit_hash[:8]}")

                return checkpoint_id

            else:
                # Check if no changes to commit
                error = stderr.decode()

                if "nothing to commit" in error:
                    logger.info(f"ℹ️  No changes to commit for checkpoint: {name}")

                    # Still create checkpoint metadata (pointing to current commit)
                    hash_result = await asyncio.create_subprocess_exec(
                        "git", "rev-parse", "HEAD",
                        cwd=str(self.workspace_path),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                    hash_stdout, _ = await hash_result.communicate()
                    commit_hash = hash_stdout.decode().strip()

                    self._checkpoints[checkpoint_id] = {
                        "checkpoint_id": checkpoint_id,
                        "name": name,
                        "message": message,
                        "commit_hash": commit_hash,
                        "created_at": datetime.now().isoformat(),
                        "metadata": metadata or {}
                    }

                    return checkpoint_id

                else:
                    logger.error(f"❌ Git commit failed: {error}")
                    raise RuntimeError(f"Git commit failed: {error}")

        except Exception as e:
            logger.error(f"❌ Checkpoint creation failed: {e}", exc_info=True)
            raise RuntimeError(f"Checkpoint creation failed: {e}") from e

    async def list_checkpoints(self) -> list[dict[str, Any]]:
        """
        List all checkpoints.

        Returns:
            List of checkpoint metadata
        """
        return list(self._checkpoints.values())

    async def get_checkpoint(
        self,
        checkpoint_id: str
    ) -> dict[str, Any] | None:
        """
        Get checkpoint metadata.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint metadata or None
        """
        return self._checkpoints.get(checkpoint_id)

    async def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
        create_branch: bool = True
    ) -> bool:
        """
        Rollback to checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to rollback to
            create_branch: Create branch before rollback (safe mode)

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If checkpoint not found
            RuntimeError: If git rollback fails
        """
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        try:
            commit_hash = checkpoint["commit_hash"]

            # Create branch if requested (safe mode)
            if create_branch:
                branch_name = f"before_rollback_{datetime.now().timestamp()}"

                branch_result = await asyncio.create_subprocess_exec(
                    "git", "branch", branch_name,
                    cwd=str(self.workspace_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                await branch_result.wait()

                if branch_result.returncode == 0:
                    logger.info(f"📌 Created backup branch: {branch_name}")

            # Reset to checkpoint
            reset_result = await asyncio.create_subprocess_exec(
                "git", "reset", "--hard", commit_hash,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await reset_result.communicate()

            if reset_result.returncode == 0:
                logger.info(f"⏮️  Rolled back to checkpoint: {checkpoint['name']}")
                logger.info(f"   Commit: {commit_hash[:8]}")
                return True

            else:
                error = stderr.decode()
                logger.error(f"❌ Git reset failed: {error}")
                raise RuntimeError(f"Git reset failed: {error}")

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}", exc_info=True)
            raise RuntimeError(f"Rollback failed: {e}") from e

    async def create_branch(
        self,
        branch_name: str,
        from_checkpoint: str | None = None
    ) -> str:
        """
        Create new branch.

        Args:
            branch_name: Branch name
            from_checkpoint: Checkpoint to branch from (default: current)

        Returns:
            Branch ID

        Raises:
            RuntimeError: If branch creation fails
        """
        try:
            # Get starting point
            if from_checkpoint:
                checkpoint = self._checkpoints.get(from_checkpoint)

                if not checkpoint:
                    raise ValueError(f"Checkpoint not found: {from_checkpoint}")

                start_point = checkpoint["commit_hash"]

            else:
                start_point = "HEAD"

            # Create branch
            branch_result = await asyncio.create_subprocess_exec(
                "git", "branch", branch_name, start_point,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await branch_result.communicate()

            if branch_result.returncode == 0:
                # Store branch metadata
                branch_id = f"branch_{datetime.now().timestamp()}"

                self._branches[branch_id] = {
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "from_checkpoint": from_checkpoint,
                    "created_at": datetime.now().isoformat()
                }

                logger.info(f"🌿 Branch created: {branch_name}")

                return branch_id

            else:
                error = stderr.decode()
                logger.error(f"❌ Branch creation failed: {error}")
                raise RuntimeError(f"Branch creation failed: {error}")

        except Exception as e:
            logger.error(f"❌ Branch creation failed: {e}", exc_info=True)
            raise RuntimeError(f"Branch creation failed: {e}") from e

    async def switch_branch(
        self,
        branch_name: str
    ) -> bool:
        """
        Switch to branch.

        Args:
            branch_name: Branch name to switch to

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If checkout fails
        """
        try:
            checkout_result = await asyncio.create_subprocess_exec(
                "git", "checkout", branch_name,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await checkout_result.communicate()

            if checkout_result.returncode == 0:
                logger.info(f"🔄 Switched to branch: {branch_name}")
                return True

            else:
                error = stderr.decode()
                logger.error(f"❌ Checkout failed: {error}")
                raise RuntimeError(f"Checkout failed: {error}")

        except Exception as e:
            logger.error(f"❌ Branch switch failed: {e}", exc_info=True)
            raise RuntimeError(f"Branch switch failed: {e}") from e

    async def get_diff(
        self,
        checkpoint_id: str,
        compare_to: str | None = None
    ) -> str:
        """
        Get diff for checkpoint.

        Args:
            checkpoint_id: Checkpoint ID
            compare_to: Compare to this checkpoint (default: previous commit)

        Returns:
            Diff output

        Raises:
            ValueError: If checkpoint not found
            RuntimeError: If diff fails
        """
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        try:
            commit_hash = checkpoint["commit_hash"]

            # Get diff target
            if compare_to:
                compare_checkpoint = self._checkpoints.get(compare_to)

                if not compare_checkpoint:
                    raise ValueError(f"Compare checkpoint not found: {compare_to}")

                diff_target = compare_checkpoint["commit_hash"]

            else:
                diff_target = f"{commit_hash}^"  # Previous commit

            # Get diff
            diff_result = await asyncio.create_subprocess_exec(
                "git", "diff", diff_target, commit_hash,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await diff_result.communicate()

            if diff_result.returncode == 0:
                return stdout.decode()

            else:
                error = stderr.decode()
                logger.error(f"❌ Diff failed: {error}")
                raise RuntimeError(f"Diff failed: {error}")

        except Exception as e:
            logger.error(f"❌ Diff retrieval failed: {e}", exc_info=True)
            raise RuntimeError(f"Diff retrieval failed: {e}") from e

    async def get_commit_history(
        self,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get git commit history.

        Args:
            limit: Number of commits to retrieve

        Returns:
            List of commit info
        """
        try:
            log_result = await asyncio.create_subprocess_exec(
                "git", "log", f"-{limit}", "--pretty=format:%H|%s|%an|%at",
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await log_result.communicate()

            if log_result.returncode == 0:
                commits = []

                for line in stdout.decode().strip().split('\n'):
                    if line:
                        parts = line.split('|')

                        if len(parts) >= 4:
                            commits.append({
                                "commit_hash": parts[0],
                                "message": parts[1],
                                "author": parts[2],
                                "timestamp": datetime.fromtimestamp(int(parts[3])).isoformat()
                            })

                return commits

            else:
                logger.error(f"❌ Git log failed: {stderr.decode()}")
                return []

        except Exception as e:
            logger.error(f"❌ Commit history retrieval failed: {e}")
            return []


# Global singleton
_git_checkpoint_instance: GitCheckpointManager | None = None


def get_git_checkpoint_manager(
    workspace_path: str | None = None
) -> GitCheckpointManager:
    """
    Get global GitCheckpointManager instance (singleton).

    Args:
        workspace_path: Workspace path (required on first call)

    Returns:
        Global GitCheckpointManager instance

    Raises:
        ValueError: If workspace_path not provided on first call
    """
    global _git_checkpoint_instance

    if _git_checkpoint_instance is None:
        if workspace_path is None:
            raise ValueError("workspace_path required for first call")

        _git_checkpoint_instance = GitCheckpointManager(workspace_path)

    return _git_checkpoint_instance
