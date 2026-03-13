"""
Fetch Real Reviews from Groww Play Store and Save to JSON/CSV

This script fetches 1000 real reviews from Groww's Play Store page
for the last 10 weeks, applies filters, and saves to JSON/CSV files.
"""

import argparse
import sys
import os

# Add the current directory to sys.path to allow relative imports of app.*
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.playstore.client import PlayStoreClient
from app.services.filters.review_filter import ReviewFilter
from app.services.dedup.deduplication_service import DeduplicationService
from app.services.storage.file_storage import FileStorageService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fetch reviews from Play Store and save to files"""
    
    parser = argparse.ArgumentParser(description="Fetch Groww Play Store reviews")
    parser.add_argument("--count", type=int, default=1000, help="Number of reviews to fetch")
    parser.add_argument("--days", type=int, default=70, help="Number of days to fetch reviews for")
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Directory to save output files'
    )
    
    args = parser.parse_args()

    print("="*60)
    print("FETCHING REAL REVIEWS FROM GROWW PLAY STORE")
    print("="*60)
    print()
    print(f"Configuration:")
    print(f"  - Reviews to fetch: {args.count}")
    print(f"  - Period: Last {args.days} days")
    print(f"  - App: com.nextbillion.groww")
    print(f"  - Output Directory: {args.output_dir}")
    print()
    
    # Initialize services
    print("Step 1: Initializing services...")
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    storage_service = FileStorageService(data_dir=args.output_dir)
    client = PlayStoreClient()
    review_filter = ReviewFilter()
    dedup_service = DeduplicationService()
    print("OK: Services initialized")
    print()
    
    # Step 1: Fetch reviews
    print("Step 2: Fetching reviews from Play Store...")
    print("(This may take a few minutes due to API rate limiting)")
    raw_reviews = client.fetch_reviews(
        count=args.count,
        period_days=args.days
    )
    print(f"OK: Fetched {len(raw_reviews)} reviews")
    print()
    
    if not raw_reviews:
        print("ERROR: No reviews fetched from Play Store!")
        return 1
        
    # Step 2: Filter reviews
    print("Step 3: Filtering reviews...")
    filtered_reviews, filter_stats = review_filter.filter_reviews(raw_reviews)
    print(f"OK: Filter stats: {filter_stats}")
    print()
    
    if not filtered_reviews:
        print("ERROR: No reviews passed filtering!")
        return 1
    
    # Step 3: Saving reviews to files (Overwriting previous data)
    print("Step 4: Saving reviews to files...")
    
    # Save to JSON
    json_filepath = storage_service.save_reviews_json(
        filtered_reviews,
        filename="groww_reviews.json"
    )
    print(f"OK: Saved to JSON (Overwritten): {json_filepath}")
    
    # Save to CSV
    csv_filepath = storage_service.save_reviews_csv(
        filtered_reviews,
        filename="groww_reviews.csv"
    )
    print(f"OK: Saved to CSV (Overwritten): {csv_filepath}")
    print()
    
    # Display results
    print("="*60)
    print("INGESTION RESULTS")
    print("="*60)
    print()
    
    print(f"Fetch Statistics:")
    print(f"  - Reviews fetched: {len(raw_reviews)}")
    print()
    
    print(f"Filter Statistics:")
    print(f"  - Total processed: {filter_stats.get('total', 0)}")
    print(f"  - PII removed: {filter_stats.get('pii_removed', 0)}")
    print(f"  - Non-English filtered: {filter_stats.get('non_english', 0)}")
    print(f"  - Too short (<5 words): {filter_stats.get('too_short', 0)}")
    print(f"  - Passed filtering: {filter_stats.get('passed', 0)}")
    print()
    
    print(f"Storage:")
    print(f"  - JSON file: {json_filepath}")
    print(f"  - CSV file: {csv_filepath}")
    print(f"  - Total reviews saved (Fresh Overwrite): {len(filtered_reviews)}")
    print()
    
    print(f"OK: Successfully saved {len(filtered_reviews)} reviews to files!")
    print()
    print("="*60)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
