"""
LLM Configuration and Provider Management
Supports OpenAI, Anthropic, and Google Gemini models
"""
import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMConfig:
    """Configuration for LLM providers"""
    
    # Default models for each provider
    DEFAULT_MODELS = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "gemini": "gemini-2.0-flash-exp"
    }
    
    @staticmethod
    def get_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> BaseChatModel:
        """
        Get an LLM instance based on provider and model
        
        Args:
            provider: LLM provider (openai, anthropic, gemini). If None, reads from env.
            model: Model name. If None, reads from env or uses default.
            temperature: Temperature for generation
            
        Returns:
            Configured LLM instance
            
        Raises:
            ValueError: If provider is invalid or API key is missing
        """
        # Get provider from env if not specified
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        # Get model from env if not specified
        if model is None:
            model = os.getenv("LLM_MODEL")
            if model is None:
                model = LLMConfig.DEFAULT_MODELS.get(provider)
        
        # Create LLM based on provider
        if provider == "openai":
            return LLMConfig._get_openai_llm(model, temperature)
        elif provider == "anthropic":
            return LLMConfig._get_anthropic_llm(model, temperature)
        elif provider == "gemini":
            return LLMConfig._get_gemini_llm(model, temperature)
        else:
            raise ValueError(
                f"Invalid LLM provider: {provider}. "
                f"Must be one of: openai, anthropic, gemini"
            )
    
    @staticmethod
    def _get_openai_llm(model: str, temperature: float) -> ChatOpenAI:
        """Get OpenAI LLM instance"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
    
    @staticmethod
    def _get_anthropic_llm(model: str, temperature: float) -> ChatAnthropic:
        """Get Anthropic LLM instance"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
    
    @staticmethod
    def _get_gemini_llm(model: str, temperature: float) -> ChatGoogleGenerativeAI:
        """Get Google Gemini LLM instance"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key
        )
    
    @staticmethod
    def get_available_providers() -> dict:
        """
        Get list of available providers based on API keys in environment
        
        Returns:
            Dict with provider names as keys and availability as values
        """
        return {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "gemini": bool(os.getenv("GOOGLE_API_KEY"))
        }
    
    @staticmethod
    def get_current_config() -> dict:
        """
        Get current LLM configuration from environment
        
        Returns:
            Dict with provider, model, and available providers
        """
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        model = os.getenv("LLM_MODEL", LLMConfig.DEFAULT_MODELS.get(provider))
        
        return {
            "provider": provider,
            "model": model,
            "available_providers": LLMConfig.get_available_providers()
        }
