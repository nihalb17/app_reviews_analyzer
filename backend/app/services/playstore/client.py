from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google_play_scraper import reviews, Sort
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayStoreClient:
    """Client for fetching reviews from Google Play Store"""
    
    def __init__(self, app_package: str = "com.nextbillion.groww"):
        self.app_package = app_package
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def fetch_reviews(
        self,
        count: int = 100,
        period_days: Optional[int] = None,
        sort: Sort = Sort.NEWEST
    ) -> List[Dict[str, Any]]:
        """
        Fetch reviews from Play Store with pagination support
        
        Args:
            count: Number of reviews to fetch (max 1000)
            period_days: Filter reviews from last N days
            sort: Sort order (NEWEST, RATING)
        
        Returns:
            List of review dictionaries
        """
        count = min(count, 1000)  # Enforce max limit
        all_reviews = []
        continuation_token = None
        
        # Calculate date threshold if period specified
        date_threshold = None
        if period_days:
            date_threshold = datetime.now() - timedelta(days=period_days)
            logger.info(f"Fetching reviews from last {period_days} days")
        
        logger.info(f"Starting to fetch {count} reviews for {self.app_package}")
        
        while len(all_reviews) < count:
            batch_size = min(100, count - len(all_reviews))
            
            for attempt in range(self.max_retries):
                try:
                    result, continuation_token = reviews(
                        self.app_package,
                        lang='en',
                        country='in',
                        sort=sort,
                        count=batch_size,
                        continuation_token=continuation_token
                    )
                    
                    if not result:
                        logger.info("No more reviews available")
                        break
                    
                    # Filter by date if specified
                    for review in result:
                        review_date = review.get('at')
                        if date_threshold and review_date and review_date < date_threshold:
                            logger.info(f"Reached date threshold, stopping fetch")
                            return all_reviews
                        
                        all_reviews.append(self._normalize_review(review))
                    
                    logger.info(f"Fetched {len(all_reviews)} reviews so far...")
                    break
                    
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"Failed to fetch reviews after {self.max_retries} attempts")
                        raise
            
            # Stop if no continuation token (no more pages)
            if not continuation_token:
                logger.info("No more pages available")
                break
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        logger.info(f"Successfully fetched {len(all_reviews)} reviews")
        return all_reviews
    
    def _normalize_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize review data to consistent format"""
        return {
            'review_id': review.get('reviewId'),
            'content': review.get('content', ''),
            'rating': review.get('score', 0),
            'review_date': review.get('at'),
            'app_version': review.get('reviewCreatedVersion'),
            'thumbs_up': review.get('thumbsUpCount', 0),
            'user_name': review.get('userName', ''),
        }


class PlayStoreAPIError(Exception):
    """Custom exception for Play Store API errors"""
    pass
