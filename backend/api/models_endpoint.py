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

@router.get("/descriptions")
async def get_model_descriptions():
    """
    Return detailed model descriptions with pros/cons and use cases
    - OpenAI: 15 models (including Realtime, o1, etc.)
    - Anthropic: 5 models (Opus, Sonnet, Haiku)
    - Perplexity: 5 models (Sonar variants)
    """
    try:
        descriptions = {
            "openai": {
                "models": [
                    {
                        "id": "gpt-4o-2024-11-20",
                        "name": "GPT-4o (November 2024)",
                        "tier": "Premium",
                        "pros": ["Multimodal capabilities", "Excellent at system architecture", "Fast responses", "128K context"],
                        "cons": ["Higher cost than mini", "Not specialized for pure coding"],
                        "bestFor": "System design, architecture planning, documentation, multimodal tasks",
                        "costPerMToken": {"input": 2.5, "output": 10.0}
                    },
                    {
                        "id": "chatgpt-4o-latest",
                        "name": "ChatGPT-4o (Latest)",
                        "tier": "Premium",
                        "pros": ["Latest improvements", "Best general performance", "Continuously updated"],
                        "cons": ["May change without notice", "Less predictable"],
                        "bestFor": "General purpose, latest features, experimental workflows",
                        "costPerMToken": {"input": 5.0, "output": 15.0}
                    },
                    {
                        "id": "gpt-4o-mini-2024-07-18",
                        "name": "GPT-4o Mini",
                        "tier": "Efficient",
                        "pros": ["Very cost-effective", "Fast", "Good for reviews", "128K context"],
                        "cons": ["Less capable than full GPT-4o", "May miss edge cases"],
                        "bestFor": "Code reviews, quick analyses, cost-conscious workflows, high-volume tasks",
                        "costPerMToken": {"input": 0.15, "output": 0.6}
                    },
                    {
                        "id": "gpt-4o-realtime-preview",
                        "name": "GPT-4o Realtime (Preview)",
                        "tier": "Experimental",
                        "pros": ["Real-time audio/text", "Voice interactions", "Low latency"],
                        "cons": ["Preview only", "Limited availability", "Higher cost"],
                        "bestFor": "Voice assistants, real-time interactions, conversational AI",
                        "costPerMToken": {"input": 5.0, "output": 20.0}
                    },
                    {
                        "id": "gpt-4o-audio-preview",
                        "name": "GPT-4o Audio (Preview)",
                        "tier": "Experimental",
                        "pros": ["Audio processing", "Voice capabilities", "Transcription"],
                        "cons": ["Preview only", "Limited availability"],
                        "bestFor": "Audio analysis, transcription, voice processing",
                        "costPerMToken": {"input": 2.5, "output": 10.0}
                    },
                    {
                        "id": "o1-preview",
                        "name": "o1 Preview (Reasoning)",
                        "tier": "Experimental",
                        "pros": ["Advanced reasoning", "Complex problem solving", "Chain-of-thought"],
                        "cons": ["Much slower", "Very high cost", "Limited availability"],
                        "bestFor": "Complex logic, mathematical reasoning, research, algorithm design",
                        "costPerMToken": {"input": 15.0, "output": 60.0}
                    },
                    {
                        "id": "o1-mini",
                        "name": "o1 Mini (Reasoning)",
                        "tier": "Experimental",
                        "pros": ["Faster than o1", "Good reasoning at lower cost", "STEM focused"],
                        "cons": ["Less capable than full o1", "Still slower than GPT-4o"],
                        "bestFor": "Quick reasoning tasks, cost-effective problem solving, STEM education",
                        "costPerMToken": {"input": 3.0, "output": 12.0}
                    },
                    {
                        "id": "gpt-4-turbo-2024-04-09",
                        "name": "GPT-4 Turbo (April 2024)",
                        "tier": "Standard",
                        "pros": ["Proven reliability", "128K context", "Good general performance"],
                        "cons": ["Superseded by GPT-4o", "Slower than 4o"],
                        "bestFor": "Legacy workflows, proven stable tasks, large context needs",
                        "costPerMToken": {"input": 10.0, "output": 30.0}
                    },
                    {
                        "id": "gpt-4-0125-preview",
                        "name": "GPT-4 0125 Preview",
                        "tier": "Standard",
                        "pros": ["Reduced lazy responses", "Better task completion"],
                        "cons": ["Older model", "Superseded by 4o"],
                        "bestFor": "Tasks requiring thorough completion, legacy compatibility",
                        "costPerMToken": {"input": 10.0, "output": 30.0}
                    },
                    {
                        "id": "gpt-3.5-turbo",
                        "name": "GPT-3.5 Turbo",
                        "tier": "Budget",
                        "pros": ["Very low cost", "Fast", "Good for simple tasks"],
                        "cons": ["Less capable", "Limited context (16K)"],
                        "bestFor": "Simple queries, high-volume simple tasks, testing",
                        "costPerMToken": {"input": 0.5, "output": 1.5}
                    },
                    {
                        "id": "gpt-3.5-turbo-16k",
                        "name": "GPT-3.5 Turbo 16K",
                        "tier": "Budget",
                        "pros": ["Low cost", "16K context", "Fast"],
                        "cons": ["Less capable than GPT-4 series"],
                        "bestFor": "Cost-conscious workflows with moderate context needs",
                        "costPerMToken": {"input": 1.0, "output": 2.0}
                    },
                    {
                        "id": "gpt-4-32k",
                        "name": "GPT-4 32K",
                        "tier": "Standard",
                        "pros": ["Large 32K context", "Good for long documents"],
                        "cons": ["Expensive", "Slower", "Superseded by Turbo"],
                        "bestFor": "Long document analysis, legacy large-context workflows",
                        "costPerMToken": {"input": 60.0, "output": 120.0}
                    },
                    {
                        "id": "gpt-4",
                        "name": "GPT-4 (Base)",
                        "tier": "Standard",
                        "pros": ["Proven reliability", "Good general performance"],
                        "cons": ["8K context limit", "Superseded by Turbo/4o"],
                        "bestFor": "Legacy workflows, specific GPT-4 requirements",
                        "costPerMToken": {"input": 30.0, "output": 60.0}
                    },
                    {
                        "id": "gpt-4-vision-preview",
                        "name": "GPT-4 Vision (Preview)",
                        "tier": "Experimental",
                        "pros": ["Image understanding", "Visual analysis"],
                        "cons": ["Preview only", "Superseded by GPT-4o multimodal"],
                        "bestFor": "Image analysis (legacy), visual reasoning",
                        "costPerMToken": {"input": 10.0, "output": 30.0}
                    },
                    {
                        "id": "gpt-5-mini-2025-09-20",
                        "name": "GPT-5 Mini (2025)",
                        "tier": "Next-Gen",
                        "pros": ["Latest generation", "Fast", "Cost-effective"],
                        "cons": ["May not be available yet", "Preview status"],
                        "bestFor": "Code review, quick tasks, future-proofing",
                        "costPerMToken": {"input": 0.2, "output": 0.8}
                    }
                ],
                "total": 15,
                "recommended": {
                    "architecture": "gpt-4o-2024-11-20",
                    "review": "gpt-4o-mini-2024-07-18",
                    "reasoning": "o1-preview",
                    "general": "chatgpt-4o-latest",
                    "budget": "gpt-3.5-turbo"
                }
            },
            "anthropic": {
                "models": [
                    {
                        "id": "claude-opus-4-1-20250805",
                        "name": "Claude Opus 4.1",
                        "tier": "Supreme",
                        "pros": ["Best reasoning", "Supreme judgment", "Conflict resolution", "200K context"],
                        "cons": ["Most expensive", "Slower responses", "Overkill for simple tasks"],
                        "bestFor": "Critical decisions, complex reasoning, final arbitration, conflict resolution",
                        "costPerMToken": {"input": 15.0, "output": 75.0}
                    },
                    {
                        "id": "claude-4.1-sonnet-20250920",
                        "name": "Claude Sonnet 4.1",
                        "tier": "Premium",
                        "pros": ["Excellent at coding", "Fast", "Balanced cost/performance", "200K context"],
                        "cons": ["Not as capable as Opus for reasoning"],
                        "bestFor": "Code generation, implementation, bug fixing, refactoring",
                        "costPerMToken": {"input": 3.0, "output": 15.0}
                    },
                    {
                        "id": "claude-3-7-sonnet-20250219",
                        "name": "Claude 3.7 Sonnet",
                        "tier": "Standard",
                        "pros": ["Extended thinking", "Good reasoning", "Cost-effective", "200K context"],
                        "cons": ["Older than 4.1", "Slower than 4.1"],
                        "bestFor": "General tasks, thinking-heavy workflows, extended reasoning",
                        "costPerMToken": {"input": 3.0, "output": 15.0}
                    },
                    {
                        "id": "claude-3-5-haiku-20241022",
                        "name": "Claude 3.5 Haiku",
                        "tier": "Fast",
                        "pros": ["Very fast", "Cost-effective", "Good for simple tasks", "200K context"],
                        "cons": ["Less capable than Sonnet", "Not for complex reasoning"],
                        "bestFor": "Quick responses, simple implementations, high-volume tasks, fast iteration",
                        "costPerMToken": {"input": 0.8, "output": 4.0}
                    },
                    {
                        "id": "claude-3-opus-20240229",
                        "name": "Claude 3 Opus (Legacy)",
                        "tier": "Legacy",
                        "pros": ["Still very capable", "Proven reliability", "200K context"],
                        "cons": ["Older model", "Superseded by 4.1 Opus"],
                        "bestFor": "Legacy workflows, proven stable tasks, backward compatibility",
                        "costPerMToken": {"input": 15.0, "output": 75.0}
                    }
                ],
                "total": 5,
                "recommended": {
                    "coding": "claude-4.1-sonnet-20250920",
                    "reasoning": "claude-opus-4-1-20250805",
                    "fast": "claude-3-5-haiku-20241022",
                    "general": "claude-3-7-sonnet-20250219"
                }
            },
            "perplexity": {
                "models": [
                    {
                        "id": "llama-3.1-sonar-huge-128k-online",
                        "name": "Llama 3.1 Sonar Huge (Online)",
                        "tier": "Premium+",
                        "pros": ["Best research capability", "Comprehensive answers", "Real-time web access", "128K context"],
                        "cons": ["Most expensive", "Slower", "Overkill for simple lookups"],
                        "bestFor": "In-depth research, competitive analysis, market research, comprehensive reports",
                        "costPerMToken": {"input": 5.0, "output": 5.0}
                    },
                    {
                        "id": "llama-3.1-sonar-large-128k-online",
                        "name": "Llama 3.1 Sonar Large (Online)",
                        "tier": "Premium",
                        "pros": ["Better reasoning", "Real-time web", "Large context", "Balanced cost"],
                        "cons": ["More expensive than small"],
                        "bestFor": "Comprehensive research, detailed analyses, technical documentation lookup",
                        "costPerMToken": {"input": 1.0, "output": 1.0}
                    },
                    {
                        "id": "llama-3.1-sonar-small-128k-online",
                        "name": "Llama 3.1 Sonar Small (Online)",
                        "tier": "Standard",
                        "pros": ["Real-time web access", "Fast", "Cost-effective", "128K context"],
                        "cons": ["Less capable than huge", "May miss nuances"],
                        "bestFor": "Quick web research, fact-checking, documentation lookup, fast queries",
                        "costPerMToken": {"input": 0.2, "output": 0.2}
                    },
                    {
                        "id": "llama-3.1-70b-instruct",
                        "name": "Llama 3.1 70B Instruct (Offline)",
                        "tier": "Offline",
                        "pros": ["No web access needed", "Fast", "Privacy", "70B parameters"],
                        "cons": ["No real-time data", "No web search", "Stale knowledge"],
                        "bestFor": "Code analysis, offline tasks, privacy-sensitive work, internal processing",
                        "costPerMToken": {"input": 0.5, "output": 0.5}
                    },
                    {
                        "id": "mixtral-8x7b-instruct",
                        "name": "Mixtral 8x7B Instruct",
                        "tier": "Efficient",
                        "pros": ["Very fast", "Low cost", "Good quality", "Mixture of Experts"],
                        "cons": ["Smaller model", "Less capable", "Limited knowledge"],
                        "bestFor": "Simple research, quick lookups, high-volume queries, budget workflows",
                        "costPerMToken": {"input": 0.1, "output": 0.1}
                    }
                ],
                "total": 5,
                "recommended": {
                    "research": "llama-3.1-sonar-huge-128k-online",
                    "fast": "llama-3.1-sonar-small-128k-online",
                    "offline": "llama-3.1-70b-instruct",
                    "budget": "mixtral-8x7b-instruct"
                }
            }
        }

        logger.info(f"✅ Returned model descriptions: {descriptions['openai']['total']} GPT, {descriptions['anthropic']['total']} Claude, {descriptions['perplexity']['total']} Perplexity models")
        return descriptions

    except Exception as e:
        logger.error(f"Error getting model descriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model descriptions: {str(e)}")