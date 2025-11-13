"""
Framework Detector - Automatically detects project framework

Supports:
- Frontend Frameworks: React, Vue, Angular, Svelte, Next.js, Nuxt, etc.
- Backend Frameworks: FastAPI, Flask, Django, Express, etc.
- Detection based on: package.json, requirements.txt, configuration files
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
import re


@dataclass
class FrameworkInfo:
    """Framework detection result"""
    type: str  # 'react', 'vue', 'angular', 'fastapi', 'flask', etc.
    version: Optional[str]
    language: str  # 'javascript', 'typescript', 'python'
    app_type: str  # 'frontend', 'backend', 'fullstack'
    entry_point: Optional[str]
    package_manager: Optional[str]  # 'npm', 'yarn', 'pip', etc.
    build_tool: Optional[str]  # 'webpack', 'vite', 'next', etc.
    test_framework: Optional[str]  # 'jest', 'vitest', 'pytest', 'playwright'
    confidence: float  # 0.0-1.0
    config_files: list  # Detected config files
    detected_packages: Dict[str, str]  # Detected key packages


class FrameworkDetector:
    """Auto-detects project framework and technology stack"""

    def __init__(self, app_path: str):
        """
        Initialize framework detector
        
        Args:
            app_path: Path to project root
        """
        self.app_path = Path(app_path)
        if not self.app_path.exists():
            raise ValueError(f"Path does not exist: {app_path}")

    def detect_framework(self) -> FrameworkInfo:
        """
        Detect project framework and technology stack
        
        Returns:
            FrameworkInfo with detected framework details
        """
        # Try JavaScript/TypeScript first
        if self._has_package_json():
            return self._detect_javascript_framework()
        
        # Try Python
        if self._has_requirements_txt() or self._has_pyproject_toml():
            return self._detect_python_framework()
        
        # Fallback: Generic detection
        return self._detect_generic()

    def _has_package_json(self) -> bool:
        """Check if project has package.json"""
        return (self.app_path / "package.json").exists()

    def _has_requirements_txt(self) -> bool:
        """Check if project has requirements.txt"""
        return (self.app_path / "requirements.txt").exists()

    def _has_pyproject_toml(self) -> bool:
        """Check if project has pyproject.toml"""
        return (self.app_path / "pyproject.toml").exists()

    def _detect_javascript_framework(self) -> FrameworkInfo:
        """Detect JavaScript/TypeScript framework"""
        
        package_json_path = self.app_path / "package.json"
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        dependencies = {
            **package_data.get('dependencies', {}),
            **package_data.get('devDependencies', {}),
        }
        
        config_files = self._find_config_files(['tsconfig.json', 'vite.config.ts', 'webpack.config.js'])
        
        # Detect framework type
        if 'react' in dependencies:
            return FrameworkInfo(
                type='react',
                version=dependencies.get('react'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='frontend',
                entry_point=self._find_entry_point(['src/main.tsx', 'src/index.tsx', 'src/index.js']),
                package_manager=self._detect_package_manager(),
                build_tool=self._detect_build_tool(dependencies),
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'react': dependencies.get('react')}
            )
        
        elif 'vue' in dependencies:
            return FrameworkInfo(
                type='vue',
                version=dependencies.get('vue'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='frontend',
                entry_point=self._find_entry_point(['src/main.ts', 'src/main.js']),
                package_manager=self._detect_package_manager(),
                build_tool=self._detect_build_tool(dependencies),
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'vue': dependencies.get('vue')}
            )
        
        elif '@angular/core' in dependencies:
            return FrameworkInfo(
                type='angular',
                version=dependencies.get('@angular/core'),
                language='typescript',
                app_type='frontend',
                entry_point='src/main.ts',
                package_manager=self._detect_package_manager(),
                build_tool='angular-cli',
                test_framework='jasmine',
                confidence=0.95,
                config_files=config_files,
                detected_packages={'@angular/core': dependencies.get('@angular/core')}
            )
        
        elif 'svelte' in dependencies:
            return FrameworkInfo(
                type='svelte',
                version=dependencies.get('svelte'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='frontend',
                entry_point=self._find_entry_point(['src/main.ts', 'src/main.js']),
                package_manager=self._detect_package_manager(),
                build_tool=self._detect_build_tool(dependencies),
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'svelte': dependencies.get('svelte')}
            )
        
        elif 'next' in dependencies:
            return FrameworkInfo(
                type='next.js',
                version=dependencies.get('next'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='fullstack',
                entry_point='pages/index.tsx',
                package_manager=self._detect_package_manager(),
                build_tool='next',
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'next': dependencies.get('next')}
            )
        
        elif 'nuxt' in dependencies:
            return FrameworkInfo(
                type='nuxt',
                version=dependencies.get('nuxt'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='fullstack',
                entry_point='app.vue',
                package_manager=self._detect_package_manager(),
                build_tool='nuxt',
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'nuxt': dependencies.get('nuxt')}
            )
        
        elif 'express' in dependencies:
            return FrameworkInfo(
                type='express',
                version=dependencies.get('express'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='backend',
                entry_point=self._find_entry_point(['src/server.ts', 'src/index.ts', 'server.js']),
                package_manager=self._detect_package_manager(),
                build_tool=None,
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.95,
                config_files=config_files,
                detected_packages={'express': dependencies.get('express')}
            )
        
        else:
            return FrameworkInfo(
                type='generic-node',
                version=package_data.get('version'),
                language='typescript' if (self.app_path / 'tsconfig.json').exists() else 'javascript',
                app_type='unknown',
                entry_point=self._find_entry_point(['src/main.ts', 'src/index.ts', 'index.js']),
                package_manager=self._detect_package_manager(),
                build_tool=self._detect_build_tool(dependencies),
                test_framework=self._detect_test_framework(dependencies),
                confidence=0.5,
                config_files=config_files,
                detected_packages={}
            )

    def _detect_python_framework(self) -> FrameworkInfo:
        """Detect Python framework"""
        
        dependencies = {}
        
        # Read requirements.txt
        req_path = self.app_path / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies[line.split('==')[0].split('>=')[0]] = 'installed'
        
        # Read pyproject.toml
        pyproject_path = self.app_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                content = f.read()
                if 'fastapi' in content:
                    dependencies['fastapi'] = 'fastapi'
                if 'flask' in content:
                    dependencies['flask'] = 'flask'
                if 'django' in content:
                    dependencies['django'] = 'django'

        # Detect framework
        if 'fastapi' in dependencies:
            return FrameworkInfo(
                type='fastapi',
                version=None,
                language='python',
                app_type='backend',
                entry_point=self._find_entry_point(['main.py', 'app.py', 'server.py']),
                package_manager='pip',
                build_tool=None,
                test_framework='pytest',
                confidence=0.95,
                config_files=self._find_config_files(['pyproject.toml']),
                detected_packages={'fastapi': 'installed'}
            )
        
        elif 'flask' in dependencies:
            return FrameworkInfo(
                type='flask',
                version=None,
                language='python',
                app_type='backend',
                entry_point=self._find_entry_point(['app.py', 'main.py', 'server.py']),
                package_manager='pip',
                build_tool=None,
                test_framework='pytest',
                confidence=0.95,
                config_files=self._find_config_files(['pyproject.toml']),
                detected_packages={'flask': 'installed'}
            )
        
        elif 'django' in dependencies:
            return FrameworkInfo(
                type='django',
                version=None,
                language='python',
                app_type='backend',
                entry_point='manage.py',
                package_manager='pip',
                build_tool=None,
                test_framework='unittest',
                confidence=0.95,
                config_files=self._find_config_files(['pyproject.toml']),
                detected_packages={'django': 'installed'}
            )
        
        else:
            return FrameworkInfo(
                type='generic-python',
                version=None,
                language='python',
                app_type='unknown',
                entry_point=self._find_entry_point(['main.py', 'app.py']),
                package_manager='pip',
                build_tool=None,
                test_framework='pytest',
                confidence=0.5,
                config_files=self._find_config_files(['pyproject.toml']),
                detected_packages={}
            )

    def _detect_generic(self) -> FrameworkInfo:
        """Fallback generic detection"""
        
        return FrameworkInfo(
            type='unknown',
            version=None,
            language='unknown',
            app_type='unknown',
            entry_point=None,
            package_manager=None,
            build_tool=None,
            test_framework=None,
            confidence=0.0,
            config_files=[],
            detected_packages={}
        )

    def _detect_package_manager(self) -> str:
        """Detect package manager (npm, yarn, pnpm, pip)"""
        if (self.app_path / 'yarn.lock').exists():
            return 'yarn'
        elif (self.app_path / 'pnpm-lock.yaml').exists():
            return 'pnpm'
        elif (self.app_path / 'package.json').exists():
            return 'npm'
        else:
            return None

    def _detect_build_tool(self, dependencies: Dict) -> Optional[str]:
        """Detect build tool"""
        if 'vite' in dependencies:
            return 'vite'
        elif 'webpack' in dependencies:
            return 'webpack'
        elif '@vitejs/plugin-react' in dependencies:
            return 'vite'
        elif 'next' in dependencies:
            return 'next'
        else:
            return None

    def _detect_test_framework(self, dependencies: Dict) -> Optional[str]:
        """Detect test framework"""
        if 'jest' in dependencies:
            return 'jest'
        elif 'vitest' in dependencies:
            return 'vitest'
        elif 'playwright' in dependencies:
            return 'playwright'
        elif 'cypress' in dependencies:
            return 'cypress'
        elif 'mocha' in dependencies:
            return 'mocha'
        else:
            return None

    def _find_entry_point(self, candidates: list) -> Optional[str]:
        """Find entry point from candidates"""
        for candidate in candidates:
            if (self.app_path / candidate).exists():
                return candidate
        return None

    def _find_config_files(self, candidates: list) -> list:
        """Find config files"""
        found = []
        for candidate in candidates:
            if (self.app_path / candidate).exists():
                found.append(candidate)
        return found

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        info = self.detect_framework()
        return {
            'type': info.type,
            'version': info.version,
            'language': info.language,
            'app_type': info.app_type,
            'entry_point': info.entry_point,
            'package_manager': info.package_manager,
            'build_tool': info.build_tool,
            'test_framework': info.test_framework,
            'confidence': info.confidence,
            'config_files': info.config_files,
        }