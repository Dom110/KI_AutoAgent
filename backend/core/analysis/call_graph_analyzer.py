from __future__ import annotations

"""
Function Call Graph Analyzer
Builds comprehensive call graph showing which functions call which other functions
Critical for impact analysis, dead code detection, and refactoring safety
"""

import logging
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)


class CallGraphAnalyzer:
    """
    Analyzes function call relationships to build comprehensive call graph

    Features:
    - Call graph construction (who calls whom)
    - Entry point detection (main, init, etc.)
    - Hot path analysis (most frequently called)
    - Dead code detection (functions never called)
    - Recursive call detection
    - Call clustering (groups of related functions)
    """

    def __init__(self):
        self.call_graph = {}
        self.reverse_call_graph = {}
        self.entry_points = []
        self.hot_functions = []
        self.unused_functions = []

    async def build_call_graph(self, code_index: dict[str, Any]) -> dict[str, Any]:
        """
        Build complete function call graph from code index

        Args:
            code_index: Output from CodeIndexer.build_full_index()

        Returns:
            {
                'nodes': [
                    {'function_id': 'file.py:foo', 'calls': 5, 'called_by': 3, 'is_recursive': False}
                ],
                'edges': [
                    {'from': 'file1.py:foo', 'to': 'file2.py:bar', 'count': 1, 'async': False}
                ],
                'entry_points': ['main.py:main', 'server.py:init'],
                'hot_paths': [
                    {'path': ['main', 'process', 'execute'], 'frequency': 10}
                ],
                'unused_functions': ['utils.py:unused_helper'],
                'clusters': [
                    {'id': 'cluster_1', 'functions': [...], 'cohesion': 0.85}
                ],
                'metrics': {
                    'total_functions': 150,
                    'total_calls': 450,
                    'max_depth': 8,
                    'avg_calls_per_function': 3.0
                }
            }
        """
        logger.info("Building function call graph...")

        ast_data = code_index.get("ast", {}).get("files", {})
        if not ast_data:
            logger.warning("No AST data available for call graph analysis")
            return self._empty_call_graph()

        # Step 1: Build function registry (all functions in codebase)
        function_registry = self._build_function_registry(ast_data)
        logger.info(f"Function registry: {len(function_registry)} functions")

        # Step 2: Build call graph (who calls whom)
        call_graph, reverse_call_graph = self._build_call_relationships(
            ast_data, function_registry
        )
        self.call_graph = call_graph
        self.reverse_call_graph = reverse_call_graph

        # Step 3: Detect entry points (functions not called by others)
        entry_points = self._detect_entry_points(function_registry, reverse_call_graph)
        self.entry_points = entry_points
        logger.info(f"Entry points detected: {len(entry_points)}")

        # Step 4: Find unused functions (not called, not entry points)
        unused_functions = self._find_unused_functions(
            function_registry, reverse_call_graph, entry_points
        )
        self.unused_functions = unused_functions
        logger.info(f"Unused functions: {len(unused_functions)}")

        # Step 5: Detect hot paths (most frequently called sequences)
        hot_paths = self._detect_hot_paths(call_graph, entry_points)

        # Step 6: Build nodes with metrics
        nodes = self._build_nodes(function_registry, call_graph, reverse_call_graph)

        # Step 7: Build edges
        edges = self._build_edges(call_graph, ast_data)

        # Step 8: Cluster analysis (groups of related functions)
        clusters = self._analyze_clusters(call_graph, function_registry)

        # Step 9: Calculate metrics
        metrics = self._calculate_metrics(nodes, edges, call_graph)

        result = {
            "nodes": nodes,
            "edges": edges,
            "entry_points": entry_points,
            "hot_paths": hot_paths,
            "unused_functions": unused_functions,
            "clusters": clusters,
            "metrics": metrics,
            "timestamp": None,  # Will be set by caller
        }

        logger.info(f"Call graph built: {len(nodes)} nodes, {len(edges)} edges")
        return result

    def _build_function_registry(
        self, ast_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Build registry of all functions in codebase

        Returns:
            {'file.py:function_name': {'file': 'file.py', 'name': 'function_name', 'line': 10, ...}}
        """
        registry = {}

        for file_path, file_data in ast_data.items():
            functions = file_data.get("functions", [])
            for func in functions:
                func_id = f"{file_path}:{func['name']}"
                registry[func_id] = {
                    "file": file_path,
                    "name": func["name"],
                    "line": func.get("line", 0),
                    "async": func.get("async", False),
                    "parameters": func.get("parameters", []),
                    "calls": func.get("calls", []),
                }

        return registry

    def _build_call_relationships(
        self, ast_data: dict[str, Any], function_registry: dict[str, dict[str, Any]]
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """
        Build call graph and reverse call graph

        Returns:
            (call_graph, reverse_call_graph)
            call_graph: {'func_id': ['called_func1', 'called_func2']}
            reverse_call_graph: {'func_id': ['caller1', 'caller2']}
        """
        call_graph = defaultdict(list)
        reverse_call_graph = defaultdict(list)

        for func_id, func_data in function_registry.items():
            file_path = func_data["file"]
            func_data["name"]

            # Get all functions this function calls
            calls = func_data.get("calls", [])

            for called_func_name in calls:
                # Try to resolve called function to full func_id
                called_func_id = self._resolve_function_id(
                    called_func_name, file_path, function_registry
                )

                if called_func_id:
                    call_graph[func_id].append(called_func_id)
                    reverse_call_graph[called_func_id].append(func_id)

        return dict(call_graph), dict(reverse_call_graph)

    def _resolve_function_id(
        self,
        func_name: str,
        current_file: str,
        function_registry: dict[str, dict[str, Any]],
    ) -> str:
        """
        Resolve function name to full function ID

        Strategy:
        1. Check in current file first
        2. Check in imported files
        3. Check globally
        """
        # 1. Check current file
        local_id = f"{current_file}:{func_name}"
        if local_id in function_registry:
            return local_id

        # 2. Check all files (global search)
        for func_id in function_registry:
            if func_id.endswith(f":{func_name}"):
                return func_id

        # Not found - might be external library call
        return None

    def _detect_entry_points(
        self,
        function_registry: dict[str, dict[str, Any]],
        reverse_call_graph: dict[str, list[str]],
    ) -> list[str]:
        """
        Detect entry points (functions not called by other functions)

        Entry points are:
        - Functions named 'main', 'init', 'setup', 'run', 'start'
        - Functions not called by any other function (potential entry points)
        - Functions with decorators like @app.route, @click.command
        """
        entry_points = []

        entry_point_names = {
            "main",
            "init",
            "setup",
            "run",
            "start",
            "__init__",
            "__main__",
        }

        for func_id, func_data in function_registry.items():
            func_name = func_data["name"]

            # Check if function name is a known entry point
            if func_name in entry_point_names:
                entry_points.append(func_id)
                continue

            # Check if function is not called by anyone (potential entry point)
            if (
                func_id not in reverse_call_graph
                or len(reverse_call_graph[func_id]) == 0
            ):
                # Only consider it entry point if it's in a main/server/app file
                file_path = func_data["file"]
                if any(
                    keyword in file_path
                    for keyword in ["main", "server", "app", "__main__"]
                ):
                    entry_points.append(func_id)

        return entry_points

    def _find_unused_functions(
        self,
        function_registry: dict[str, dict[str, Any]],
        reverse_call_graph: dict[str, list[str]],
        entry_points: list[str],
    ) -> list[str]:
        """
        Find functions that are never called

        A function is unused if:
        - It's not called by any other function
        - It's not an entry point
        - It's not a special method (__init__, __str__, etc.)
        """
        unused = []

        special_methods = {
            "__init__",
            "__str__",
            "__repr__",
            "__call__",
            "__enter__",
            "__exit__",
        }

        for func_id, func_data in function_registry.items():
            func_name = func_data["name"]

            # Skip special methods
            if (
                func_name in special_methods
                or func_name.startswith("__")
                and func_name.endswith("__")
            ):
                continue

            # Skip entry points
            if func_id in entry_points:
                continue

            # Check if called by anyone
            if (
                func_id not in reverse_call_graph
                or len(reverse_call_graph[func_id]) == 0
            ):
                unused.append(func_id)

        return unused

    def _detect_hot_paths(
        self, call_graph: dict[str, list[str]], entry_points: list[str]
    ) -> list[dict[str, Any]]:
        """
        Detect hot paths (most frequently traversed call sequences)

        Use BFS from entry points to find common paths
        """
        hot_paths = []

        # For each entry point, traverse and find common paths
        for entry_point in entry_points[:5]:  # Limit to top 5 entry points
            paths = self._bfs_paths(entry_point, call_graph, max_depth=4)

            for path in paths:
                if len(path) >= 2:
                    hot_paths.append(
                        {
                            "path": path,
                            "frequency": 1,  # TODO: Calculate actual frequency from execution logs
                            "depth": len(path),
                        }
                    )

        # Sort by depth (longer paths = more interesting)
        hot_paths.sort(key=lambda x: x["depth"], reverse=True)

        return hot_paths[:10]  # Return top 10 hot paths

    def _bfs_paths(
        self, start: str, call_graph: dict[str, list[str]], max_depth: int = 4
    ) -> list[list[str]]:
        """
        BFS to find all paths from start node up to max_depth
        """
        paths = []
        queue = deque([(start, [start])])
        visited = set()

        while queue:
            node, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if node in visited:
                continue
            visited.add(node)

            paths.append(path)

            # Add children to queue
            for child in call_graph.get(node, []):
                if child not in path:  # Avoid cycles
                    queue.append((child, path + [child]))

        return paths

    def _build_nodes(
        self,
        function_registry: dict[str, dict[str, Any]],
        call_graph: dict[str, list[str]],
        reverse_call_graph: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        """
        Build node list with metrics
        """
        nodes = []

        for func_id, func_data in function_registry.items():
            calls_count = len(call_graph.get(func_id, []))
            called_by_count = len(reverse_call_graph.get(func_id, []))

            # Check if recursive
            is_recursive = func_id in call_graph.get(func_id, [])

            nodes.append(
                {
                    "function_id": func_id,
                    "name": func_data["name"],
                    "file": func_data["file"],
                    "line": func_data["line"],
                    "calls": calls_count,
                    "called_by": called_by_count,
                    "is_recursive": is_recursive,
                    "async": func_data.get("async", False),
                }
            )

        return nodes

    def _build_edges(
        self, call_graph: dict[str, list[str]], ast_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Build edge list
        """
        edges = []

        for from_func, to_funcs in call_graph.items():
            for to_func in to_funcs:
                # Get async status from AST
                file_path = from_func.split(":")[0]
                func_name = from_func.split(":")[1]
                is_async = False

                file_data = ast_data.get(file_path, {})
                for func in file_data.get("functions", []):
                    if func["name"] == func_name:
                        is_async = func.get("async", False)
                        break

                edges.append(
                    {
                        "from": from_func,
                        "to": to_func,
                        "count": 1,  # TODO: Count actual call frequency
                        "async": is_async,
                    }
                )

        return edges

    def _analyze_clusters(
        self,
        call_graph: dict[str, list[str]],
        function_registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Find clusters of related functions (high cohesion)
        """
        # Simple clustering: Group by file
        file_clusters = defaultdict(list)

        for func_id in function_registry:
            file_path = func_id.split(":")[0]
            file_clusters[file_path].append(func_id)

        clusters = []
        for i, (file_path, functions) in enumerate(file_clusters.items()):
            if len(functions) > 1:
                # Calculate cohesion (how much functions in this file call each other)
                internal_calls = 0
                external_calls = 0

                for func_id in functions:
                    for called_func in call_graph.get(func_id, []):
                        if called_func in functions:
                            internal_calls += 1
                        else:
                            external_calls += 1

                total_calls = internal_calls + external_calls
                cohesion = internal_calls / total_calls if total_calls > 0 else 0

                clusters.append(
                    {
                        "id": f"cluster_{i}",
                        "file": file_path,
                        "functions": functions,
                        "size": len(functions),
                        "cohesion": round(cohesion, 2),
                        "internal_calls": internal_calls,
                        "external_calls": external_calls,
                    }
                )

        # Sort by cohesion (highest first)
        clusters.sort(key=lambda x: x["cohesion"], reverse=True)

        return clusters

    def _calculate_metrics(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        call_graph: dict[str, list[str]],
    ) -> dict[str, Any]:
        """
        Calculate overall call graph metrics
        """
        total_functions = len(nodes)
        total_calls = len(edges)

        # Calculate max depth (longest call chain)
        max_depth = 0
        for node in nodes:
            func_id = node["function_id"]
            depth = self._calculate_call_depth(func_id, call_graph)
            max_depth = max(max_depth, depth)

        # Average calls per function
        avg_calls = total_calls / total_functions if total_functions > 0 else 0

        return {
            "total_functions": total_functions,
            "total_calls": total_calls,
            "max_call_depth": max_depth,
            "avg_calls_per_function": round(avg_calls, 2),
            "functions_with_no_calls": len([n for n in nodes if n["calls"] == 0]),
            "functions_not_called": len([n for n in nodes if n["called_by"] == 0]),
        }

    def _calculate_call_depth(
        self, func_id: str, call_graph: dict[str, list[str]], visited: set[str] = None
    ) -> int:
        """
        Calculate maximum call depth from this function (DFS)
        """
        if visited is None:
            visited = set()

        if func_id in visited:
            return 0  # Cycle detected

        visited.add(func_id)

        children = call_graph.get(func_id, [])
        if not children:
            return 1

        max_child_depth = max(
            (
                self._calculate_call_depth(child, call_graph, visited.copy())
                for child in children
            ),
            default=0,
        )

        return 1 + max_child_depth

    def _empty_call_graph(self) -> dict[str, Any]:
        """Return empty call graph structure"""
        return {
            "nodes": [],
            "edges": [],
            "entry_points": [],
            "hot_paths": [],
            "unused_functions": [],
            "clusters": [],
            "metrics": {
                "total_functions": 0,
                "total_calls": 0,
                "max_call_depth": 0,
                "avg_calls_per_function": 0,
            },
        }
