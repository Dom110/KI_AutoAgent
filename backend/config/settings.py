"""
Globale Backend Settings
Zentrale Konfiguration für alle Agents und Services
"""

import os
from pathlib import Path

class Settings:
    """Globale Backend-Einstellungen"""

    # Sprach-Einstellungen
    DEFAULT_LANGUAGE = "de"  # Deutsch als Standard
    RESPONSE_LANGUAGE = os.getenv("KI_LANGUAGE", "de")

    # Sprach-Direktiven für System Prompts
    LANGUAGE_DIRECTIVES = {
        "de": """
🇩🇪 KRITISCHE REGEL:
Du MUSST IMMER auf Deutsch antworten, egal in welcher Sprache die Frage gestellt wird.
Dies gilt für ALLE Antworten, Erklärungen, Fehlermeldungen und Ausgaben.
Verwende deutsche Fachbegriffe wo möglich, aber behalte englische Begriffe bei Code/Technologie.
""",
        "en": """
🇬🇧 CRITICAL RULE:
You MUST ALWAYS respond in English, regardless of the query language.
This applies to ALL answers, explanations, error messages, and outputs.
""",
    }

    # System-weite Timeouts
    DEFAULT_TIMEOUT = 120  # Sekunden
    INFRASTRUCTURE_ANALYSIS_TIMEOUT = 180  # 3 Minuten für komplexe Analysen
    SIMPLE_QUERY_TIMEOUT = 30  # Schnelle Antworten

    # Cache Einstellungen
    CACHE_VALIDITY_MINUTES = None  # None = Unbegrenzt, nur File-Watcher invalidiert
    # Cache wird automatisch durch File-Watcher bei Code-Änderungen invalidiert
    # None = Cache bleibt gültig bis Dateiänderung oder manueller Clear
    USE_PERSISTENT_CACHE = True  # Redis/SQLite nutzen

    # Analyse Einstellungen
    MAX_FILES_FOR_METRICS = None  # Kein Limit (None) oder Zahl
    RESPECT_GITIGNORE = True  # .gitignore beachten
    PROGRESS_UPDATE_INTERVAL = 50  # Update alle X Dateien
    VERBOSE_PROGRESS_MESSAGES = False  # Detaillierte Progress-Messages (z.B. "Found X dependencies")
    SHOW_SCAN_DETAILS = False  # Zeige Details wie DB scan, API scan, etc.

    # Plan First Mode
    PLAN_FIRST_DEFAULT = True  # Vorschläge statt Auto-Implementation
    AUTO_IMPLEMENT = False  # Keine automatische Implementierung

    # Debug und Logging
    DEBUG_MODE = os.getenv("KI_DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("KI_LOG_LEVEL", "INFO")

    # Agent Thinking Transparenz
    SEND_THINKING_UPDATES = True  # Agent-Gedanken zum Frontend senden
    THINKING_DETAIL_LEVEL = "high"  # low, medium, high

    @classmethod
    def get_language_directive(cls) -> str:
        """Hole die aktuelle Sprach-Direktive"""
        return cls.LANGUAGE_DIRECTIVES.get(cls.RESPONSE_LANGUAGE, cls.LANGUAGE_DIRECTIVES["de"])

    @classmethod
    def get_timeout(cls, task_type: str = "default") -> int:
        """Hole Timeout basierend auf Task-Typ"""
        timeouts = {
            "infrastructure": cls.INFRASTRUCTURE_ANALYSIS_TIMEOUT,
            "simple": cls.SIMPLE_QUERY_TIMEOUT,
            "default": cls.DEFAULT_TIMEOUT
        }
        return timeouts.get(task_type, cls.DEFAULT_TIMEOUT)

# Globale Instanz
settings = Settings()