from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def execution_mode(self) -> str:
        pass

    @abstractmethod
    async def analyze_food_image(
        self, image_bytes: bytes, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify food items and estimate nutritional breakdown."""
        pass

    @abstractmethod
    async def assess_visible_freshness(
        self, image_bytes: bytes, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess visual signs of freshness/spoilage with safety bounds."""
        pass

    @abstractmethod
    async def analyze_kitchen_image(
        self, image_bytes: bytes, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform observational sanitation & hygiene inspection on kitchen image."""
        pass

    @abstractmethod
    async def analyze_video_frames(
        self, frames: List[Tuple[float, bytes]]
    ) -> Dict[str, Any]:
        """Perform observational analysis over sampled timestamped video frames."""
        pass

    @abstractmethod
    async def generate_recipe(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured recipe with instructions, allergens, and substitutions."""
        pass

    @abstractmethod
    async def generate_meal_plan(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized 7-day or daily meal plan."""
        pass

    @abstractmethod
    async def transcribe_audio(
        self, audio_bytes: bytes
    ) -> Dict[str, Any]:
        """Transcribe spoken user recipe / dietary instructions."""
        pass
