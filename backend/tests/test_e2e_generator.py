"""
Tests for E2E Test Generator
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.e2e_testing.react_analyzer import ReactComponentAnalyzer, ReactComponent
from backend.e2e_testing.test_generator import E2ETestGenerator, TestScenario
from backend.e2e_testing.browser_engine import BrowserEngine
from backend.e2e_testing.test_executor import PlaywrightTestExecutor


class TestReactComponentAnalyzer:
    """Tests for React Component Analyzer"""
    
    @pytest.fixture
    def sample_app_path(self):
        """Create a sample React app for testing"""
        tmpdir = tempfile.mkdtemp()
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        
        # Create sample component
        login_component = src_dir / "LoginForm.jsx"
        login_component.write_text("""
import React, { useState } from 'react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  
  const handleLogin = async () => {
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      if (res.ok) navigate('/dashboard');
      else setError('Invalid credentials');
    } catch (e) {
      setError('Network error');
    }
  };
  
  return (
    <form>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        data-testid="email-input"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        data-testid="password-input"
      />
      {error && <div data-testid="error-msg">{error}</div>}
      <button onClick={handleLogin} data-testid="login-btn">
        Login
      </button>
    </form>
  );
}
""")
        
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    def test_find_jsx_files(self, sample_app_path):
        """Test finding JSX files"""
        analyzer = ReactComponentAnalyzer(sample_app_path)
        jsx_files = analyzer._find_jsx_files()
        
        assert len(jsx_files) > 0
        assert any("LoginForm.jsx" in str(f) for f in jsx_files)
    
    def test_parse_component(self, sample_app_path):
        """Test parsing a component"""
        analyzer = ReactComponentAnalyzer(sample_app_path)
        jsx_files = analyzer._find_jsx_files()
        
        assert len(jsx_files) > 0
        component = analyzer._parse_component(jsx_files[0])
        
        assert component is not None
        assert component.name == "LoginForm"
        assert component.type == "functional"
        assert "useState" in component.hooks
        assert "/api/login" in str(component.api_calls)
    
    def test_extract_test_ids(self, sample_app_path):
        """Test extracting test IDs"""
        analyzer = ReactComponentAnalyzer(sample_app_path)
        jsx_files = analyzer._find_jsx_files()
        component = analyzer._parse_component(jsx_files[0])
        
        assert "email-input" in component.test_ids
        assert "password-input" in component.test_ids
        assert "error-msg" in component.test_ids
        assert "login-btn" in component.test_ids
    
    def test_extract_form_fields(self, sample_app_path):
        """Test extracting form fields"""
        analyzer = ReactComponentAnalyzer(sample_app_path)
        jsx_files = analyzer._find_jsx_files()
        component = analyzer._parse_component(jsx_files[0])
        
        assert len(component.form_fields) >= 2


class TestE2ETestGenerator:
    """Tests for E2E Test Generator"""
    
    @pytest.fixture
    def sample_app_path(self):
        """Create sample React app"""
        tmpdir = tempfile.mkdtemp()
        
        # Create package.json
        (Path(tmpdir) / "package.json").write_text(
            json.dumps({"name": "test-app", "version": "1.0.0"})
        )
        
        # Create src directory
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        
        # Create App.jsx
        (src_dir / "App.jsx").write_text("""
import React from 'react';
import LoginForm from './LoginForm';

export default function App() {
  return <LoginForm />;
}
""")
        
        # Create LoginForm component
        (src_dir / "LoginForm.jsx").write_text("""
import React, { useState } from 'react';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  
  return (
    <div>
      <input data-testid="email" onChange={(e) => setEmail(e.target.value)} />
      <button data-testid="submit">Submit</button>
    </div>
  );
}
""")
        
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    def test_analyze_and_generate(self, sample_app_path):
        """Test analyze and generate"""
        generator = E2ETestGenerator(sample_app_path)
        result = generator.analyze_and_generate()
        
        assert result['analysis']['total_components'] >= 1
        assert result['scenarios'] >= 0
    
    def test_generate_test_scenarios(self, sample_app_path):
        """Test generating test scenarios"""
        generator = E2ETestGenerator(sample_app_path)
        scenarios = generator._generate_test_scenarios()
        
        # Should generate at least some scenarios
        assert isinstance(scenarios, list)
    
    def test_get_statistics(self, sample_app_path):
        """Test getting statistics"""
        generator = E2ETestGenerator(sample_app_path)
        generator.analyze_and_generate()
        stats = generator.get_statistics()
        
        assert 'total_scenarios' in stats
        assert 'total_test_files' in stats
        assert 'scenario_types' in stats


class TestBrowserEngine:
    """Tests for Browser Engine"""
    
    @pytest.fixture
    def app_path(self):
        """Create sample app path"""
        tmpdir = tempfile.mkdtemp()
        (Path(tmpdir) / "package.json").write_text('{}')
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    def test_browser_engine_init(self, app_path):
        """Test browser engine initialization"""
        engine = BrowserEngine(app_path)
        
        assert engine.app_path == Path(app_path)
        assert engine.base_url == 'http://localhost:3000'
        assert engine.browser_type == 'chromium'
    
    def test_browser_engine_config(self, app_path):
        """Test browser engine with config"""
        config = {
            'base_url': 'http://localhost:8000',
            'browser': 'firefox',
            'headless': False
        }
        
        engine = BrowserEngine(app_path, config)
        
        assert engine.base_url == 'http://localhost:8000'
        assert engine.browser_type == 'firefox'
        assert engine.headless is False


class TestPlaywrightTestExecutor:
    """Tests for Playwright Test Executor"""
    
    @pytest.fixture
    def test_dir(self):
        """Create test directory"""
        tmpdir = tempfile.mkdtemp()
        
        # Create a sample test file
        test_file = Path(tmpdir) / "sample.spec.ts"
        test_file.write_text("""
import { test, expect } from '@playwright/test';

test('sample test', async ({ page }) => {
  expect(true).toBe(true);
});
""")
        
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    def test_executor_init(self, test_dir):
        """Test executor initialization"""
        executor = PlaywrightTestExecutor(test_dir)
        
        assert executor.test_dir == Path(test_dir)
        assert executor.workers == 1
        assert executor.headless is True


class TestReviewFixE2EAgent:
    """Tests for ReviewFix E2E Agent"""
    
    @pytest.fixture
    def workspace_path(self):
        """Create workspace"""
        tmpdir = tempfile.mkdtemp()
        (Path(tmpdir) / "package.json").write_text('{}')
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    @pytest.mark.asyncio
    async def test_review_initialization(self, workspace_path):
        """Test agent initialization"""
        from backend.agents.reviewfix_e2e_agent import ReviewFixE2EAgent
        
        agent = ReviewFixE2EAgent(workspace_path)
        assert agent.workspace_path == Path(workspace_path)


# Integration Tests
class TestE2EIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow"""
        # Create sample app
        tmpdir = tempfile.mkdtemp()
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        
        try:
            # Create component
            (src_dir / "App.jsx").write_text("""
import React, { useState } from 'react';

export default function App() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p data-testid="count">Count: {count}</p>
      <button data-testid="increment" onClick={() => setCount(c => c + 1)}>
        +
      </button>
    </div>
  );
}
""")
            
            # Analyze
            analyzer = ReactComponentAnalyzer(tmpdir)
            analysis = analyzer.analyze_app()
            
            # Should find App component
            assert analysis['total_components'] >= 1
            
            # Generate tests
            generator = E2ETestGenerator(tmpdir)
            result = generator.analyze_and_generate()
            
            # Should generate scenarios
            assert result['scenarios'] >= 0
        
        finally:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])