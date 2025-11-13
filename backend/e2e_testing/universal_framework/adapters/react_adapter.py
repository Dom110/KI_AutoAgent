"""
React Framework Adapter

Converts React-specific analysis to universal UniversalAppStructure.
Uses existing ReactComponentAnalyzer logic.
"""

from typing import List, Dict, Optional
from pathlib import Path
import re
import json

from ..base_analyzer import (
    BaseComponentAnalyzer,
    UniversalAppStructure,
    Component,
    ComponentType,
    Property,
    StateVariable,
    EventHandler,
    APICall,
    Route,
    Service,
)


class ReactAdapter(BaseComponentAnalyzer):
    """
    React framework adapter
    
    Analyzes React apps and converts to UniversalAppStructure.
    Inherits from existing ReactComponentAnalyzer logic.
    """

    def __init__(self, app_path: str):
        super().__init__(app_path)
        self.app_path_obj = Path(app_path)

    def analyze_app(self) -> UniversalAppStructure:
        """
        Analyze React app
        
        Returns:
            UniversalAppStructure with React app analysis
        """
        components = self.extract_components()
        routes = self.extract_routes()
        services = self.extract_services()
        api_calls = self.extract_api_calls()

        return UniversalAppStructure(
            framework='react',
            language=self._detect_language(),
            app_type='frontend',
            components=components,
            routes=routes,
            services=services,
            entry_point=self._find_entry_point(),
            build_command='npm run build',
            test_command='npm test',
        )

    def extract_components(self) -> List[Component]:
        """
        Extract React components from codebase
        
        Uses regex patterns to detect:
        - Function components
        - Class components
        - Hooks (useState, useEffect, etc.)
        - Props
        - Event handlers
        - JSX elements
        """
        components = []

        # Find all .tsx and .jsx files
        tsx_files = list(self.app_path_obj.rglob('*.tsx'))
        jsx_files = list(self.app_path_obj.rglob('*.jsx'))
        
        for file_path in tsx_files + jsx_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip test files and node_modules
            if 'test' in str(file_path) or 'node_modules' in str(file_path):
                continue

            component = self._parse_component_file(file_path, content)
            if component:
                components.append(component)

        return components

    def extract_routes(self) -> List[Route]:
        """Extract React Router routes"""
        routes = []

        # Look for react-router config
        route_files = list(self.app_path_obj.rglob('*router*.ts*'))
        route_files += list(self.app_path_obj.rglob('*route*.ts*'))

        for file_path in route_files:
            if 'node_modules' in str(file_path):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract routes using regex
            # Pattern: path: "/users/:id", element: <UserDetail />
            route_pattern = r'path:\s*["\']([^"\']+)["\']'
            
            for match in re.finditer(route_pattern, content):
                path = match.group(1)
                routes.append(Route(
                    path=path,
                    component='',
                    protected=False,
                    parameters=self._extract_route_params(path)
                ))

        return routes

    def extract_services(self) -> List[Service]:
        """Extract service/utility files"""
        services = []

        # Look for service/utils directories
        service_dirs = [
            self.app_path_obj / 'src' / 'services',
            self.app_path_obj / 'src' / 'utils',
            self.app_path_obj / 'src' / 'api',
        ]

        for service_dir in service_dirs:
            if not service_dir.exists():
                continue

            for ts_file in service_dir.rglob('*.ts'):
                if 'test' not in str(ts_file):
                    service = Service(
                        name=ts_file.stem,
                        file_path=str(ts_file.relative_to(self.app_path_obj))
                    )
                    services.append(service)

        return services

    def extract_api_calls(self) -> List[APICall]:
        """Extract API calls from components"""
        api_calls = []

        # Find all fetch/axios calls
        tsx_files = list(self.app_path_obj.rglob('*.tsx'))
        
        for file_path in tsx_files:
            if 'node_modules' in str(file_path):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract fetch calls
            fetch_pattern = r'fetch\(["\']([^"\']+)["\']'
            for match in re.finditer(fetch_pattern, content):
                endpoint = match.group(1)
                api_calls.append(APICall(
                    endpoint=endpoint,
                    method='GET'
                ))

            # Extract axios calls
            axios_pattern = r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']'
            for match in re.finditer(axios_pattern, content):
                method = match.group(1).upper()
                endpoint = match.group(2)
                api_calls.append(APICall(
                    endpoint=endpoint,
                    method=method
                ))

        return api_calls

    def _parse_component_file(self, file_path: Path, content: str) -> Optional[Component]:
        """Parse single React component file"""
        
        component_name = file_path.stem
        
        # Extract props
        props = self._extract_props(content)
        
        # Extract state variables
        state_vars = self._extract_state_variables(content)
        
        # Extract event handlers
        handlers = self._extract_event_handlers(content)
        
        # Extract test IDs
        test_ids = self._extract_test_ids(content)
        
        # Extract form fields
        form_fields = self._extract_form_fields(content)
        
        # Determine component type
        component_type = ComponentType.COMPONENT
        if 'page' in component_name.lower():
            component_type = ComponentType.PAGE

        component = Component(
            name=component_name,
            file_path=str(file_path.relative_to(self.app_path_obj)),
            type=component_type,
            language=self._detect_language(),
            properties=props,
            state_variables=state_vars,
            event_handlers=handlers,
            test_ids=test_ids,
            form_fields=form_fields,
        )

        return component

    def _extract_props(self, content: str) -> List[Property]:
        """Extract component props"""
        props = []
        
        # Look for interface/type Props
        props_pattern = r'(?:interface|type)\s+Props\s*{([^}]+)}'
        match = re.search(props_pattern, content)
        
        if match:
            props_content = match.group(1)
            lines = props_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':')
                    prop_name = parts[0].strip()
                    prop_type = parts[1].strip().rstrip(';')
                    required = '?' not in prop_name
                    
                    props.append(Property(
                        name=prop_name.replace('?', ''),
                        type=prop_type,
                        required=required
                    ))
        
        return props

    def _extract_state_variables(self, content: str) -> List[StateVariable]:
        """Extract useState variables"""
        state_vars = []
        
        # Pattern: const [state, setState] = useState(...)
        useState_pattern = r'const\s+\[(\w+),\s*\w+\]\s*=\s*useState\((.*?)\)'
        
        for match in re.finditer(useState_pattern, content, re.DOTALL):
            var_name = match.group(1)
            initial_value = match.group(2).strip()
            
            state_vars.append(StateVariable(
                name=var_name,
                type='state',
                initial_value=initial_value
            ))
        
        return state_vars

    def _extract_event_handlers(self, content: str) -> List[EventHandler]:
        """Extract event handlers"""
        handlers = []
        
        # Patterns: onClick, onChange, onSubmit, etc.
        handler_pattern = r'(on[A-Z]\w+)=\{(\w+)\}'
        
        for match in re.finditer(handler_pattern, content):
            event_type = match.group(1)
            handler_name = match.group(2)
            
            handlers.append(EventHandler(
                name=handler_name,
                event_type=event_type,
                action=f'Handles {event_type}'
            ))
        
        return handlers

    def _extract_test_ids(self, content: str) -> List[str]:
        """Extract data-testid attributes"""
        test_ids = []
        
        # Pattern: data-testid="..."
        testid_pattern = r'data-testid=["\']([^"\']+)["\']'
        
        for match in re.finditer(testid_pattern, content):
            test_id = match.group(1)
            test_ids.append(test_id)
        
        return test_ids

    def _extract_form_fields(self, content: str) -> List[str]:
        """Extract form fields"""
        form_fields = []
        
        # Look for input, textarea, select elements with names or test ids
        input_pattern = r'<input[^>]*(?:name|data-testid)=["\']([^"\']+)["\']'
        
        for match in re.finditer(input_pattern, content):
            field_name = match.group(1)
            form_fields.append(field_name)
        
        return form_fields

    def _extract_route_params(self, path: str) -> List[str]:
        """Extract parameters from route path"""
        # Pattern: /users/:id -> ['id']
        param_pattern = r':(\w+)'
        return re.findall(param_pattern, path)

    def _detect_language(self) -> str:
        """Detect TypeScript vs JavaScript"""
        if (self.app_path_obj / 'tsconfig.json').exists():
            return 'typescript'
        return 'javascript'

    def _find_entry_point(self) -> Optional[str]:
        """Find React entry point"""
        candidates = [
            'src/main.tsx',
            'src/index.tsx',
            'src/main.ts',
            'src/index.ts',
            'src/index.jsx',
            'src/index.js',
        ]
        
        for candidate in candidates:
            if (self.app_path_obj / candidate).exists():
                return candidate
        
        return None