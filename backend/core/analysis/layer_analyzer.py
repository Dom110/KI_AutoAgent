from __future__ import annotations

"""
System Layers Analyzer
Detects architectural layers and validates layer separation
Critical for architecture validation and refactoring guidance
"""

import logging
import os
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class LayerAnalyzer:
    """
    Analyzes system architecture layers and detects violations

    Architectural Layers:
    1. Presentation Layer (UI, Controllers, Views)
    2. Business Layer (Services, Business Logic, Domain)
    3. Data Layer (Database, ORM, Repositories)
    4. Infrastructure Layer (Utils, Config, External Services)

    Features:
    - Automatic layer detection based on folder structure
    - Layer violation detection (e.g., UI directly accessing Database)
    - Dependency direction validation
    - Architecture quality scoring
    """

    # Layer definitions with keywords
    LAYER_PATTERNS = {
        "presentation": {
            "keywords": [
                "ui",
                "view",
                "controller",
                "frontend",
                "react",
                "vue",
                "angular",
                "template",
                "component",
            ],
            "level": 3,  # Top layer
            "allowed_dependencies": ["business", "infrastructure"],
        },
        "business": {
            "keywords": [
                "service",
                "business",
                "domain",
                "logic",
                "use_case",
                "usecase",
                "handler",
                "processor",
            ],
            "level": 2,  # Middle layer
            "allowed_dependencies": ["data", "infrastructure"],
        },
        "data": {
            "keywords": [
                "database",
                "db",
                "repository",
                "dao",
                "model",
                "orm",
                "entity",
                "migration",
                "schema",
            ],
            "level": 1,  # Bottom layer
            "allowed_dependencies": ["infrastructure"],
        },
        "infrastructure": {
            "keywords": [
                "utils",
                "util",
                "helper",
                "config",
                "settings",
                "logger",
                "cache",
                "queue",
                "external",
            ],
            "level": 0,  # Base layer
            "allowed_dependencies": [],  # Infrastructure should not depend on other layers
        },
    }

    def __init__(self):
        self.layers = {}
        self.violations = []
        self.quality_score = 0.0

    async def detect_system_layers(self, code_index: dict[str, Any]) -> dict[str, Any]:
        """
        Detect system layers from code index

        Args:
            code_index: Output from CodeIndexer.build_full_index()

        Returns:
            {
                'layers': [
                    {
                        'name': 'presentation',
                        'level': 3,
                        'components': ['frontend/ui.py', 'controllers/main.py'],
                        'allowed_dependencies': ['business', 'infrastructure'],
                        'violations': []
                    }
                ],
                'violations': [
                    {
                        'from': 'frontend/ui.py',
                        'to': 'database/models.py',
                        'from_layer': 'presentation',
                        'to_layer': 'data',
                        'severity': 'error',
                        'suggestion': 'Use business layer as intermediary'
                    }
                ],
                'quality_score': 0.85,
                'metrics': {
                    'total_files': 50,
                    'layered_files': 45,
                    'unlayered_files': 5,
                    'total_violations': 3,
                    'critical_violations': 1
                }
            }
        """
        logger.info("Detecting system layers...")

        ast_data = code_index.get("ast", {}).get("files", {})
        import_graph = code_index.get("import_graph", {})

        if not ast_data:
            logger.warning("No AST data available for layer analysis")
            return self._empty_layer_analysis()

        # Step 1: Classify files into layers
        file_layers = self._classify_files_into_layers(ast_data)
        logger.info(f"Files classified into layers: {len(file_layers)}")

        # Step 2: Build layer structure
        layers = self._build_layer_structure(file_layers)
        self.layers = layers

        # Step 3: Detect layer violations
        violations = self._detect_layer_violations(file_layers, import_graph)
        self.violations = violations
        logger.info(f"Layer violations detected: {len(violations)}")

        # Step 4: Calculate quality score
        quality_score = self._calculate_quality_score(file_layers, violations, ast_data)
        self.quality_score = quality_score

        # Step 5: Calculate metrics
        metrics = self._calculate_metrics(file_layers, violations, ast_data)

        result = {
            "layers": layers,
            "violations": violations,
            "quality_score": quality_score,
            "metrics": metrics,
            "timestamp": None,  # Will be set by caller
        }

        logger.info(f"Layer analysis complete: Quality score = {quality_score:.2f}")
        return result

    def _classify_files_into_layers(self, ast_data: dict[str, Any]) -> dict[str, str]:
        """
        Classify each file into an architectural layer

        Returns:
            {'file_path.py': 'presentation', 'other.py': 'business'}
        """
        file_layers = {}

        for file_path in ast_data.keys():
            layer = self._detect_file_layer(file_path)
            file_layers[file_path] = layer

        return file_layers

    def _detect_file_layer(self, file_path: str) -> str:
        """
        Detect which layer a file belongs to based on path and name

        Strategy:
        1. Check folder structure (e.g., 'frontend/', 'services/', 'database/')
        2. Check file name (e.g., 'controller.py', 'repository.py')
        3. Default to 'infrastructure' if unclear
        """
        file_path_lower = file_path.lower()

        # Score each layer based on keyword matches
        layer_scores = defaultdict(int)

        for layer_name, layer_config in self.LAYER_PATTERNS.items():
            keywords = layer_config["keywords"]

            for keyword in keywords:
                # Check in full path
                if keyword in file_path_lower:
                    layer_scores[layer_name] += 1

                # Bonus points for folder name match
                if (
                    f"/{keyword}/" in file_path_lower
                    or f"/{keyword}s/" in file_path_lower
                ):
                    layer_scores[layer_name] += 2

                # Bonus points for file name match
                file_name = os.path.basename(file_path_lower)
                if keyword in file_name:
                    layer_scores[layer_name] += 1

        # Return layer with highest score
        if layer_scores:
            best_layer = max(layer_scores, key=layer_scores.get)
            return best_layer

        # Default to infrastructure
        return "infrastructure"

    def _build_layer_structure(
        self, file_layers: dict[str, str]
    ) -> list[dict[str, Any]]:
        """
        Build layer structure with components
        """
        # Group files by layer
        layer_components = defaultdict(list)
        for file_path, layer in file_layers.items():
            layer_components[layer].append(file_path)

        # Build layer structure
        layers = []
        for layer_name, layer_config in self.LAYER_PATTERNS.items():
            components = layer_components.get(layer_name, [])

            layers.append(
                {
                    "name": layer_name,
                    "level": layer_config["level"],
                    "components": components,
                    "component_count": len(components),
                    "allowed_dependencies": layer_config["allowed_dependencies"],
                    "violations": [],  # Will be filled in next step
                }
            )

        # Sort by level (top to bottom)
        layers.sort(key=lambda x: x["level"], reverse=True)

        return layers

    def _detect_layer_violations(
        self, file_layers: dict[str, str], import_graph: dict[str, list[str]]
    ) -> list[dict[str, Any]]:
        """
        Detect violations of layer architecture

        A violation occurs when:
        1. A file imports from a higher layer (e.g., business → presentation)
        2. A file imports from a disallowed layer (e.g., presentation → data)
        3. Infrastructure layer imports from other layers
        """
        violations = []

        for from_file, imported_files in import_graph.items():
            from_layer = file_layers.get(from_file, "infrastructure")

            for imported_file in imported_files:
                # Try to resolve imported file to actual file path
                to_file = self._resolve_import_to_file(imported_file, file_layers)
                if not to_file:
                    continue

                to_layer = file_layers.get(to_file, "infrastructure")

                # Check if this is a violation
                violation = self._check_layer_violation(
                    from_file, from_layer, to_file, to_layer
                )
                if violation:
                    violations.append(violation)

        return violations

    def _resolve_import_to_file(
        self, import_name: str, file_layers: dict[str, str]
    ) -> str:
        """
        Resolve import name to actual file path

        Example: 'services.user' → 'backend/services/user.py'
        """
        # Try to find matching file in file_layers
        for file_path in file_layers.keys():
            # Convert file path to import path
            import_path = file_path.replace("/", ".").replace(".py", "")

            if import_name in import_path or import_path in import_name:
                return file_path

        return None

    def _check_layer_violation(
        self, from_file: str, from_layer: str, to_file: str, to_layer: str
    ) -> dict[str, Any]:
        """
        Check if importing from_layer → to_layer is a violation

        Violations:
        1. Lower layer importing from higher layer (e.g., business → presentation)
        2. Layer importing from disallowed layer (e.g., presentation → data)
        3. Infrastructure importing from any other layer
        """
        # Same layer - always allowed
        if from_layer == to_layer:
            return None

        from_config = self.LAYER_PATTERNS.get(from_layer, {})
        to_config = self.LAYER_PATTERNS.get(to_layer, {})

        from_level = from_config.get("level", 0)
        to_level = to_config.get("level", 0)
        allowed_deps = from_config.get("allowed_dependencies", [])

        # Violation 1: Importing from higher layer (upward dependency)
        if to_level > from_level:
            return {
                "from": from_file,
                "to": to_file,
                "from_layer": from_layer,
                "to_layer": to_layer,
                "severity": "error",
                "type": "upward_dependency",
                "suggestion": f'{from_layer} should not depend on {to_layer}. Refactor to use {allowed_deps[0] if allowed_deps else "infrastructure"}.',
            }

        # Violation 2: Importing from disallowed layer
        if to_layer not in allowed_deps:
            # Infrastructure is always allowed (unless you're infrastructure)
            if to_layer == "infrastructure":
                return None

            return {
                "from": from_file,
                "to": to_file,
                "from_layer": from_layer,
                "to_layer": to_layer,
                "severity": "warning",
                "type": "disallowed_dependency",
                "suggestion": f"{from_layer} should not directly depend on {to_layer}. Allowed: {allowed_deps}.",
            }

        # No violation
        return None

    def _calculate_quality_score(
        self,
        file_layers: dict[str, str],
        violations: list[dict[str, Any]],
        ast_data: dict[str, Any],
    ) -> float:
        """
        Calculate architecture quality score (0.0 - 1.0)

        Factors:
        - Files properly layered: +points
        - Violations: -points (more severe = more deduction)
        - Layer balance: +points (not all in one layer)
        """
        total_files = len(ast_data)
        if total_files == 0:
            return 0.0

        # Base score: How many files are layered?
        layered_files = len(file_layers)
        base_score = layered_files / total_files

        # Deduct for violations
        error_violations = len([v for v in violations if v["severity"] == "error"])
        warning_violations = len([v for v in violations if v["severity"] == "warning"])

        violation_penalty = (error_violations * 0.1) + (warning_violations * 0.05)
        violation_penalty = min(violation_penalty, 0.5)  # Cap at 50% penalty

        # Bonus for layer balance (not all files in one layer)
        layer_counts = defaultdict(int)
        for layer in file_layers.values():
            layer_counts[layer] += 1

        layer_balance = len(layer_counts) / len(self.LAYER_PATTERNS)  # 0.0 - 1.0

        # Final score
        quality_score = (base_score * 0.6) + (layer_balance * 0.2) - violation_penalty
        quality_score = max(0.0, min(1.0, quality_score))  # Clamp to 0.0 - 1.0

        return round(quality_score, 2)

    def _calculate_metrics(
        self,
        file_layers: dict[str, str],
        violations: list[dict[str, Any]],
        ast_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate layer analysis metrics
        """
        total_files = len(ast_data)
        layered_files = len(file_layers)
        unlayered_files = total_files - layered_files

        # Count violations by severity
        critical_violations = len([v for v in violations if v["severity"] == "error"])
        warning_violations = len([v for v in violations if v["severity"] == "warning"])

        # Layer distribution
        layer_distribution = defaultdict(int)
        for layer in file_layers.values():
            layer_distribution[layer] += 1

        return {
            "total_files": total_files,
            "layered_files": layered_files,
            "unlayered_files": unlayered_files,
            "total_violations": len(violations),
            "critical_violations": critical_violations,
            "warning_violations": warning_violations,
            "layer_distribution": dict(layer_distribution),
        }

    def _empty_layer_analysis(self) -> dict[str, Any]:
        """Return empty layer analysis structure"""
        return {
            "layers": [],
            "violations": [],
            "quality_score": 0.0,
            "metrics": {
                "total_files": 0,
                "layered_files": 0,
                "unlayered_files": 0,
                "total_violations": 0,
                "critical_violations": 0,
                "warning_violations": 0,
            },
        }
