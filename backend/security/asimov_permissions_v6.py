"""
Asimov Permissions Manager v6.2

Implements permission-based access control for AI agents.

Design Philosophy:
- DENY BY DEFAULT: All actions denied unless explicitly permitted
- LEAST PRIVILEGE: Agents get minimum permissions needed
- EXPLICIT GRANTS: Permissions require justification
- AUDITABLE: All permission checks logged

Permission Types:
- CAN_WRITE_FILES: Write/create files in workspace
- CAN_DELETE_FILES: Delete files (dangerous!)
- CAN_EXECUTE_CODE: Execute shell commands
- CAN_WEB_SEARCH: Access Perplexity/web search
- CAN_INSTALL_PACKAGES: Install npm/pip packages
- CAN_MODIFY_SYSTEM: Modify system files (.env, config)
- CAN_READ_FILES: Read files (usually granted to all)

Default Agent Permissions:
- research: CAN_WEB_SEARCH, CAN_READ_FILES
- architect: CAN_WRITE_FILES (ADR only), CAN_READ_FILES
- codesmith: CAN_WRITE_FILES, CAN_READ_FILES
- reviewfix: CAN_WRITE_FILES, CAN_READ_FILES
- supervisor: CAN_READ_FILES only

Integration:
- File Tools: Check permissions before write/delete
- Tool Registry: Filter tools based on permissions
- Workflow: Track permission usage and violations

Author: KI AutoAgent Team
Version: 6.2.0
Python: 3.13+
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Available permissions for AI agents."""

    CAN_READ_FILES = "can_read_files"
    CAN_WRITE_FILES = "can_write_files"
    CAN_DELETE_FILES = "can_delete_files"
    CAN_EXECUTE_CODE = "can_execute_code"
    CAN_WEB_SEARCH = "can_web_search"
    CAN_INSTALL_PACKAGES = "can_install_packages"
    CAN_MODIFY_SYSTEM = "can_modify_system"


class PermissionDenied(Exception):
    """Exception raised when permission is denied."""

    def __init__(self, agent_id: str, permission: Permission, action: str):
        self.agent_id = agent_id
        self.permission = permission
        self.action = action
        super().__init__(
            f"Permission denied: {agent_id} lacks {permission.value} for action '{action}'"
        )


class AsimovPermissionsManager:
    """
    Manage agent permissions (Asimov-compliant).

    Default policy: DENY ALL, explicit grants only.

    Example:
        manager = AsimovPermissionsManager()

        # Check permission
        if manager.check_permission("codesmith", Permission.CAN_WRITE_FILES):
            # Write file
            pass

        # Enforce permission (raises PermissionDenied)
        await manager.check_and_enforce(
            agent_id="research",
            action="write_file('/tmp/test.py')",
            permission=Permission.CAN_WRITE_FILES
        )
    """

    def __init__(self):
        """Initialize permissions manager with default agent permissions."""

        # Default permissions per agent
        self.agent_permissions: dict[str, set[Permission]] = {
            # Research Agent: Web search + read only
            "research": {
                Permission.CAN_WEB_SEARCH,
                Permission.CAN_READ_FILES
            },

            # Architect Agent: Write ADR files + read
            "architect": {
                Permission.CAN_WRITE_FILES,  # Architecture Decision Records only
                Permission.CAN_READ_FILES
            },

            # Codesmith Agent: Write code files + read
            "codesmith": {
                Permission.CAN_WRITE_FILES,
                Permission.CAN_READ_FILES,
                Permission.CAN_EXECUTE_CODE  # For running formatters
            },

            # ReviewFix Agent: Write fixes + read
            "reviewfix": {
                Permission.CAN_WRITE_FILES,
                Permission.CAN_READ_FILES
            },

            # Fixer (legacy name)
            "fixer": {
                Permission.CAN_WRITE_FILES,
                Permission.CAN_READ_FILES
            },

            # Reviewer Agent: Read-only
            "reviewer": {
                Permission.CAN_READ_FILES
            },

            # Supervisor Agent: Read-only (orchestrates, doesn't modify)
            "supervisor": {
                Permission.CAN_READ_FILES
            }
        }

        # Permission audit log
        self.audit_log: list[dict[str, Any]] = []

        # Permission usage stats
        self.stats: dict[str, dict[str, int]] = {}

        logger.info("🔐 Asimov Permissions Manager initialized")
        logger.info(f"  Default agents: {len(self.agent_permissions)}")

    def check_permission(
        self,
        agent_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if agent has permission.

        Args:
            agent_id: Agent identifier
            permission: Required permission

        Returns:
            True if permitted, False otherwise

        Example:
            if manager.check_permission("codesmith", Permission.CAN_WRITE_FILES):
                # Agent has permission
                pass
        """
        agent_perms = self.agent_permissions.get(agent_id, set())
        has_permission = permission in agent_perms

        # Log check
        self._log_audit(
            agent_id=agent_id,
            permission=permission,
            action="check",
            result="granted" if has_permission else "denied"
        )

        return has_permission

    def grant_permission(
        self,
        agent_id: str,
        permission: Permission,
        reason: str,
        granted_by: str = "system"
    ) -> bool:
        """
        Grant permission to agent (requires justification).

        Args:
            agent_id: Agent identifier
            permission: Permission to grant
            reason: Justification for grant (REQUIRED)
            granted_by: Who granted this permission

        Returns:
            True if granted, False if denied

        Example:
            manager.grant_permission(
                agent_id="research",
                permission=Permission.CAN_WRITE_FILES,
                reason="Research needs to save findings to markdown files",
                granted_by="admin"
            )
        """
        if not reason:
            logger.error(f"❌ Permission grant DENIED: No reason provided")
            return False

        logger.info(f"🔓 Permission grant request: {agent_id} → {permission.value}")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Granted by: {granted_by}")

        if agent_id not in self.agent_permissions:
            self.agent_permissions[agent_id] = set()

        self.agent_permissions[agent_id].add(permission)

        # Log grant
        self._log_audit(
            agent_id=agent_id,
            permission=permission,
            action="grant",
            result="success",
            metadata={
                "reason": reason,
                "granted_by": granted_by
            }
        )

        logger.info(f"  ✅ Permission granted")
        return True

    def revoke_permission(
        self,
        agent_id: str,
        permission: Permission,
        reason: str = "manual_revoke"
    ) -> bool:
        """
        Revoke permission from agent.

        Args:
            agent_id: Agent identifier
            permission: Permission to revoke
            reason: Reason for revocation

        Returns:
            True if revoked, False if agent didn't have permission
        """
        if agent_id in self.agent_permissions:
            if permission in self.agent_permissions[agent_id]:
                self.agent_permissions[agent_id].discard(permission)

                # Log revoke
                self._log_audit(
                    agent_id=agent_id,
                    permission=permission,
                    action="revoke",
                    result="success",
                    metadata={"reason": reason}
                )

                logger.info(f"🔒 Permission revoked: {agent_id} → {permission.value}")
                return True

        return False

    async def check_and_enforce(
        self,
        agent_id: str,
        action: str,
        permission: Permission,
        raise_on_deny: bool = False
    ) -> tuple[bool, str]:
        """
        Check permission and enforce policy.

        Args:
            agent_id: Agent identifier
            action: Action description (for logging)
            permission: Required permission
            raise_on_deny: If True, raises PermissionDenied exception

        Returns:
            (allowed, message)

        Raises:
            PermissionDenied: If permission denied and raise_on_deny=True

        Example:
            allowed, msg = await manager.check_and_enforce(
                agent_id="research",
                action="write_file('/tmp/findings.md')",
                permission=Permission.CAN_WRITE_FILES,
                raise_on_deny=True  # Will raise exception if denied
            )
        """
        if self.check_permission(agent_id, permission):
            # Track usage stats
            self._track_usage(agent_id, permission)

            logger.debug(f"✅ Permission granted: {agent_id} → {action}")
            return (True, "Permission granted")

        # Permission denied
        logger.warning(f"🚫 Permission denied: {agent_id} → {action}")
        logger.warning(f"   Required: {permission.value}")
        logger.warning(f"   Agent permissions: {self.get_agent_permissions(agent_id)}")

        message = f"Agent {agent_id} lacks permission: {permission.value}"

        if raise_on_deny:
            raise PermissionDenied(agent_id, permission, action)

        return (False, message)

    def get_agent_permissions(self, agent_id: str) -> list[str]:
        """
        Get list of permissions for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of permission values (e.g., ["can_read_files", "can_write_files"])
        """
        perms = self.agent_permissions.get(agent_id, set())
        return [p.value for p in perms]

    def get_all_agents(self) -> list[dict[str, Any]]:
        """
        Get all agents and their permissions.

        Returns:
            List of dicts with agent_id and permissions
        """
        return [
            {
                "agent_id": agent_id,
                "permissions": [p.value for p in perms]
            }
            for agent_id, perms in self.agent_permissions.items()
        ]

    def get_audit_log(self, agent_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get permission audit log.

        Args:
            agent_id: Filter by agent (None = all agents)
            limit: Maximum entries to return

        Returns:
            List of audit log entries
        """
        if agent_id is None:
            return self.audit_log[-limit:]

        filtered = [
            entry for entry in self.audit_log
            if entry["agent_id"] == agent_id
        ]
        return filtered[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """
        Get permission usage statistics.

        Returns:
            Dict with:
            - total_checks: Total permission checks
            - total_grants: Total permission grants
            - total_denials: Total permission denials
            - by_agent: Stats per agent
            - by_permission: Stats per permission
        """
        total_checks = len([e for e in self.audit_log if e["action"] == "check"])
        total_grants = len([e for e in self.audit_log if e["action"] == "grant"])
        total_denials = len([e for e in self.audit_log if e["action"] == "check" and e["result"] == "denied"])

        by_agent = {}
        by_permission = {}

        for entry in self.audit_log:
            agent = entry["agent_id"]
            perm = entry["permission"]

            if agent not in by_agent:
                by_agent[agent] = {"checks": 0, "grants": 0, "denials": 0}
            if perm not in by_permission:
                by_permission[perm] = {"checks": 0, "grants": 0, "denials": 0}

            if entry["action"] == "check":
                by_agent[agent]["checks"] += 1
                by_permission[perm]["checks"] += 1
                if entry["result"] == "denied":
                    by_agent[agent]["denials"] += 1
                    by_permission[perm]["denials"] += 1
            elif entry["action"] == "grant":
                by_agent[agent]["grants"] += 1
                by_permission[perm]["grants"] += 1

        return {
            "total_checks": total_checks,
            "total_grants": total_grants,
            "total_denials": total_denials,
            "by_agent": by_agent,
            "by_permission": by_permission
        }

    def _log_audit(
        self,
        agent_id: str,
        permission: Permission,
        action: str,
        result: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Log permission check/grant/revoke to audit log.

        Args:
            agent_id: Agent identifier
            permission: Permission involved
            action: Action type (check, grant, revoke)
            result: Result (granted, denied, success)
            metadata: Additional metadata
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "permission": permission.value,
            "action": action,
            "result": result,
            "metadata": metadata or {}
        }

        self.audit_log.append(entry)

        # Keep audit log size manageable (last 10,000 entries)
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def _track_usage(self, agent_id: str, permission: Permission) -> None:
        """
        Track permission usage statistics.

        Args:
            agent_id: Agent identifier
            permission: Permission used
        """
        if agent_id not in self.stats:
            self.stats[agent_id] = {}

        perm_key = permission.value
        if perm_key not in self.stats[agent_id]:
            self.stats[agent_id][perm_key] = 0

        self.stats[agent_id][perm_key] += 1


# Global permissions manager instance
_permissions_manager: AsimovPermissionsManager | None = None


def get_permissions_manager() -> AsimovPermissionsManager:
    """Get global permissions manager instance."""
    global _permissions_manager
    if _permissions_manager is None:
        _permissions_manager = AsimovPermissionsManager()
    return _permissions_manager


# Export
__all__ = [
    "AsimovPermissionsManager",
    "Permission",
    "PermissionDenied",
    "get_permissions_manager"
]
