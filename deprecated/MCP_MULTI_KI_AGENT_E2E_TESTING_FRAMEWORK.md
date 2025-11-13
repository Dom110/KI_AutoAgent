# 🤖 MCP Multi KI Agenten E2E Testing Framework
## Vollständige Strategie zum Testen von KI Agenten, die Software entwickeln

**Version:** 1.0  
**Datum:** 2025  
**Status:** CONCEPT READY FOR IMPLEMENTATION

---

## 📋 INHALTSVERZEICHNIS

1. [Unterschiede zu klassischem E2E Testing](#unterschiede)
2. [Test-Pyramide für KI Agenten](#test-pyramide)
3. [Vollständige Test-Architektur](#test-architektur)
4. [Spezifische Test-Szenarien](#test-szenarien)
5. [Test-Harness & Infrastruktur](#test-harness)
6. [Validierungskriterien](#validierungskriterien)
7. [Implementierungs-Roadmap](#roadmap)

---

## 🎯 Unterschiede zu klassischem E2E Testing {#unterschiede}

### Klassisches E2E Testing (Web-App):
```
User Input
  → Browser
  → Frontend (React/Vue)
  → Backend API
  → Database
  ✓ Assertion: "Button is visible"
  ✓ Assertion: "Data saved in DB"
```

### KI Agent E2E Testing (ANDERS!):
```
Requirements Document
  → KI Agent (Claude/GPT)
  → Parses & Plans (Supervisor Agent)
  → Creates App Structure (Codesmith Agent)
  → Generates Code (ComponentWriter Agent)
  → Deploys & Tests (E2E Test Generator Agent)
  → ReviewFix Agent (Quality Control)
  ✓ Assertion: "Generated code is syntactically correct"
  ✓ Assertion: "Generated app matches requirements"
  ✓ Assertion: "Generated E2E tests pass"
  ✓ Assertion: "Multi-framework support works"
  ✓ Assertion: "MCP Collaboration succeeded"
```

### **KEY INSIGHT**: 
- Klassisches E2E: *Testet die App, die der Benutzer bedient*
- KI Agent E2E: *Testet den Agenten, der Quellcode schreibt*

---

## 📊 Test-Pyramide für KI Agenten {#test-pyramide}

```
                    ┌─────────────────────────┐
                    │   E2E TESTS (10-20)    │
                    │  Full Workflow Tests    │
                    │  Agent + MCP + Deploy  │
                    └────────────┬────────────┘
                                 ▲
                    ┌────────────┴────────────┐
                    │  INTEGRATION TESTS     │
                    │      (50-100)          │
                    │ Agent + MCP Interaction│
                    │ Code Generation Quality│
                    └────────────┬────────────┘
                                 ▲
                ┌────────────────┴────────────────┐
                │   UNIT TESTS (200-500)         │
                │  Individual Agent Functions    │
                │  Component Analysis            │
                │  Code Validation               │
                └────────────────────────────────┘
```

### Test-Verteilung:
- **Unit Tests**: 60-70% (Foundation, fast, isolated)
- **Integration Tests**: 20-30% (Agent collaboration, MCP usage)
- **E2E Tests**: 10-15% (Full workflows, deployment, real scenarios)

---

## 🏗️ Vollständige Test-Architektur {#test-architektur}

### Test-Stack für MCP Multi KI Agenten:

```python
# ============================================================
# LEVEL 1: UNIT TESTS - Einzelne Agent-Funktionen
# ============================================================

class TestFrameworkDetector:
    """Testet automatische Framework-Erkennung"""
    
    def test_react_detection_from_package_json():
        # Input: package.json mit React dependency
        # Expected: Framework = "react", confidence = 0.95+
        pass
    
    def test_vue_detection_from_config():
        # Input: vite.config.js mit Vue plugin
        # Expected: Framework = "vue", confidence = 0.9+
        pass
    
    def test_fastapi_detection_from_requirements():
        # Input: requirements.txt mit fastapi
        # Expected: Framework = "fastapi", confidence = 0.95+
        pass
    
    def test_multi_framework_detection_priority():
        # Input: monorepo mit React + FastAPI
        # Expected: Correct separation Frontend/Backend
        pass


class TestComponentAnalyzer:
    """Testet Code-Analyse für jedes Framework"""
    
    def test_react_component_extraction():
        # Input: React component code
        # Output: UniversalComponent with hooks, state, handlers
        assert component.hooks == ["useState", "useEffect"]
        assert component.state_variables == ["count"]
        pass
    
    def test_vue_template_parsing():
        # Input: Vue .vue file
        # Output: UniversalComponent with methods, data, templates
        assert component.methods == ["increment"]
        assert component.data_properties == ["count"]
        pass
    
    def test_fastapi_route_extraction():
        # Input: FastAPI app.py
        # Output: UniversalAPIRoute with endpoint, method, models
        assert route.path == "/api/users"
        assert route.method == "GET"
        assert route.parameters == ["user_id"]
        pass


class TestCodeGeneration:
    """Testet Code-Generierung"""
    
    def test_react_code_generated_is_valid():
        # Input: Component definition
        # Output: Valid React code
        generated_code = agent.generate_code(component)
        assert ast.parse(generated_code)  # Valid Python syntax? Nein! React is JS!
        # Correct: assert validate_jsx(generated_code)
        pass
    
    def test_generated_code_matches_spec():
        # Input: Component spec
        # Output: Code matches all requirements
        spec = {"props": ["name", "age"], "handlers": ["onClick"]}
        code = agent.generate_code(spec)
        assert "name" in code
        assert "age" in code
        assert "onClick" in code
        pass
    
    def test_test_generation_for_all_frameworks():
        # Input: Component definition (any framework)
        # Output: Valid Playwright tests
        tests = agent.generate_e2e_tests(component)
        # Should have Happy Path, Error Cases, Edge Cases
        assert len(tests) >= 3
        pass


# ============================================================
# LEVEL 2: INTEGRATION TESTS - Agent Collaboration
# ============================================================

class TestAgentCollaboration:
    """Testet Multi-Agent Workflows"""
    
    def test_supervisor_agent_routing():
        """Supervisor muss Anfrage korrekt an andere Agents routen"""
        request = {
            "type": "create_app",
            "framework": "react",
            "features": ["authentication", "dashboard"]
        }
        
        # Supervisor soll zu ComponentWriter routen
        result = await supervisor.process(request)
        assert result.next_agent == "ComponentWriter"
        assert result.framework == "react"
    
    def test_codesmith_app_structure():
        """Codesmith muss konsistente App-Struktur erstellen"""
        spec = get_test_app_spec()
        structure = await codesmith.create_structure(spec)
        
        # Validiere Struktur
        assert has_required_files(structure)
        assert is_valid_project_layout(structure)
        assert has_configuration_files(structure)
    
    def test_component_writer_multi_framework():
        """ComponentWriter muss in mehreren Frameworks schreiben"""
        component_spec = {
            "name": "UserForm",
            "inputs": ["email", "password"],
            "actions": ["submit"]
        }
        
        for framework in ["react", "vue", "angular"]:
            code = await component_writer.generate(component_spec, framework)
            assert is_valid_code(code, framework)
            assert has_required_functionality(code)
    
    def test_e2e_generator_creates_valid_tests():
        """E2E Generator muss valide Playwright Tests erstellen"""
        app_structure = get_sample_app_structure()
        tests = await e2e_generator.generate(app_structure)
        
        # Validiere Tests
        assert len(tests) > 0
        assert all(is_valid_playwright_code(t) for t in tests)
        assert all(has_data_testid_selectors(t) for t in tests)
    
    def test_reviewfix_quality_checks():
        """ReviewFix muss Code validieren und Fehler fixen"""
        generated_code = get_buggy_generated_code()
        fixed_code = await reviewfix.review_and_fix(generated_code)
        
        assert is_valid_syntax(fixed_code)
        assert all_issues_fixed(fixed_code)
        assert complexity_score(fixed_code) >= required_score


# ============================================================
# LEVEL 3: E2E TESTS - Vollständige Workflows
# ============================================================

class TestFullAppDevelopmentWorkflow:
    """Testet kompletten Development Cycle"""
    
    async def test_end_to_end_react_app_creation():
        """
        SCENARIO: User fordert React Todo App an
        
        1. Anfrage in System
        2. Supervisor parst & plant
        3. Codesmith erstellt Struktur
        4. ComponentWriter generates React code
        5. E2E Generator creates Playwright tests
        6. ReviewFix validiert & fixt
        7. App deployed zu temp container
        8. Playwright Tests run gegen live app
        9. Tests pass ✓
        """
        
        # SETUP
        requirements = """
        Create a React Todo Application with:
        - Input field to add todos
        - Display list of todos
        - Mark complete/incomplete
        - Delete todo
        - Local storage persistence
        """
        
        # TEST EXECUTION
        result = await full_workflow.execute(
            requirements=requirements,
            framework="react",
            test_user_actions=True
        )
        
        # VALIDATIONS
        assert result.status == "SUCCESS"
        assert result.app_created == True
        assert result.app_deployable == True
        assert result.e2e_tests_generated == True
        assert result.e2e_tests_passed == True
        assert result.generated_code_quality >= 0.85
        assert result.test_coverage >= 0.80
    
    async def test_end_to_end_vue_app_creation():
        """SCENARIO: User fordert Vue Dashboard an"""
        requirements = """
        Create a Vue.js Dashboard with:
        - Real-time data chart
        - User statistics
        - Export to CSV
        - Dark mode toggle
        """
        
        result = await full_workflow.execute(
            requirements=requirements,
            framework="vue",
            test_user_actions=True
        )
        
        assert result.status == "SUCCESS"
        assert all_assertions_passed(result)
    
    async def test_end_to_end_fastapi_app_creation():
        """SCENARIO: User fordert FastAPI REST API an"""
        requirements = """
        Create a FastAPI backend for:
        - User management (CRUD)
        - Authentication (JWT)
        - Rate limiting
        - API documentation
        """
        
        result = await full_workflow.execute(
            requirements=requirements,
            framework="fastapi",
            test_user_actions=True
        )
        
        assert result.status == "SUCCESS"
        assert all_backend_assertions_passed(result)


# ============================================================
# INTEGRATION: Agent + MCP Servers
# ============================================================

class TestMCPIntegration:
    """Testet MCP Server Integration"""
    
    async def test_mcp_codesmith_server():
        """Codesmith als MCP Server"""
        mcp_server = MCPServer("codesmith")
        
        result = await mcp_server.call_tool({
            "tool": "create_project_structure",
            "params": {
                "framework": "react",
                "app_type": "spa"
            }
        })
        
        assert result.success == True
        assert result.structure is not None
    
    async def test_mcp_component_writer_server():
        """ComponentWriter als MCP Server"""
        mcp_server = MCPServer("component_writer")
        
        result = await mcp_server.call_tool({
            "tool": "generate_component",
            "params": {
                "component_spec": {...},
                "framework": "react"
            }
        })
        
        assert is_valid_code(result.code, "react")
    
    async def test_mcp_e2e_test_generator_server():
        """E2E Test Generator als MCP Server"""
        mcp_server = MCPServer("e2e_test_generator")
        
        result = await mcp_server.call_tool({
            "tool": "generate_tests",
            "params": {"app_structure": {...}}
        })
        
        assert len(result.tests) > 0
        assert all(is_valid_playwright_code(t) for t in result.tests)


# ============================================================
# DEPLOYMENT & LIVE TESTING
# ============================================================

class TestGeneratedAppDeployment:
    """Testet Deployment der generierten App"""
    
    async def test_react_app_deployment():
        """Generierte React App muss sich deployen lassen"""
        app_code = await get_generated_react_app()
        
        # Deploy zu Test Container
        container = await deploy_to_container(
            app_code,
            framework="react",
            port=3001
        )
        
        # Verify Container läuft
        assert container.is_running()
        assert container.port_accessible(3001)
        
        # App laden
        response = await http_get(f"http://localhost:3001")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
    
    async def test_playwright_tests_against_live_app():
        """Generierte Playwright Tests müssen gegen Live App laufen"""
        # Deploy App
        app_url = await deploy_generated_app()
        
        # Get generated tests
        tests = await get_generated_e2e_tests()
        
        # Run tests
        results = await run_playwright_tests(
            tests=tests,
            target_url=app_url
        )
        
        # Assertions
        assert results.passed_count > 0
        assert results.failed_count == 0
        assert results.execution_time < 60  # 60 seconds max
```

---

## 🧪 Spezifische Test-Szenarien {#test-szenarien}

### Szenario 1: Happy Path - React Todo App

```python
async def test_scenario_react_todo_happy_path():
    """
    USER: "Create a React Todo Application"
    
    Expected Flow:
    1. ✓ Supervisor detects "create_app" + React
    2. ✓ Codesmith creates project structure
    3. ✓ ComponentWriter generates components:
       - TodoList.jsx
       - TodoItem.jsx
       - AddTodoForm.jsx
    4. ✓ Services generated for state management
    5. ✓ E2E Generator creates tests for:
       - Add todo flow
       - Mark complete flow
       - Delete todo flow
    6. ✓ ReviewFix validates all code
    7. ✓ App deployed successfully
    8. ✓ All Playwright tests pass
    """
    
    request = {
        "action": "create_app",
        "description": "React Todo Application",
        "features": [
            "add_todo",
            "mark_complete",
            "delete_todo",
            "local_storage"
        ]
    }
    
    result = await mcp_orchestrator.execute_workflow(request)
    
    # Validierungen
    assert result.supervisor_routing_correct()
    assert result.codesmith_structure_created()
    assert result.components_generated == 3
    assert result.tests_generated >= 3
    assert result.code_quality_score >= 0.85
    assert result.e2e_tests_passed == True
    
    return result.summary()
```

### Szenario 2: Error Recovery - Vue App mit Buggy Code

```python
async def test_scenario_error_recovery_vue():
    """
    SCENARIO: ComponentWriter generates buggy Vue code
    ReviewFix muss Bugs erkennen und fixen
    
    Flow:
    1. Codesmith creates Vue structure
    2. ComponentWriter generates Vue components (WITH BUGS)
       - Missing imports
       - Undefined variables
       - Invalid template syntax
    3. ReviewFix Agent detects issues:
       - Runs syntax validation
       - Checks for undefined references
       - Tests template validity
    4. ReviewFix Agent fixes issues:
       - Adds missing imports
       - Fixes undefined variables
       - Corrects template syntax
    5. Verification: Fixed code passes all checks
    """
    
    # Inject intentional bugs
    buggy_component = """
    <template>
      <div>
        <button @click="handleClick">{{ nonExistentVar }}</button>
        <p>{{ undefined_prop }}</p>
        <WrongComponent /> <!-- Component not imported -->
      </div>
    </template>
    
    <script>
    export default {
      methods: {
        handleClick() {
          this.undefinedMethod(); // Doesn't exist
        }
      }
    }
    </script>
    """
    
    # ReviewFix fixes it
    fixed = await reviewfix_agent.fix_code(buggy_component)
    
    # Validations
    assert is_syntactically_valid(fixed)
    assert all_vars_defined(fixed)
    assert all_components_imported(fixed)
    assert all_methods_exist(fixed)
    
    # Should be deployable
    assert can_build_and_deploy(fixed)
```

### Szenario 3: Multi-Framework Support

```python
async def test_scenario_multi_framework_same_spec():
    """
    SAME APP SPEC in multiple frameworks
    Verify generated apps are functionally equivalent
    """
    
    app_spec = {
        "name": "User Dashboard",
        "features": ["user_list", "user_details", "add_user"],
        "pages": ["dashboard", "user_details"]
    }
    
    results = {}
    for framework in ["react", "vue", "angular"]:
        # Generate in each framework
        generated_app = await generate_app(app_spec, framework)
        
        # Deploy & test
        app_url = await deploy(generated_app)
        test_results = await run_e2e_tests(app_url)
        
        results[framework] = {
            "generated": len(generated_app.files),
            "deployable": test_results.deployable,
            "e2e_passed": test_results.passed,
            "test_count": len(test_results.tests)
        }
    
    # All frameworks should have similar characteristics
    assert results["react"]["test_count"] == results["vue"]["test_count"]
    assert results["vue"]["test_count"] == results["angular"]["test_count"]
    
    # All should be deployable
    assert all(r["deployable"] for r in results.values())
    
    # All E2E tests should pass
    assert all(r["e2e_passed"] for r in results.values())
    
    return results
```

### Szenario 4: Integration Testing - MCP Server Collaboration

```python
async def test_scenario_full_mcp_collaboration():
    """
    Test vollständige MCP Server Zusammenarbeit
    
    Flow:
    1. User fragt KI Agent (Claude)
    2. Claude calls MCP Supervisor Server
    3. Supervisor routes to Codesmith MCP Server
    4. Codesmith routes to ComponentWriter MCP Server
    5. ComponentWriter routes to E2E Generator MCP Server
    6. E2E Generator routes to ReviewFix MCP Server
    7. All data flows correctly between MCP servers
    """
    
    user_request = "Create a production-ready CRUD app in React"
    
    # Initialize MCP servers
    mcp_services = {
        "supervisor": await start_mcp_server("supervisor"),
        "codesmith": await start_mcp_server("codesmith"),
        "component_writer": await start_mcp_server("component_writer"),
        "e2e_generator": await start_mcp_server("e2e_generator"),
        "reviewfix": await start_mcp_server("reviewfix")
    }
    
    # Execute through MCP chain
    flow_trace = []
    
    # Step 1: Supervisor
    supervisor_result = await mcp_services["supervisor"].call_tool(
        "parse_request",
        {"request": user_request}
    )
    flow_trace.append(("supervisor", supervisor_result))
    
    # Step 2: Codesmith
    codesmith_result = await mcp_services["codesmith"].call_tool(
        "create_structure",
        supervisor_result
    )
    flow_trace.append(("codesmith", codesmith_result))
    
    # Step 3: ComponentWriter
    component_result = await mcp_services["component_writer"].call_tool(
        "generate_components",
        codesmith_result
    )
    flow_trace.append(("component_writer", component_result))
    
    # Step 4: E2E Generator
    test_result = await mcp_services["e2e_generator"].call_tool(
        "generate_tests",
        component_result
    )
    flow_trace.append(("e2e_generator", test_result))
    
    # Step 5: ReviewFix
    final_result = await mcp_services["reviewfix"].call_tool(
        "review_and_fix",
        {"code": component_result, "tests": test_result}
    )
    flow_trace.append(("reviewfix", final_result))
    
    # Validations
    assert all(r[1].success for r in flow_trace)
    assert final_result.quality_score >= 0.85
    assert final_result.ready_for_deployment == True
    
    return {
        "flow_trace": flow_trace,
        "final_result": final_result
    }
```

---

## 🛠️ Test-Harness & Infrastruktur {#test-harness}

### Test-Harness Architektur:

```python
# ============================================================
# TEST HARNESS CORE
# ============================================================

class KIAgentTestHarness:
    """Zentrale Test-Infrastruktur für KI Agenten"""
    
    def __init__(self):
        self.mcp_manager = MCPServerManager()
        self.docker_manager = DockerManager()
        self.state_tracer = StateTracer()
        self.assertion_validator = AssertionValidator()
        self.performance_monitor = PerformanceMonitor()
    
    async def setup_test_environment(self):
        """Bereitet komplette Test-Umgebung vor"""
        
        # 1. Start alle MCP Servers
        self.mcp_services = {
            "supervisor": await self.mcp_manager.start("supervisor"),
            "codesmith": await self.mcp_manager.start("codesmith"),
            "component_writer": await self.mcp_manager.start("component_writer"),
            "e2e_generator": await self.mcp_manager.start("e2e_generator"),
            "reviewfix": await self.mcp_manager.start("reviewfix")
        }
        
        # 2. Starte Docker Registry für Apps
        self.docker_registry = await self.docker_manager.start_registry()
        
        # 3. Initialize Tracing
        self.state_tracer.clear()
        self.state_tracer.enable()
        
        return True
    
    async def run_test(self, test_spec):
        """Führt einen Test durch und sammelt Daten"""
        
        test_execution = TestExecution(
            test_name=test_spec.name,
            timestamp=datetime.now()
        )
        
        try:
            # Execute test
            result = await self.execute_agent_workflow(test_spec)
            test_execution.result = result
            test_execution.status = "PASSED" if result.success else "FAILED"
            
        except Exception as e:
            test_execution.status = "ERROR"
            test_execution.error = str(e)
            test_execution.traceback = traceback.format_exc()
        
        finally:
            # Collect metrics
            test_execution.state_trace = self.state_tracer.get_trace()
            test_execution.performance_metrics = self.performance_monitor.get_metrics()
            
        return test_execution
    
    async def execute_agent_workflow(self, spec):
        """Führt Agent-Workflow aus mit State Tracing"""
        
        # Trace: Start
        self.state_tracer.log("WORKFLOW_START", spec)
        
        # Call Supervisor
        supervisor_response = await self.call_mcp_service(
            "supervisor",
            "process_request",
            {"request": spec.user_request}
        )
        self.state_tracer.log("SUPERVISOR_RESPONSE", supervisor_response)
        
        # Route durch weitere Agents basierend auf Response
        workflow_result = supervisor_response
        for next_agent in supervisor_response.routing_chain:
            workflow_result = await self.call_mcp_service(
                next_agent,
                "execute",
                workflow_result
            )
            self.state_tracer.log(f"{next_agent.upper()}_RESPONSE", workflow_result)
        
        # Trace: End
        self.state_tracer.log("WORKFLOW_END", workflow_result)
        
        return workflow_result
    
    async def call_mcp_service(self, service_name, tool_name, params):
        """Ruft MCP Service auf mit Error Handling"""
        
        service = self.mcp_services[service_name]
        
        try:
            result = await service.call_tool(tool_name, params)
            return result
        except Exception as e:
            # State tracing for debugging
            self.state_tracer.log("ERROR", {
                "service": service_name,
                "tool": tool_name,
                "error": str(e)
            })
            raise
    
    async def validate_generated_artifacts(self, artifacts):
        """Validiert alle generierten Artefakte"""
        
        validations = {}
        
        # 1. Code Syntax Validation
        for file in artifacts.code_files:
            validations[file.name] = {
                "syntax_valid": self.validate_syntax(file.content, file.language),
                "linting": self.run_linter(file.content, file.language),
                "complexity": self.measure_complexity(file.content)
            }
        
        # 2. Test Validation
        for test_file in artifacts.test_files:
            validations[test_file.name] = {
                "is_valid_test": self.validate_test_structure(test_file.content),
                "has_assertions": self.has_assertions(test_file.content),
                "assertion_count": self.count_assertions(test_file.content)
            }
        
        # 3. Architecture Validation
        validations["architecture"] = {
            "has_required_structure": self.validate_app_structure(artifacts),
            "follows_framework_conventions": self.validate_conventions(artifacts),
            "dependencies_resolvable": self.validate_dependencies(artifacts)
        }
        
        return validations


# ============================================================
# STATE TRACING - Debugging & Analysis
# ============================================================

class StateTracer:
    """Traced jeden State & Transition durch Workflow"""
    
    def __init__(self):
        self.trace_log = []
        self.enabled = False
    
    def log(self, event_type, data):
        """Log ein Event mit Timestamp"""
        if not self.enabled:
            return
        
        self.trace_log.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "call_stack": inspect.stack()[:5]
        })
    
    def get_trace(self):
        """Get vollständigen Trace für Debugging"""
        return self.trace_log
    
    def visualize_workflow(self):
        """Visualisiert Workflow als Diagramm"""
        diagram = []
        for i, event in enumerate(self.trace_log):
            diagram.append(f"{i:3d}. {event['event_type']:30s} @ {event['timestamp']}")
        return "\n".join(diagram)


# ============================================================
# DEPLOYMENT & LIVE TESTING
# ============================================================

class DeploymentTestManager:
    """Managet Deployment und Live Testing"""
    
    async def deploy_generated_app(self, app_code, framework):
        """Deployed generierte App zu Container"""
        
        # 1. Create Dockerfile
        dockerfile = generate_dockerfile(framework, app_code)
        
        # 2. Build Docker Image
        image = await self.docker_manager.build_image(
            name=f"test-app-{framework}",
            dockerfile=dockerfile,
            context=app_code
        )
        
        # 3. Run Container
        container = await self.docker_manager.run_container(
            image=image,
            port=self.get_available_port(),
            timeout=300  # 5 minutes
        )
        
        # 4. Health Check
        health_status = await self.check_container_health(container)
        if not health_status:
            raise RuntimeError(f"Container health check failed: {container.logs()}")
        
        return container
    
    async def run_e2e_tests_against_app(self, app_container, test_code):
        """Führt Playwright Tests gegen Live App aus"""
        
        app_url = f"http://localhost:{app_container.port}"
        
        # 1. Update test URLs
        test_code = test_code.replace("APP_URL", app_url)
        
        # 2. Run Playwright
        result = await self.run_playwright_tests(test_code)
        
        # 3. Collect Results
        return {
            "passed": result.passed_count,
            "failed": result.failed_count,
            "duration": result.duration,
            "output": result.stdout,
            "errors": result.stderr if result.failed_count > 0 else None
        }
    
    async def check_container_health(self, container):
        """Überprüft ob Container gesund läuft"""
        
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = await http_get(f"http://localhost:{container.port}")
                if response.status_code < 500:
                    return True
            except Exception:
                pass
            
            await asyncio.sleep(2)
        
        return False


# ============================================================
# PERFORMANCE MONITORING
# ============================================================

class PerformanceMonitor:
    """Monitert Performance während Tests"""
    
    def __init__(self):
        self.metrics = {}
    
    def measure_agent_response_time(self, agent_name):
        """Decorator: Misst Response-Zeit eines Agents"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start = time.time()
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                self.metrics[agent_name] = {
                    "response_time": duration,
                    "timestamp": datetime.now()
                }
                
                return result
            return wrapper
        return decorator
    
    def get_metrics(self):
        """Get alle Performance-Metriken"""
        return self.metrics


# ============================================================
# TEST RESULT REPORTING
# ============================================================

class TestReporter:
    """Erstellt Test-Reports"""
    
    def generate_html_report(self, test_results):
        """Erstellt HTML Report aller Tests"""
        
        html = f"""
        <html>
        <head>
            <title>KI Agent E2E Test Report</title>
            <style>
                body {{ font-family: Arial; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid; padding: 8px; text-align: left; }}
            </style>
        </head>
        <body>
            <h1>KI Agent E2E Test Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Total Tests</th>
                    <td>{len(test_results)}</td>
                </tr>
                <tr>
                    <th>Passed</th>
                    <td class="passed">{sum(1 for r in test_results if r.status == 'PASSED')}</td>
                </tr>
                <tr>
                    <th>Failed</th>
                    <td class="failed">{sum(1 for r in test_results if r.status == 'FAILED')}</td>
                </tr>
            </table>
            
            <h2>Test Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_test_rows(test_results)}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html
    
    def generate_json_report(self, test_results):
        """Erstellt JSON Report für CI/CD Integration"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total": len(test_results),
            "passed": sum(1 for r in test_results if r.status == 'PASSED'),
            "failed": sum(1 for r in test_results if r.status == 'FAILED'),
            "tests": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": r.duration,
                    "error": r.error if r.status == 'FAILED' else None
                }
                for r in test_results
            ]
        }
```

---

## ✅ Validierungskriterien {#validierungskriterien}

### 1. **Code Quality Metrics**

```python
class CodeQualityValidator:
    
    # Syntax Validation
    def has_valid_syntax(code, language):
        try:
            if language == "python":
                ast.parse(code)
            elif language in ["javascript", "typescript"]:
                js_ast.parse(code)
            return True
        except:
            return False
    
    # Completeness
    def has_all_required_functions(code, spec):
        """Alle geforderten Funktionen implementiert?"""
        required = spec.required_functions
        return all(f in code for f in required)
    
    # Best Practices
    def follows_conventions(code, framework):
        """Code folgt Framework-Konventionen"""
        checks = {
            "react": check_react_conventions,
            "vue": check_vue_conventions,
            "fastapi": check_fastapi_conventions
        }
        return checks[framework](code)
    
    # Complexity
    def has_reasonable_complexity(code):
        """Cyclomatic Complexity nicht zu hoch"""
        complexity = calculate_complexity(code)
        return complexity < 15  # Arbitrary threshold
    
    # Type Safety
    def has_type_hints(code, language):
        """Code hat Type Hints (für Python/TS)"""
        if language in ["python", "typescript"]:
            return check_type_coverage(code) >= 0.80
        return True
```

### 2. **E2E Test Quality Metrics**

```python
class TestQualityValidator:
    
    # Test Coverage
    def has_sufficient_test_coverage(generated_code, test_code):
        """Mindestens 80% Code Coverage"""
        coverage = calculate_coverage(generated_code, test_code)
        return coverage >= 0.80
    
    # Test Types
    def has_test_variety(test_code):
        """Tests haben verschiedene Szenarien"""
        has_happy_path = "describe('happy path')" in test_code.lower()
        has_error_cases = "describe('error')" in test_code.lower()
        has_edge_cases = "describe('edge')" in test_code.lower()
        return has_happy_path and has_error_cases and has_edge_cases
    
    # Test Assertions
    def has_meaningful_assertions(test_code):
        """Tests haben aussagekräftige Assertions"""
        assertions = re.findall(r'expect\(|assert\(', test_code)
        return len(assertions) >= 5  # Mindestens 5 Assertions
    
    # Selector Usage
    def uses_data_testid_selectors(test_code):
        """Tests verwenden data-testid Selektoren"""
        testid_count = test_code.count('[data-testid=')
        total_selectors = len(re.findall(r'querySelector|getByTestId', test_code))
        return (testid_count / total_selectors) >= 0.9 if total_selectors > 0 else False
    
    # Test Isolations
    def tests_are_isolated(test_code):
        """Jeder Test ist unabhängig"""
        # Check für beforeEach/afterEach
        has_setup_teardown = "beforeEach" in test_code and "afterEach" in test_code
        # Check für shared state
        shared_state = re.findall(r'let.*=.*;.*let.*=', test_code)
        return has_setup_teardown and len(shared_state) == 0
```

### 3. **Generated App Validation**

```python
class GeneratedAppValidator:
    
    # Build Success
    def app_builds_successfully(app_code, framework):
        """App kompiliert/transpiliert erfolgreich"""
        try:
            run_build_command(framework, app_code)
            return True
        except:
            return False
    
    # No Runtime Errors
    def no_runtime_errors_on_startup(app_path):
        """App startet ohne Fehler"""
        # Deploy container
        container = deploy_temp_container(app_path)
        # Check logs
        logs = container.logs()
        errors = re.findall(r'ERROR|Exception|Cannot find', logs)
        return len(errors) == 0
    
    # API Responsiveness
    def api_endpoints_respond(app_url):
        """Alle APIs antworten"""
        endpoints = get_endpoints_from_spec()
        for endpoint in endpoints:
            response = http_request(app_url + endpoint)
            if response.status_code >= 500:
                return False
        return True
    
    # State Management
    def state_persists_correctly(app_url):
        """Zustand wird korrekt beibehalten"""
        # Add data
        # Refresh page
        # Verify data still there
        return True
```

### 4. **Multi-Framework Compatibility**

```python
class MultiFrameworkValidator:
    
    def same_spec_produces_similar_apps(spec, frameworks):
        """Verschiedene Frameworks produzieren funktional äquivalente Apps"""
        
        apps = {}
        for fw in frameworks:
            apps[fw] = generate_app(spec, fw)
        
        # Check: All apps have similar structure
        assert len(apps["react"].components) == len(apps["vue"].components)
        
        # Check: All apps have same number of tests
        assert len(apps["react"].tests) == len(apps["vue"].tests)
        
        # Check: All apps are deployable
        for fw, app in apps.items():
            container = deploy_app(app, fw)
            assert container.is_running()
        
        return True
    
    def framework_switching_works(app_id):
        """User kann zwischen Frameworks wechseln"""
        
        # Generate React version
        react_app = generate_existing_app(app_id, "react")
        
        # Generate same app in Vue
        vue_app = generate_existing_app(app_id, "vue")
        
        # Both should be deployable
        react_container = deploy_app(react_app, "react")
        vue_container = deploy_app(vue_app, "vue")
        
        # Run same tests against both
        tests = load_tests(app_id)
        
        react_results = run_tests(tests, react_container.url)
        vue_results = run_tests(tests, vue_container.url)
        
        assert react_results.passed_count == vue_results.passed_count
        
        return True
```

---

## 🗺️ Implementierungs-Roadmap {#roadmap}

### Phase 1: Foundation (Woche 1-2)
- [ ] TestHarness Basis-Struktur
- [ ] MCP Server Integration
- [ ] State Tracing
- [ ] Basic Unit Tests

### Phase 2: Agent Integration (Woche 3-4)
- [ ] Agent Mocking & Stubbing
- [ ] Integration Tests
- [ ] Error Scenario Testing

### Phase 3: Deployment & Live Testing (Woche 5-6)
- [ ] Docker Container Management
- [ ] App Deployment
- [ ] Playwright Integration
- [ ] E2E Test Execution

### Phase 4: Quality & Metrics (Woche 7-8)
- [ ] Code Quality Validators
- [ ] Performance Monitoring
- [ ] Report Generation

### Phase 5: CI/CD Integration (Woche 9-10)
- [ ] GitHub Actions Integration
- [ ] Automated Test Runs
- [ ] Continuous Monitoring

---

## 📊 Metriken & Dashboards

### Key Performance Indicators (KPIs):

```
┌─────────────────────────────────────────────────┐
│ KI AGENT E2E TESTING DASHBOARD                  │
├─────────────────────────────────────────────────┤
│                                                 │
│ SUCCESS RATE:        ✓ 95% (380/400 tests)     │
│ AVG. RESPONSE TIME:  2.3 seconds                │
│ CODE QUALITY SCORE:  8.7/10                     │
│ TEST COVERAGE:       87%                        │
│ E2E PASS RATE:       92%                        │
│                                                 │
│ FRAMEWORK COVERAGE:                             │
│  ✓ React:      100% (95/95 tests)              │
│  ✓ Vue:         98% (92/94 tests)              │
│  ✓ Angular:     96% (91/95 tests)              │
│  ✓ FastAPI:     94% (89/95 tests)              │
│  ✓ Flask:       93% (88/95 tests)              │
│                                                 │
│ FAILURE ANALYSIS:                               │
│  • Syntax Errors:           2% (8 cases)        │
│  • Build Failures:          1% (4 cases)        │
│  • Runtime Issues:          2% (8 cases)        │
│                                                 │
│ PERFORMANCE:                                    │
│  • Avg Test Duration:      145 seconds          │
│  • Slowest Test:           287 seconds          │
│  • Fastest Test:            12 seconds          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🎯 SUMMARY

### Wie man E2E Tests für MCP Multi KI Agenten durchführt:

| Aspekt | Ansatz |
|--------|--------|
| **Was testen?** | Den Agenten selbst (nicht die generierte App) |
| **Wo testen?** | Auf 3 Levels: Unit → Integration → E2E |
| **Wie testen?** | State Tracing + Deployment + Live Playwright Tests |
| **Infrastruktur?** | MCP Servers + Docker + Playwright + Test Harness |
| **Metriken?** | Code Quality, Test Coverage, E2E Pass Rate |
| **Automation?** | Vollständig automatisiert in CI/CD Pipeline |

### Die größte Herausforderung:

**"Testing a system that creates tests"** 🤯

Lösung: **Hierarchical Validation**
1. Validiere Agent Output (generierter Code)
2. Validiere generierte Tests (Syntax, Struktur, Assertions)
3. Führe generierte Tests gegen Live App aus (echte Validierung)
4. Überprüfe Testergebnisse (bestanden oder nicht)

---

**VERSION**: 1.0 | **STATUS**: READY FOR IMPLEMENTATION ✅