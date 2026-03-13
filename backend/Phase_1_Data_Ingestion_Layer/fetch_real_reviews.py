"""
Fetch Real Reviews from Groww Play Store

This script fetches 1000 real reviews from Groww's Play Store page
for the last 8 weeks, applies filters, and saves to database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ingestion_service import run_ingestion
from app.database import init_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fetch 1000 reviews from last 8 weeks and save to database"""
    
    print("="*60)
    print("FETCHING REAL REVIEWS FROM GROWW PLAY STORE")
    print("="*60)
    print()
    
    # Configuration
    REVIEW_COUNT = 1000
    PERIOD_DAYS = 56  # 8 weeks = 56 days
    
    print(f"Configuration:")
    print(f"  - Reviews to fetch: {REVIEW_COUNT}")
    print(f"  - Period: Last {PERIOD_DAYS} days (8 weeks)")
    print(f"  - App: com.nextbillion.groww")
    print()
    
    # Initialize database
    print("Step 1: Initializing database...")
    init_db()
    print("✓ Database initialized")
    print()
    
    # Run ingestion
    print("Step 2: Fetching and processing reviews...")
    print("(This may take a few minutes due to API rate limiting)")
    print()
    
    results = run_ingestion(
        count=REVIEW_COUNT,
        period_days=PERIOD_DAYS,
        init_database=False  # Already initialized above
    )
    
    # Display results
    print()
    print("="*60)
    print("INGESTION RESULTS")
    print("="*60)
    print()
    
    if results['status'] == 'success':
        print("✓ Ingestion completed successfully")
        print()
        
        # Fetch stats
        fetch_stats = results.get('fetch_stats', {})
        print(f"Fetch Statistics:")
        print(f"  - Reviews fetched: {fetch_stats.get('fetched', 0)}")
        print()
        
        # Filter stats
        filter_stats = results.get('filter_stats', {})
        print(f"Filter Statistics:")
        print(f"  - Total processed: {filter_stats.get('total', 0)}")
        print(f"  - PII removed: {filter_stats.get('pii_removed', 0)}")
        print(f"  - Non-English filtered: {filter_stats.get('non_english', 0)}")
        print(f"  - Too short (<5 words): {filter_stats.get('too_short', 0)}")
        print(f"  - Passed filtering: {filter_stats.get('passed', 0)}")
        print()
        
        # Deduplication stats
        dedup_stats = results.get('dedup_stats', {})
        print(f"Deduplication Statistics:")
        print(f"  - Input reviews: {dedup_stats.get('input', 0)}")
        print(f"  - Duplicates found: {dedup_stats.get('duplicates', 0)}")
        print(f"  - Unique reviews: {dedup_stats.get('unique', 0)}")
        print()
        
        # Save stats
        save_stats = results.get('save_stats', {})
        print(f"Database Statistics:")
        print(f"  - Reviews saved: {save_stats.get('saved', 0)}")
        print(f"  - Duplicates skipped: {save_stats.get('duplicates', 0)}")
        print(f"  - Failed to save: {save_stats.get('failed', 0)}")
        print()
        
        # Summary
        total_unique = dedup_stats.get('unique', 0)
        saved = save_stats.get('saved', 0)
        print(f"Summary:")
        print(f"  - Total unique reviews ingested: {total_unique}")
        print(f"  - Reviews saved to database: {saved}")
        print()
        
        if saved > 0:
            print(f"✓ Successfully saved {saved} reviews to database!")
        else:
            print("⚠ No new reviews were saved (all may be duplicates)")
            
    else:
        print("✗ Ingestion failed!")
        print(f"Error: {results.get('error', 'Unknown error')}")
        return 1
    
    print()
    print("="*60)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
