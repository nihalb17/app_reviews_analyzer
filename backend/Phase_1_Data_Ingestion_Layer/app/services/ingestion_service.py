"""
Phase 1: Data Ingestion Service

Orchestrates the complete data ingestion flow:
1. Fetch reviews from Play Store
2. Filter reviews (PII, language, word count)
3. Deduplicate reviews
4. Save to database
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.playstore.client import PlayStoreClient
from app.services.filters.review_filter import ReviewFilter
from app.services.dedup.deduplication_service import DeduplicationService
from app.services.repository.review_repository import ReviewRepository
from app.database import get_db_session, init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionService:
    """Main service for Phase 1 - Data Ingestion"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.playstore_client = PlayStoreClient()
        self.review_filter = ReviewFilter()
        self.dedup_service = DeduplicationService()
        
        if db_session:
            self.db = db_session
            self.review_repo = ReviewRepository(db_session)
        else:
            self.db = None
            self.review_repo = None
    
    def ingest_reviews(
        self,
        count: int = 100,
        period_days: Optional[int] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Complete ingestion flow
        
        Args:
            count: Number of reviews to fetch
            period_days: Filter reviews from last N days
            save_to_db: Whether to save reviews to database
        
        Returns:
            Dictionary with results and statistics
        """
        results = {
            'status': 'success',
            'fetch_stats': {},
            'filter_stats': {},
            'dedup_stats': {},
            'save_stats': {},
            'reviews': []
        }
        
        try:
            # Step 1: Fetch reviews from Play Store
            logger.info(f"Step 1: Fetching {count} reviews from Play Store...")
            raw_reviews = self.playstore_client.fetch_reviews(
                count=count,
                period_days=period_days
            )
            results['fetch_stats'] = {
                'fetched': len(raw_reviews)
            }
            logger.info(f"Fetched {len(raw_reviews)} reviews")
            
            if not raw_reviews:
                logger.warning("No reviews fetched")
                return results
            
            # Step 2: Filter reviews
            logger.info("Step 2: Filtering reviews...")
            filtered_reviews, filter_stats = self.review_filter.filter_reviews(raw_reviews)
            results['filter_stats'] = filter_stats
            logger.info(f"Filter stats: {filter_stats}")
            
            if not filtered_reviews:
                logger.warning("No reviews passed filtering")
                return results
            
            # Step 3: Deduplicate reviews
            logger.info("Step 3: Deduplicating reviews...")
            
            # Get existing hashes from database if saving
            existing_hashes = set()
            if save_to_db and self.review_repo:
                existing_hashes = self.review_repo.get_existing_hashes()
                logger.info(f"Found {len(existing_hashes)} existing reviews in database")
            
            unique_reviews, dedup_stats = self.dedup_service.deduplicate(
                filtered_reviews,
                existing_hashes=existing_hashes
            )
            results['dedup_stats'] = dedup_stats
            logger.info(f"Deduplication stats: {dedup_stats}")
            
            if not unique_reviews:
                logger.warning("No unique reviews after deduplication")
                return results
            
            # Step 4: Save to database
            if save_to_db and self.review_repo:
                logger.info("Step 4: Saving reviews to database...")
                save_stats = self.review_repo.save_reviews(unique_reviews)
                results['save_stats'] = save_stats
                logger.info(f"Save stats: {save_stats}")
            else:
                logger.info("Step 4: Skipping database save (save_to_db=False or no db connection)")
                results['save_stats'] = {'saved': 0, 'skipped': len(unique_reviews)}
            
            results['reviews'] = unique_reviews
            logger.info(f"Ingestion complete. Total unique reviews: {len(unique_reviews)}")
            
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def get_stored_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Any]:
        """Get stored reviews from database"""
        if not self.review_repo:
            raise ValueError("Database not initialized")
        
        return self.review_repo.get_reviews_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )


def run_ingestion(
    count: int = 100,
    period_days: Optional[int] = None,
    init_database: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run ingestion with database initialization
    
    Args:
        count: Number of reviews to fetch
        period_days: Filter reviews from last N days
        init_database: Whether to initialize database tables
    
    Returns:
        Ingestion results
    """
    # Initialize database if requested
    if init_database:
        init_db()
    
    # Create session and run ingestion
    db_session = get_db_session()
    try:
        service = DataIngestionService(db_session=db_session)
        results = service.ingest_reviews(
            count=count,
            period_days=period_days,
            save_to_db=True
        )
        return results
    finally:
        db_session.close()


if __name__ == "__main__":
    # Example usage
    print("Running Phase 1 Data Ingestion...")
    results = run_ingestion(count=50, period_days=30)
    print(f"\nResults: {results}")
