"""
Test Cases for Phase 2: Theme Extractor
Test IDs: P2-T06 to P2-T10
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
from unittest.mock import Mock, patch, MagicMock

from app.services.themes.theme_extractor import ThemeExtractor, ThemeExtractionError
from app.models.theme import Theme


class TestThemeExtractor(unittest.TestCase):
    """P2-T06 to P2-T10: Test Theme Extractor functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_reviews = [
            {
                'review_id': 'r1',
                'content': 'App crashes frequently',
                'cleaned_content': 'App crashes frequently',
                'rating': 1
            },
            {
                'review_id': 'r2',
                'content': 'Great features but slow',
                'cleaned_content': 'Great features but slow',
                'rating': 3
            },
            {
                'review_id': 'r3',
                'content': 'Love the new update',
                'cleaned_content': 'Love the new update',
                'rating': 5
            }
        ]
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_extractor.GroqClient')
    def test_extractor_initialization(self, mock_client):
        """P2-T06: Verify ThemeExtractor initializes with API key"""
        extractor = ThemeExtractor(api_key='test_key')
        
        self.assertIsNotNone(extractor.groq_client)
        self.assertEqual(extractor.sample_size, 200)
    
    @patch('app.services.themes.theme_extractor.settings')
    def test_extractor_requires_api_key(self, mock_settings):
        """P2-T06: Verify ThemeExtractor fails without API key"""
        mock_settings.GROQ_API_KEY = ""
        
        with patch('app.services.themes.theme_extractor.GroqClient'):
            with self.assertRaises(ValueError) as context:
                ThemeExtractor()
            
            self.assertIn("API key is required", str(context.exception))
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_extractor.GroqClient')
    def test_extract_themes_returns_result(self, mock_client_class):
        """P2-T07: Verify extract_themes returns ThemeExtractionResult"""
        # Mock the Groq client
        mock_client = MagicMock()
        mock_client.extract_themes.return_value = [
            {
                'name': 'Technical Issues',
                'description': 'App crashes and bugs',
                'sentiment': 'negative',
                'keywords': ['crash', 'bug']
            }
        ]
        mock_client_class.return_value = mock_client
        
        extractor = ThemeExtractor(api_key='test_key')
        result = extractor.extract_themes(self.sample_reviews, role='Product')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.role, 'Product')
        self.assertEqual(len(result.themes), 1)
        self.assertEqual(result.themes[0].name, 'Technical Issues')
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_extractor.GroqClient')
    def test_extract_themes_for_different_roles(self, mock_client_class):
        """P2-T08: Verify theme extraction works for all roles"""
        mock_client = MagicMock()
        mock_client.extract_themes.return_value = [
            {
                'name': 'Test Theme',
                'description': 'Test description',
                'sentiment': 'negative',
                'keywords': ['test']
            }
        ]
        mock_client_class.return_value = mock_client
        
        extractor = ThemeExtractor(api_key='test_key')
        roles = ['Product', 'Support', 'UI/UX', 'Leadership']
        
        for role in roles:
            result = extractor.extract_themes(self.sample_reviews, role=role)
            self.assertEqual(result.role, role)
    
    def test_sample_reviews_with_diverse_ratings(self):
        """P2-T09: Verify sampling includes diverse ratings"""
        # Create reviews with different ratings
        reviews = []
        for rating in [1, 2, 3, 4, 5]:
            for i in range(20):
                reviews.append({
                    'review_id': f'r{rating}_{i}',
                    'content': f'Review with rating {rating}',
                    'rating': rating
                })
        
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            with patch('app.services.themes.theme_extractor.GroqClient'):
                extractor = ThemeExtractor(api_key='test_key')
                sampled = extractor._sample_reviews(reviews, sample_size=50)
                
                # Check that we got samples from different ratings
                ratings_in_sample = set(r['rating'] for r in sampled)
                self.assertGreater(len(ratings_in_sample), 1)
    
    def test_sample_reviews_returns_all_if_small(self):
        """P2-T09: Verify all reviews returned if less than sample size"""
        small_reviews = self.sample_reviews[:3]
        
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            with patch('app.services.themes.theme_extractor.GroqClient'):
                extractor = ThemeExtractor(api_key='test_key')
                sampled = extractor._sample_reviews(small_reviews, sample_size=200)
                
                self.assertEqual(len(sampled), 3)
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_extractor.GroqClient')
    def test_extract_themes_limits_max_themes(self, mock_client_class):
        """P2-T10: Verify max_themes parameter is respected"""
        # Return more themes than max
        mock_client = MagicMock()
        mock_client.extract_themes.return_value = [
            {'name': f'Theme {i}', 'description': f'Desc {i}', 
             'sentiment': 'negative', 'keywords': ['test']}
            for i in range(10)
        ]
        mock_client_class.return_value = mock_client
        
        extractor = ThemeExtractor(api_key='test_key')
        
        # Mock the logger to avoid the warning
        with patch('app.services.themes.theme_extractor.logger'):
            result = extractor.extract_themes(
                self.sample_reviews,
                role='Product',
                max_themes=5
            )
        
        # Should limit to 5 themes
        self.assertLessEqual(len(result.themes), 5)


class TestThemeExtractorErrorHandling(unittest.TestCase):
    """Additional error handling tests"""
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_extractor.GroqClient')
    def test_empty_reviews_list(self, mock_client_class):
        """Test handling of empty reviews list"""
        mock_client = MagicMock()
        mock_client.extract_themes.return_value = []
        mock_client_class.return_value = mock_client
        
        extractor = ThemeExtractor(api_key='test_key')
        result = extractor.extract_themes([], role='Product')
        
        self.assertEqual(len(result.themes), 0)
        self.assertEqual(result.total_reviews, 0)


def run_tests():
    """Run all Phase 2 extractor tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestThemeExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeExtractorErrorHandling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
