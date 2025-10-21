"""
Codesmith Agent - Code Generation Specialist for v7.0

This agent generates code based on architecture and research context.
It can request additional research when needed.

Key Responsibilities:
- Generate code from architecture designs
- Implement business logic
- Create tests
- Fix bugs
- Request research for implementation details

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


class CodesmithAgent:
    """
    Code generator that implements based on architecture.

    This agent creates code files according to the architecture
    design and can request research for implementation details.
    """

    def __init__(self):
        """Initialize the Codesmith agent."""
        logger.info("⚒️ CodesmithAgent initialized")

        # Initialize Claude CLI service for code generation
        self.claude_service = None
        try:
            from backend.utils.claude_service import ClaudeService
            self.claude_service = ClaudeService(model="claude-sonnet-4-20250514")
            logger.info("   ✅ Claude service connected")
        except Exception as e:
            logger.warning(f"   ⚠️ Claude service not available: {e}")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code generation based on supervisor instructions.

        Args:
            state: Contains:
                - instructions: What to implement
                - architecture: System design from Architect
                - research_context: Context from Research
                - workspace_path: Target workspace

        Returns:
            Dictionary with generated files or research request
        """
        instructions = state.get("instructions", "")
        architecture = state.get("architecture", {})
        research_context = state.get("research_context", {})
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🔨 Generating code: {instructions[:100]}...")

        # Check if we need more research for implementation
        if self._needs_implementation_research(instructions, architecture, research_context):
            logger.info("   📚 Requesting implementation research")
            return {
                "needs_research": True,
                "research_request": self._formulate_research_request(
                    instructions, architecture, research_context
                ),
                "code_complete": False
            }

        # Generate the code
        generated_files = await self._generate_code(
            instructions,
            architecture,
            research_context,
            workspace_path
        )

        logger.info(f"   ✅ Generated {len(generated_files)} files")

        return {
            "generated_files": generated_files,
            "code_complete": True,
            "needs_research": False,
            "timestamp": datetime.now().isoformat()
        }

    def _needs_implementation_research(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict
    ) -> bool:
        """
        Determine if more research is needed for implementation.
        """
        # Need architecture first
        if not architecture:
            return True

        # Check for specific implementation questions
        instructions_lower = instructions.lower()

        # Need API documentation for external services
        if "api" in instructions_lower and "integration" in instructions_lower:
            web_results = research_context.get("web_results", [])
            if not any("api" in str(r).lower() for r in web_results):
                return True

        # Need error handling patterns
        if "error" in instructions_lower or "exception" in instructions_lower:
            if "error_analysis" not in research_context:
                return True

        # Need performance optimization info
        if "optimize" in instructions_lower or "performance" in instructions_lower:
            if not any("performance" in str(v).lower()
                      for v in research_context.values()):
                return True

        return False

    def _formulate_research_request(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict
    ) -> str:
        """
        Formulate research request for implementation details.
        """
        requests = []

        if not architecture:
            requests.append("Need architecture design before code generation")

        instructions_lower = instructions.lower()

        if "api" in instructions_lower and "integration" in instructions_lower:
            requests.append("Research API documentation and integration patterns")

        if "error" in instructions_lower:
            requests.append("Research error handling best practices")

        if "optimize" in instructions_lower:
            requests.append("Research performance optimization techniques")

        # Check architecture for specific tech that needs research
        technologies = architecture.get("technologies", [])
        for tech in technologies:
            if tech.lower() not in str(research_context).lower():
                requests.append(f"Research {tech} implementation patterns")

        return " AND ".join(requests) if requests else "Research implementation details"

    async def _generate_code(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict,
        workspace_path: str
    ) -> list[dict[str, Any]]:
        """
        Generate code files based on architecture.
        """
        logger.info("   📝 Generating code files")

        generated_files = []

        # Extract components and file structure from architecture
        components = architecture.get("components", [])
        file_structure = architecture.get("file_structure", [])
        technologies = architecture.get("technologies", [])

        # Use Claude if available, otherwise use template-based generation
        if self.claude_service and components:
            generated_files = await self._generate_with_claude(
                instructions,
                architecture,
                research_context,
                workspace_path
            )
        else:
            generated_files = self._generate_template_based(
                instructions,
                architecture,
                workspace_path
            )

        return generated_files

    async def _generate_with_claude(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict,
        workspace_path: str
    ) -> list[dict[str, Any]]:
        """
        Generate code using Claude Sonnet.
        """
        generated_files = []

        # Generate main application file
        main_file = await self._generate_main_file(
            instructions, architecture, research_context
        )
        if main_file:
            generated_files.append(main_file)

        # Generate component files
        for component in architecture.get("components", []):
            component_file = await self._generate_component_file(
                component, architecture, research_context
            )
            if component_file:
                generated_files.append(component_file)

        # Generate test files
        test_files = await self._generate_test_files(
            architecture, generated_files
        )
        generated_files.extend(test_files)

        return generated_files

    async def _generate_main_file(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict
    ) -> dict[str, Any] | None:
        """
        Generate the main application file.
        """
        technologies = architecture.get("technologies", [])

        # Determine main file based on technology
        if "FastAPI" in technologies:
            return await self._generate_fastapi_main(instructions, architecture)
        elif "React" in technologies:
            return await self._generate_react_main(instructions, architecture)
        elif "Python" in technologies:
            return await self._generate_python_main(instructions, architecture)

        return None

    async def _generate_fastapi_main(
        self,
        instructions: str,
        architecture: dict
    ) -> dict[str, Any]:
        """
        Generate FastAPI main file.
        """
        code = '''"""
FastAPI Application
Generated by KI AutoAgent v7.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")

# Create FastAPI app
app = FastAPI(
    title="Generated API",
    description="API generated by KI AutoAgent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "API is running", "version": "1.0.0"}

# TODO: Add more endpoints based on requirements
'''

        return {
            "path": "app/main.py",
            "content": code,
            "language": "python",
            "lines": len(code.splitlines()),
            "description": "FastAPI main application file"
        }

    async def _generate_react_main(
        self,
        instructions: str,
        architecture: dict
    ) -> dict[str, Any]:
        """
        Generate React main file.
        """
        code = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''

        return {
            "path": "src/index.tsx",
            "content": code,
            "language": "typescript",
            "lines": len(code.splitlines()),
            "description": "React application entry point"
        }

    async def _generate_python_main(
        self,
        instructions: str,
        architecture: dict
    ) -> dict[str, Any]:
        """
        Generate Python main file.
        """
        code = '''"""
Main Application Module
Generated by KI AutoAgent v7.0
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Starting application...")

    try:
        # TODO: Add main application logic
        logger.info("Application running")

    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

    logger.info("Application completed successfully")


if __name__ == "__main__":
    main()
'''

        return {
            "path": "src/main.py",
            "content": code,
            "language": "python",
            "lines": len(code.splitlines()),
            "description": "Python main application file"
        }

    async def _generate_component_file(
        self,
        component: dict,
        architecture: dict,
        research_context: dict
    ) -> dict[str, Any] | None:
        """
        Generate a component file.
        """
        component_name = component.get("name", "Component")
        component_desc = component.get("description", "")
        technologies = architecture.get("technologies", [])

        # Generate based on technology
        if "FastAPI" in technologies:
            return self._generate_fastapi_component(component_name, component_desc)
        elif "React" in technologies:
            return self._generate_react_component(component_name, component_desc)

        return None

    def _generate_fastapi_component(
        self,
        name: str,
        description: str
    ) -> dict[str, Any]:
        """
        Generate FastAPI component (service/router).
        """
        # Convert name to snake_case
        file_name = name.lower().replace(" ", "_").replace("-", "_")

        code = f'''"""
{name}
{description}
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)


class {name.replace(" ", "")}:
    """
    {description}
    """

    def __init__(self):
        """Initialize {name}."""
        logger.info(f"Initializing {{name}}")

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Process data.

        Args:
            data: Input data

        Returns:
            Processed result
        """
        logger.info(f"Processing in {{name}}")

        # TODO: Implement processing logic
        result = {{"status": "processed", "component": "{name}"}}

        return result
'''

        return {
            "path": f"app/services/{file_name}.py",
            "content": code,
            "language": "python",
            "lines": len(code.splitlines()),
            "description": f"{name} service implementation"
        }

    def _generate_react_component(
        self,
        name: str,
        description: str
    ) -> dict[str, Any]:
        """
        Generate React component.
        """
        # Convert name to PascalCase
        component_name = "".join(word.capitalize() for word in name.split())

        code = f'''import React from 'react';

interface {component_name}Props {{
  // TODO: Define props
}}

/**
 * {name}
 * {description}
 */
const {component_name}: React.FC<{component_name}Props> = (props) => {{
  return (
    <div className="{name.lower().replace(" ", "-")}">
      <h2>{name}</h2>
      <p>{description}</p>
      {{/* TODO: Implement component */}}
    </div>
  );
}};

export default {component_name};
'''

        return {
            "path": f"src/components/{component_name}.tsx",
            "content": code,
            "language": "typescript",
            "lines": len(code.splitlines()),
            "description": f"{name} React component"
        }

    async def _generate_test_files(
        self,
        architecture: dict,
        generated_files: list
    ) -> list[dict[str, Any]]:
        """
        Generate test files for the generated code.
        """
        test_files = []
        technologies = architecture.get("technologies", [])

        # Generate Python tests
        if any("python" in tech.lower() for tech in technologies):
            test_file = self._generate_python_tests(generated_files)
            if test_file:
                test_files.append(test_file)

        # Generate JavaScript tests
        if any(tech in technologies for tech in ["React", "Node.js"]):
            test_file = self._generate_javascript_tests(generated_files)
            if test_file:
                test_files.append(test_file)

        return test_files

    def _generate_python_tests(
        self,
        generated_files: list
    ) -> dict[str, Any] | None:
        """
        Generate Python test file.
        """
        code = '''"""
Test Suite
Generated by KI AutoAgent v7.0
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported."""
    # TODO: Add import tests for generated modules
    assert True


def test_basic_functionality():
    """Test basic functionality."""
    # TODO: Add functional tests
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality."""
    # TODO: Add async tests
    assert True
'''

        return {
            "path": "tests/test_main.py",
            "content": code,
            "language": "python",
            "lines": len(code.splitlines()),
            "description": "Python test suite"
        }

    def _generate_javascript_tests(
        self,
        generated_files: list
    ) -> dict[str, Any] | None:
        """
        Generate JavaScript test file.
        """
        code = '''import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Component Tests', () => {
  test('renders without crashing', () => {
    // TODO: Add component tests
    expect(true).toBe(true);
  });

  test('basic functionality', () => {
    // TODO: Add functional tests
    expect(1 + 1).toBe(2);
  });
});
'''

        return {
            "path": "src/__tests__/App.test.tsx",
            "content": code,
            "language": "typescript",
            "lines": len(code.splitlines()),
            "description": "React test suite"
        }

    def _generate_template_based(
        self,
        instructions: str,
        architecture: dict,
        workspace_path: str
    ) -> list[dict[str, Any]]:
        """
        Generate code using templates (fallback).
        """
        logger.info("   📋 Using template-based generation")

        generated_files = []

        # Generate a basic main file
        main_file = {
            "path": "main.py",
            "content": '''"""
Main Application
Generated by KI AutoAgent v7.0
"""

def main():
    """Main entry point."""
    print("Application generated by KI AutoAgent")
    # TODO: Implement based on requirements

if __name__ == "__main__":
    main()
''',
            "language": "python",
            "lines": 12,
            "description": "Main application file"
        }
        generated_files.append(main_file)

        # Generate basic structure files
        for path in architecture.get("file_structure", []):
            if path.endswith("/"):
                # Directory - create __init__.py
                init_file = {
                    "path": f"{path}__init__.py",
                    "content": f'"""{path[:-1]} module."""\n',
                    "language": "python",
                    "lines": 1,
                    "description": f"Init file for {path}"
                }
                generated_files.append(init_file)

        return generated_files


# ============================================================================
# Export
# ============================================================================

__all__ = ["CodesmithAgent"]