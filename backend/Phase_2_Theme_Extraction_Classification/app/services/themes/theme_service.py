"""
Phase 2: Theme Extraction & Classification Service

Main service that orchestrates theme extraction and classification.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.theme import Theme, ThemeExtractionResult, Classification
from app.services.themes.theme_extractor import ThemeExtractor
from app.services.themes.theme_classifier import ThemeClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeService:
    """Main service for Phase 2 - Theme Extraction & Classification"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.extractor = ThemeExtractor()
        self.classifier = ThemeClassifier()
    
    def process_reviews(
        self,
        reviews: List[Dict[str, Any]],
        role: str,
        max_themes: int = 5
    ) -> Dict[str, Any]:
        """
        Complete Phase 2 processing: extract themes and classify reviews
        
        Args:
            reviews: List of review dictionaries
            role: Target role (Product, Support, UI/UX, Leadership)
            max_themes: Maximum number of themes (3-5)
        
        Returns:
            Dictionary with themes, classifications, and stats
        """
        logger.info("="*60)
        logger.info("PHASE 2: THEME EXTRACTION & CLASSIFICATION")
        logger.info("="*60)
        
        results = {
            'status': 'success',
            'role': role,
            'total_reviews': len(reviews),
            'themes': [],
            'classifications': [],
            'stats': {}
        }
        
        try:
            # Step 1: Extract themes
            logger.info(f"\nStep 1: Extracting themes for {role}...")
            extraction_result = self.extractor.extract_themes(
                reviews=reviews,
                role=role,
                max_themes=max_themes
            )
            
            themes = extraction_result.themes
            results['themes'] = [t.to_dict() for t in themes]
            results['extraction'] = extraction_result.to_dict()
            
            logger.info(f"OK: Extracted {len(themes)} themes")
            
            # Step 2: Classify reviews
            logger.info(f"\nStep 2: Classifying {len(reviews)} reviews...")
            classifications, classify_stats = self.classifier.classify_reviews(
                reviews=reviews,
                themes=themes
            )
            
            results['classifications'] = [c.to_dict() for c in classifications]
            results['stats'] = classify_stats
            
            logger.info(f"OK: Classified {classify_stats['classified']} reviews")
            logger.info(f"  Excluded {classify_stats['excluded']} reviews (no theme fit)")
            
            # Step 3: Save results
            logger.info(f"\nStep 3: Saving results...")
            self._save_results(results, role)
            
            logger.info("OK: Phase 2 complete!")
            
        except Exception as e:
            logger.error(f"Phase 2 failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def _save_results(self, results: Dict[str, Any], role: str):
        """Save theme extraction results to file (overwrites existing)"""
        # Sanitize role name for filename (remove/replace special characters)
        safe_role = role.lower().replace('/', '_').replace('\\', '_')
        filename = f"themes_{safe_role}.json"
        
        # Ensure data_dir exists
        os.makedirs(self.data_dir, exist_ok=True)
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"OK: Results saved to: {filepath}")


def run_phase2(
    reviews_file: str,
    role: str = "Product",
    max_themes: int = 5,
    output_dir: str = "data"
) -> Dict[str, Any]:
    """
    Run Phase 2 on reviews from a JSON file
    
    Args:
        reviews_file: Path to JSON file with reviews
        role: Target role
        max_themes: Maximum number of themes
        output_dir: Directory to save results
    
    Returns:
        Processing results
    """
    # Load reviews
    logger.info(f"Loading reviews from: {reviews_file}")
    with open(reviews_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats: {reviews: [...]} and [...]
    if isinstance(data, dict) and 'reviews' in data:
        reviews = data['reviews']
    elif isinstance(data, list):
        reviews = data
    else:
        raise ValueError("Invalid reviews file format")
    
    logger.info(f"Loaded {len(reviews)} reviews")
    
    # Process
    service = ThemeService(data_dir=output_dir)
    results = service.process_reviews(reviews, role, max_themes)
    
    return results


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python theme_service.py <reviews_file> [role]")
        sys.exit(1)
    
    reviews_file = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "Product"
    
    results = run_phase2(reviews_file, role)
    print(f"\nResults: {json.dumps(results, indent=2)}")
