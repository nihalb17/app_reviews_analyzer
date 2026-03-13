from typing import List, Dict, Any, Set, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeduplicationService:
    """Service for deduplicating reviews"""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def deduplicate(
        self,
        reviews: List[Dict[str, Any]],
        existing_hashes: Set[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Remove duplicate reviews based on content hash
        
        Args:
            reviews: List of reviews with 'content_hash' field
            existing_hashes: Set of hashes already in database (optional)
        
        Returns:
            Tuple of (unique_reviews, dedup_stats)
        """
        stats = {
            'input': len(reviews),
            'duplicates': 0,
            'unique': 0
        }
        
        unique_reviews = []
        current_hashes = set()
        
        # Use provided existing hashes or empty set
        self.seen_hashes = existing_hashes or set()
        
        for review in reviews:
            content_hash = review.get('content_hash')
            
            if not content_hash:
                logger.warning(f"Review missing content_hash: {review.get('review_id')}")
                continue
            
            # Check if hash exists in current batch or database
            if content_hash in current_hashes or content_hash in self.seen_hashes:
                stats['duplicates'] += 1
                continue
            
            current_hashes.add(content_hash)
            unique_reviews.append(review)
            stats['unique'] += 1
        
        logger.info(f"Deduplication stats: {stats}")
        return unique_reviews, stats
    
    def get_unique_hashes(self, reviews: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique hashes from reviews"""
        return {r.get('content_hash') for r in reviews if r.get('content_hash')}
