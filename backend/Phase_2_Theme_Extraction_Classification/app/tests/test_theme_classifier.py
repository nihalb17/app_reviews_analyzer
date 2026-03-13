"""
Test Cases for Phase 2: Theme Classifier
Test IDs: P2-T11 to P2-T15
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
from unittest.mock import Mock, patch, MagicMock

from app.services.themes.theme_classifier import ThemeClassifier, ThemeClassificationError
from app.models.theme import Theme, Classification


class TestThemeClassifier(unittest.TestCase):
    """P2-T11 to P2-T15: Test Theme Classifier functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.themes = [
            Theme(
                name="Technical Issues",
                description="App crashes and bugs",
                sentiment="negative",
                theme_id="theme_1"
            ),
            Theme(
                name="Usability",
                description="Navigation problems",
                sentiment="negative",
                theme_id="theme_2"
            )
        ]
        
        self.reviews = [
            {
                'review_id': 'r1',
                'content': 'App keeps crashing',
                'cleaned_content': 'App keeps crashing'
            },
            {
                'review_id': 'r2',
                'content': 'Hard to navigate',
                'cleaned_content': 'Hard to navigate'
            },
            {
                'review_id': 'r3',
                'content': 'Crashes when I open',
                'cleaned_content': 'Crashes when I open'
            }
        ]
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_classifier_initialization(self, mock_client):
        """P2-T11: Verify ThemeClassifier initializes with API key"""
        classifier = ThemeClassifier(api_key='test_key')
        
        self.assertIsNotNone(classifier.groq_client)
        self.assertEqual(classifier.batch_size, 50)
    
    @patch('app.services.themes.theme_classifier.settings')
    def test_classifier_requires_api_key(self, mock_settings):
        """P2-T11: Verify ThemeClassifier fails without API key"""
        mock_settings.GROQ_API_KEY = ""
        
        with patch('app.services.themes.theme_classifier.GroqClient'):
            with self.assertRaises(ValueError) as context:
                ThemeClassifier()
            
            self.assertIn("API key is required", str(context.exception))
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_classify_reviews_returns_classifications(self, mock_client_class):
        """P2-T12: Verify classify_reviews returns classifications"""
        # Mock the Groq client
        mock_client = MagicMock()
        mock_client.classify_reviews.return_value = [
            {
                'review_id': 'r1',
                'theme_name': 'Technical Issues',
                'confidence': 0.95
            },
            {
                'review_id': 'r2',
                'theme_name': 'Usability',
                'confidence': 0.87
            },
            {
                'review_id': 'r3',
                'theme_name': 'Technical Issues',
                'confidence': 0.92
            }
        ]
        mock_client_class.return_value = mock_client
        
        classifier = ThemeClassifier(api_key='test_key')
        classifications, stats = classifier.classify_reviews(self.reviews, self.themes)
        
        self.assertEqual(len(classifications), 3)
        self.assertEqual(stats['classified'], 3)
        self.assertEqual(stats['total'], 3)
        
        # Verify review assignments
        r1_class = next(c for c in classifications if c.review_id == 'r1')
        self.assertEqual(r1_class.theme_name, 'Technical Issues')
        self.assertEqual(r1_class.confidence, 0.95)
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_classify_reviews_assigns_to_themes(self, mock_client_class):
        """P2-T13: Verify reviews are assigned to theme objects"""
        mock_client = MagicMock()
        mock_client.classify_reviews.return_value = [
            {'review_id': 'r1', 'theme_name': 'Technical Issues', 'confidence': 0.9},
            {'review_id': 'r2', 'theme_name': 'Usability', 'confidence': 0.85},
            {'review_id': 'r3', 'theme_name': 'Technical Issues', 'confidence': 0.88}
        ]
        mock_client_class.return_value = mock_client
        
        classifier = ThemeClassifier(api_key='test_key')
        classifications, stats = classifier.classify_reviews(self.reviews, self.themes)
        
        # Check that themes have reviews assigned
        tech_theme = next(t for t in self.themes if t.name == 'Technical Issues')
        usability_theme = next(t for t in self.themes if t.name == 'Usability')
        
        self.assertEqual(len(tech_theme.review_ids), 2)  # r1 and r3
        self.assertEqual(len(usability_theme.review_ids), 1)  # r2
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_low_confidence_reviews_excluded(self, mock_client_class):
        """P2-T14: Verify low confidence classifications are excluded"""
        mock_client = MagicMock()
        mock_client.classify_reviews.return_value = [
            {'review_id': 'r1', 'theme_name': 'Technical Issues', 'confidence': 0.95},
            {'review_id': 'r2', 'theme_name': 'Usability', 'confidence': 0.3},  # Low confidence
            {'review_id': 'r3', 'theme_name': 'Technical Issues', 'confidence': 0.92}
        ]
        mock_client_class.return_value = mock_client
        
        classifier = ThemeClassifier(api_key='test_key')
        classifications, stats = classifier.classify_reviews(self.reviews, self.themes)
        
        # Only high confidence should be classified
        self.assertEqual(stats['classified'], 2)
        self.assertEqual(stats['excluded'], 1)
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_batch_processing(self, mock_client_class):
        """P2-T15: Verify reviews are processed in batches"""
        # Create many reviews to trigger batching
        many_reviews = [
            {'review_id': f'r{i}', 'content': f'Review {i}', 'cleaned_content': f'Review {i}'}
            for i in range(120)
        ]
        
        mock_client = MagicMock()
        # Return classifications for each batch
        def side_effect(reviews, themes):
            return [
                {'review_id': r['review_id'], 'theme_name': 'Technical Issues', 'confidence': 0.9}
                for r in reviews
            ]
        
        mock_client.classify_reviews.side_effect = side_effect
        mock_client_class.return_value = mock_client
        
        classifier = ThemeClassifier(api_key='test_key')
        classifier.batch_size = 50  # Process 50 at a time
        
        classifications, stats = classifier.classify_reviews(many_reviews, self.themes)
        
        # Should have called classify_reviews multiple times (batches)
        self.assertGreater(mock_client.classify_reviews.call_count, 1)
        self.assertEqual(stats['classified'], 120)


class TestThemeClassifierEdgeCases(unittest.TestCase):
    """Additional edge case tests"""
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_empty_reviews_list(self, mock_client_class):
        """Test handling of empty reviews list"""
        mock_client = MagicMock()
        mock_client.classify_reviews.return_value = []
        mock_client_class.return_value = mock_client
        
        themes = [Theme(name="Test", description="Test", sentiment="negative")]
        classifier = ThemeClassifier(api_key='test_key')
        
        classifications, stats = classifier.classify_reviews([], themes)
        
        self.assertEqual(len(classifications), 0)
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['classified'], 0)
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'})
    @patch('app.services.themes.theme_classifier.GroqClient')
    def test_unknown_theme_name_handling(self, mock_client_class):
        """Test handling of unknown theme names from LLM"""
        mock_client = MagicMock()
        mock_client.classify_reviews.return_value = [
            {'review_id': 'r1', 'theme_name': 'Unknown Theme', 'confidence': 0.9}
        ]
        mock_client_class.return_value = mock_client
        
        themes = [Theme(name="Known Theme", description="Test", sentiment="negative")]
        classifier = ThemeClassifier(api_key='test_key')
        
        reviews = [{'review_id': 'r1', 'content': 'Test', 'cleaned_content': 'Test'}]
        classifications, stats = classifier.classify_reviews(reviews, themes)
        
        # Unknown theme should result in exclusion
        self.assertEqual(stats['excluded'], 1)


def run_tests():
    """Run all Phase 2 classifier tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestThemeClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeClassifierEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
