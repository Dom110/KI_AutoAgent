"""
Enhancement for TaskRequest to include file writing directive
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class EnhancedTaskRequest:
    """Enhanced task request with file writing support"""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    write_files: bool = False  # NEW: Flag to force file writing
    target_files: List[str] = field(default_factory=list)  # NEW: Expected files
    implementation_mode: str = "text"  # NEW: "text" or "files"

    def to_file_task(self, file_path: str = None):
        """Convert to file writing task"""
        self.write_files = True
        self.implementation_mode = "files"
        if file_path:
            self.target_files.append(file_path)
        return self


# Enhancement for Orchestrator task decomposition
def enhance_subtask_for_file_writing(subtask: dict) -> dict:
    """
    Enhance subtask to include file writing directive
    """
    task_desc = subtask.get('description', '').lower()

    # Detect implementation tasks
    if any(keyword in task_desc for keyword in ['implement', 'create', 'build', 'write']):
        subtask['write_files'] = True
        subtask['expected_output'] = {
            'type': 'files',
            'format': 'actual_files',
            'validation': 'file_exists'
        }

        # Add specific file writing instruction
        if 'codesmith' in subtask.get('agent', '').lower():
            subtask['instruction'] = "USE implement_code_to_file() to create actual files"
        elif 'architect' in subtask.get('agent', '').lower():
            subtask['instruction'] = "USE create_file() to create actual configuration files"

    return subtask


# Example usage in Orchestrator
async def decompose_task_with_file_writing(self, prompt: str) -> List[dict]:
    """
    Enhanced task decomposition that ensures file writing
    """
    # Original decomposition
    subtasks = await self._original_decompose(prompt)

    # Enhance each subtask
    enhanced_subtasks = []
    for subtask in subtasks:
        enhanced = enhance_subtask_for_file_writing(subtask)
        enhanced_subtasks.append(enhanced)

    # Log file writing tasks
    file_tasks = [st for st in enhanced_subtasks if st.get('write_files')]
    if file_tasks:
        logger.info(f"📝 {len(file_tasks)} subtasks will write actual files")

    return enhanced_subtasks