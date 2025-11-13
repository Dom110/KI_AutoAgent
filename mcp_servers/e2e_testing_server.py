#!/usr/bin/env python3
"""
MCP Server: E2E Testing
Provides E2E test generation and execution capabilities
"""

import asyncio
import json
import sys
from typing import Any, Dict, List
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.e2e_testing.test_generator import E2ETestGenerator
from backend.e2e_testing.test_executor import PlaywrightTestExecutor
from mcp.server import Server
from mcp.types import Tool
import mcp.types as types


class E2ETestingMCPServer:
    """MCP Server for E2E testing"""
    
    def __init__(self):
        self.server = Server("e2e-testing-server")
        self.generators = {}
        self.executors = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent | types.ToolResultBlockParam]:
            """Handle tool calls"""
            
            if name == "analyze_react_app":
                return await self._analyze_react_app(arguments)
            elif name == "generate_tests":
                return await self._generate_tests(arguments)
            elif name == "run_tests":
                return await self._run_tests(arguments)
            elif name == "run_test_file":
                return await self._run_test_file(arguments)
            elif name == "get_test_scenarios":
                return await self._get_test_scenarios(arguments)
            elif name == "export_tests":
                return await self._export_tests(arguments)
            elif name == "get_statistics":
                return await self._get_statistics(arguments)
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="analyze_react_app",
                    description="Analyze React app structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_path": {
                                "type": "string",
                                "description": "Path to React app"
                            }
                        },
                        "required": ["app_path"]
                    }
                ),
                Tool(
                    name="generate_tests",
                    description="Generate E2E tests from app analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_path": {
                                "type": "string",
                                "description": "Path to React app"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for tests"
                            }
                        },
                        "required": ["app_path"]
                    }
                ),
                Tool(
                    name="run_tests",
                    description="Run all E2E tests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_dir": {
                                "type": "string",
                                "description": "Directory containing tests"
                            }
                        },
                        "required": ["test_dir"]
                    }
                ),
                Tool(
                    name="run_test_file",
                    description="Run specific test file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_file": {
                                "type": "string",
                                "description": "Path to test file"
                            }
                        },
                        "required": ["test_file"]
                    }
                ),
                Tool(
                    name="get_test_scenarios",
                    description="Get generated test scenarios",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_path": {
                                "type": "string",
                                "description": "Path to React app"
                            }
                        },
                        "required": ["app_path"]
                    }
                ),
                Tool(
                    name="export_tests",
                    description="Export tests to file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_path": {
                                "type": "string",
                                "description": "Path to React app"
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Output file path"
                            }
                        },
                        "required": ["app_path", "output_file"]
                    }
                ),
                Tool(
                    name="get_statistics",
                    description="Get test generation statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_path": {
                                "type": "string",
                                "description": "Path to React app"
                            }
                        },
                        "required": ["app_path"]
                    }
                ),
            ]
    
    async def _analyze_react_app(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Analyze React app"""
        try:
            app_path = args.get("app_path")
            
            generator = E2ETestGenerator(app_path)
            analysis = generator.analyzer.analyze_app()
            
            self.generators[app_path] = generator
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "components": analysis['total_components'],
                    "components_with_forms": len(generator.analyzer.get_components_with_forms()),
                    "components_with_api": len(generator.analyzer.get_components_with_api_calls()),
                    "components_with_routes": len(generator.analyzer.get_components_with_routes()),
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _generate_tests(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Generate tests"""
        try:
            app_path = args.get("app_path")
            output_dir = args.get("output_dir", f"{app_path}/tests/e2e")
            
            generator = E2ETestGenerator(app_path)
            result = await asyncio.to_thread(generator.analyze_and_generate)
            generator.write_test_files(output_dir)
            
            self.generators[app_path] = generator
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "scenarios_generated": result['scenarios'],
                    "test_files": len(result['test_files']),
                    "output_dir": output_dir,
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _run_tests(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Run tests"""
        try:
            test_dir = args.get("test_dir")
            
            executor = PlaywrightTestExecutor(test_dir)
            result = await executor.run_all_tests()
            
            self.executors[test_dir] = executor
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "total_tests": result.get('total_tests', 0),
                    "passed": result.get('passed_tests', 0),
                    "failed": result.get('failed_tests', 0),
                    "success_rate": result.get('success_rate', 0),
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _run_test_file(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Run test file"""
        try:
            test_file = args.get("test_file")
            
            executor = PlaywrightTestExecutor(str(Path(test_file).parent))
            result = await executor.run_test_file(test_file)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "suite": result.suite_name,
                    "total": result.total_tests,
                    "passed": result.passed_tests,
                    "failed": result.failed_tests,
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _get_test_scenarios(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get test scenarios"""
        try:
            app_path = args.get("app_path")
            
            if app_path not in self.generators:
                generator = E2ETestGenerator(app_path)
                generator.analyze_and_generate()
                self.generators[app_path] = generator
            else:
                generator = self.generators[app_path]
            
            scenarios_by_type = {}
            for scenario in generator.scenarios:
                scenario_type = scenario.scenario_type
                if scenario_type not in scenarios_by_type:
                    scenarios_by_type[scenario_type] = []
                scenarios_by_type[scenario_type].append({
                    'component': scenario.component_name,
                    'title': scenario.title,
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "scenarios": scenarios_by_type,
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _export_tests(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Export tests"""
        try:
            app_path = args.get("app_path")
            output_file = args.get("output_file")
            
            if app_path not in self.generators:
                generator = E2ETestGenerator(app_path)
                generator.analyze_and_generate()
                self.generators[app_path] = generator
            else:
                generator = self.generators[app_path]
            
            generator.export_scenarios(output_file)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "output_file": output_file,
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def _get_statistics(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get statistics"""
        try:
            app_path = args.get("app_path")
            
            if app_path not in self.generators:
                generator = E2ETestGenerator(app_path)
                generator.analyze_and_generate()
                self.generators[app_path] = generator
            else:
                generator = self.generators[app_path]
            
            stats = generator.get_statistics()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "statistics": stats,
                })
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )]
    
    async def run(self, port: int = 3002):
        """Run MCP server"""
        print(f"🚀 E2E Testing MCP Server starting on port {port}...")
        
        print("📝 Available tools:")
        tools = await self.server.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


async def main():
    """Main entry point"""
    server = E2ETestingMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())