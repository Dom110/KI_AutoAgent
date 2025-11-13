"""
Port Manager & Process Lifecycle Handler
Ensures clean server startup by detecting and managing existing processes on the server port.

Features:
- Detect if server is already running on target port
- Identify the process using the port
- Gracefully terminate existing processes
- Wait for port to become available
- Provide detailed diagnostics
"""

import os
import socket
import subprocess
import asyncio
import signal
import time
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ANSI Colors
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class PortManager:
    """Manages server port lifecycle"""
    
    def __init__(self, port: int = 8002, host: str = "localhost"):
        self.port = port
        self.host = host
        self.server_process_pid: Optional[int] = None
    
    def is_port_open(self) -> bool:
        """
        Check if a port is available (open/not in use).
        Returns True if port is available, False if in use.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex((self.host, self.port))
                # result == 0 means connection successful (port is in use)
                # result != 0 means port is available
                return result != 0
        except Exception as e:
            logger.warning(f"⚠️ Error checking port availability: {e}")
            return False
    
    def find_process_on_port(self) -> Optional[int]:
        """
        Find the PID of the process using the target port.
        Uses lsof on macOS/Linux, netstat on Windows.
        Returns PID if found, None otherwise.
        """
        try:
            if os.name == 'posix':  # macOS/Linux
                cmd = f"lsof -i :{self.port} -t"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    if pids[0]:
                        return int(pids[0])
            else:  # Windows
                cmd = f"netstat -ano | findstr :{self.port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    parts = result.stdout.strip().split()
                    if len(parts) > 4:
                        return int(parts[-1])
        except Exception as e:
            logger.warning(f"⚠️ Could not find process on port: {e}")
        
        return None
    
    def get_process_info(self, pid: int) -> dict:
        """
        Get information about a process by PID.
        Returns dict with process details.
        """
        info = {
            "pid": pid,
            "command": "unknown",
            "name": "unknown",
            "status": "unknown"
        }
        
        try:
            if os.name == 'posix':  # macOS/Linux
                # Get process command
                cmd = f"ps -p {pid} -o comm="
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                if result.stdout:
                    info["command"] = result.stdout.strip()
                    info["name"] = Path(result.stdout.strip()).name
                
                # Check if process is still running
                cmd = f"ps -p {pid} > /dev/null 2>&1 && echo 'running' || echo 'stopped'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                if result.stdout:
                    info["status"] = result.stdout.strip()
        except Exception as e:
            logger.warning(f"⚠️ Could not get process info for PID {pid}: {e}")
        
        return info
    
    def kill_process(self, pid: int, force: bool = False, timeout: int = 5) -> bool:
        """
        Terminate a process gracefully, then forcefully if needed.
        Returns True if successfully killed, False otherwise.
        """
        if not isinstance(pid, int) or pid <= 0:
            logger.error(f"❌ Invalid PID: {pid}")
            return False
        
        try:
            # First, try graceful termination with SIGTERM
            if os.name == 'posix':
                if not force:
                    logger.info(f"   Sending SIGTERM to PID {pid}...")
                    os.kill(pid, signal.SIGTERM)
                    
                    # Wait for process to terminate
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        try:
                            # Check if process still exists
                            os.kill(pid, 0)
                            time.sleep(0.1)
                        except ProcessLookupError:
                            logger.info(f"   ✅ Process {pid} terminated gracefully")
                            return True
                    
                    logger.warning(f"   ⚠️ Process {pid} did not terminate, using SIGKILL...")
                
                # Force kill with SIGKILL
                logger.info(f"   Sending SIGKILL to PID {pid}...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
                
                # Verify process is dead
                try:
                    os.kill(pid, 0)
                    logger.error(f"❌ Failed to kill process {pid}")
                    return False
                except ProcessLookupError:
                    logger.info(f"   ✅ Process {pid} force killed")
                    return True
            else:
                # Windows
                subprocess.run(f"taskkill /PID {pid} /F", shell=True, timeout=5)
                logger.info(f"   ✅ Process {pid} terminated")
                return True
        
        except ProcessLookupError:
            logger.info(f"   ✅ Process {pid} already terminated")
            return True
        except Exception as e:
            logger.error(f"❌ Error killing process {pid}: {e}")
            return False
    
    async def cleanup_port(self, verbose: bool = True) -> bool:
        """
        Check if port is in use and kill any process using it.
        Returns True if port is now available, False if cleanup failed.
        """
        # Check if port is available
        if self.is_port_open():
            if verbose:
                logger.info(f"✅ Port {self.port} is available")
            return True
        
        if verbose:
            logger.warning(f"⚠️ Port {self.port} is in use")
        
        # Find process using the port
        pid = self.find_process_on_port()
        if pid is None:
            logger.warning(f"⚠️ Could not identify process on port {self.port}")
            if verbose:
                print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  PORT {self.port} IN USE{Colors.END}")
                print(f"   Could not automatically kill the process.")
                print(f"   Please manually run: kill -9 $(lsof -t -i:{self.port})")
                print(f"   Or: pkill -9 -f 'uvicorn.*8002'\n")
            return False
        
        # Get process info
        proc_info = self.get_process_info(pid)
        
        if verbose:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}🔄 CLEANING UP EXISTING SERVER{Colors.END}")
            print(f"   Found process using port {self.port}:")
            print(f"   • PID: {proc_info['pid']}")
            print(f"   • Command: {proc_info['command']}")
            print(f"   • Status: {proc_info['status']}")
        
        # Kill the process
        if self.kill_process(pid, force=False):
            # Verify port is now available
            await asyncio.sleep(0.5)
            if self.is_port_open():
                if verbose:
                    print(f"   ✅ Port {self.port} is now available\n")
                return True
        
        # If graceful kill failed, try force kill
        logger.warning(f"⚠️ Graceful kill failed, attempting force kill...")
        if self.kill_process(pid, force=True):
            await asyncio.sleep(0.5)
            if self.is_port_open():
                if verbose:
                    print(f"   ✅ Port {self.port} is now available (force killed)\n")
                return True
        
        if verbose:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ FAILED TO CLEANUP PORT{Colors.END}")
            print(f"   Could not terminate process {pid}")
            print(f"   Manual cleanup needed: kill -9 {pid}\n")
        
        return False
    
    async def wait_for_port(self, timeout: int = 30, check_interval: float = 0.5) -> bool:
        """
        Wait for the port to become available.
        Returns True if port becomes available within timeout, False otherwise.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_port_open():
                return True
            
            await asyncio.sleep(check_interval)
        
        logger.error(f"❌ Port {self.port} did not become available within {timeout}s")
        return False


async def ensure_port_available(
    port: int = 8002,
    host: str = "localhost",
    auto_cleanup: bool = True,
    verbose: bool = True
) -> bool:
    """
    Ensure the target port is available for the server to bind to.
    
    Args:
        port: Port number to check
        host: Host address
        auto_cleanup: Automatically kill process on port if in use
        verbose: Print diagnostic information
    
    Returns:
        True if port is available, False if cleanup failed
    """
    manager = PortManager(port=port, host=host)
    
    # Check if port is already available
    if manager.is_port_open():
        if verbose:
            logger.info(f"✅ Port {port} is available")
        return True
    
    # Port is in use
    if not auto_cleanup:
        logger.error(f"❌ Port {port} is already in use and auto_cleanup is disabled")
        return False
    
    # Try to clean up
    if await manager.cleanup_port(verbose=verbose):
        return await manager.wait_for_port(timeout=5)
    
    return False


def print_port_status(port: int = 8002, host: str = "localhost"):
    """Print current status of the port"""
    manager = PortManager(port=port, host=host)
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔍 PORT STATUS CHECK{Colors.END}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    
    if manager.is_port_open():
        print(f"   Status: {Colors.GREEN}✅ AVAILABLE{Colors.END}")
    else:
        print(f"   Status: {Colors.RED}❌ IN USE{Colors.END}")
        pid = manager.find_process_on_port()
        if pid:
            info = manager.get_process_info(pid)
            print(f"   Process: {info['command']} (PID: {pid})")
    print()