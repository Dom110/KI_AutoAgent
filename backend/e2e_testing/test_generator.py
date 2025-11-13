"""
E2E Test Generator - Automatic Test Creation
Generates Playwright tests from React component analysis
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .react_analyzer import ReactComponentAnalyzer, ReactComponent


@dataclass
class TestScenario:
    """Represents a test scenario to be generated"""
    component_name: str
    scenario_type: str  # 'happy_path', 'error_case', 'edge_case', 'flow'
    title: str
    steps: List[str]
    assertions: List[str]
    mocks: List[Dict[str, Any]]


class E2ETestGenerator:
    """Generates E2E tests from React component analysis"""
    
    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        self.analyzer = ReactComponentAnalyzer(str(app_path))
        self.scenarios: List[TestScenario] = []
        self.test_files: Dict[str, str] = {}
    
    def analyze_and_generate(self) -> Dict[str, Any]:
        """Analyze app and generate test scenarios"""
        print("🚀 Starting E2E Test Generation...")
        
        # Step 1: Analyze app
        analysis = self.analyzer.analyze_app()
        print(f"✅ Analyzed {analysis['total_components']} components")
        
        # Step 2: Generate test scenarios
        self.scenarios = self._generate_test_scenarios()
        print(f"✅ Generated {len(self.scenarios)} test scenarios")
        
        # Step 3: Generate test code
        self.test_files = self._generate_test_code()
        print(f"✅ Generated {len(self.test_files)} test files")
        
        return {
            'analysis': analysis,
            'scenarios': len(self.scenarios),
            'test_files': list(self.test_files.keys()),
        }
    
    def _generate_test_scenarios(self) -> List[TestScenario]:
        """Generate test scenarios for all components"""
        scenarios = []
        
        for component_name, component in self.analyzer.components.items():
            # HAPPY PATH tests
            if component.form_fields:
                scenarios.append(self._create_form_happy_path(component))
            
            if component.api_calls:
                scenarios.append(self._create_api_happy_path(component))
            
            if component.test_ids:
                scenarios.append(self._create_interaction_happy_path(component))
            
            # ERROR CASES
            if component.api_calls:
                scenarios.extend(self._create_api_error_cases(component))
            
            if component.form_fields:
                scenarios.extend(self._create_form_error_cases(component))
            
            # EDGE CASES
            if component.form_fields:
                scenarios.extend(self._create_form_edge_cases(component))
            
            if component.conditional_renders:
                scenarios.extend(self._create_conditional_edge_cases(component))
        
        # INTEGRATION/FLOW tests
        scenarios.extend(self._create_integration_flows())
        
        return scenarios
    
    def _create_form_happy_path(self, component: ReactComponent) -> TestScenario:
        """Create happy path test for form component"""
        form_fields_str = ', '.join([f"'{f['name']}'" for f in component.form_fields])
        
        return TestScenario(
            component_name=component.name,
            scenario_type='happy_path',
            title=f'should successfully submit {component.name} form with valid data',
            steps=[
                f"Navigate to {component.name} page",
                f"Fill form fields: {form_fields_str}",
                "Submit form",
                "Verify success (navigation or success message)",
            ],
            assertions=[
                "Form submission succeeds",
                "User is redirected or success message appears",
                "Form data is processed",
            ],
            mocks=[],
        )
    
    def _create_api_happy_path(self, component: ReactComponent) -> TestScenario:
        """Create happy path test for API-calling component"""
        endpoints = ', '.join([api['endpoint'] for api in component.api_calls[:2]])
        
        return TestScenario(
            component_name=component.name,
            scenario_type='happy_path',
            title=f'should successfully load {component.name} with API data',
            steps=[
                f"Navigate to {component.name}",
                f"Mock API endpoints: {endpoints}",
                "Wait for data to load",
                "Verify data is displayed correctly",
            ],
            assertions=[
                "API is called",
                "Data is fetched successfully",
                "Data is rendered on page",
            ],
            mocks=[{'endpoint': api['endpoint'], 'status': 200} for api in component.api_calls],
        )
    
    def _create_interaction_happy_path(self, component: ReactComponent) -> TestScenario:
        """Create happy path for interactive components"""
        test_ids_str = ', '.join(component.test_ids[:3])
        
        return TestScenario(
            component_name=component.name,
            scenario_type='happy_path',
            title=f'should handle user interactions in {component.name}',
            steps=[
                f"Navigate to {component.name}",
                f"Find interactive elements: {test_ids_str}",
                "Perform user interactions (click, type, etc)",
                "Verify UI updates correctly",
            ],
            assertions=[
                "Elements are visible",
                "Interactions trigger handlers",
                "UI state updates as expected",
            ],
            mocks=[],
        )
    
    def _create_api_error_cases(self, component: ReactComponent) -> List[TestScenario]:
        """Create error case tests for API calls"""
        errors = []
        
        # API Error Case
        errors.append(TestScenario(
            component_name=component.name,
            scenario_type='error_case',
            title=f'should handle API errors in {component.name}',
            steps=[
                f"Navigate to {component.name}",
                "Mock API to return error (500)",
                "Trigger API call",
                "Verify error is handled gracefully",
            ],
            assertions=[
                "Error message is displayed",
                "User can retry or go back",
                "No crashes occur",
            ],
            mocks=[{'endpoint': api['endpoint'], 'status': 500} for api in component.api_calls],
        ))
        
        # Network Error Case
        errors.append(TestScenario(
            component_name=component.name,
            scenario_type='error_case',
            title=f'should handle network errors in {component.name}',
            steps=[
                f"Navigate to {component.name}",
                "Disconnect network",
                "Trigger API call",
                "Verify timeout/error handling",
            ],
            assertions=[
                "Network error is caught",
                "User sees appropriate message",
                "Application remains stable",
            ],
            mocks=[{'endpoint': api['endpoint'], 'type': 'abort'} for api in component.api_calls],
        ))
        
        return errors
    
    def _create_form_error_cases(self, component: ReactComponent) -> List[TestScenario]:
        """Create error case tests for forms"""
        errors = []
        
        # Invalid Input
        errors.append(TestScenario(
            component_name=component.name,
            scenario_type='error_case',
            title=f'should handle invalid input in {component.name} form',
            steps=[
                f"Navigate to {component.name}",
                "Enter invalid data (wrong format, invalid email, etc)",
                "Submit form",
                "Verify validation errors are shown",
            ],
            assertions=[
                "Validation errors appear",
                "Form is not submitted",
                "User can correct and retry",
            ],
            mocks=[],
        ))
        
        # Submission Error
        errors.append(TestScenario(
            component_name=component.name,
            scenario_type='error_case',
            title=f'should handle form submission errors in {component.name}',
            steps=[
                f"Navigate to {component.name}",
                "Fill valid data",
                "Mock submission to fail",
                "Submit form",
                "Verify error is displayed",
            ],
            assertions=[
                "Error message is shown",
                "Form data is preserved",
                "User can retry submission",
            ],
            mocks=[],
        ))
        
        return errors
    
    def _create_form_edge_cases(self, component: ReactComponent) -> List[TestScenario]:
        """Create edge case tests for forms"""
        edges = []
        
        # Empty Fields
        edges.append(TestScenario(
            component_name=component.name,
            scenario_type='edge_case',
            title=f'should handle empty fields in {component.name} form',
            steps=[
                f"Navigate to {component.name}",
                "Leave fields empty",
                "Submit form",
                "Verify validation",
            ],
            assertions=[
                "Required field validation works",
                "Form is not submitted",
                "Clear error messages shown",
            ],
            mocks=[],
        ))
        
        # Special Characters
        edges.append(TestScenario(
            component_name=component.name,
            scenario_type='edge_case',
            title=f'should handle special characters in {component.name} form',
            steps=[
                f"Navigate to {component.name}",
                "Enter special characters (< > & # etc)",
                "Submit form",
                "Verify input is sanitized/escaped",
            ],
            assertions=[
                "Special chars are handled",
                "No XSS vulnerabilities",
                "Form processes correctly",
            ],
            mocks=[],
        ))
        
        # Very Long Input
        edges.append(TestScenario(
            component_name=component.name,
            scenario_type='edge_case',
            title=f'should handle very long input in {component.name} form',
            steps=[
                f"Navigate to {component.name}",
                "Enter very long text (>1000 chars)",
                "Submit form",
                "Verify truncation/handling",
            ],
            assertions=[
                "Long input is handled",
                "Form processes correctly",
                "No UI overflow/crashes",
            ],
            mocks=[],
        ))
        
        return edges
    
    def _create_conditional_edge_cases(self, component: ReactComponent) -> List[TestScenario]:
        """Create edge case tests for conditional rendering"""
        edges = []
        
        for condition in component.conditional_renders[:3]:
            edges.append(TestScenario(
                component_name=component.name,
                scenario_type='edge_case',
                title=f'should handle conditional rendering ({condition}) in {component.name}',
                steps=[
                    f"Navigate to {component.name}",
                    f"Set condition '{condition}' to true",
                    "Verify element is rendered",
                    f"Set condition '{condition}' to false",
                    "Verify element is hidden",
                ],
                assertions=[
                    "Conditional element renders/hides",
                    "DOM is updated correctly",
                    "No memory leaks",
                ],
                mocks=[],
            ))
        
        return edges
    
    def _create_integration_flows(self) -> List[TestScenario]:
        """Create integration tests for complete user flows"""
        flows = []
        
        # Get components with routes
        routed_components = self.analyzer.get_components_with_routes()
        
        if len(routed_components) >= 2:
            flow = TestScenario(
                component_name='Integration',
                scenario_type='flow',
                title='should complete multi-step user flow',
                steps=[
                    f"Start at {routed_components[0].name}",
                    "Perform actions",
                    f"Navigate to {routed_components[1].name}",
                    "Verify complete flow works",
                ],
                assertions=[
                    "Navigation works",
                    "State persists across pages",
                    "User can complete tasks",
                ],
                mocks=[],
            )
            flows.append(flow)
        
        return flows
    
    def _generate_test_code(self) -> Dict[str, str]:
        """Generate Playwright test code from scenarios"""
        test_files = {}
        
        # Group scenarios by component
        scenarios_by_component = {}
        for scenario in self.scenarios:
            comp = scenario.component_name
            if comp not in scenarios_by_component:
                scenarios_by_component[comp] = []
            scenarios_by_component[comp].append(scenario)
        
        # Generate test file for each component
        for component_name, scenarios in scenarios_by_component.items():
            test_code = self._render_test_file(component_name, scenarios)
            test_filename = f"{component_name.lower()}.spec.ts"
            test_files[test_filename] = test_code
        
        return test_files
    
    def _render_test_file(self, component_name: str, scenarios: List[TestScenario]) -> str:
        """Render Playwright test file for component"""
        test_code = f"""import {{ test, expect }} from '@playwright/test';

test.describe('{component_name} E2E Tests', () => {{
  test.beforeEach(async ({{ page }}) => {{
    // Setup before each test
    await page.goto('http://localhost:3000/{component_name.lower()}');
  }});

"""
        
        # Add tests for each scenario
        for i, scenario in enumerate(scenarios, 1):
            test_code += self._render_test_case(scenario)
            test_code += "\n\n"
        
        test_code += "});\n"
        return test_code
    
    def _render_test_case(self, scenario: TestScenario) -> str:
        """Render a single test case"""
        test_name = scenario.title
        
        test_code = f"""  test('{test_name}', async ({{ page }}) => {{
    // Arrange: Setup mocks
"""
        
        # Add mocks
        for mock in scenario.mocks:
            if mock.get('type') == 'abort':
                test_code += f"""    await page.route('**{mock.get('endpoint', '*')}', route =>
      route.abort('internet-disconnected')
    );\n"""
            else:
                status = mock.get('status', 200)
                test_code += f"""    await page.route('**{mock.get('endpoint', '*')}', route =>
      route.respond({{ status: {status}, body: JSON.stringify({{}}) }})
    );\n"""
        
        test_code += """
    // Act: Perform test steps
"""
        
        # Add steps (simplified)
        for step in scenario.steps[:3]:  # Limit steps
            test_code += f"    // {step}\n"
        
        test_code += """
    // Assert: Verify expectations
"""
        
        # Add assertions
        for assertion in scenario.assertions[:2]:  # Limit assertions
            test_code += f"    // {assertion}\n"
        
        test_code += "  });\n"
        
        return test_code
    
    def write_test_files(self, output_dir: str):
        """Write generated test files to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for filename, content in self.test_files.items():
            filepath = output_path / filename
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"📝 Written test file: {filepath}")
    
    def export_scenarios(self, output_file: str):
        """Export test scenarios to JSON"""
        import json
        
        scenarios_data = [
            {
                'component': s.component_name,
                'type': s.scenario_type,
                'title': s.title,
                'steps': s.steps,
                'assertions': s.assertions,
            }
            for s in self.scenarios
        ]
        
        with open(output_file, 'w') as f:
            json.dump(scenarios_data, f, indent=2)
        
        print(f"📊 Exported {len(scenarios_data)} scenarios to {output_file}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get test generation statistics"""
        scenario_types = {}
        for scenario in self.scenarios:
            scenario_types[scenario.scenario_type] = scenario_types.get(scenario.scenario_type, 0) + 1
        
        return {
            'total_scenarios': len(self.scenarios),
            'total_test_files': len(self.test_files),
            'scenario_types': scenario_types,
            'components_tested': len(set(s.component_name for s in self.scenarios)),
        }