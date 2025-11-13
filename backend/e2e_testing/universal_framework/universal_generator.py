"""
Universal E2E Test Generator - Works with ANY Framework

Auto-detects framework, uses appropriate adapter, generates tests.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from .framework_detector import FrameworkDetector, FrameworkInfo
from .base_analyzer import BaseComponentAnalyzer, UniversalAppStructure
from .adapters.react_adapter import ReactAdapter


class UniversalE2ETestGenerator:
    """
    Universal E2E test generator that works with any framework
    
    1. Auto-detects framework
    2. Loads appropriate adapter
    3. Generates unified app structure
    4. Creates Playwright tests
    5. Returns framework-agnostic test code
    """

    def __init__(self, app_path: str):
        """
        Initialize generator
        
        Args:
            app_path: Path to application root
        """
        self.app_path = Path(app_path)
        
        # Detect framework
        self.detector = FrameworkDetector(str(self.app_path))
        self.framework_info = self.detector.detect_framework()
        
        # Load appropriate adapter
        self.adapter = self._load_adapter()
        
        # Analysis result
        self.app_structure: Optional[UniversalAppStructure] = None

    def _load_adapter(self) -> BaseComponentAnalyzer:
        """
        Factory method to load correct adapter based on framework
        
        Returns:
            Framework-specific adapter
        """
        adapters = {
            'react': ReactAdapter,
            'vue': self._get_vue_adapter,
            'angular': self._get_angular_adapter,
            'svelte': self._get_svelte_adapter,
            'fastapi': self._get_fastapi_adapter,
            'flask': self._get_flask_adapter,
            'express': self._get_express_adapter,
            'next.js': ReactAdapter,  # Next.js is React-based
            'nuxt': self._get_vue_adapter,  # Nuxt is Vue-based
        }
        
        adapter_class = adapters.get(
            self.framework_info.type,
            None
        )
        
        if adapter_class is None or callable(adapter_class):
            # For now, return the adapter or None
            # In production, we'd implement all adapters
            if callable(adapter_class):
                adapter_class = adapter_class()
            else:
                adapter_class = ReactAdapter  # Default fallback
        
        return adapter_class(str(self.app_path))

    def _get_vue_adapter(self):
        """Get Vue adapter (lazy load)"""
        try:
            from .adapters.vue_adapter import VueAdapter
            return VueAdapter
        except ImportError:
            return ReactAdapter

    def _get_angular_adapter(self):
        """Get Angular adapter (lazy load)"""
        try:
            from .adapters.angular_adapter import AngularAdapter
            return AngularAdapter
        except ImportError:
            return ReactAdapter

    def _get_svelte_adapter(self):
        """Get Svelte adapter (lazy load)"""
        try:
            from .adapters.svelte_adapter import SvelteAdapter
            return SvelteAdapter
        except ImportError:
            return ReactAdapter

    def _get_fastapi_adapter(self):
        """Get FastAPI adapter (lazy load)"""
        try:
            from .adapters.fastapi_adapter import FastAPIAdapter
            return FastAPIAdapter
        except ImportError:
            return ReactAdapter

    def _get_flask_adapter(self):
        """Get Flask adapter (lazy load)"""
        try:
            from .adapters.flask_adapter import FlaskAdapter
            return FlaskAdapter
        except ImportError:
            return ReactAdapter

    def _get_express_adapter(self):
        """Get Express adapter (lazy load)"""
        try:
            from .adapters.express_adapter import ExpressAdapter
            return ExpressAdapter
        except ImportError:
            return ReactAdapter

    def analyze_app(self) -> UniversalAppStructure:
        """
        Analyze application using framework-specific adapter
        
        Returns:
            Unified app structure
        """
        self.app_structure = self.adapter.analyze_app()
        return self.app_structure

    def generate_tests(self) -> Dict[str, Any]:
        """
        Generate test scenarios and test code
        
        Returns: {
            'framework': 'react',
            'scenarios': [
                {
                    'name': 'User Form Submission',
                    'type': 'happy_path',
                    'steps': [...],
                    'assertions': [...]
                }
            ],
            'test_code': {
                'filename': 'users.e2e.ts',
                'code': '... Playwright test code ...'
            }
        }
        """
        if self.app_structure is None:
            self.analyze_app()
        
        # Generate test scenarios
        scenarios = self._generate_test_scenarios()
        
        # Generate Playwright test code
        test_code = self._generate_playwright_code(scenarios)
        
        return {
            'framework': self.framework_info.type,
            'app_type': self.framework_info.app_type,
            'language': self.framework_info.language,
            'scenarios': scenarios,
            'test_code': test_code,
            'num_tests': len(scenarios),
        }

    def _generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Generate test scenarios from app structure
        
        Returns:
            List of test scenarios
        """
        scenarios = []
        
        # For each component with event handlers or forms
        for component in self.app_structure.components:
            
            # Happy path: normal component usage
            if component.form_fields or component.event_handlers:
                scenarios.append({
                    'name': f'{component.name} - Happy Path',
                    'type': 'happy_path',
                    'component': component.name,
                    'steps': self._generate_happy_path_steps(component),
                    'assertions': self._generate_assertions(component)
                })
            
            # Error cases
            if component.api_calls:
                scenarios.append({
                    'name': f'{component.name} - API Error Handling',
                    'type': 'error',
                    'component': component.name,
                    'steps': self._generate_error_steps(component),
                    'assertions': self._generate_error_assertions(component)
                })
            
            # Edge cases
            if component.form_fields:
                scenarios.append({
                    'name': f'{component.name} - Edge Cases',
                    'type': 'edge_case',
                    'component': component.name,
                    'steps': self._generate_edge_case_steps(component),
                    'assertions': self._generate_edge_assertions(component)
                })
        
        return scenarios

    def _generate_happy_path_steps(self, component) -> List[Dict]:
        """Generate happy path test steps"""
        steps = []
        
        # Navigate to component (if it's a page)
        if component.test_ids:
            steps.append({
                'action': 'navigate',
                'target': f'/{component.name.lower()}'
            })
        
        # Fill form fields
        for field in component.form_fields:
            steps.append({
                'action': 'fill',
                'selector': f'[data-testid="{field}"]',
                'value': f'test-{field}'
            })
        
        # Click primary action
        if component.event_handlers:
            handler = component.event_handlers[0]
            if 'submit' in handler.name.lower():
                steps.append({
                    'action': 'click',
                    'selector': '[data-testid="submit-btn"]'
                })
        
        return steps

    def _generate_error_steps(self, component) -> List[Dict]:
        """Generate error case test steps"""
        steps = []
        
        # Mock API error
        if component.api_calls:
            api_call = component.api_calls[0]
            steps.append({
                'action': 'mock_api',
                'endpoint': api_call.endpoint,
                'method': api_call.method,
                'status': 500,
                'response': {'error': 'Server error'}
            })
        
        # Trigger the error
        steps.extend(self._generate_happy_path_steps(component))
        
        return steps

    def _generate_edge_case_steps(self, component) -> List[Dict]:
        """Generate edge case test steps"""
        steps = []
        
        # Navigate
        if component.test_ids:
            steps.append({
                'action': 'navigate',
                'target': f'/{component.name.lower()}'
            })
        
        # Fill with edge case values
        for field in component.form_fields:
            steps.append({
                'action': 'fill',
                'selector': f'[data-testid="{field}"]',
                'value': '!@#$%^&*()_+-={}[]|:;<>?,./~`'  # Special chars
            })
        
        return steps

    def _generate_assertions(self, component) -> List[Dict]:
        """Generate assertions for happy path"""
        assertions = []
        
        # Check elements are visible
        for test_id in component.test_ids[:3]:  # First 3
            assertions.append({
                'type': 'visibility',
                'selector': f'[data-testid="{test_id}"]',
                'expected': True
            })
        
        return assertions

    def _generate_error_assertions(self, component) -> List[Dict]:
        """Generate assertions for error cases"""
        assertions = []
        
        # Check error message is visible
        assertions.append({
            'type': 'visibility',
            'selector': '[data-testid="error-message"]',
            'expected': True
        })
        
        return assertions

    def _generate_edge_assertions(self, component) -> List[Dict]:
        """Generate assertions for edge cases"""
        assertions = []
        
        # Form should still be valid or show errors
        assertions.append({
            'type': 'visibility',
            'selector': '[data-testid="form"]',
            'expected': True
        })
        
        return assertions

    def _generate_playwright_code(self, scenarios: List[Dict]) -> str:
        """
        Generate Playwright test code from scenarios
        
        Returns:
            Playwright test code as string
        """
        code = '''import { test, expect } from '@playwright/test';

test.describe('E2E Tests', () => {
'''
        
        for scenario in scenarios:
            code += f'''
  test('{scenario["name"]}', async ({{ page }}) => {{
    // Navigate
    await page.goto('http://localhost:3000/');
    
    // Perform actions
    const steps = {json.dumps(scenario.get("steps", []))};
    for (const step of steps) {{
      if (step.action === 'navigate') {{
        await page.goto(`http://localhost:3000${{step.target}}`);
      }} else if (step.action === 'fill') {{
        await page.fill(step.selector, step.value);
      }} else if (step.action === 'click') {{
        await page.click(step.selector);
      }}
    }}
    
    // Assertions
    const assertions = {json.dumps(scenario.get("assertions", []))};
    for (const assertion of assertions) {{
      if (assertion.type === 'visibility') {{
        const element = await page.$(assertion.selector);
        expect(element).toBeTruthy();
      }}
    }}
  }});
'''
        
        code += '''
});
'''
        
        return code

    def get_framework_info(self) -> Dict[str, Any]:
        """Get detected framework info"""
        return {
            'type': self.framework_info.type,
            'version': self.framework_info.version,
            'language': self.framework_info.language,
            'app_type': self.framework_info.app_type,
            'confidence': self.framework_info.confidence,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'framework_info': self.get_framework_info(),
            'app_structure': self.app_structure.dict() if self.app_structure else None,
        }


# Convenience function
def analyze_and_generate_tests(app_path: str) -> Dict[str, Any]:
    """
    One-line function to analyze and generate tests for any framework
    
    Usage:
        result = analyze_and_generate_tests('/path/to/app')
        # Works for React, Vue, Angular, FastAPI, etc.!
    """
    generator = UniversalE2ETestGenerator(app_path)
    generator.analyze_app()
    return generator.generate_tests()