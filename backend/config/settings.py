"""
Globale Backend Settings
Zentrale Konfiguration für alle Agents und Services
"""

import os


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
    VERBOSE_PROGRESS_MESSAGES = (
        False  # Detaillierte Progress-Messages (z.B. "Found X dependencies")
    )
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

    # ========================================
    # v5.0 LangGraph Workflow Settings
    # ========================================
    LANGGRAPH_ENABLED = True
    LANGGRAPH_CHECKPOINT_INTERVAL = 5  # Save state every N agent steps
    LANGGRAPH_MAX_ITERATIONS = 20  # Max workflow iterations before stopping
    LANGGRAPH_PARALLEL_EXECUTION = False  # Allow parallel agent execution
    LANGGRAPH_STATE_MANAGEMENT = "sqlite"  # memory, sqlite, checkpoint

    # ========================================
    # Agent Quality & Validation Settings
    # ========================================
    AGENT_QUALITY_THRESHOLD = 0.75  # Min quality score (0-1) to accept output
    AGENT_MAX_RETRIES = 3  # Max retry attempts per agent
    AGENT_REVIEWER_ITERATIONS = 2  # How many review cycles
    AGENT_FIXER_ITERATIONS = 3  # How many fix attempts before escalating

    # ========================================
    # Alternative Fixer KI Settings (v5.1.0)
    # ========================================
    ALTERNATIVE_FIXER_ENABLED = True  # Enable alternative fixer AI when primary fails
    ALTERNATIVE_FIXER_MODEL = "gpt-4o"  # gpt-4o, gpt-5, gpt-5-mini, claude-opus-4
    ALTERNATIVE_FIXER_PROVIDER = "openai"  # Auto-detected from model
    ALTERNATIVE_FIXER_TRIGGER_ITERATION = 11  # Trigger after N collaborations
    ALTERNATIVE_FIXER_TEMPERATURE = 0.7  # Creativity level (0.0-1.0)
    ALTERNATIVE_FIXER_MAX_TOKENS = 4096  # Max response length
    ALTERNATIVE_FIXER_TIMEOUT = 120  # Timeout in seconds

    # ========================================
    # Routing & Orchestration Settings
    # ========================================
    ROUTING_STRATEGY = "hybrid"  # keyword, confidence, hybrid
    ROUTING_CONFIDENCE_THRESHOLD = 0.8  # Min confidence for auto-routing
    ROUTING_FALLBACK_AGENT = "orchestrator"  # orchestrator, codesmith, ask-user
    ROUTING_ENABLE_KEYWORD_MATCHING = True
    ROUTING_ENABLE_SEMANTIC_MATCHING = True

    # ========================================
    # Performance & Monitoring Settings
    # ========================================
    MONITORING_ENABLED = True
    MONITORING_LOG_AGENT_METRICS = False  # Log to .ki_autoagent_ws/metrics.json (workspace) or ~/.ki_autoagent/data/metrics.json (global)
    MONITORING_TRACK_ROUTING_SUCCESS = True
    MONITORING_ALERT_ON_FAILURES = True

    # ========================================
    # Context & Memory Settings
    # ========================================
    CONTEXT_MAX_TOKENS_PER_AGENT = 8000  # Max context tokens per agent
    CONTEXT_INCLUDE_HISTORY = True  # Include chat history in context
    CONTEXT_HISTORY_DEPTH = 10  # How many previous messages to include
    MEMORY_ENABLED = False  # Long-term memory (experimental)
    MEMORY_STORAGE_BACKEND = "sqlite"  # sqlite, json, memory

    # ========================================
    # Cost Management Settings
    # ========================================
    COST_TRACK_USAGE = True
    COST_MONTHLY_BUDGET = 100.0  # USD, 0 = unlimited
    COST_ALERT_ON_THRESHOLD = 0.8  # Alert at 80% of budget
    COST_PREFER_CHEAPER_MODELS = False

    # ========================================
    # VideoAgent Settings (v5.8.2)
    # ========================================
    VIDEOAGENT_ENABLED = True  # Enable VideoAgent for video understanding
    VIDEOAGENT_MODEL = "gemini-2.0-flash-exp"  # Gemini model for video analysis
    VIDEOAGENT_TEMPERATURE = 0.7  # Creativity level (0.0-1.0)
    VIDEOAGENT_MAX_TOKENS = 8000  # Max response tokens
    VIDEOAGENT_OUTPUT_DIR = (
        "~/.ki_autoagent/data/video_output"  # Output directory for results
    )
    VIDEOAGENT_CLEANUP_AFTER_ANALYSIS = (
        True  # Delete video from Gemini API after analysis
    )
    VIDEOAGENT_BATCH_SIZE = 20  # Max videos per batch
    VIDEOAGENT_DUAL_OUTPUT = True  # Always generate JSON + Markdown (required)
    VIDEOAGENT_MULTI_LANGUAGE = True  # Support multi-language instructions

    @classmethod
    def get_language_directive(cls) -> str:
        """Hole die aktuelle Sprach-Direktive"""
        return cls.LANGUAGE_DIRECTIVES.get(
            cls.RESPONSE_LANGUAGE, cls.LANGUAGE_DIRECTIVES["de"]
        )

    @classmethod
    def get_timeout(cls, task_type: str = "default") -> int:
        """Hole Timeout basierend auf Task-Typ"""
        timeouts = {
            "infrastructure": cls.INFRASTRUCTURE_ANALYSIS_TIMEOUT,
            "simple": cls.SIMPLE_QUERY_TIMEOUT,
            "default": cls.DEFAULT_TIMEOUT,
        }
        return timeouts.get(task_type, cls.DEFAULT_TIMEOUT)

    @classmethod
    def update_from_vscode(cls, vscode_settings: dict) -> None:
        """
        Update backend settings from VS Code extension settings.

        Maps VS Code setting keys (e.g., 'langgraph.enabled') to backend constants.

        Args:
            vscode_settings: Dictionary with VS Code settings
        """
        # LangGraph Settings
        if "langgraph.enabled" in vscode_settings:
            cls.LANGGRAPH_ENABLED = vscode_settings["langgraph.enabled"]
        if "langgraph.checkpointInterval" in vscode_settings:
            cls.LANGGRAPH_CHECKPOINT_INTERVAL = vscode_settings[
                "langgraph.checkpointInterval"
            ]
        if "langgraph.maxIterations" in vscode_settings:
            cls.LANGGRAPH_MAX_ITERATIONS = vscode_settings["langgraph.maxIterations"]
        if "langgraph.parallelExecution" in vscode_settings:
            cls.LANGGRAPH_PARALLEL_EXECUTION = vscode_settings[
                "langgraph.parallelExecution"
            ]
        if "langgraph.stateManagement" in vscode_settings:
            cls.LANGGRAPH_STATE_MANAGEMENT = vscode_settings[
                "langgraph.stateManagement"
            ]

        # Agent Quality Settings
        if "agents.qualityThreshold" in vscode_settings:
            cls.AGENT_QUALITY_THRESHOLD = vscode_settings["agents.qualityThreshold"]
        if "agents.maxRetries" in vscode_settings:
            cls.AGENT_MAX_RETRIES = vscode_settings["agents.maxRetries"]
        if "agents.reviewerIterations" in vscode_settings:
            cls.AGENT_REVIEWER_ITERATIONS = vscode_settings["agents.reviewerIterations"]
        if "agents.fixerIterations" in vscode_settings:
            cls.AGENT_FIXER_ITERATIONS = vscode_settings["agents.fixerIterations"]

        # Alternative Fixer Settings (v5.1.0)
        if "alternativeFixer.enabled" in vscode_settings:
            cls.ALTERNATIVE_FIXER_ENABLED = vscode_settings["alternativeFixer.enabled"]
        if "alternativeFixer.model" in vscode_settings:
            cls.ALTERNATIVE_FIXER_MODEL = vscode_settings["alternativeFixer.model"]
            # Auto-detect provider from model
            cls.ALTERNATIVE_FIXER_PROVIDER = cls._auto_detect_provider(
                cls.ALTERNATIVE_FIXER_MODEL
            )
        if "alternativeFixer.triggerAfterIterations" in vscode_settings:
            cls.ALTERNATIVE_FIXER_TRIGGER_ITERATION = vscode_settings[
                "alternativeFixer.triggerAfterIterations"
            ]
        if "alternativeFixer.temperature" in vscode_settings:
            cls.ALTERNATIVE_FIXER_TEMPERATURE = vscode_settings[
                "alternativeFixer.temperature"
            ]

        # Routing Settings
        if "routing.strategy" in vscode_settings:
            cls.ROUTING_STRATEGY = vscode_settings["routing.strategy"]
        if "routing.confidenceThreshold" in vscode_settings:
            cls.ROUTING_CONFIDENCE_THRESHOLD = vscode_settings[
                "routing.confidenceThreshold"
            ]
        if "routing.fallbackAgent" in vscode_settings:
            cls.ROUTING_FALLBACK_AGENT = vscode_settings["routing.fallbackAgent"]
        if "routing.enableKeywordMatching" in vscode_settings:
            cls.ROUTING_ENABLE_KEYWORD_MATCHING = vscode_settings[
                "routing.enableKeywordMatching"
            ]
        if "routing.enableSemanticMatching" in vscode_settings:
            cls.ROUTING_ENABLE_SEMANTIC_MATCHING = vscode_settings[
                "routing.enableSemanticMatching"
            ]

        # Monitoring Settings
        if "monitoring.enabled" in vscode_settings:
            cls.MONITORING_ENABLED = vscode_settings["monitoring.enabled"]
        if "monitoring.logAgentMetrics" in vscode_settings:
            cls.MONITORING_LOG_AGENT_METRICS = vscode_settings[
                "monitoring.logAgentMetrics"
            ]
        if "monitoring.trackRoutingSuccess" in vscode_settings:
            cls.MONITORING_TRACK_ROUTING_SUCCESS = vscode_settings[
                "monitoring.trackRoutingSuccess"
            ]
        if "monitoring.alertOnFailures" in vscode_settings:
            cls.MONITORING_ALERT_ON_FAILURES = vscode_settings[
                "monitoring.alertOnFailures"
            ]

        # Context Settings
        if "context.maxTokensPerAgent" in vscode_settings:
            cls.CONTEXT_MAX_TOKENS_PER_AGENT = vscode_settings[
                "context.maxTokensPerAgent"
            ]
        if "context.includeHistory" in vscode_settings:
            cls.CONTEXT_INCLUDE_HISTORY = vscode_settings["context.includeHistory"]
        if "context.historyDepth" in vscode_settings:
            cls.CONTEXT_HISTORY_DEPTH = vscode_settings["context.historyDepth"]

        # Memory Settings
        if "memory.enabled" in vscode_settings:
            cls.MEMORY_ENABLED = vscode_settings["memory.enabled"]
        if "memory.storageBackend" in vscode_settings:
            cls.MEMORY_STORAGE_BACKEND = vscode_settings["memory.storageBackend"]

        # Cost Settings
        if "cost.trackUsage" in vscode_settings:
            cls.COST_TRACK_USAGE = vscode_settings["cost.trackUsage"]
        if "cost.monthlyBudget" in vscode_settings:
            cls.COST_MONTHLY_BUDGET = vscode_settings["cost.monthlyBudget"]
        if "cost.alertOnThreshold" in vscode_settings:
            cls.COST_ALERT_ON_THRESHOLD = vscode_settings["cost.alertOnThreshold"]
        if "cost.preferCheaperModels" in vscode_settings:
            cls.COST_PREFER_CHEAPER_MODELS = vscode_settings["cost.preferCheaperModels"]

        # VideoAgent Settings (v5.8.2)
        if "videoAgent.enabled" in vscode_settings:
            cls.VIDEOAGENT_ENABLED = vscode_settings["videoAgent.enabled"]
        if "videoAgent.model" in vscode_settings:
            cls.VIDEOAGENT_MODEL = vscode_settings["videoAgent.model"]
        if "videoAgent.temperature" in vscode_settings:
            cls.VIDEOAGENT_TEMPERATURE = vscode_settings["videoAgent.temperature"]
        if "videoAgent.maxTokens" in vscode_settings:
            cls.VIDEOAGENT_MAX_TOKENS = vscode_settings["videoAgent.maxTokens"]
        if "videoAgent.outputDir" in vscode_settings:
            cls.VIDEOAGENT_OUTPUT_DIR = vscode_settings["videoAgent.outputDir"]
        if "videoAgent.cleanupAfterAnalysis" in vscode_settings:
            cls.VIDEOAGENT_CLEANUP_AFTER_ANALYSIS = vscode_settings[
                "videoAgent.cleanupAfterAnalysis"
            ]
        if "videoAgent.batchSize" in vscode_settings:
            cls.VIDEOAGENT_BATCH_SIZE = vscode_settings["videoAgent.batchSize"]

    @classmethod
    def _auto_detect_provider(cls, model: str) -> str:
        """
        Auto-detect provider from model name

        Args:
            model: Model name (e.g., gpt-4o, claude-opus-4)

        Returns:
            Provider name (openai, anthropic, google)
        """
        model_lower = model.lower()
        if model_lower.startswith("gpt-"):
            return "openai"
        elif model_lower.startswith("claude-"):
            return "anthropic"
        elif model_lower.startswith("gemini-"):
            return "google"
        else:
            # Default to openai for unknown models
            return "openai"

    @classmethod
    def to_dict(cls) -> dict:
        """
        Export all v5.0 settings as dictionary.

        Returns:
            Dictionary with all configurable settings
        """
        return {
            # LangGraph
            "langgraph": {
                "enabled": cls.LANGGRAPH_ENABLED,
                "checkpointInterval": cls.LANGGRAPH_CHECKPOINT_INTERVAL,
                "maxIterations": cls.LANGGRAPH_MAX_ITERATIONS,
                "parallelExecution": cls.LANGGRAPH_PARALLEL_EXECUTION,
                "stateManagement": cls.LANGGRAPH_STATE_MANAGEMENT,
            },
            # Agent Quality
            "agents": {
                "qualityThreshold": cls.AGENT_QUALITY_THRESHOLD,
                "maxRetries": cls.AGENT_MAX_RETRIES,
                "reviewerIterations": cls.AGENT_REVIEWER_ITERATIONS,
                "fixerIterations": cls.AGENT_FIXER_ITERATIONS,
            },
            # Alternative Fixer (v5.1.0)
            "alternativeFixer": {
                "enabled": cls.ALTERNATIVE_FIXER_ENABLED,
                "model": cls.ALTERNATIVE_FIXER_MODEL,
                "provider": cls.ALTERNATIVE_FIXER_PROVIDER,
                "triggerAfterIterations": cls.ALTERNATIVE_FIXER_TRIGGER_ITERATION,
                "temperature": cls.ALTERNATIVE_FIXER_TEMPERATURE,
                "maxTokens": cls.ALTERNATIVE_FIXER_MAX_TOKENS,
                "timeout": cls.ALTERNATIVE_FIXER_TIMEOUT,
            },
            # Routing
            "routing": {
                "strategy": cls.ROUTING_STRATEGY,
                "confidenceThreshold": cls.ROUTING_CONFIDENCE_THRESHOLD,
                "fallbackAgent": cls.ROUTING_FALLBACK_AGENT,
                "enableKeywordMatching": cls.ROUTING_ENABLE_KEYWORD_MATCHING,
                "enableSemanticMatching": cls.ROUTING_ENABLE_SEMANTIC_MATCHING,
            },
            # Monitoring
            "monitoring": {
                "enabled": cls.MONITORING_ENABLED,
                "logAgentMetrics": cls.MONITORING_LOG_AGENT_METRICS,
                "trackRoutingSuccess": cls.MONITORING_TRACK_ROUTING_SUCCESS,
                "alertOnFailures": cls.MONITORING_ALERT_ON_FAILURES,
            },
            # Context
            "context": {
                "maxTokensPerAgent": cls.CONTEXT_MAX_TOKENS_PER_AGENT,
                "includeHistory": cls.CONTEXT_INCLUDE_HISTORY,
                "historyDepth": cls.CONTEXT_HISTORY_DEPTH,
            },
            # Memory
            "memory": {
                "enabled": cls.MEMORY_ENABLED,
                "storageBackend": cls.MEMORY_STORAGE_BACKEND,
            },
            # Cost
            "cost": {
                "trackUsage": cls.COST_TRACK_USAGE,
                "monthlyBudget": cls.COST_MONTHLY_BUDGET,
                "alertOnThreshold": cls.COST_ALERT_ON_THRESHOLD,
                "preferCheaperModels": cls.COST_PREFER_CHEAPER_MODELS,
            },
            # VideoAgent (v5.8.2)
            "videoAgent": {
                "enabled": cls.VIDEOAGENT_ENABLED,
                "model": cls.VIDEOAGENT_MODEL,
                "temperature": cls.VIDEOAGENT_TEMPERATURE,
                "maxTokens": cls.VIDEOAGENT_MAX_TOKENS,
                "outputDir": cls.VIDEOAGENT_OUTPUT_DIR,
                "cleanupAfterAnalysis": cls.VIDEOAGENT_CLEANUP_AFTER_ANALYSIS,
                "batchSize": cls.VIDEOAGENT_BATCH_SIZE,
                "dualOutput": cls.VIDEOAGENT_DUAL_OUTPUT,
                "multiLanguage": cls.VIDEOAGENT_MULTI_LANGUAGE,
            },
        }


# Globale Instanz
settings = Settings()
