"""
Configuration Manager für flexible API Key und Settings Verwaltung

Prioritäten:
1. Runtime Context (vom Frontend übermittelt) - HÖCHSTE Priorität
2. Environment Variables (.env Datei) - STANDARD
3. Backend Config File (config.yaml) - FALLBACK

Unterstützt mehrere Frontends (VS Code, Web UI, CLI, etc.)
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MissingAPIKeyError(Exception):
    """Exception wenn ein benötigter API Key fehlt"""
    pass

class ConfigManager:
    """
    Zentrale Konfiguration mit Prioritäten-System
    Backend bleibt unabhängig von spezifischen Frontends
    """

    _instance = None
    _config_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config_file()
        return cls._instance

    def _load_config_file(self):
        """Lade Config File falls vorhanden"""
        config_paths = [
            Path('backend/config/api_keys.yaml'),
            Path('backend/config/api_keys.local.yaml'),
            Path('config/api_keys.yaml'),
            Path('config/api_keys.local.yaml'),
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        self._config_cache = yaml.safe_load(f) or {}
                        logger.info(f"✅ Config geladen aus: {config_path}")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Laden der Config {config_path}: {e}")

    @staticmethod
    def get_api_key(key_name: str, context: Optional[Dict] = None) -> str:
        """
        Hole API Key mit Prioritäten-System

        Args:
            key_name: Name des API Keys (z.B. 'OPENAI_API_KEY')
            context: Optionaler Context vom Frontend

        Returns:
            API Key String

        Raises:
            MissingAPIKeyError: Wenn Key nicht gefunden
        """
        # Priorität 1: Context vom Frontend (falls vorhanden)
        if context and 'api_keys' in context:
            if key_name in context['api_keys'] and context['api_keys'][key_name]:
                logger.debug(f"✅ {key_name} aus Frontend Context")
                return context['api_keys'][key_name]

        # Priorität 2: Environment Variable
        env_key = os.getenv(key_name)
        if env_key:
            logger.debug(f"✅ {key_name} aus Environment Variable")
            return env_key

        # Priorität 3: Config File
        manager = ConfigManager()
        if key_name in manager._config_cache:
            value = manager._config_cache[key_name]
            # Unterstütze ${ENV_VAR} Syntax in Config
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                value = os.getenv(env_var, '')

            if value:
                logger.debug(f"✅ {key_name} aus Config File")
                return value

        # Kein Key gefunden -> EXCEPTION mit hilfreichen Infos
        raise MissingAPIKeyError(
            f"\n❌ KRITISCHER FEHLER: API Key '{key_name}' nicht gefunden!\n"
            f"   \n"
            f"   Konfigurationsmöglichkeiten (in Priorität):\n"
            f"   1. Vom Frontend übermitteln (context)\n"
            f"   2. Environment Variable setzen:\n"
            f"      export {key_name}='your-api-key'\n"
            f"   3. Config File erstellen:\n"
            f"      backend/config/api_keys.yaml\n"
            f"   4. .env Datei im Projekt-Root\n"
            f"   \n"
            f"   Backend kann NICHT ohne diesen Key starten!"
        )

    @staticmethod
    def get_setting(key: str, default: Any = None, context: Optional[Dict] = None) -> Any:
        """
        Hole allgemeine Einstellung (nicht nur API Keys)

        Args:
            key: Settings Key
            default: Default Wert falls nicht gefunden
            context: Optionaler Context

        Returns:
            Setting Value oder Default
        """
        # Gleiche Prioritäten wie API Keys
        if context and 'settings' in context:
            if key in context['settings']:
                return context['settings'][key]

        # Environment Variable (mit KI_ Prefix)
        env_value = os.getenv(f"KI_{key.upper()}", None)
        if env_value is not None:
            return env_value

        # Config File
        manager = ConfigManager()
        if key in manager._config_cache:
            return manager._config_cache[key]

        return default

    @staticmethod
    def validate_api_keys(required_keys: Dict[str, str], context: Optional[Dict] = None) -> Dict[str, bool]:
        """
        Validiere mehrere API Keys auf einmal

        Args:
            required_keys: Dict mit key_name -> usage_description
            context: Optionaler Context

        Returns:
            Dict mit key_name -> is_available

        Raises:
            MissingAPIKeyError: Bei kritischen fehlenden Keys
        """
        results = {}
        missing_critical = []

        for key_name, usage in required_keys.items():
            try:
                value = ConfigManager.get_api_key(key_name, context)
                results[key_name] = bool(value)
            except MissingAPIKeyError:
                results[key_name] = False
                missing_critical.append(f"   • {key_name}: {usage}")

        if missing_critical:
            raise MissingAPIKeyError(
                f"\n❌ KRITISCHE API KEYS FEHLEN:\n" +
                "\n".join(missing_critical) +
                f"\n\nBackend kann nicht starten!\n"
                f"Siehe Dokumentation: backend/docs/FRONTEND_INTEGRATION.md"
            )

        return results

# Globale Instanz für einfachen Zugriff
config_manager = ConfigManager()