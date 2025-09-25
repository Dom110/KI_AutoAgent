"""
Code metrics calculation using Radon

Provides:
- Cyclomatic Complexity
- Halstead Metrics
- Maintainability Index
- Lines of Code metrics
"""

import ast
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class RadonMetrics:
    """
    Code metrics analyzer for quality assessment

    Features:
    - Cyclomatic complexity calculation
    - Halstead metrics
    - Maintainability index
    - Code quality scoring
    """

    def __init__(self):
        self.metrics_cache = {}
        self.thresholds = {
            'complexity': {
                'low': 5,
                'medium': 10,
                'high': 20,
                'very_high': 50
            },
            'maintainability': {
                'very_high': 100,
                'high': 80,
                'medium': 60,
                'low': 40,
                'very_low': 20
            }
        }

    async def calculate_all_metrics(self, target_path: str = '.', progress_callback=None) -> Dict:
        """
        Calculate comprehensive code metrics

        Args:
            target_path: Path to analyze
            progress_callback: Optional callback for progress updates

        Returns:
            Complete metrics report
        """
        logger.info(f"Calculating code metrics for {target_path}")

        metrics = {
            'complexity': {},
            'halstead': {},
            'maintainability': {},
            'loc': {},
            'summary': {},
            'hotspots': []
        }

        path = Path(target_path)

        # Count Python files
        py_files = list(path.rglob('*.py'))
        total_files = len(py_files)
        processed = 0

        # Analyze each Python file
        for py_file in py_files:
            processed += 1
            if progress_callback and (processed % 10 == 0 or total_files < 50):
                await progress_callback(f"📊 Calculating metrics ({processed}/{total_files} files)...")

            try:
                content = py_file.read_text(encoding='utf-8')
                file_metrics = await self._analyze_file(str(py_file), content)

                # Store metrics
                metrics['complexity'][str(py_file)] = file_metrics['complexity']
                metrics['halstead'][str(py_file)] = file_metrics['halstead']
                metrics['maintainability'][str(py_file)] = file_metrics['maintainability']
                metrics['loc'][str(py_file)] = file_metrics['loc']

                # Identify hotspots
                if file_metrics['complexity']['average'] > self.thresholds['complexity']['high']:
                    metrics['hotspots'].append({
                        'file': str(py_file),
                        'complexity': file_metrics['complexity']['average'],
                        'reason': 'High complexity'
                    })

            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")

        # Calculate summary
        metrics['summary'] = self._calculate_summary(metrics)

        return metrics

    async def _analyze_file(self, file_path: str, content: str) -> Dict:
        """Analyze a single file"""
        metrics = {
            'complexity': {},
            'halstead': {},
            'maintainability': 0,
            'loc': {}
        }

        # Lines of Code metrics
        metrics['loc'] = self._calculate_loc(content)

        # Parse AST
        try:
            tree = ast.parse(content)

            # Cyclomatic Complexity
            metrics['complexity'] = self._calculate_complexity(tree, content)

            # Halstead Metrics
            metrics['halstead'] = self._calculate_halstead(tree, content)

            # Maintainability Index
            metrics['maintainability'] = self._calculate_maintainability(
                metrics['complexity']['average'],
                metrics['halstead'].get('volume', 0),
                metrics['loc']['loc']
            )

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

        return metrics

    def _calculate_loc(self, content: str) -> Dict:
        """Calculate Lines of Code metrics"""
        lines = content.split('\n')

        loc = {
            'total': len(lines),
            'code': 0,
            'comment': 0,
            'blank': 0
        }

        in_multiline_string = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                loc['blank'] += 1
            elif stripped.startswith('#'):
                loc['comment'] += 1
            elif '"""' in stripped or "'''" in stripped:
                loc['comment'] += 1
                in_multiline_string = not in_multiline_string
            elif in_multiline_string:
                loc['comment'] += 1
            else:
                loc['code'] += 1

        loc['loc'] = loc['code']  # Logical lines of code

        return loc

    def _calculate_complexity(self, tree: ast.AST, content: str) -> Dict:
        """Calculate Cyclomatic Complexity"""
        complexity = {
            'functions': {},
            'classes': {},
            'total': 1,  # Base complexity
            'average': 0
        }

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1
                self.function_complexity = {}
                self.class_complexity = {}
                self.current_function = None
                self.current_class = None

            def visit_FunctionDef(self, node):
                old_func = self.current_function
                self.current_function = node.name
                self.function_complexity[node.name] = 1
                self.generic_visit(node)
                self.current_function = old_func

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                self.class_complexity[node.name] = 1
                self.generic_visit(node)
                self.current_class = old_class

            def visit_If(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_While(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_For(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_With(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_Assert(self, node):
                self._add_complexity(1)
                self.generic_visit(node)

            def visit_BoolOp(self, node):
                # Add complexity for and/or operations
                self._add_complexity(len(node.values) - 1)
                self.generic_visit(node)

            def _add_complexity(self, value):
                self.complexity += value
                if self.current_function:
                    self.function_complexity[self.current_function] += value
                if self.current_class:
                    self.class_complexity[self.current_class] += value

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        complexity['functions'] = visitor.function_complexity
        complexity['classes'] = visitor.class_complexity
        complexity['total'] = visitor.complexity

        # Calculate average
        all_complexities = list(visitor.function_complexity.values())
        if all_complexities:
            complexity['average'] = sum(all_complexities) / len(all_complexities)
        else:
            complexity['average'] = complexity['total']

        # Find most complex functions
        if visitor.function_complexity:
            sorted_funcs = sorted(visitor.function_complexity.items(),
                                key=lambda x: x[1], reverse=True)
            complexity['most_complex'] = sorted_funcs[:5]

        return complexity

    def _calculate_halstead(self, tree: ast.AST, content: str) -> Dict:
        """Calculate Halstead metrics"""
        halstead = {
            'operators': {},
            'operands': {},
            'n1': 0,  # Total operators
            'n2': 0,  # Total operands
            'N1': 0,  # Distinct operators
            'N2': 0,  # Distinct operands
            'vocabulary': 0,
            'length': 0,
            'volume': 0,
            'difficulty': 0,
            'effort': 0,
            'time': 0,
            'bugs': 0
        }

        class HalsteadVisitor(ast.NodeVisitor):
            def __init__(self):
                self.operators = {}
                self.operands = {}

            def visit_BinOp(self, node):
                op_name = node.op.__class__.__name__
                self.operators[op_name] = self.operators.get(op_name, 0) + 1
                self.generic_visit(node)

            def visit_UnaryOp(self, node):
                op_name = node.op.__class__.__name__
                self.operators[op_name] = self.operators.get(op_name, 0) + 1
                self.generic_visit(node)

            def visit_Compare(self, node):
                for op in node.ops:
                    op_name = op.__class__.__name__
                    self.operators[op_name] = self.operators.get(op_name, 0) + 1
                self.generic_visit(node)

            def visit_Name(self, node):
                self.operands[node.id] = self.operands.get(node.id, 0) + 1
                self.generic_visit(node)

            def visit_Constant(self, node):
                value = str(node.value)
                self.operands[value] = self.operands.get(value, 0) + 1
                self.generic_visit(node)

            def visit_Call(self, node):
                self.operators['call'] = self.operators.get('call', 0) + 1
                self.generic_visit(node)

            def visit_Attribute(self, node):
                self.operators['.'] = self.operators.get('.', 0) + 1
                self.generic_visit(node)

        visitor = HalsteadVisitor()
        visitor.visit(tree)

        halstead['operators'] = visitor.operators
        halstead['operands'] = visitor.operands

        # Calculate metrics
        halstead['n1'] = sum(visitor.operators.values())
        halstead['n2'] = sum(visitor.operands.values())
        halstead['N1'] = len(visitor.operators)
        halstead['N2'] = len(visitor.operands)

        halstead['vocabulary'] = halstead['N1'] + halstead['N2']
        halstead['length'] = halstead['n1'] + halstead['n2']

        if halstead['vocabulary'] > 0:
            halstead['volume'] = halstead['length'] * math.log2(halstead['vocabulary'])

        if halstead['N2'] > 0:
            halstead['difficulty'] = (halstead['N1'] / 2) * (halstead['n2'] / halstead['N2'])

        halstead['effort'] = halstead['volume'] * halstead['difficulty']
        halstead['time'] = halstead['effort'] / 18  # Stroud number
        halstead['bugs'] = halstead['volume'] / 3000  # Empirical constant

        return halstead

    def _calculate_maintainability(self, complexity: float, volume: float, loc: int) -> float:
        """
        Calculate Maintainability Index

        Based on the formula:
        MI = 171 - 5.2 * ln(Volume) - 0.23 * Complexity - 16.2 * ln(LOC)

        Normalized to 0-100 scale
        """
        if loc == 0 or volume == 0:
            return 100.0

        mi = 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)

        # Normalize to 0-100
        mi = max(0, mi * 100 / 171)

        return round(mi, 2)

    def _calculate_summary(self, metrics: Dict) -> Dict:
        """Calculate summary statistics"""
        summary = {
            'total_files': len(metrics['complexity']),
            'total_loc': sum(m['loc'] for m in metrics['loc'].values()),
            'average_complexity': 0,
            'average_maintainability': 0,
            'quality_score': 0,
            'risk_level': 'low'
        }

        # Average complexity
        all_complexities = []
        for file_metrics in metrics['complexity'].values():
            if 'average' in file_metrics:
                all_complexities.append(file_metrics['average'])

        if all_complexities:
            summary['average_complexity'] = sum(all_complexities) / len(all_complexities)

        # Average maintainability
        all_maintainability = list(metrics['maintainability'].values())
        if all_maintainability:
            summary['average_maintainability'] = sum(all_maintainability) / len(all_maintainability)

        # Calculate quality score
        summary['quality_score'] = self._calculate_quality_score(
            summary['average_complexity'],
            summary['average_maintainability']
        )

        # Determine risk level
        if summary['average_complexity'] > 20:
            summary['risk_level'] = 'high'
        elif summary['average_complexity'] > 10:
            summary['risk_level'] = 'medium'
        else:
            summary['risk_level'] = 'low'

        # Add recommendations
        summary['recommendations'] = self._generate_recommendations(metrics)

        return summary

    def _calculate_quality_score(self, complexity: float, maintainability: float) -> float:
        """Calculate overall quality score (0-100)"""
        # Weight: 40% maintainability, 60% complexity
        complexity_score = max(0, 100 - (complexity * 5))  # Penalize high complexity
        quality = (maintainability * 0.4) + (complexity_score * 0.6)

        return round(quality, 2)

    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Check complexity
        if metrics['summary'].get('average_complexity', 0) > 10:
            recommendations.append(
                "Consider refactoring complex functions. "
                f"Average complexity is {metrics['summary']['average_complexity']:.1f} (target: <10)"
            )

        # Check maintainability
        if metrics['summary'].get('average_maintainability', 100) < 60:
            recommendations.append(
                "Low maintainability index detected. "
                "Consider simplifying code structure and reducing coupling"
            )

        # Check hotspots
        if len(metrics.get('hotspots', [])) > 5:
            recommendations.append(
                f"Found {len(metrics['hotspots'])} complexity hotspots. "
                "Focus refactoring efforts on these files first"
            )

        # Check code/comment ratio
        total_code = 0
        total_comment = 0
        for loc_metrics in metrics['loc'].values():
            total_code += loc_metrics.get('code', 0)
            total_comment += loc_metrics.get('comment', 0)

        if total_code > 0:
            comment_ratio = (total_comment / total_code) * 100
            if comment_ratio < 10:
                recommendations.append(
                    f"Low comment ratio ({comment_ratio:.1f}%). "
                    "Consider adding more documentation"
                )

        return recommendations

    async def identify_refactoring_candidates(self, metrics: Dict) -> List[Dict]:
        """
        Identify functions/classes that need refactoring

        Args:
            metrics: Calculated metrics

        Returns:
            List of refactoring candidates
        """
        candidates = []

        # Check complexity
        for file_path, complexity in metrics['complexity'].items():
            for func_name, func_complexity in complexity.get('functions', {}).items():
                if func_complexity > self.thresholds['complexity']['high']:
                    candidates.append({
                        'type': 'function',
                        'name': func_name,
                        'file': file_path,
                        'complexity': func_complexity,
                        'priority': 'high' if func_complexity > self.thresholds['complexity']['very_high'] else 'medium',
                        'suggestion': 'Extract method or simplify logic'
                    })

        # Check maintainability
        for file_path, maintainability in metrics['maintainability'].items():
            if maintainability < self.thresholds['maintainability']['low']:
                candidates.append({
                    'type': 'file',
                    'name': Path(file_path).name,
                    'file': file_path,
                    'maintainability': maintainability,
                    'priority': 'high',
                    'suggestion': 'Major refactoring needed - consider splitting file'
                })

        # Sort by priority
        candidates.sort(key=lambda x: (x['priority'] != 'high', x.get('complexity', 0)), reverse=True)

        return candidates[:10]  # Return top 10 candidates