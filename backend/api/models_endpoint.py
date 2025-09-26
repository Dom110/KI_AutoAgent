"""
Model Discovery API Endpoints
Provides FastAPI endpoints for discovering and querying available AI models from all providers
"""

from fastapi import APIRouter, HTTPException
import yaml
import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router for model endpoints
router = APIRouter(prefix="/api/models", tags=["models"])

def load_models_from_config() -> Dict[str, List[Dict]]:
    """Load models from backend/config/agents.yaml"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "agents.yaml")

    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        # Extract models from agent configuration
        agent_models = {}
        if 'agents' in config:
            for agent_id, agent_config in config['agents'].items():
                model = agent_config.get('model')
                if model:
                    # Categorize by provider
                    if 'gpt' in model.lower():
                        provider = 'openai'
                    elif 'claude' in model.lower():
                        provider = 'anthropic'
                    elif 'llama' in model.lower() or 'sonar' in model.lower():
                        provider = 'perplexity'
                    else:
                        provider = 'unknown'

                    if provider not in agent_models:
                        agent_models[provider] = []

                    # Add model if not already present
                    if model not in [m['model_id'] for m in agent_models[provider]]:
                        agent_models[provider].append({
                            'model_id': model,
                            'name': model,
                            'used_by': [agent_id]
                        })
                    else:
                        # Add agent to existing model entry
                        for m in agent_models[provider]:
                            if m['model_id'] == model:
                                if agent_id not in m['used_by']:
                                    m['used_by'].append(agent_id)

        # Add available_models section if present
        if 'available_models' in config:
            available = config['available_models']
            for provider, models in available.items():
                if provider not in agent_models:
                    agent_models[provider] = []

                for model_info in models:
                    model_id = model_info.get('model_id')
                    if model_id and model_id not in [m['model_id'] for m in agent_models[provider]]:
                        agent_models[provider].append({
                            'model_id': model_id,
                            'name': model_info.get('name', model_id),
                            'capabilities': model_info.get('capabilities', []),
                            'used_by': []
                        })

        return agent_models

    except Exception as e:
        logger.error(f"Failed to load models from config: {e}")
        return {}

def load_models_from_available_json() -> Dict[str, List[str]]:
    """Load models from available_models.json if present"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "available_models.json")

    try:
        with open(json_path, 'r') as file:
            data = json.load(file)

        models = {}
        for provider in ['openai', 'anthropic', 'perplexity']:
            if provider in data and 'available' in data[provider]:
                models[provider] = data[provider]['available']

        return models

    except Exception as e:
        logger.warning(f"Could not load available_models.json: {e}")
        return {}

def get_model_recommendations(provider: str, models: List[str]) -> Dict[str, str]:
    """Get recommended models for different use cases"""
    recommendations = {}

    if provider == 'openai':
        # Latest GPT models
        gpt_models = [m for m in models if 'gpt' in m.lower()]
        if gpt_models:
            # Prefer newer models
            latest_gpt = sorted(gpt_models, key=lambda x: x.lower().replace('gpt-', ''), reverse=True)
            recommendations['general'] = latest_gpt[0]
            recommendations['code'] = latest_gpt[0]
            recommendations['reasoning'] = latest_gpt[0]

            # Fast model - prefer mini versions
            mini_models = [m for m in gpt_models if 'mini' in m.lower()]
            recommendations['fast'] = mini_models[0] if mini_models else latest_gpt[0]

    elif provider == 'anthropic':
        # Claude models
        claude_models = [m for m in models if 'claude' in m.lower()]
        if claude_models:
            # Prefer Opus for reasoning, Sonnet for code
            opus_models = [m for m in claude_models if 'opus' in m.lower()]
            sonnet_models = [m for m in claude_models if 'sonnet' in m.lower()]

            recommendations['general'] = claude_models[0]  # First available
            recommendations['code'] = sonnet_models[0] if sonnet_models else claude_models[0]
            recommendations['reasoning'] = opus_models[0] if opus_models else claude_models[0]
            recommendations['fast'] = sonnet_models[0] if sonnet_models else claude_models[0]

    elif provider == 'perplexity':
        # Perplexity models
        if models:
            recommendations['general'] = models[0]
            recommendations['code'] = models[0]
            recommendations['reasoning'] = models[0]
            recommendations['fast'] = models[0]

    return recommendations

def get_latest_models(models: List[str], limit: int = 3) -> List[str]:
    """Get the latest models based on naming patterns"""
    # Sort models to prioritize newer versions
    sorted_models = sorted(models, key=lambda x: x.lower(), reverse=True)
    return sorted_models[:limit]

@router.get("/")
async def get_all_models():
    """Return all available models from all providers"""
    try:
        # Load from both sources
        config_models = load_models_from_config()
        json_models = load_models_from_available_json()

        # Merge results
        all_models = {}
        for provider in ['openai', 'anthropic', 'perplexity']:
            models_list = []

            # Add from config
            if provider in config_models:
                models_list.extend([m['model_id'] for m in config_models[provider]])

            # Add from JSON
            if provider in json_models:
                models_list.extend(json_models[provider])

            # Remove duplicates
            all_models[provider] = list(set(models_list))

        return {
            "timestamp": datetime.now().isoformat(),
            "providers": list(all_models.keys()),
            "total_models": sum(len(models) for models in all_models.values()),
            "models": all_models
        }

    except Exception as e:
        logger.error(f"Error getting all models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(e)}")

@router.get("/openai")
async def get_openai_models():
    """Return OpenAI models with detailed information"""
    try:
        config_models = load_models_from_config()
        json_models = load_models_from_available_json()

        # Combine OpenAI models
        models_list = []
        if 'openai' in config_models:
            models_list.extend([m['model_id'] for m in config_models['openai']])
        if 'openai' in json_models:
            models_list.extend(json_models['openai'])

        models_list = list(set(models_list))  # Remove duplicates

        return {
            "provider": "openai",
            "models": models_list,
            "latest": get_latest_models(models_list, 3),
            "recommended": get_model_recommendations("openai", models_list),
            "count": len(models_list)
        }

    except Exception as e:
        logger.error(f"Error getting OpenAI models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve OpenAI models: {str(e)}")

@router.get("/anthropic")
async def get_anthropic_models():
    """Return Anthropic models with detailed information"""
    try:
        config_models = load_models_from_config()
        json_models = load_models_from_available_json()

        # Combine Anthropic models
        models_list = []
        if 'anthropic' in config_models:
            models_list.extend([m['model_id'] for m in config_models['anthropic']])
        if 'anthropic' in json_models:
            models_list.extend(json_models['anthropic'])

        models_list = list(set(models_list))  # Remove duplicates

        return {
            "provider": "anthropic",
            "models": models_list,
            "latest": get_latest_models(models_list, 3),
            "recommended": get_model_recommendations("anthropic", models_list),
            "count": len(models_list)
        }

    except Exception as e:
        logger.error(f"Error getting Anthropic models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Anthropic models: {str(e)}")

@router.get("/perplexity")
async def get_perplexity_models():
    """Return Perplexity models with detailed information"""
    try:
        config_models = load_models_from_config()
        json_models = load_models_from_available_json()

        # Combine Perplexity models
        models_list = []
        if 'perplexity' in config_models:
            models_list.extend([m['model_id'] for m in config_models['perplexity']])
        if 'perplexity' in json_models:
            models_list.extend(json_models['perplexity'])

        models_list = list(set(models_list))  # Remove duplicates

        return {
            "provider": "perplexity",
            "models": models_list,
            "latest": get_latest_models(models_list, 3),
            "recommended": get_model_recommendations("perplexity", models_list),
            "count": len(models_list)
        }

    except Exception as e:
        logger.error(f"Error getting Perplexity models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Perplexity models: {str(e)}")

@router.get("/agents")
async def get_agent_model_mapping():
    """Return which models are used by which agents"""
    try:
        config_models = load_models_from_config()

        agent_mapping = {}
        for provider, models in config_models.items():
            for model_info in models:
                if 'used_by' in model_info and model_info['used_by']:
                    model_id = model_info['model_id']
                    agent_mapping[model_id] = {
                        'provider': provider,
                        'agents': model_info['used_by'],
                        'name': model_info.get('name', model_id)
                    }

        return {
            "agent_models": agent_mapping,
            "total_mappings": len(agent_mapping)
        }

    except Exception as e:
        logger.error(f"Error getting agent model mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent mappings: {str(e)}")

@router.post("/refresh")
async def refresh_model_cache():
    """Force refresh of model discovery cache"""
    try:
        # This would trigger a refresh of available_models.json
        # For now, just return current timestamp
        return {
            "status": "refreshed",
            "timestamp": datetime.now().isoformat(),
            "message": "Model cache refresh requested (implementation depends on model discovery service)"
        }

    except Exception as e:
        logger.error(f"Error refreshing model cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh models: {str(e)}")