"""
Architecture Manager v1.0
Maintains system architecture as source of truth

This module manages architecture documentation for codebases:
- Creates and maintains architecture files in .ki_autoagent/architecture/
- Provides consistency checking between code and docs
- Reverse-engineers architecture from existing code
- Generates diagrams and visualizations

Location: workspace/.ki_autoagent/architecture/
Files managed:
- system_overview.md: High-level system description
- components.json: Component definitions and relationships
- tech_stack.yaml: Technologies, frameworks, libraries used
- patterns.md: Design patterns and best practices
- api_spec.yaml: API definitions (optional)
- database_schema.sql: Database structure (optional)

Author: KI AutoAgent Team
Version: 1.0.0
Date: 2025-10-14
"""

from __future__ import annotations

from pathlib import Path
import json
import yaml
import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ArchitectureManager:
    """
    Manages system architecture documentation.

    Provides methods to save, load, update, and verify architecture
    documentation against actual codebase structure.
    """

    def __init__(self, workspace_path: str):
        """
        Initialize Architecture Manager.

        Args:
            workspace_path: Absolute path to workspace root
        """
        self.workspace_path = Path(workspace_path)
        self.arch_dir = self.workspace_path / ".ki_autoagent_ws" / "architecture"

        # Create architecture directory if it doesn't exist
        self.arch_dir.mkdir(parents=True, exist_ok=True)

        # Define file paths
        self.overview_file = self.arch_dir / "system_overview.md"
        self.components_file = self.arch_dir / "components.json"
        self.tech_stack_file = self.arch_dir / "tech_stack.yaml"
        self.patterns_file = self.arch_dir / "patterns.md"
        self.api_spec_file = self.arch_dir / "api_spec.yaml"
        self.db_schema_file = self.arch_dir / "database_schema.sql"

        logger.debug(f"📐 ArchitectureManager initialized for: {workspace_path}")
        logger.debug(f"   Architecture dir: {self.arch_dir}")

    async def save_architecture(self, design: dict) -> None:
        """
        Save architecture documentation from design dict.

        Args:
            design: Architecture design with structure:
                {
                    "overview": "System description...",
                    "components": [
                        {"name": "X", "type": "...", "responsibilities": "..."},
                        ...
                    ],
                    "tech_stack": {
                        "languages": ["Python", "TypeScript"],
                        "frameworks": ["FastAPI", "React"],
                        "databases": ["PostgreSQL"]
                    },
                    "patterns": [
                        {"name": "MVC", "description": "..."},
                        ...
                    ],
                    "api_spec": {...},  # Optional
                    "database": {...}   # Optional
                }
        """
        logger.info(f"💾 Saving architecture documentation...")

        try:
            # 1. System Overview
            if "overview" in design:
                await self._save_overview(design["overview"])

            # 2. Components
            if "components" in design:
                await self._save_components(design["components"])

            # 3. Tech Stack
            if "tech_stack" in design:
                await self._save_tech_stack(design["tech_stack"])

            # 4. Patterns
            if "patterns" in design:
                await self._save_patterns(design["patterns"])

            # 5. API Spec (optional)
            if "api_spec" in design:
                await self._save_api_spec(design["api_spec"])

            # 6. Database Schema (optional)
            if "database" in design:
                await self._save_database_schema(design["database"])

            # 7. Metadata
            await self._save_metadata({
                "created": datetime.now().isoformat(),
                "version": "1.0.0",
                "workspace": str(self.workspace_path)
            })

            logger.info(f"✅ Architecture documentation saved to: {self.arch_dir}")

        except Exception as e:
            logger.error(f"❌ Failed to save architecture: {e}")
            raise

    async def load_architecture(self) -> dict:
        """
        Load existing architecture or return empty dict.

        Returns:
            Architecture dict with same structure as save_architecture expects,
            or empty dict if no architecture exists.
        """
        logger.debug(f"📖 Loading architecture from: {self.arch_dir}")

        if not self.arch_dir.exists():
            logger.debug("   No architecture directory found")
            return {}

        try:
            architecture = {}

            # Load each component
            if self.overview_file.exists():
                architecture["overview"] = self.overview_file.read_text()

            if self.components_file.exists():
                architecture["components"] = json.loads(self.components_file.read_text())

            if self.tech_stack_file.exists():
                architecture["tech_stack"] = yaml.safe_load(self.tech_stack_file.read_text())

            if self.patterns_file.exists():
                architecture["patterns"] = self._parse_patterns_md(
                    self.patterns_file.read_text()
                )

            if self.api_spec_file.exists():
                architecture["api_spec"] = yaml.safe_load(self.api_spec_file.read_text())

            if self.db_schema_file.exists():
                architecture["database"] = self.db_schema_file.read_text()

            logger.info(f"✅ Loaded architecture: {len(architecture)} sections")
            return architecture

        except Exception as e:
            logger.error(f"❌ Failed to load architecture: {e}")
            return {}

    async def update_architecture(self, changes: dict) -> None:
        """
        Update existing architecture with changes (intelligent merge).

        Args:
            changes: Partial architecture dict with updates
        """
        logger.info(f"🔄 Updating architecture...")

        # Load existing
        existing = await self.load_architecture()

        # Merge changes
        merged = self._merge_architecture(existing, changes)

        # Save merged result
        await self.save_architecture(merged)

        logger.info(f"✅ Architecture updated")

    async def verify_consistency(
        self,
        tree_sitter_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Compare actual code structure with documented architecture.

        Args:
            tree_sitter_analysis: Analysis from tree_sitter_analyzer

        Returns:
            {
                "consistent": bool,
                "score": 0.0-1.0,
                "discrepancies": [
                    {"type": "missing_component", "name": "X"},
                    {"type": "extra_file", "path": "Y"},
                    {"type": "tech_mismatch", "expected": "A", "found": "B"}
                ],
                "suggestions": ["Add docs for X", "Remove Y"]
            }
        """
        logger.info(f"🔍 Verifying architecture consistency...")

        # Load documented architecture
        architecture = await self.load_architecture()

        if not architecture:
            logger.warning("⚠️  No architecture documentation found")
            return {
                "consistent": False,
                "score": 0.0,
                "discrepancies": [{"type": "no_architecture", "message": "No architecture docs"}],
                "suggestions": ["Create architecture documentation"]
            }

        discrepancies = []
        suggestions = []

        # Check components
        if "components" in architecture:
            comp_check = self._verify_components(
                architecture["components"],
                tree_sitter_analysis
            )
            discrepancies.extend(comp_check["discrepancies"])
            suggestions.extend(comp_check["suggestions"])

        # Check tech stack
        if "tech_stack" in architecture:
            tech_check = self._verify_tech_stack(
                architecture["tech_stack"],
                tree_sitter_analysis
            )
            discrepancies.extend(tech_check["discrepancies"])
            suggestions.extend(tech_check["suggestions"])

        # Calculate consistency score
        total_checks = len(architecture.get("components", [])) + len(architecture.get("tech_stack", {}).get("languages", []))
        if total_checks == 0:
            score = 1.0
        else:
            score = max(0.0, 1.0 - (len(discrepancies) / total_checks))

        consistent = score > 0.8 and len(discrepancies) == 0

        result = {
            "consistent": consistent,
            "score": round(score, 2),
            "discrepancies": discrepancies,
            "suggestions": suggestions
        }

        logger.info(f"✅ Consistency check complete: score={score:.2f}, consistent={consistent}")
        return result

    async def generate_architecture_from_code(
        self,
        tree_sitter_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Reverse-engineer architecture from existing code.

        Args:
            tree_sitter_analysis: Analysis from tree_sitter_analyzer

        Returns:
            Architecture dict that can be passed to save_architecture()
        """
        logger.info(f"🔨 Generating architecture from code...")

        architecture = {
            "overview": self._generate_overview(tree_sitter_analysis),
            "components": self._infer_components(tree_sitter_analysis),
            "tech_stack": self._infer_tech_stack(tree_sitter_analysis),
            "patterns": self._infer_patterns(tree_sitter_analysis)
        }

        logger.info(f"✅ Generated architecture: {len(architecture['components'])} components")
        return architecture

    async def export_diagrams(self) -> dict[str, Any]:
        """
        Generate Mermaid diagrams from architecture.

        Returns:
            {"component_diagram": "...", "flow_diagram": "..."}
        """
        logger.info(f"📊 Generating diagrams...")

        architecture = await self.load_architecture()

        diagrams = {}

        if "components" in architecture:
            diagrams["component_diagram"] = self._generate_component_diagram(
                architecture["components"]
            )

        logger.info(f"✅ Generated {len(diagrams)} diagrams")
        return diagrams

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _save_overview(self, overview: str) -> None:
        """Save system overview markdown."""
        content = f"""# System Overview

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{overview}
"""
        self.overview_file.write_text(content)
        logger.debug(f"   ✓ Saved overview")

    async def _save_components(self, components: list) -> None:
        """Save components as JSON."""
        self.components_file.write_text(json.dumps(components, indent=2))
        logger.debug(f"   ✓ Saved {len(components)} components")

    async def _save_tech_stack(self, tech_stack: dict) -> None:
        """Save tech stack as YAML."""
        self.tech_stack_file.write_text(yaml.dump(tech_stack, default_flow_style=False))
        logger.debug(f"   ✓ Saved tech stack")

    async def _save_patterns(self, patterns: list) -> None:
        """Save design patterns as markdown."""
        content = f"""# Design Patterns

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""
        for pattern in patterns:
            content += f"""## {pattern.get('name', 'Unknown')}

**Description:** {pattern.get('description', 'N/A')}

**Usage:** {pattern.get('usage', 'N/A')}

---

"""
        self.patterns_file.write_text(content)
        logger.debug(f"   ✓ Saved {len(patterns)} patterns")

    async def _save_api_spec(self, api_spec: dict) -> None:
        """Save API spec as YAML."""
        self.api_spec_file.write_text(yaml.dump(api_spec, default_flow_style=False))
        logger.debug(f"   ✓ Saved API spec")

    async def _save_database_schema(self, database: dict) -> None:
        """Save database schema as SQL."""
        if isinstance(database, dict):
            # Convert dict to SQL
            schema = self._dict_to_sql(database)
        else:
            schema = str(database)

        self.db_schema_file.write_text(schema)
        logger.debug(f"   ✓ Saved database schema")

    async def _save_metadata(self, metadata: dict) -> None:
        """Save metadata as JSON."""
        metadata_file = self.arch_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        logger.debug(f"   ✓ Saved metadata")

    def _parse_patterns_md(self, content: str) -> list[dict[str, Any]]:
        """Parse patterns from markdown."""
        # Simple parser - split by ## headers
        patterns = []
        sections = content.split("## ")[1:]  # Skip first empty section

        for section in sections:
            lines = section.strip().split("\n")
            if lines:
                name = lines[0].strip()
                patterns.append({"name": name, "description": section})

        return patterns

    def _merge_architecture(self, existing: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """Intelligently merge architecture changes."""
        merged = existing.copy()

        for key, value in changes.items():
            if key in merged and isinstance(value, dict) and isinstance(merged[key], dict):
                # Deep merge for dicts
                merged[key].update(value)
            elif key in merged and isinstance(value, list) and isinstance(merged[key], list):
                # Append for lists (avoid duplicates)
                for item in value:
                    if item not in merged[key]:
                        merged[key].append(item)
            else:
                # Direct replacement
                merged[key] = value

        return merged

    def _verify_components(self, documented: list[dict[str, Any]], analysis: dict[str, Any]) -> dict[str, Any]:
        """Verify documented components exist in code."""
        discrepancies = []
        suggestions = []

        # Check if documented components have files
        for component in documented:
            name = component.get("name", "")
            # Simple check: does a directory or file with this name exist?
            # (This is basic - could be enhanced)

        return {"discrepancies": discrepancies, "suggestions": suggestions}

    def _verify_tech_stack(self, documented: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        """Verify documented tech stack matches code."""
        discrepancies = []
        suggestions = []

        # Check languages
        doc_langs = set(documented.get("languages", []))
        code_langs = set(analysis.get("languages", {}).keys())

        missing = doc_langs - code_langs
        extra = code_langs - doc_langs

        for lang in missing:
            discrepancies.append({
                "type": "tech_missing",
                "language": lang,
                "message": f"Documented language {lang} not found in code"
            })

        for lang in extra:
            suggestions.append(f"Add {lang} to tech stack documentation")

        return {"discrepancies": discrepancies, "suggestions": suggestions}

    def _generate_overview(self, analysis: dict[str, Any]) -> str:
        """Generate overview from code analysis."""
        # FIX v6.4: analysis["files"] is an int, not a list!
        file_count = analysis.get("files", 0)
        if isinstance(file_count, list):
            file_count = len(file_count)
        languages = list(analysis.get("languages", {}).keys())

        return f"""This system consists of {file_count} files across {len(languages)} languages.

**Languages:** {", ".join(languages)}

**Structure:** Code analysis detected the following structure:
- {analysis.get('classes', 0)} classes
- {analysis.get('functions', 0)} functions
- ~{analysis.get('lines', 0)} lines of code

This overview was automatically generated from code analysis.
"""

    def _infer_components(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Infer components from directory structure."""
        components = []

        # FIX v6.4: analysis["files"] is an int, not a list!
        # We can't infer components without file list, so return empty
        files = analysis.get("files", [])
        if isinstance(files, int) or not isinstance(files, list):
            return []

        # Group files by directory
        dirs = {}
        for file_path in files:
            dir_name = str(Path(file_path).parent)
            if dir_name not in dirs:
                dirs[dir_name] = []
            dirs[dir_name].append(file_path)

        # Create component for each significant directory
        for dir_name, files in dirs.items():
            if dir_name != "." and len(files) > 0:
                components.append({
                    "name": Path(dir_name).name,
                    "type": "module",
                    "files": files,
                    "responsibilities": f"Contains {len(files)} files"
                })

        return components

    def _infer_tech_stack(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Infer tech stack from imports and file types."""
        return {
            "languages": list(analysis.get("languages", {}).keys()),
            "frameworks": [],  # Would need import analysis
            "databases": [],   # Would need dependency analysis
            "tools": []
        }

    def _infer_patterns(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Infer design patterns from code structure."""
        patterns = []

        # Simple heuristic: if many classes, likely OOP
        if analysis.get("classes", 0) > 5:
            patterns.append({
                "name": "Object-Oriented Design",
                "description": f"System uses {analysis['classes']} classes"
            })

        return patterns

    def _generate_component_diagram(self, components: list[dict[str, Any]]) -> str:
        """Generate Mermaid component diagram."""
        diagram = "graph TD\n"

        for i, comp in enumerate(components):
            name = comp.get("name", f"Component{i}")
            diagram += f"    {name}[{name}]\n"

        return diagram

    def _dict_to_sql(self, database: dict[str, Any]) -> str:
        """Convert database dict to SQL schema."""
        sql = "-- Database Schema\n-- Generated by Architecture Manager\n\n"

        for table_name, table_def in database.items():
            sql += f"CREATE TABLE {table_name} (\n"
            if isinstance(table_def, dict):
                columns = table_def.get("columns", [])
                sql += ",\n".join(f"  {col}" for col in columns)
            sql += "\n);\n\n"

        return sql
