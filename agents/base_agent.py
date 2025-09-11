"""
Base Agent - Basis-Klasse für alle Agenten
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

class BaseAgent(ABC):
    """
    Abstrakte Basis-Klasse für alle Agenten im System
    Definiert das gemeinsame Interface und Basis-Funktionalität
    """
    
    def __init__(self, name: str, role: str, model: str):
        self.name = name
        self.role = role
        self.model = model
        self.execution_count = 0
        self.total_tokens_used = 0
        self.system_prompt = ""
        self.temperature = 0.3
        self.max_tokens = 4000
        
        # API Keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        print(f"🤖 {self.name} initialisiert (Rolle: {self.role}, Modell: {self.model})")
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Gibt die Fähigkeiten des Agenten zurück
        Muss von jeder Subklasse implementiert werden
        """
        pass
    
    @abstractmethod
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Führt eine Aufgabe aus
        Muss von jeder Subklasse implementiert werden
        """
        pass
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        """
        Baut den Prompt für das LLM auf
        """
        prompt_parts = []
        
        # Add system prompt if available
        if self.system_prompt:
            prompt_parts.append(f"System: {self.system_prompt}\n")
        
        # Add task
        prompt_parts.append(f"Task: {task}\n")
        
        # Add context if available
        if context:
            prompt_parts.append("Context:")
            for key, value in context.items():
                if value:
                    # Limit context value length
                    value_str = str(value)[:500] if len(str(value)) > 500 else str(value)
                    prompt_parts.append(f"  {key}: {value_str}")
            prompt_parts.append("")
        
        # Add instruction
        prompt_parts.append("Please complete the task based on the context provided.")
        
        return "\n".join(prompt_parts)
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Ruft das LLM mit dem Prompt auf
        Kann von Subklassen überschrieben werden für spezifische APIs
        """
        # This is a placeholder - actual implementation depends on the model
        self.execution_count += 1
        
        # For testing/demo purposes
        return f"Response from {self.name} using {self.model}: Task completed successfully."
    
    def _extract_code(self, response: str) -> str:
        """
        Extrahiert Code aus der LLM-Antwort
        """
        import re
        
        # Look for code blocks
        code_blocks = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            return "\n\n".join(code_blocks)
        
        # If no code blocks, return the whole response
        return response
    
    def _validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validiert Python-Code
        """
        import ast
        
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Try to parse the code
            ast.parse(code)
            validation_result["valid"] = True
        except SyntaxError as e:
            validation_result["errors"].append(f"Syntax Error: {str(e)}")
        except Exception as e:
            validation_result["errors"].append(f"Parse Error: {str(e)}")
        
        # Basic checks
        if "import os" in code and "os.system" in code:
            validation_result["warnings"].append("Potential security risk: os.system usage")
        
        if "eval(" in code or "exec(" in code:
            validation_result["warnings"].append("Potential security risk: eval/exec usage")
        
        return validation_result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den Agenten zurück
        """
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model,
            "execution_count": self.execution_count,
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_execution": (
                self.total_tokens_used / self.execution_count 
                if self.execution_count > 0 else 0
            )
        }
    
    def reset_stats(self):
        """
        Setzt die Statistiken zurück
        """
        self.execution_count = 0
        self.total_tokens_used = 0
    
    def __repr__(self):
        return f"{self.name}(role='{self.role}', model='{self.model}')"