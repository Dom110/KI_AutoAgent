"""
Instruction merger for handling additional instructions during pause
ASIMOV RULE 3: Check for ALL conflicts, not just the first one
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts between instructions"""
    CONTRADICTION = "contradiction"
    SCOPE_CHANGE = "scope_change"
    PRIORITY_CONFLICT = "priority_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    SAFETY_CONCERN = "safety_concern"


@dataclass
class InstructionConflict:
    """Represents a conflict between instructions"""
    type: ConflictType
    description: str
    original_instruction: str
    new_instruction: str
    severity: str  # 'high', 'medium', 'low'
    resolution_options: List[str]


class InstructionMerger:
    """
    Merges additional instructions with current task
    Detects and resolves conflicts
    """

    def __init__(self):
        self.conflict_patterns = self._load_conflict_patterns()

    def _load_conflict_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """Load patterns for detecting conflicts"""
        return {
            'contradictions': [
                (r'create|add|implement', r'remove|delete|eliminate'),
                (r'increase|maximize|more', r'decrease|minimize|less'),
                (r'async|asynchronous', r'sync|synchronous'),
                (r'public|open', r'private|restricted'),
                (r'enable|activate', r'disable|deactivate'),
                (r'optimize for speed', r'optimize for memory'),
                (r'use\s+(\w+)', r'don\'t use\s+\1'),
            ],
            'scope_changes': [
                (r'entire|whole|all', r'specific|single|only'),
                (r'global', r'local'),
                (r'project-wide', r'file-specific'),
                (r'all\s+files', r'this\s+file'),
            ],
            'safety_concerns': [
                (r'delete\s+all', r''),
                (r'drop\s+database', r''),
                (r'rm\s+-rf', r''),
                (r'force\s+push', r''),
                (r'ignore\s+errors', r''),
                (r'skip\s+validation', r''),
            ]
        }

    async def detect_conflicts(
        self,
        current_task: str,
        new_instructions: str,
        context: Dict[str, Any] = None
    ) -> List[InstructionConflict]:
        """
        Detect conflicts between current task and new instructions
        ASIMOV RULE 3: Find ALL conflicts, not just the first
        """
        conflicts = []

        # Check for direct contradictions
        contradictions = self._find_contradictions(current_task, new_instructions)
        conflicts.extend(contradictions)

        # Check for scope changes
        scope_changes = self._find_scope_changes(current_task, new_instructions)
        conflicts.extend(scope_changes)

        # Check for safety concerns
        safety_issues = self._find_safety_concerns(new_instructions)
        conflicts.extend(safety_issues)

        # Check for priority conflicts
        priority_conflicts = self._find_priority_conflicts(current_task, new_instructions, context)
        conflicts.extend(priority_conflicts)

        return conflicts

    def _find_contradictions(self, current: str, new: str) -> List[InstructionConflict]:
        """Find direct contradictions between instructions"""
        conflicts = []
        current_lower = current.lower()
        new_lower = new.lower()

        for pattern1, pattern2 in self.conflict_patterns['contradictions']:
            # Check if current has pattern1 and new has pattern2
            if re.search(pattern1, current_lower) and re.search(pattern2, new_lower):
                conflicts.append(InstructionConflict(
                    type=ConflictType.CONTRADICTION,
                    description=f"Instructions contradict: '{pattern1}' vs '{pattern2}'",
                    original_instruction=self._extract_context(current, pattern1),
                    new_instruction=self._extract_context(new, pattern2),
                    severity='high',
                    resolution_options=[
                        'Use new instruction (replace)',
                        'Keep original instruction',
                        'Merge both (may cause issues)',
                        'Request clarification'
                    ]
                ))
            # Check reverse
            elif re.search(pattern2, current_lower) and re.search(pattern1, new_lower):
                conflicts.append(InstructionConflict(
                    type=ConflictType.CONTRADICTION,
                    description=f"Instructions contradict: '{pattern2}' vs '{pattern1}'",
                    original_instruction=self._extract_context(current, pattern2),
                    new_instruction=self._extract_context(new, pattern1),
                    severity='high',
                    resolution_options=[
                        'Use new instruction (replace)',
                        'Keep original instruction',
                        'Request clarification'
                    ]
                ))

        return conflicts

    def _find_scope_changes(self, current: str, new: str) -> List[InstructionConflict]:
        """Find scope changes between instructions"""
        conflicts = []
        current_lower = current.lower()
        new_lower = new.lower()

        for broad_pattern, narrow_pattern in self.conflict_patterns['scope_changes']:
            if re.search(broad_pattern, current_lower) and re.search(narrow_pattern, new_lower):
                conflicts.append(InstructionConflict(
                    type=ConflictType.SCOPE_CHANGE,
                    description=f"Scope narrowed from '{broad_pattern}' to '{narrow_pattern}'",
                    original_instruction=self._extract_context(current, broad_pattern),
                    new_instruction=self._extract_context(new, narrow_pattern),
                    severity='medium',
                    resolution_options=[
                        'Accept scope change',
                        'Keep original scope',
                        'Apply to both scopes'
                    ]
                ))

        return conflicts

    def _find_safety_concerns(self, new: str) -> List[InstructionConflict]:
        """Find safety concerns in new instructions"""
        conflicts = []
        new_lower = new.lower()

        for dangerous_pattern, _ in self.conflict_patterns['safety_concerns']:
            if re.search(dangerous_pattern, new_lower):
                conflicts.append(InstructionConflict(
                    type=ConflictType.SAFETY_CONCERN,
                    description=f"Potentially dangerous operation: '{dangerous_pattern}'",
                    original_instruction="",
                    new_instruction=self._extract_context(new, dangerous_pattern),
                    severity='high',
                    resolution_options=[
                        'Confirm dangerous operation',
                        'Cancel operation',
                        'Modify to safe alternative'
                    ]
                ))

        return conflicts

    def _find_priority_conflicts(
        self,
        current: str,
        new: str,
        context: Dict[str, Any]
    ) -> List[InstructionConflict]:
        """Find priority conflicts"""
        conflicts = []

        # Check for conflicting optimization priorities
        if 'performance' in current.lower() and 'readability' in new.lower():
            conflicts.append(InstructionConflict(
                type=ConflictType.PRIORITY_CONFLICT,
                description="Conflicting priorities: performance vs readability",
                original_instruction="Optimize for performance",
                new_instruction="Optimize for readability",
                severity='low',
                resolution_options=[
                    'Balance both priorities',
                    'Prioritize performance',
                    'Prioritize readability'
                ]
            ))

        return conflicts

    def _extract_context(self, text: str, pattern: str, context_chars: int = 50) -> str:
        """Extract context around a pattern match"""
        match = re.search(pattern, text.lower())
        if match:
            start = max(0, match.start() - context_chars)
            end = min(len(text), match.end() + context_chars)
            return f"...{text[start:end]}..."
        return text[:100] + "..." if len(text) > 100 else text

    async def merge_instructions(
        self,
        current_task: str,
        new_instructions: str,
        resolution_strategy: str = 'append'
    ) -> Dict[str, Any]:
        """
        Merge new instructions with current task
        ASIMOV RULE 2: Complete implementation of merge
        """
        if resolution_strategy == 'replace':
            return {
                'merged': new_instructions,
                'strategy': 'replaced',
                'original': current_task
            }

        elif resolution_strategy == 'append':
            merged = f"{current_task}\n\nAdditional instructions:\n{new_instructions}"
            return {
                'merged': merged,
                'strategy': 'appended',
                'original': current_task
            }

        elif resolution_strategy == 'prepend':
            merged = f"Priority instructions:\n{new_instructions}\n\nOriginal task:\n{current_task}"
            return {
                'merged': merged,
                'strategy': 'prepended',
                'original': current_task
            }

        elif resolution_strategy == 'smart_merge':
            # Intelligent merging based on content analysis
            merged = await self._smart_merge(current_task, new_instructions)
            return {
                'merged': merged,
                'strategy': 'smart_merged',
                'original': current_task
            }

        else:
            raise ValueError(f"Unknown merge strategy: {resolution_strategy}")

    async def _smart_merge(self, current: str, new: str) -> str:
        """
        Intelligently merge instructions based on content
        """
        # Parse both instructions
        current_parts = self._parse_instructions(current)
        new_parts = self._parse_instructions(new)

        # Merge parts intelligently
        merged_parts = {
            'goal': new_parts.get('goal') or current_parts.get('goal'),
            'requirements': list(set(
                current_parts.get('requirements', []) +
                new_parts.get('requirements', [])
            )),
            'constraints': list(set(
                current_parts.get('constraints', []) +
                new_parts.get('constraints', [])
            )),
            'notes': current_parts.get('notes', '') + '\n' + new_parts.get('notes', '')
        }

        # Reconstruct merged instructions
        merged = []
        if merged_parts['goal']:
            merged.append(f"Goal: {merged_parts['goal']}")
        if merged_parts['requirements']:
            merged.append(f"Requirements:\n" + '\n'.join(f"- {r}" for r in merged_parts['requirements']))
        if merged_parts['constraints']:
            merged.append(f"Constraints:\n" + '\n'.join(f"- {c}" for c in merged_parts['constraints']))
        if merged_parts['notes'].strip():
            merged.append(f"Notes: {merged_parts['notes'].strip()}")

        return '\n\n'.join(merged)

    def _parse_instructions(self, text: str) -> Dict[str, Any]:
        """Parse instructions into structured components"""
        parts = {
            'goal': None,
            'requirements': [],
            'constraints': [],
            'notes': ''
        }

        lines = text.split('\n')
        current_section = 'notes'

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if line.lower().startswith('goal:'):
                parts['goal'] = line[5:].strip()
            elif line.lower().startswith('requirement') or line.lower().startswith('- '):
                if line.startswith('- '):
                    parts['requirements'].append(line[2:].strip())
                current_section = 'requirements'
            elif line.lower().startswith('constraint'):
                current_section = 'constraints'
            elif current_section == 'requirements' and line.startswith('  '):
                parts['requirements'].append(line.strip())
            elif current_section == 'constraints' and line.startswith('  '):
                parts['constraints'].append(line.strip())
            else:
                parts['notes'] += line + '\n'

        return parts

    async def request_clarification(
        self,
        conflicts: List[InstructionConflict],
        current_task: str,
        new_instructions: str
    ) -> Dict[str, Any]:
        """
        Format clarification request for user
        """
        clarification = {
            'type': 'CLARIFICATION_NEEDED',
            'conflicts': [],
            'current_task': current_task,
            'new_instructions': new_instructions,
            'options': []
        }

        for conflict in conflicts:
            clarification['conflicts'].append({
                'type': conflict.type.value,
                'description': conflict.description,
                'severity': conflict.severity,
                'original': conflict.original_instruction,
                'new': conflict.new_instruction,
                'resolution_options': conflict.resolution_options
            })

        # Add global options
        clarification['options'] = [
            {'id': 'replace_all', 'label': 'Replace entire task with new instructions'},
            {'id': 'append_all', 'label': 'Add new instructions to current task'},
            {'id': 'cancel', 'label': 'Cancel new instructions and continue'},
            {'id': 'stop', 'label': 'Stop task and rollback'},
            {'id': 'custom', 'label': 'Resolve conflicts individually'}
        ]

        return clarification