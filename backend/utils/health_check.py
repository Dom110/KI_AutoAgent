"""
Health Check & Diagnostics System
Provides comprehensive system status and error reporting for KI AutoAgent
"""

import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
import socket
import subprocess
import signal
import time

logger = logging.getLogger(__name__)

# ANSI Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class HealthStatus:
    """Health check status enum"""
    OK = "✅ OK"
    WARNING = "⚠️ WARNING"
    ERROR = "❌ ERROR"
    CRITICAL = "🔴 CRITICAL"

class SystemDiagnostics:
    """Comprehensive system health check"""
    
    def __init__(self):
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.startup_time = datetime.now()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        
    def add_check(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a health check result"""
        self.checks[name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        if "ERROR" in status or "CRITICAL" in status:
            self.errors.append(f"{name}: {message}")
        elif "WARNING" in status:
            self.warnings.append(f"{name}: {message}")
    
    def print_banner(self):
        """Print prominent error banner if there are issues"""
        if not self.errors and not self.warnings:
            return
        
        print("\n" + "=" * 100)
        print(f"{Colors.BOLD}{Colors.RED}🚨 SYSTEM STATUS REPORT{Colors.END}")
        print("=" * 100)
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ERRORS (Must fix before proceeding):{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS (May affect functionality):{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "=" * 100 + "\n")
    
    def print_full_report(self):
        """Print comprehensive diagnostic report"""
        print("\n" + "=" * 100)
        print(f"{Colors.BOLD}{Colors.BLUE}📊 SYSTEM DIAGNOSTICS REPORT{Colors.END}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100 + "\n")
        
        for check_name, check_data in self.checks.items():
            status = check_data["status"]
            message = check_data["message"]
            
            if "✅" in status:
                color = Colors.GREEN
            elif "⚠️" in status:
                color = Colors.YELLOW
            else:
                color = Colors.RED
            
            print(f"{color}{status}{Colors.END} {Colors.BOLD}{check_name}{Colors.END}")
            print(f"    {message}")
            
            if check_data["details"]:
                for key, value in check_data["details"].items():
                    print(f"    • {key}: {value}")
            print()
        
        print("=" * 100 + "\n")
    
    async def run_all_checks(self) -> bool:
        """Run all diagnostic checks, returns True if all critical checks pass"""
        await self.check_python_version()
        await self.check_environment_variables()
        await self.check_api_keys()
        await self.check_dependencies()
        await self.check_port_availability()
        
        # Print prominent error banner
        self.print_banner()
        
        return len(self.errors) == 0
    
    async def check_python_version(self):
        """Check Python version"""
        import sys
        version = sys.version_info
        
        if version >= (3, 13, 8):
            self.add_check(
                "Python Version",
                HealthStatus.OK,
                f"Python {version.major}.{version.minor}.{version.micro} ✓",
                {"version": f"{version.major}.{version.minor}.{version.micro}"}
            )
        else:
            self.add_check(
                "Python Version",
                HealthStatus.CRITICAL,
                f"Python {version.major}.{version.minor}.{version.micro} - Requires 3.13.8+",
                {"version": f"{version.major}.{version.minor}.{version.micro}", "required": "3.13.8+"}
            )
    
    async def check_environment_variables(self):
        """Check critical environment variables"""
        home = Path.home()
        env_file = home / ".ki_autoagent" / "config" / ".env"
        
        if env_file.exists():
            self.add_check(
                "Environment File",
                HealthStatus.OK,
                f"Found: {env_file}",
                {"path": str(env_file)}
            )
        else:
            self.add_check(
                "Environment File",
                HealthStatus.ERROR,
                f"Missing: {env_file}",
                {"path": str(env_file), "action": "Create .env file with API keys"}
            )
    
    async def check_api_keys(self):
        """Check if API keys are loaded"""
        openai_key = os.getenv("OPENAI_API_KEY")
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        
        if openai_key:
            self.add_check(
                "OpenAI API Key",
                HealthStatus.OK,
                "Key loaded",
                {"key_length": len(openai_key), "starts_with": openai_key[:7] + "..."}
            )
        else:
            self.add_check(
                "OpenAI API Key",
                HealthStatus.CRITICAL,
                "Not found or not loaded",
                {"solution": "Set OPENAI_API_KEY environment variable"}
            )
        
        if perplexity_key:
            self.add_check(
                "Perplexity API Key",
                HealthStatus.OK,
                "Key loaded",
                {"key_length": len(perplexity_key), "starts_with": perplexity_key[:7] + "..."}
            )
        else:
            self.add_check(
                "Perplexity API Key",
                HealthStatus.WARNING,
                "Not found (optional service)",
                {"note": "Some research features will not work"}
            )
    
    async def check_dependencies(self):
        """Check critical Python dependencies"""
        required_modules = {
            "fastapi": "Web framework",
            "uvicorn": "ASGI server",
            "websockets": "WebSocket support",
            "langgraph": "Workflow orchestration",
            "langchain_openai": "OpenAI integration",
            "pydantic": "Data validation",
        }
        
        missing = []
        for module, description in required_modules.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(f"{module} ({description})")
        
        if not missing:
            self.add_check(
                "Python Dependencies",
                HealthStatus.OK,
                f"All {len(required_modules)} required packages installed",
                {"packages": len(required_modules)}
            )
        else:
            self.add_check(
                "Python Dependencies",
                HealthStatus.ERROR,
                f"Missing {len(missing)} package(s): {', '.join(missing)}",
                {"missing_count": len(missing), "packages": missing}
            )
    
    async def check_port_availability(self, port: int = 8002, host: str = "localhost") -> bool:
        """Check if server port is available and clean up if needed"""
        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            # result == 0 means connection successful (port in use)
            # result != 0 means port is available
            if result != 0:
                self.add_check(
                    "Server Port",
                    HealthStatus.OK,
                    f"Port {port} is available and ready for binding",
                    {"port": port, "host": host, "status": "available"}
                )
                return True
            
            # Port is in use - try to find and kill the process
            logger.warning(f"⚠️ Port {port} is in use, attempting cleanup...")
            
            pid = self._find_process_on_port(port)
            if pid:
                proc_info = self._get_process_info(pid)
                logger.warning(f"   Found process: {proc_info['command']} (PID: {pid})")
                
                # Try to kill the process
                if self._kill_process(pid):
                    await asyncio.sleep(1)  # Wait for port to be released
                    
                    # Check if port is now available
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result != 0:
                        self.add_check(
                            "Server Port",
                            HealthStatus.OK,
                            f"Port {port} was cleaned up and is now available",
                            {"port": port, "host": host, "status": "available", "previous_pid": pid}
                        )
                        return True
                    else:
                        self.add_check(
                            "Server Port",
                            HealthStatus.WARNING,
                            f"Port {port} is still in use after cleanup attempt",
                            {"port": port, "host": host, "status": "in_use", "pid": pid}
                        )
                        return False
            else:
                self.add_check(
                    "Server Port",
                    HealthStatus.WARNING,
                    f"Port {port} is in use but could not identify process",
                    {"port": port, "host": host, "status": "in_use"}
                )
                return False
        
        except Exception as e:
            self.add_check(
                "Server Port",
                HealthStatus.WARNING,
                f"Could not check port availability: {str(e)[:50]}",
                {"port": port, "error": str(e)[:50]}
            )
            return False
    
    def _find_process_on_port(self, port: int) -> Optional[int]:
        """Find PID of process using the port (macOS/Linux)"""
        try:
            if os.name == 'posix':
                cmd = f"lsof -i :{port} -t"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    if pids[0]:
                        return int(pids[0])
        except Exception as e:
            logger.debug(f"Could not find process on port: {e}")
        return None
    
    def _get_process_info(self, pid: int) -> dict:
        """Get process information"""
        info = {"pid": pid, "command": "unknown"}
        try:
            if os.name == 'posix':
                cmd = f"ps -p {pid} -o comm="
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                if result.stdout:
                    info["command"] = result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not get process info: {e}")
        return info
    
    def _kill_process(self, pid: int) -> bool:
        """Kill a process gracefully, then forcefully if needed"""
        try:
            if os.name == 'posix':
                # Try SIGTERM first
                logger.info(f"   Sending SIGTERM to PID {pid}...")
                os.kill(pid, signal.SIGTERM)
                
                # Wait for termination
                for _ in range(10):
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        time.sleep(0.1)
                    except ProcessLookupError:
                        logger.info(f"   ✅ Process {pid} terminated")
                        return True
                
                # Force kill if still running
                logger.warning(f"   ⚠️ Process did not terminate, using SIGKILL...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
                
                try:
                    os.kill(pid, 0)
                    logger.error(f"   ❌ Failed to kill process {pid}")
                    return False
                except ProcessLookupError:
                    logger.info(f"   ✅ Process {pid} force killed")
                    return True
        except Exception as e:
            logger.warning(f"   ⚠️ Error killing process {pid}: {e}")
            return False
        return False
    
    async def check_api_connectivity(self, timeout: int = 5) -> bool:
        """Check if APIs are reachable"""
        openai_ok = False
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Test OpenAI
                try:
                    resp = await client.get("https://api.openai.com/v1/models")
                    if resp.status_code == 200:
                        openai_ok = True
                        self.add_check("OpenAI API", HealthStatus.OK, "Reachable and responding")
                    elif resp.status_code == 401:
                        self.add_check("OpenAI API", HealthStatus.ERROR, "Authentication failed (401) - Check your API key")
                    elif resp.status_code == 429:
                        self.add_check("OpenAI API", HealthStatus.WARNING, "Rate limited (429) - Wait before retrying")
                    else:
                        self.add_check("OpenAI API", HealthStatus.WARNING, f"HTTP {resp.status_code}")
                except Exception as e:
                    self.add_check("OpenAI API", HealthStatus.WARNING, f"Connection issue: {str(e)[:50]}")
        except Exception as e:
            self.add_check("API Connectivity", HealthStatus.WARNING, f"Could not test: {str(e)[:50]}")
        
        return openai_ok


async def run_startup_diagnostics() -> SystemDiagnostics:
    """Run full startup diagnostics and display results"""
    diag = SystemDiagnostics()
    all_critical_pass = await diag.run_all_checks()
    return diag


def print_startup_header():
    """Print startup header with system info"""
    print("\n" + "=" * 100)
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 KI AutoAgent v7.0 - STARTUP{Colors.END}")
    print("=" * 100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {__import__('sys').version.split()[0]}")
    print("=" * 100 + "\n")


def print_ready_message():
    """Print server ready message"""
    print("\n" + "=" * 100)
    print(f"{Colors.GREEN}{Colors.BOLD}✅ SERVER READY!{Colors.END}")
    print("=" * 100)
    print(f"WebSocket: {Colors.CYAN}ws://localhost:8002/ws/chat{Colors.END}")
    print(f"Health Check: {Colors.CYAN}http://localhost:8002/health{Colors.END}")
    print(f"Full Diagnostics: {Colors.CYAN}http://localhost:8002/diagnostics{Colors.END}")
    print("=" * 100 + "\n")


def print_port_status(port: int = 8002, host: str = "localhost"):
    """Print current port status"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        print(f"\n{Colors.CYAN}{Colors.BOLD}🔍 PORT STATUS{Colors.END}")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        
        if result != 0:
            print(f"   Status: {Colors.GREEN}✅ AVAILABLE{Colors.END}")
        else:
            print(f"   Status: {Colors.RED}❌ IN USE{Colors.END}")
            # Try to find the process
            try:
                cmd = f"lsof -i :{port} -t"
                proc_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if proc_result.stdout.strip():
                    pid = proc_result.stdout.strip().split('\n')[0]
                    print(f"   PID: {pid}")
                    # Get process name
                    cmd = f"ps -p {pid} -o comm="
                    name_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                    if name_result.stdout:
                        print(f"   Process: {name_result.stdout.strip()}")
            except:
                pass
        print()
    except Exception as e:
        logger.debug(f"Could not check port status: {e}")