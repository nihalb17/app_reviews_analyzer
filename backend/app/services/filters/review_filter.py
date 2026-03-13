import re
import hashlib
from typing import List, Dict, Any, Tuple
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0


class ReviewFilter:
    """Filters reviews based on various criteria"""
    
    def __init__(self, min_words: int = 5, lang_confidence: float = 0.9):
        self.min_words = min_words
        self.lang_confidence = lang_confidence
        
        # PII Patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?91[-\s]?)?[6-9]\d{9}\b'),
            'pan': re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'),
            'aadhaar': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'account_number': re.compile(r'\b\d{9,18}\b'),
        }
    
    def filter_reviews(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Apply all filters to reviews
        
        Returns:
            Tuple of (filtered_reviews, filter_stats)
        """
        stats = {
            'total': len(reviews),
            'pii_removed': 0,
            'non_english': 0,
            'too_short': 0,
            'passed': 0
        }
        
        filtered = []
        
        for review in reviews:
            content = review.get('content', '')
            
            # 1. Check for PII
            cleaned_content, has_pii = self._remove_pii(content)
            if has_pii:
                stats['pii_removed'] += 1
                # Continue with cleaned content
            
            # 2. Check word count
            if not self._has_min_words(cleaned_content):
                stats['too_short'] += 1
                continue
            
            # 3. Check language
            if not self._is_english(cleaned_content):
                stats['non_english'] += 1
                continue
            
            # Generate content hash for deduplication
            content_hash = self._generate_hash(cleaned_content)
            
            # Add cleaned content and hash to review
            review['cleaned_content'] = cleaned_content
            review['content_hash'] = content_hash
            review['has_pii'] = has_pii
            
            filtered.append(review)
            stats['passed'] += 1
        
        logger.info(f"Filter stats: {stats}")
        return filtered, stats
    
    def _remove_pii(self, content: str) -> Tuple[str, bool]:
        """
        Remove PII from content
        
        Returns:
            Tuple of (cleaned_content, has_pii)
        """
        has_pii = False
        cleaned = content
        
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(cleaned):
                has_pii = True
                cleaned = pattern.sub(f'[{pii_type.upper()}_REDACTED]', cleaned)
        
        return cleaned, has_pii
    
    def _has_min_words(self, content: str) -> bool:
        """Check if content has minimum word count"""
        words = content.split()
        return len(words) >= self.min_words
    
    def _is_english(self, content: str) -> bool:
        """Check if content is in English"""
        try:
            # langdetect returns language code
            lang = detect(content)
            return lang == 'en'
        except LangDetectException:
            logger.warning(f"Language detection failed for content: {content[:50]}...")
            return False
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return False
    
    def _generate_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.lower().strip().encode()).hexdigest()


class FilterError(Exception):
    """Custom exception for filter errors"""
    pass
