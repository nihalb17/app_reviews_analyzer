"""
File-based storage for reviews (JSON/CSV)
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for storing and loading reviews from files"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_reviews_json(
        self,
        reviews: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Save reviews to JSON file
        
        Args:
            reviews: List of review dictionaries
            filename: Optional filename (default: reviews_YYYYMMDD_HHMMSS.json)
        
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reviews_{timestamp}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        # Add metadata
        data = {
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "count": len(reviews)
            },
            "reviews": reviews
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved {len(reviews)} reviews to {filepath}")
        return filepath
    
    def save_reviews_csv(
        self,
        reviews: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Save reviews to CSV file
        
        Args:
            reviews: List of review dictionaries
            filename: Optional filename (default: reviews_YYYYMMDD_HHMMSS.csv)
        
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reviews_{timestamp}.csv"
        
        filepath = os.path.join(self.data_dir, filename)
        
        if not reviews:
            logger.warning("No reviews to save")
            return filepath
        
        # Define CSV columns
        columns = [
            'review_id',
            'content',
            'cleaned_content',
            'rating',
            'review_date',
            'app_version',
            'thumbs_up',
            'content_hash'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(reviews)
        
        logger.info(f"Saved {len(reviews)} reviews to {filepath}")
        return filepath
    
    def load_reviews_json(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load reviews from JSON file
        
        Args:
            filename: Name of the JSON file
        
        Returns:
            List of review dictionaries
        """
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        reviews = data.get('reviews', [])
        logger.info(f"Loaded {len(reviews)} reviews from {filepath}")
        return reviews
    
    def load_reviews_csv(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load reviews from CSV file
        
        Args:
            filename: Name of the CSV file
        
        Returns:
            List of review dictionaries
        """
        filepath = os.path.join(self.data_dir, filename)
        
        reviews = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(dict(row))
        
        logger.info(f"Loaded {len(reviews)} reviews from {filepath}")
        return reviews
    
    def get_existing_hashes(self) -> set:
        """
        Get all existing content hashes from stored files
        
        Returns:
            Set of content hashes
        """
        hashes = set()
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                try:
                    reviews = self.load_reviews_json(filename)
                    for review in reviews:
                        if 'content_hash' in review:
                            hashes.add(review['content_hash'])
                except Exception as e:
                    logger.warning(f"Failed to load {filename}: {e}")
        
        return hashes
    
    def list_files(self) -> List[str]:
        """List all stored review files"""
        files = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith(('.json', '.csv')):
                files.append(filename)
        return sorted(files)
