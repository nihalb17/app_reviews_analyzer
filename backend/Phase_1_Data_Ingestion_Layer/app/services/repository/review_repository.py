from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.review import Review
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewRepository:
    """Repository for review database operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Save reviews to database
        
        Returns:
            Stats dict with saved and duplicate counts
        """
        stats = {
            'saved': 0,
            'duplicates': 0,
            'failed': 0
        }
        
        for review_data in reviews:
            try:
                review = Review(
                    review_id=review_data['review_id'],
                    content=review_data['content'],
                    cleaned_content=review_data.get('cleaned_content'),
                    rating=review_data['rating'],
                    review_date=review_data['review_date'],
                    app_version=review_data.get('app_version'),
                    thumbs_up=review_data.get('thumbs_up', 0),
                    content_hash=review_data['content_hash']
                )
                
                self.db.add(review)
                self.db.commit()
                stats['saved'] += 1
                
            except IntegrityError:
                self.db.rollback()
                stats['duplicates'] += 1
                logger.debug(f"Duplicate review skipped: {review_data['review_id']}")
            except Exception as e:
                self.db.rollback()
                stats['failed'] += 1
                logger.error(f"Failed to save review {review_data.get('review_id')}: {str(e)}")
        
        logger.info(f"Save reviews stats: {stats}")
        return stats
    
    def get_existing_hashes(self) -> Set[str]:
        """Get all existing content hashes from database"""
        hashes = self.db.query(Review.content_hash).all()
        return {h[0] for h in hashes if h[0]}
    
    def get_reviews_by_date_range(
        self,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        limit: int = 1000
    ) -> List[Review]:
        """Get reviews within date range"""
        query = self.db.query(Review)
        
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        return query.order_by(Review.review_date.desc()).limit(limit).all()
    
    def review_exists(self, review_id: str) -> bool:
        """Check if review already exists"""
        return self.db.query(Review).filter(Review.review_id == review_id).first() is not None
    
    def hash_exists(self, content_hash: str) -> bool:
        """Check if content hash already exists"""
        return self.db.query(Review).filter(Review.content_hash == content_hash).first() is not None
