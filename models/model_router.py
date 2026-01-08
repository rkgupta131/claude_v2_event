"""
Model Router - Routes requests to different AI providers based on model_family and model_name
"""

import os
from typing import Dict, Optional
from abc import ABC, abstractmethod
from events.stream_events import StreamEventEmitter


# ==========================================================
# ABSTRACT BASE CLASS
# ==========================================================

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    def generate_project(self, prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
        """Generate a new project."""
        pass
    
    @abstractmethod
    def generate_patch(self, modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
        """Generate modifications for an existing project."""
        pass


# ==========================================================
# ANTHROPIC PROVIDER (Claude)
# ==========================================================

class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider."""
    
    def __init__(self, model_name: str):
        super().__init__(model_name)
        from models.gemini_client_qa import MODEL
        
        # Override the global MODEL in gemini_client_qa
        import models.gemini_client_qa as claude_module
        claude_module.MODEL = model_name
    
    def generate_project(self, prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
        """Generate a new project using Claude."""
        from models.gemini_client_qa import generate_project
        return generate_project(prompt, emitter)
    
    def generate_patch(self, modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
        """Generate modifications using Claude."""
        from models.gemini_client_qa import generate_patch
        return generate_patch(modification_prompt, base_project, emitter)


# ==========================================================
# OPENAI PROVIDER (GPT)
# ==========================================================

class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def generate_project(self, prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
        """Generate a new project using OpenAI GPT."""
        # Import the generation logic
        from models.openai_client import generate_project_openai
        return generate_project_openai(prompt, self.model_name, self.client, emitter)
    
    def generate_patch(self, modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
        """Generate modifications using OpenAI GPT."""
        from models.openai_client import generate_patch_openai
        return generate_patch_openai(modification_prompt, base_project, self.model_name, self.client, emitter)


# ==========================================================
# GOOGLE PROVIDER (Gemini)
# ==========================================================

class GoogleProvider(AIProvider):
    """Google Gemini provider."""
    
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    def generate_project(self, prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
        """Generate a new project using Google Gemini."""
        raise NotImplementedError("Google Gemini provider not yet implemented")
    
    def generate_patch(self, modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
        """Generate modifications using Google Gemini."""
        raise NotImplementedError("Google Gemini provider not yet implemented")


# ==========================================================
# MISTRAL PROVIDER
# ==========================================================

class MistralProvider(AIProvider):
    """Mistral AI provider."""
    
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
    
    def generate_project(self, prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
        """Generate a new project using Mistral."""
        raise NotImplementedError("Mistral provider not yet implemented")
    
    def generate_patch(self, modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
        """Generate modifications using Mistral."""
        raise NotImplementedError("Mistral provider not yet implemented")


# ==========================================================
# MODEL ROUTER
# ==========================================================

class ModelRouter:
    """Routes requests to appropriate AI provider based on model_family and model_name."""
    
    # Provider registry
    PROVIDERS = {
        "Anthropic": AnthropicProvider,
        "OpenAI": OpenAIProvider,
        "Google": GoogleProvider,
        "Mistral": MistralProvider,
    }
    
    # Default models for each provider
    DEFAULT_MODELS = {
        "Anthropic": "claude-opus-4-5-20251101",
        "OpenAI": "gpt-4",
        "Google": "gemini-pro",
        "Mistral": "mistral-large-latest",
    }
    
    @classmethod
    def get_provider(cls, model_family: str, model_name: Optional[str] = None) -> AIProvider:
        """
        Get the appropriate AI provider.
        
        Args:
            model_family: The AI provider family (e.g., "Anthropic", "OpenAI")
            model_name: Specific model name (e.g., "gpt-4", "claude-opus-4-5-20251101")
        
        Returns:
            AIProvider instance
        
        Raises:
            ValueError: If provider not supported or configuration missing
        """
        if model_family not in cls.PROVIDERS:
            raise ValueError(
                f"Unsupported model_family: {model_family}. "
                f"Supported: {', '.join(cls.PROVIDERS.keys())}"
            )
        
        # Use default model if not specified
        if not model_name:
            model_name = cls.DEFAULT_MODELS[model_family]
        
        # Validate model name for the provider
        cls._validate_model_name(model_family, model_name)
        
        # Instantiate and return provider
        provider_class = cls.PROVIDERS[model_family]
        return provider_class(model_name)
    
    @classmethod
    def _validate_model_name(cls, model_family: str, model_name: str):
        """Validate that the model name is valid for the provider."""
        
        # Known model patterns (can be expanded)
        valid_patterns = {
            "Anthropic": ["claude", "opus", "sonnet", "haiku"],
            "OpenAI": ["gpt-3.5", "gpt-4", "gpt-5"],
            "Google": ["gemini"],
            "Mistral": ["mistral", "mixtral"],
        }
        
        patterns = valid_patterns.get(model_family, [])
        model_lower = model_name.lower()
        
        if patterns and not any(pattern in model_lower for pattern in patterns):
            print(f"⚠️  Warning: Model '{model_name}' may not be valid for {model_family}")
    
    @classmethod
    def list_providers(cls) -> list:
        """List all supported providers."""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def get_default_model(cls, model_family: str) -> str:
        """Get the default model for a provider."""
        return cls.DEFAULT_MODELS.get(model_family, "")


# ==========================================================
# CONVENIENCE FUNCTIONS
# ==========================================================

def create_provider(model_family: str, model_name: Optional[str] = None) -> AIProvider:
    """
    Create an AI provider instance.
    
    Args:
        model_family: Provider name (Anthropic, OpenAI, Google, Mistral)
        model_name: Specific model name (optional)
    
    Returns:
        AIProvider instance
    """
    return ModelRouter.get_provider(model_family, model_name)


def get_supported_providers() -> Dict[str, str]:
    """Get dictionary of supported providers and their default models."""
    return {
        family: ModelRouter.get_default_model(family)
        for family in ModelRouter.list_providers()
    }


