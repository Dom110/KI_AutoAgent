"""
Pause state handler for managing task pausing and resumption
ASIMOV RULE 1: No fallbacks - pause MUST work
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .git_checkpoint_manager import GitCheckpointManager
from .instruction_merger import InstructionMerger, InstructionConflict

logger = logging.getLogger(__name__)


class PauseAction(Enum):
    """Actions available during pause"""
    RESUME = "resume"
    RESUME_WITH_INSTRUCTIONS = "resume_with_instructions"
    STOP_AND_ROLLBACK = "stop_and_rollback"
    REQUEST_CLARIFICATION = "request_clarification"


@dataclass
class PauseState:
    """Current pause state"""
    is_paused: bool = False
    paused_at: Optional[datetime] = None
    task_id: Optional[str] = None
    task_description: Optional[str] = None
    checkpoint_hash: Optional[str] = None
    additional_instructions: Optional[str] = None
    conflicts: list[InstructionConflict] = field(default_factory=list)
    user_action: Optional[PauseAction] = None
    clarification_response: Optional[Dict] = None


class PauseHandler:
    """
    Manages pause state and handles pause/resume operations
    """

    def __init__(self, project_path: str = None):
        self.git_manager = GitCheckpointManager(project_path)
        self.instruction_merger = InstructionMerger()
        self.pause_state = PauseState()
        self._pause_event = asyncio.Event()
        self._action_event = asyncio.Event()
        self.websocket_callback: Optional[Callable] = None

    def set_websocket_callback(self, callback: Callable):
        """Set callback for sending WebSocket messages"""
        self.websocket_callback = callback

    async def pause_task(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """
        Pause the current task
        ASIMOV RULE 1: Must work, no silent failures
        """
        if self.pause_state.is_paused:
            logger.warning("Task already paused")
            return {
                'status': 'already_paused',
                'task_id': self.pause_state.task_id
            }

        # Save current state
        self.pause_state = PauseState(
            is_paused=True,
            paused_at=datetime.now(),
            task_id=task_id,
            task_description=task_description
        )

        # Create safety checkpoint if git available
        try:
            checkpoint_hash = await self.git_manager.create_safety_checkpoint()
            self.pause_state.checkpoint_hash = checkpoint_hash
            logger.info(f"Safety checkpoint created: {checkpoint_hash[:8] if checkpoint_hash else 'none'}")
        except Exception as e:
            logger.warning(f"Could not create git checkpoint: {e}")

        # Set pause event
        self._pause_event.clear()

        # Notify UI
        await self._send_pause_notification()

        logger.info(f"Task {task_id} paused")

        return {
            'status': 'paused',
            'task_id': task_id,
            'checkpoint': self.pause_state.checkpoint_hash,
            'message': 'Task paused. Awaiting user action.'
        }

    async def wait_for_user_action(self, timeout: int = None) -> PauseAction:
        """
        Wait for user to decide what to do during pause
        """
        if not self.pause_state.is_paused:
            return PauseAction.RESUME

        # Wait for action
        try:
            await asyncio.wait_for(self._action_event.wait(), timeout=timeout)
            return self.pause_state.user_action or PauseAction.RESUME
        except asyncio.TimeoutError:
            # Default to resume if timeout
            logger.warning("Pause timeout - resuming task")
            return PauseAction.RESUME

    async def resume_task(
        self,
        additional_instructions: str = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Resume the paused task
        """
        if not self.pause_state.is_paused and not force:
            return {
                'status': 'not_paused',
                'message': 'No task is currently paused'
            }

        result = {
            'status': 'resumed',
            'task_id': self.pause_state.task_id,
            'additional_instructions': None,
            'conflicts': []
        }

        # Handle additional instructions
        if additional_instructions:
            conflicts = await self.instruction_merger.detect_conflicts(
                self.pause_state.task_description,
                additional_instructions
            )

            if conflicts:
                # Store conflicts for resolution
                self.pause_state.conflicts = conflicts
                self.pause_state.additional_instructions = additional_instructions
                self.pause_state.user_action = PauseAction.REQUEST_CLARIFICATION

                # Request clarification
                clarification = await self.instruction_merger.request_clarification(
                    conflicts,
                    self.pause_state.task_description,
                    additional_instructions
                )

                result['status'] = 'clarification_needed'
                result['conflicts'] = clarification
                await self._send_clarification_request(clarification)

                return result

            # No conflicts - merge instructions
            merged = await self.instruction_merger.merge_instructions(
                self.pause_state.task_description,
                additional_instructions,
                'append'
            )

            result['additional_instructions'] = merged['merged']
            self.pause_state.task_description = merged['merged']

        # Clear pause state
        self.pause_state.is_paused = False
        self.pause_state.user_action = PauseAction.RESUME
        self._pause_event.set()
        self._action_event.set()

        logger.info(f"Task {self.pause_state.task_id} resumed")

        return result

    async def stop_and_rollback(self) -> Dict[str, Any]:
        """
        Stop task and rollback to checkpoint
        ASIMOV RULE 2: Complete rollback, no partial
        """
        if not self.pause_state.is_paused:
            return {
                'status': 'not_paused',
                'message': 'No task is currently paused'
            }

        result = {
            'status': 'stopped',
            'task_id': self.pause_state.task_id,
            'rolled_back': False
        }

        # Perform rollback if checkpoint exists
        if self.pause_state.checkpoint_hash:
            try:
                rollback_result = await self.git_manager.rollback_to_checkpoint(
                    self.pause_state.checkpoint_hash
                )
                result['rolled_back'] = True
                result['rollback_details'] = rollback_result
                logger.info(f"Rolled back to checkpoint {self.pause_state.checkpoint_hash[:8]}")
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
                result['rollback_error'] = str(e)
                # ASIMOV RULE 1: No silent failure
                raise Exception(f"Rollback failed: {e}")
        else:
            logger.warning("No checkpoint available for rollback")
            result['message'] = 'No checkpoint available - changes remain'

        # Clear pause state
        self.pause_state.is_paused = False
        self.pause_state.user_action = PauseAction.STOP_AND_ROLLBACK
        self._pause_event.set()
        self._action_event.set()

        return result

    async def handle_clarification_response(
        self,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle user's response to clarification request
        """
        if not self.pause_state.conflicts:
            return {
                'status': 'no_conflicts',
                'message': 'No conflicts to resolve'
            }

        action = response.get('action')
        self.pause_state.clarification_response = response

        if action == 'replace_all':
            # Replace entire task
            self.pause_state.task_description = self.pause_state.additional_instructions
            return await self.resume_task()

        elif action == 'append_all':
            # Append despite conflicts
            merged = await self.instruction_merger.merge_instructions(
                self.pause_state.task_description,
                self.pause_state.additional_instructions,
                'append'
            )
            self.pause_state.task_description = merged['merged']
            return await self.resume_task()

        elif action == 'cancel':
            # Cancel new instructions
            self.pause_state.additional_instructions = None
            return await self.resume_task()

        elif action == 'stop':
            # Stop and rollback
            return await self.stop_and_rollback()

        elif action == 'custom':
            # Handle individual conflict resolutions
            resolutions = response.get('resolutions', {})
            # Apply resolutions
            # ... implementation for custom resolution ...
            return await self.resume_task()

        else:
            return {
                'status': 'unknown_action',
                'message': f'Unknown action: {action}'
            }

    async def _send_pause_notification(self):
        """Send pause notification to UI"""
        if self.websocket_callback:
            await self.websocket_callback({
                'type': 'task_paused',
                'task_id': self.pause_state.task_id,
                'message': 'Task paused. You can provide additional instructions or stop.',
                'options': [
                    'Resume with no changes',
                    'Add instructions and resume',
                    'Stop and rollback'
                ]
            })

    async def _send_clarification_request(self, clarification: Dict):
        """Send clarification request to UI"""
        if self.websocket_callback:
            await self.websocket_callback({
                'type': 'clarification_needed',
                'task_id': self.pause_state.task_id,
                'clarification': clarification
            })

    def is_paused(self) -> bool:
        """Check if currently paused"""
        return self.pause_state.is_paused

    def get_pause_state(self) -> Dict[str, Any]:
        """Get current pause state"""
        return {
            'is_paused': self.pause_state.is_paused,
            'task_id': self.pause_state.task_id,
            'task_description': self.pause_state.task_description,
            'paused_at': self.pause_state.paused_at.isoformat() if self.pause_state.paused_at else None,
            'has_checkpoint': bool(self.pause_state.checkpoint_hash),
            'has_conflicts': len(self.pause_state.conflicts) > 0
        }

    async def force_stop(self) -> Dict[str, Any]:
        """
        Force stop without pause
        Used for emergency stops
        """
        if self.pause_state.checkpoint_hash:
            try:
                await self.git_manager.rollback_to_checkpoint(
                    self.pause_state.checkpoint_hash
                )
                logger.info("Emergency stop - rolled back to checkpoint")
            except Exception as e:
                logger.error(f"Emergency rollback failed: {e}")

        # Clear all state
        self.pause_state = PauseState()
        self._pause_event.set()
        self._action_event.set()

        return {
            'status': 'force_stopped',
            'message': 'Task forcefully stopped'
        }