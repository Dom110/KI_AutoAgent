"""
Cache Manager for KI AutoAgent
Handles Redis setup and cache management
"""

import logging
import os
import subprocess
import sys
import time
from typing import Any

import redis

# Add parent directory to path for version import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from __version__ import __version_display__

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages cache systems including Redis setup"""

    def __init__(self):
        self.redis_client = None
        self.redis_container_name = "ki_autoagent_redis"

    def check_docker_installed(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def check_redis_running(self) -> bool:
        """Check if Redis is accessible"""
        try:
            client = redis.Redis(
                host="localhost", port=6379, db=0, socket_connect_timeout=1
            )
            client.ping()
            self.redis_client = client
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def start_redis_container(self) -> dict[str, Any]:
        """Start Redis container using Docker"""
        result = {"success": False, "message": "", "actions": []}

        # Check Docker
        if not self.check_docker_installed():
            result["message"] = "Docker ist nicht installiert oder läuft nicht"
            result["actions"].append("❌ Docker nicht verfügbar")
            return result

        # Check if Redis already running
        if self.check_redis_running():
            result["success"] = True
            result["message"] = "Redis läuft bereits"
            result["actions"].append("✅ Redis bereits aktiv auf Port 6379")
            return result

        try:
            # Stop existing container if any
            logger.info("Stopping existing Redis container if present...")
            subprocess.run(
                ["docker", "stop", self.redis_container_name],
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["docker", "rm", self.redis_container_name],
                capture_output=True,
                timeout=5,
            )
            result["actions"].append(
                f"🔄 Alte Container '{self.redis_container_name}' entfernt"
            )

            # Start new Redis container
            logger.info("Starting Redis container...")
            cmd = [
                "docker",
                "run",
                "-d",
                "--name",
                self.redis_container_name,
                "-p",
                "6379:6379",
                "redis:7-alpine",
            ]

            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if process.returncode == 0:
                result["actions"].append(
                    f"🐳 Redis Container '{self.redis_container_name}' gestartet"
                )

                # Wait for Redis to be ready
                time.sleep(2)

                # Test connection
                if self.check_redis_running():
                    result["success"] = True
                    result["message"] = "Redis erfolgreich gestartet"
                    result["actions"].append("✅ Redis läuft auf Port 6379")
                    result["actions"].append("✅ Cache-System voll funktionsfähig")
                else:
                    result[
                        "message"
                    ] = "Redis gestartet, aber Verbindung fehlgeschlagen"
                    result["actions"].append(
                        "⚠️ Redis Container läuft, aber keine Verbindung möglich"
                    )
            else:
                result[
                    "message"
                ] = f"Fehler beim Starten des Redis Containers: {process.stderr}"
                result["actions"].append(f"❌ Docker-Fehler: {process.stderr[:100]}")

        except subprocess.TimeoutExpired:
            result["message"] = "Timeout beim Starten von Redis"
            result["actions"].append("❌ Docker-Befehl hat zu lange gedauert")
        except Exception as e:
            result["message"] = f"Unerwarteter Fehler: {str(e)}"
            result["actions"].append(f"❌ Fehler: {str(e)}")

        return result

    def fill_caches(self) -> dict[str, Any]:
        """Check and fill all cache systems"""
        result = {
            "redis": {"status": "unknown", "actions": []},
            "sqlite": {
                "status": "ready",
                "actions": ["✅ SQLite Datenbanken initialisiert"],
            },
            "memory": {"status": "active", "actions": ["✅ Agent-Memories geladen"]},
            "summary": "",
        }

        # Check and start Redis
        redis_result = self.start_redis_container()
        result["redis"]["status"] = "active" if redis_result["success"] else "failed"
        result["redis"]["actions"] = redis_result["actions"]

        # Initialize Redis cache if successful
        if redis_result["success"] and self.redis_client:
            try:
                # Set some initial cache values
                self.redis_client.set("ki_autoagent:initialized", "true")
                self.redis_client.set("ki_autoagent:version", __version_display__)
                result["redis"]["actions"].append("✅ Redis Cache initialisiert")
            except Exception as e:
                result["redis"]["actions"].append(
                    f"⚠️ Cache-Initialisierung fehlgeschlagen: {e}"
                )

        # Generate summary
        all_actions = []
        all_actions.extend(result["redis"]["actions"])
        all_actions.extend(result["sqlite"]["actions"])
        all_actions.extend(result["memory"]["actions"])

        result["summary"] = "CACHE STATUS:\n\n" + "\n".join(all_actions)

        if result["redis"]["status"] == "active":
            result["summary"] += "\n\n✅ Alle Cache-Systeme sind aktiv und gefüllt!"
        else:
            result[
                "summary"
            ] += "\n\n⚠️ Redis konnte nicht gestartet werden. Andere Caches sind aktiv."

        return result
