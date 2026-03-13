"""
Theme Extraction Service

Extracts role-based themes from reviews using Groq LLM.
Analyzes 150-200 reviews to identify 3-5 distinct themes.
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.theme import Theme, ThemeExtractionResult
from app.services.llm.groq_client import GroqClient
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeExtractor:
    """Service for extracting themes from reviews"""
    
    def __init__(self, api_key: Optional[str] = None, fallback_api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.fallback_api_key = fallback_api_key or settings.GROQ_API_KEY_FALLBACK
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in .env file")
        
        self.groq_client = GroqClient(
            api_key=self.api_key,
            model=settings.GROQ_MODEL,
            fallback_api_key=self.fallback_api_key
        )
        self.sample_size = 200  # Analyze 150-200 reviews for theme extraction
    
    def extract_themes(
        self,
        reviews: List[Dict[str, Any]],
        role: str,
        max_themes: int = 5
    ) -> ThemeExtractionResult:
        """
        Extract themes from reviews for a specific role
        
        Args:
            reviews: List of review dictionaries
            role: Target role (Product, Support, UI/UX, Leadership)
            max_themes: Maximum number of themes (3-5)
        
        Returns:
            ThemeExtractionResult with extracted themes
        """
        logger.info(f"Extracting themes for role: {role}")
        logger.info(f"Total reviews available: {len(reviews)}")
        
        # Sample reviews for theme extraction (150-200 is sufficient)
        sample_reviews = self._sample_reviews(reviews, self.sample_size)
        logger.info(f"Using {len(sample_reviews)} reviews for theme extraction")
        
        # Extract themes using Groq
        theme_dicts = self.groq_client.extract_themes(
            reviews=sample_reviews,
            role=role,
            max_themes=max_themes
        )
        
        # Convert to Theme objects
        themes = []
        for theme_dict in theme_dicts:
            theme = Theme(
                name=theme_dict['name'],
                description=theme_dict['description'],
                sentiment=theme_dict['sentiment'],
                keywords=theme_dict.get('keywords', [])
            )
            themes.append(theme)
        
        # Limit themes if needed
        if len(themes) > max_themes:
            logger.warning(f"Extracted {len(themes)} themes, limiting to {max_themes}")
            themes = themes[:max_themes]
        
        result = ThemeExtractionResult(
            themes=themes,
            role=role,
            sample_size=len(sample_reviews),
            total_reviews=len(reviews)
        )
        
        logger.info(f"Extracted {len(themes)} themes for {role}")
        for theme in themes:
            logger.info(f"  - {theme.name} ({theme.sentiment})")
        
        return result
    
    def _sample_reviews(
        self,
        reviews: List[Dict[str, Any]],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """
        Sample reviews for theme extraction
        
        Strategy:
        - Prioritize diverse ratings (mix of 1-5 stars)
        - Include recent reviews
        - Random sample if needed
        """
        if len(reviews) <= sample_size:
            return reviews
        
        # Group by rating
        by_rating = {1: [], 2: [], 3: [], 4: [], 5: []}
        for review in reviews:
            rating = review.get('rating', 3)
            if rating in by_rating:
                by_rating[rating].append(review)
        
        # Sample from each rating group proportionally
        samples = []
        per_rating = sample_size // 5
        
        for rating in [5, 4, 3, 2, 1]:  # Prioritize extreme ratings
            group = by_rating[rating]
            if group:
                # Take min(per_rating, len(group)) from this rating
                n = min(per_rating, len(group))
                samples.extend(random.sample(group, n))
        
        # If we need more, fill randomly
        if len(samples) < sample_size:
            remaining = [r for r in reviews if r not in samples]
            needed = sample_size - len(samples)
            if remaining and needed > 0:
                samples.extend(random.sample(remaining, min(needed, len(remaining))))
        
        # Shuffle to avoid rating-based ordering
        random.shuffle(samples)
        
        return samples[:sample_size]


class ThemeExtractionError(Exception):
    """Custom exception for theme extraction errors"""
    pass
