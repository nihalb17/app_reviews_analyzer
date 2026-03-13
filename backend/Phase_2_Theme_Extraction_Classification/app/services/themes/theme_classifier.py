"""
Theme Classification Service

Classifies all reviews into the extracted themes using Groq LLM.
Reviews that don't fit any theme are excluded (no "Other" category).
"""

from typing import List, Dict, Any, Tuple
import logging

from app.models.theme import Theme, Classification
from app.services.llm.groq_client import GroqClient
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeClassifier:
    """Service for classifying reviews into themes"""
    
    def __init__(self, api_key: str = None, fallback_api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.fallback_api_key = fallback_api_key or settings.GROQ_API_KEY_FALLBACK
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in .env file")
        
        self.groq_client = GroqClient(
            api_key=self.api_key,
            model=settings.GROQ_MODEL,
            fallback_api_key=self.fallback_api_key
        )
        self.batch_size = 50  # Process reviews in batches
    
    def classify_reviews(
        self,
        reviews: List[Dict[str, Any]],
        themes: List[Theme]
    ) -> Tuple[List[Classification], Dict[str, int]]:
        """
        Classify all reviews into themes
        
        Args:
            reviews: List of review dictionaries
            themes: List of Theme objects
        
        Returns:
            Tuple of (classifications, stats)
        """
        logger.info(f"Classifying {len(reviews)} reviews into {len(themes)} themes")
        
        # Prepare theme info for LLM
        theme_info = [
            {
                'theme_id': t.theme_id,
                'name': t.name,
                'description': t.description
            }
            for t in themes
        ]
        
        # Create theme lookup by name
        theme_by_name = {t.name: t for t in themes}
        
        all_classifications = []
        stats = {
            'total': len(reviews),
            'classified': 0,
            'excluded': 0
        }
        
        # Process in batches
        for i in range(0, len(reviews), self.batch_size):
            batch = reviews[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(reviews)-1)//self.batch_size + 1}")
            
            batch_classifications = self._classify_batch(batch, theme_info)
            
            for classification_dict in batch_classifications:
                review_id = classification_dict['review_id']
                theme_name = classification_dict['theme_name']
                confidence = classification_dict['confidence']
                
                # Find the theme
                theme = theme_by_name.get(theme_name)
                
                if theme and confidence >= 0.5:  # Minimum confidence threshold
                    classification = Classification(
                        review_id=review_id,
                        theme_id=theme.theme_id,
                        theme_name=theme.name,
                        confidence=confidence
                    )
                    all_classifications.append(classification)
                    
                    # Add review to theme
                    theme.review_ids.append(review_id)
                    stats['classified'] += 1
                else:
                    # Review doesn't fit any theme well - exclude it
                    stats['excluded'] += 1
        
        logger.info(f"Classification complete:")
        logger.info(f"  - Classified: {stats['classified']}")
        logger.info(f"  - Excluded: {stats['excluded']}")
        
        # Log theme distribution
        for theme in themes:
            count = len(theme.review_ids)
            logger.info(f"  - {theme.name}: {count} reviews")
        
        return all_classifications, stats
    
    def _classify_batch(
        self,
        batch: List[Dict[str, Any]],
        theme_info: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Classify a batch of reviews"""
        try:
            classifications = self.groq_client.classify_reviews(batch, theme_info)
            return classifications
        except Exception as e:
            logger.error(f"Failed to classify batch: {e}")
            # Return empty classifications on failure
            return []


class ThemeClassificationError(Exception):
    """Custom exception for theme classification errors"""
    pass
