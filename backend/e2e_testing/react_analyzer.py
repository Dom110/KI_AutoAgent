"""
React Component Analyzer - AST-based Analysis
Extracts component structure, props, state, handlers, and interactions
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json


@dataclass
class ReactComponent:
    """Represents a parsed React component"""
    name: str
    file_path: str
    type: str  # 'functional' or 'class'
    props: List[str]
    state_vars: List[str]
    event_handlers: List[Dict[str, Any]]
    hooks: List[str]
    api_calls: List[Dict[str, Any]]
    routes: List[str]
    test_ids: List[str]
    conditional_renders: List[str]
    form_fields: List[Dict[str, Any]]
    imports: List[str]


class ReactComponentAnalyzer:
    """Analyzes React components using regex and pattern matching"""
    
    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        self.components: Dict[str, ReactComponent] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        
    def analyze_app(self) -> Dict[str, Any]:
        """Analyze entire React app"""
        print(f"🔍 Analyzing React app at: {self.app_path}")
        
        # Find all JSX/TSX files
        jsx_files = self._find_jsx_files()
        print(f"📄 Found {len(jsx_files)} React files")
        
        # Parse each file
        for file_path in jsx_files:
            try:
                component = self._parse_component(file_path)
                if component:
                    self.components[component.name] = component
                    print(f"✅ Parsed: {component.name} from {file_path.name}")
            except Exception as e:
                print(f"⚠️  Error parsing {file_path}: {e}")
        
        # Build dependency graph
        self._build_dependency_graph()
        
        return {
            'components': {name: asdict(comp) for name, comp in self.components.items()},
            'dependency_graph': self.dependency_graph,
            'total_components': len(self.components),
        }
    
    def _find_jsx_files(self) -> List[Path]:
        """Find all JSX/TSX files in app"""
        jsx_files = []
        
        # Common React directories
        search_dirs = [
            self.app_path / 'src',
            self.app_path / 'app',
            self.app_path,
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for pattern in ['*.jsx', '*.tsx', '*.js', '*.ts']:
                    jsx_files.extend(search_dir.rglob(pattern))
        
        # Filter out non-component files
        excluded = {'node_modules', '.next', 'dist', 'build', '__pycache__', '.git'}
        jsx_files = [f for f in jsx_files 
                     if not any(exc in f.parts for exc in excluded)]
        
        return jsx_files
    
    def _parse_component(self, file_path: Path) -> Optional[ReactComponent]:
        """Parse a single React component file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            if not self._is_react_file(content):
                return None
            
            # Extract component info
            name = self._extract_component_name(content, file_path)
            component_type = self._detect_component_type(content)
            props = self._extract_props(content)
            state_vars = self._extract_state_vars(content)
            event_handlers = self._extract_event_handlers(content)
            hooks = self._extract_hooks(content)
            api_calls = self._extract_api_calls(content)
            routes = self._extract_routes(content)
            test_ids = self._extract_test_ids(content)
            conditional_renders = self._extract_conditionals(content)
            form_fields = self._extract_form_fields(content)
            imports = self._extract_imports(content)
            
            return ReactComponent(
                name=name,
                file_path=str(file_path),
                type=component_type,
                props=props,
                state_vars=state_vars,
                event_handlers=event_handlers,
                hooks=hooks,
                api_calls=api_calls,
                routes=routes,
                test_ids=test_ids,
                conditional_renders=conditional_renders,
                form_fields=form_fields,
                imports=imports,
            )
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def _is_react_file(self, content: str) -> bool:
        """Check if file is a React component"""
        react_indicators = [
            'import React',
            'from "react"',
            "from 'react'",
            'useState',
            'useEffect',
            'JSX',
            'export default',
            'export function',
            'export const',
        ]
        return any(indicator in content for indicator in react_indicators)
    
    def _extract_component_name(self, content: str, file_path: Path) -> str:
        """Extract component name"""
        # Try to find export default component
        patterns = [
            r'export\s+default\s+(?:function\s+)?(\w+)',
            r'export\s+(?:const|function)\s+(\w+)',
            r'class\s+(\w+)\s+extends\s+(?:React\.)?Component',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Fallback to filename
        return file_path.stem.capitalize()
    
    def _detect_component_type(self, content: str) -> str:
        """Detect if component is functional or class-based"""
        if re.search(r'class\s+\w+\s+extends\s+(?:React\.)?Component', content):
            return 'class'
        return 'functional'
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract component props"""
        props = []
        
        # Functional component props in destructuring
        patterns = [
            r'function\s+\w+\s*\(\s*\{([^}]+)\}',
            r'const\s+\w+\s*=\s*\(\s*\{([^}]+)\}',
            r'function\s+\w+\s*\(\s*props',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                props_str = match.group(1) if '(' in match.group(0) else 'props'
                if props_str != 'props':
                    # Parse destructured props
                    prop_list = [p.strip() for p in props_str.split(',')]
                    props.extend(prop_list)
                break
        
        return props
    
    def _extract_state_vars(self, content: str) -> List[str]:
        """Extract React state variables"""
        state_vars = []
        
        # useState patterns
        pattern = r'(?:const|let|var)\s+\[([^,\]]+),\s*set\w+\]\s*=\s*useState'
        matches = re.findall(pattern, content)
        state_vars.extend(matches)
        
        # Class component this.state
        pattern = r'this\.state\s*=\s*\{([^}]+)\}'
        match = re.search(pattern, content)
        if match:
            state_str = match.group(1)
            # Parse state object
            state_vars.extend([s.split(':')[0].strip() for s in state_str.split(',')])
        
        return state_vars
    
    def _extract_event_handlers(self, content: str) -> List[Dict[str, Any]]:
        """Extract event handlers"""
        handlers = []
        
        # onClick, onChange, onSubmit, etc.
        event_patterns = [
            (r'onClick\s*=\s*\{([^}]+)\}', 'click'),
            (r'onChange\s*=\s*\{([^}]+)\}', 'change'),
            (r'onSubmit\s*=\s*\{([^}]+)\}', 'submit'),
            (r'onBlur\s*=\s*\{([^}]+)\}', 'blur'),
            (r'onFocus\s*=\s*\{([^}]+)\}', 'focus'),
            (r'onKeyDown\s*=\s*\{([^}]+)\}', 'keydown'),
            (r'onMouseEnter\s*=\s*\{([^}]+)\}', 'mouseenter'),
            (r'onMouseLeave\s*=\s*\{([^}]+)\}', 'mouseleave'),
        ]
        
        for pattern, event_type in event_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                handler_name = match.strip()
                if handler_name.startswith('(') and handler_name.endswith(')'):
                    continue  # Skip inline functions
                
                handlers.append({
                    'type': event_type,
                    'handler': handler_name,
                })
        
        return handlers
    
    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used"""
        hooks = []
        
        hook_patterns = [
            r'useState',
            r'useEffect',
            r'useContext',
            r'useReducer',
            r'useCallback',
            r'useMemo',
            r'useRef',
            r'useLayoutEffect',
            r'useDebugValue',
            r'useNavigate',
            r'useParams',
            r'useLocation',
            r'useQuery',
            r'useMutation',
        ]
        
        for hook in hook_patterns:
            if re.search(hook, content):
                hooks.append(hook)
        
        return hooks
    
    def _extract_api_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract API calls"""
        api_calls = []
        
        # fetch() calls
        pattern = r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        for match in matches:
            api_calls.append({
                'type': 'fetch',
                'endpoint': match,
            })
        
        # axios calls
        pattern = r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        for method, endpoint in matches:
            api_calls.append({
                'type': 'axios',
                'method': method,
                'endpoint': endpoint,
            })
        
        return api_calls
    
    def _extract_routes(self, content: str) -> List[str]:
        """Extract route navigation"""
        routes = []
        
        # useNavigate
        pattern = r'navigate\s*\(\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        routes.extend(matches)
        
        # Link to
        pattern = r'<Link\s+to\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        routes.extend(matches)
        
        # Route path
        pattern = r'<Route\s+path\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        routes.extend(matches)
        
        return routes
    
    def _extract_test_ids(self, content: str) -> List[str]:
        """Extract data-testid values"""
        test_ids = []
        
        pattern = r'data-testid\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        test_ids.extend(matches)
        
        return test_ids
    
    def _extract_conditionals(self, content: str) -> List[str]:
        """Extract conditional renders"""
        conditionals = []
        
        # Conditional rendering patterns
        pattern = r'(\w+)\s*\?\s*<'
        matches = re.findall(pattern, content)
        conditionals.extend(matches)
        
        # && rendering
        pattern = r'(\w+)\s*&&\s*<'
        matches = re.findall(pattern, content)
        conditionals.extend(matches)
        
        return conditionals
    
    def _extract_form_fields(self, content: str) -> List[Dict[str, Any]]:
        """Extract form fields"""
        form_fields = []
        
        # Input fields
        input_pattern = r'<input[^>]*type\s*=\s*[\'"](\w+)[\'"][^>]*(?:name|data-testid)\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(input_pattern, content)
        for type_, name in matches:
            form_fields.append({
                'type': 'input',
                'input_type': type_,
                'name': name,
            })
        
        # Textarea
        textarea_pattern = r'<textarea[^>]*(?:name|data-testid)\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(textarea_pattern, content)
        for name in matches:
            form_fields.append({
                'type': 'textarea',
                'name': name,
            })
        
        # Select
        select_pattern = r'<select[^>]*(?:name|data-testid)\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(select_pattern, content)
        for name in matches:
            form_fields.append({
                'type': 'select',
                'name': name,
            })
        
        return form_fields
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract imports"""
        imports = []
        
        pattern = r'import\s+(?:\{[^}]+\}|[^from]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        imports.extend(matches)
        
        return imports
    
    def _build_dependency_graph(self):
        """Build component dependency graph"""
        # For each component, find which other components it imports
        for comp_name, component in self.components.items():
            dependencies = []
            
            for import_path in component.imports:
                # Check if import is another component in the project
                for other_name, other_comp in self.components.items():
                    if other_name != comp_name:
                        # Simple matching - check if component name is in import
                        if other_name.lower() in import_path.lower():
                            dependencies.append(other_name)
            
            self.dependency_graph[comp_name] = dependencies
    
    def get_component_by_name(self, name: str) -> Optional[ReactComponent]:
        """Get component by name"""
        return self.components.get(name)
    
    def get_components_with_forms(self) -> List[ReactComponent]:
        """Get all components that have forms"""
        return [c for c in self.components.values() if c.form_fields]
    
    def get_components_with_api_calls(self) -> List[ReactComponent]:
        """Get all components that make API calls"""
        return [c for c in self.components.values() if c.api_calls]
    
    def get_components_with_routes(self) -> List[ReactComponent]:
        """Get all components that handle routing"""
        return [c for c in self.components.values() if c.routes]
    
    def export_analysis(self, output_path: str):
        """Export analysis to JSON file"""
        analysis = {
            'components': {name: asdict(comp) for name, comp in self.components.items()},
            'dependency_graph': self.dependency_graph,
            'summary': {
                'total_components': len(self.components),
                'components_with_forms': len(self.get_components_with_forms()),
                'components_with_api': len(self.get_components_with_api_calls()),
                'components_with_routes': len(self.get_components_with_routes()),
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"📊 Analysis exported to {output_path}")