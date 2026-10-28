from typing import Optional
from app.core.config import settings
from app.providers.base import BaseAIProvider
from app.providers.demo import DemoAIProvider
from app.providers.gemini import GeminiAIProvider

def get_ai_provider(mode_override: Optional[str] = None) -> BaseAIProvider:
    """
    Provider factory. Returns GeminiAIProvider if real mode is configured with valid API keys,
    otherwise returns DemoAIProvider with verified fixtures.
    """
    mode = (mode_override or settings.AI_MODE).lower()
    
    if mode == "real":
        if settings.AI_API_KEY and len(settings.AI_API_KEY.strip()) > 5:
            return GeminiAIProvider()
        else:
            # If real mode was requested but credentials are absent, return DemoAIProvider
            # with explicit logging
            return DemoAIProvider()

    return DemoAIProvider()
