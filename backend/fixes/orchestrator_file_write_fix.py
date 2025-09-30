"""
Fix for Orchestrator to properly call file writing methods
Add this to orchestrator_agent_v2.py
"""

async def _execute_subtask_with_file_writing(self, subtask: SubTask, original_request: TaskRequest = None) -> str:
    """
    Enhanced subtask execution that uses file writing methods when appropriate
    """

    # Detect if this is a file writing task
    file_writing_keywords = [
        'implement', 'create file', 'write code', 'generate code',
        'build', 'develop', 'add feature', 'fix bug', 'refactor',
        'create config', 'write test', 'update file'
    ]

    task_lower = subtask.description.lower()
    is_file_task = any(keyword in task_lower for keyword in file_writing_keywords)

    # Extract file path if mentioned
    file_path = self._extract_file_path(subtask.description)

    if is_file_task and subtask.agent == 'codesmith':
        # Use CodeSmithAgent's file writing capability
        agent = self.agent_registry.get_agent('codesmith')
        if agent and hasattr(agent, 'implement_code_to_file'):
            try:
                # Determine file path
                if not file_path:
                    file_path = self._determine_file_path(subtask.description)

                logger.info(f"📝 Instructing CodeSmithAgent to write file: {file_path}")

                result = await agent.implement_code_to_file(
                    spec=subtask.description,
                    file_path=file_path
                )

                if result.get('status') == 'success':
                    return f"✅ Successfully created {file_path} with {result.get('lines', 0)} lines of code"
                else:
                    return f"❌ Failed to create file: {result.get('error')}"

            except Exception as e:
                logger.error(f"File writing failed: {e}")
                # Fall back to regular execution

    elif is_file_task and subtask.agent == 'architect':
        # Use ArchitectAgent's file creation capability
        agent = self.agent_registry.get_agent('architect')
        if agent:
            if 'redis' in task_lower and hasattr(agent, 'create_redis_config'):
                result = await agent.create_redis_config()
                return f"✅ Created Redis configuration: {result.get('file', 'redis.config')}"

            elif 'docker' in task_lower and hasattr(agent, 'create_docker_compose'):
                result = await agent.create_docker_compose()
                return f"✅ Created Docker Compose file: {result.get('file', 'docker-compose.yml')}"

    # Default: Use regular task execution
    return await self._execute_subtask_original(subtask, original_request)

def _extract_file_path(self, description: str) -> str:
    """
    Extract file path from task description
    """
    import re

    # Look for file paths in the description
    patterns = [
        r'(?:file|create|write|update)\s+([a-zA-Z0-9_/.-]+\.(?:py|js|ts|yml|yaml|json|md|txt))',
        r'(?:in|to|at)\s+([a-zA-Z0-9_/.-]+\.(?:py|js|ts|yml|yaml|json|md|txt))',
        r'([a-zA-Z0-9_/.-]+\.(?:py|js|ts|yml|yaml|json|md|txt))'
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def _determine_file_path(self, description: str) -> str:
    """
    Determine appropriate file path based on task description
    """
    task_lower = description.lower()

    # Determine directory based on task type
    if 'test' in task_lower:
        directory = 'backend/tests/'
    elif 'agent' in task_lower:
        directory = 'backend/agents/'
    elif 'api' in task_lower or 'endpoint' in task_lower:
        directory = 'backend/api/'
    elif 'util' in task_lower or 'helper' in task_lower:
        directory = 'backend/utils/'
    elif 'service' in task_lower:
        directory = 'backend/services/'
    elif 'model' in task_lower:
        directory = 'backend/models/'
    else:
        directory = 'backend/'

    # Extract feature/component name
    feature_name = self._extract_feature_name(description)

    # Determine file extension
    if 'config' in task_lower:
        extension = '.yml'
    elif 'docker' in task_lower:
        extension = '.yml'
        feature_name = 'docker-compose'
    elif 'test' in task_lower:
        extension = '.py'
        feature_name = f'test_{feature_name}'
    else:
        extension = '.py'

    return f"{directory}{feature_name}{extension}"

def _extract_feature_name(self, description: str) -> str:
    """
    Extract feature name from description
    """
    import re

    # Remove common words
    stop_words = ['implement', 'create', 'add', 'build', 'write', 'fix', 'update',
                  'the', 'a', 'an', 'for', 'with', 'to', 'in', 'feature', 'function']

    words = description.lower().split()
    feature_words = [w for w in words if w not in stop_words and len(w) > 2]

    if feature_words:
        # Take first meaningful word and convert to snake_case
        feature = feature_words[0].replace('-', '_')
        return feature

    return 'new_feature'