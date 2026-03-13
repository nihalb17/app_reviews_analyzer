"""
Test Cases for Phase 2: Theme Models
Test IDs: P2-T01 to P2-T05
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
import json
import tempfile
from datetime import datetime

from app.models.theme import Theme, Classification, ThemeExtractionResult


class TestThemeModel(unittest.TestCase):
    """P2-T01: Test Theme model creation and serialization"""
    
    def test_theme_creation(self):
        """P2-T01: Verify Theme object can be created with all fields"""
        theme = Theme(
            name="Technical Glitches",
            description="Users report app crashes and freezes",
            sentiment="negative",
            keywords=["crash", "freeze", "bug"],
            review_ids=["rev1", "rev2"]
        )
        
        self.assertEqual(theme.name, "Technical Glitches")
        self.assertEqual(theme.sentiment, "negative")
        self.assertEqual(len(theme.keywords), 3)
        self.assertEqual(len(theme.review_ids), 2)
        self.assertIsNotNone(theme.theme_id)
        self.assertIsNotNone(theme.created_at)
    
    def test_theme_to_dict(self):
        """P2-T01: Verify Theme converts to dictionary correctly"""
        theme = Theme(
            name="Usability Issues",
            description="Navigation problems",
            sentiment="negative",
            keywords=["navigation", "ui"]
        )
        
        theme_dict = theme.to_dict()
        
        self.assertEqual(theme_dict['name'], "Usability Issues")
        self.assertEqual(theme_dict['sentiment'], "negative")
        self.assertIn('theme_id', theme_dict)
        self.assertIn('created_at', theme_dict)
    
    def test_theme_from_dict(self):
        """P2-T01: Verify Theme can be created from dictionary"""
        data = {
            'theme_id': 'test-123',
            'name': 'Feature Request',
            'description': 'Users want dark mode',
            'sentiment': 'positive',
            'keywords': ['dark mode', 'theme'],
            'review_ids': ['rev1'],
            'created_at': datetime.now().isoformat()
        }
        
        theme = Theme.from_dict(data)
        
        self.assertEqual(theme.theme_id, 'test-123')
        self.assertEqual(theme.name, 'Feature Request')
        self.assertEqual(theme.sentiment, 'positive')


class TestClassificationModel(unittest.TestCase):
    """P2-T02: Test Classification model"""
    
    def test_classification_creation(self):
        """P2-T02: Verify Classification object can be created"""
        classification = Classification(
            review_id="review_001",
            theme_id="theme_001",
            theme_name="Technical Issues",
            confidence=0.95
        )
        
        self.assertEqual(classification.review_id, "review_001")
        self.assertEqual(classification.confidence, 0.95)
    
    def test_classification_to_dict(self):
        """P2-T02: Verify Classification converts to dictionary"""
        classification = Classification(
            review_id="review_002",
            theme_id="theme_002",
            theme_name="Usability",
            confidence=0.87
        )
        
        class_dict = classification.to_dict()
        
        self.assertEqual(class_dict['review_id'], "review_002")
        self.assertEqual(class_dict['confidence'], 0.87)


class TestThemeExtractionResult(unittest.TestCase):
    """P2-T03: Test ThemeExtractionResult model"""
    
    def setUp(self):
        """Set up test data"""
        self.themes = [
            Theme(name="Theme 1", description="Desc 1", sentiment="negative"),
            Theme(name="Theme 2", description="Desc 2", sentiment="positive")
        ]
    
    def test_result_creation(self):
        """P2-T03: Verify ThemeExtractionResult can be created"""
        result = ThemeExtractionResult(
            themes=self.themes,
            role="Product",
            sample_size=100,
            total_reviews=200
        )
        
        self.assertEqual(result.role, "Product")
        self.assertEqual(len(result.themes), 2)
        self.assertEqual(result.sample_size, 100)
        self.assertEqual(result.total_reviews, 200)
    
    def test_result_to_dict(self):
        """P2-T03: Verify result converts to dictionary"""
        result = ThemeExtractionResult(
            themes=self.themes,
            role="Support",
            sample_size=50,
            total_reviews=100
        )
        
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict['role'], "Support")
        self.assertEqual(len(result_dict['themes']), 2)
        self.assertIn('created_at', result_dict)
    
    def test_save_and_load(self):
        """P2-T03: Verify result can be saved and loaded from file"""
        result = ThemeExtractionResult(
            themes=self.themes,
            role="UI/UX",
            sample_size=75,
            total_reviews=150
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save
            result.save_to_file(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # Load
            loaded = ThemeExtractionResult.load_from_file(temp_path)
            
            self.assertEqual(loaded.role, "UI/UX")
            self.assertEqual(len(loaded.themes), 2)
            self.assertEqual(loaded.sample_size, 75)
        finally:
            os.unlink(temp_path)


class TestThemeValidation(unittest.TestCase):
    """P2-T04: Test theme validation rules"""
    
    def test_theme_sentiment_values(self):
        """P2-T04: Verify theme accepts valid sentiment values"""
        valid_sentiments = ["positive", "negative", "mixed"]
        
        for sentiment in valid_sentiments:
            theme = Theme(
                name="Test Theme",
                description="Test description",
                sentiment=sentiment
            )
            self.assertEqual(theme.sentiment, sentiment)
    
    def test_theme_keywords_list(self):
        """P2-T04: Verify theme keywords are stored as list"""
        theme = Theme(
            name="Test",
            description="Test",
            sentiment="positive",
            keywords=["key1", "key2", "key3"]
        )
        
        self.assertIsInstance(theme.keywords, list)
        self.assertEqual(len(theme.keywords), 3)
    
    def test_theme_review_ids_list(self):
        """P2-T04: Verify theme review_ids are stored as list"""
        theme = Theme(
            name="Test",
            description="Test",
            sentiment="negative",
            review_ids=["r1", "r2", "r3", "r4"]
        )
        
        self.assertIsInstance(theme.review_ids, list)
        self.assertEqual(len(theme.review_ids), 4)


class TestClassificationValidation(unittest.TestCase):
    """P2-T05: Test classification validation"""
    
    def test_confidence_range(self):
        """P2-T05: Verify confidence score is within valid range"""
        # Valid confidence values
        for confidence in [0.0, 0.5, 0.95, 1.0]:
            classification = Classification(
                review_id="r1",
                theme_id="t1",
                theme_name="Test",
                confidence=confidence
            )
            self.assertEqual(classification.confidence, confidence)
    
    def test_classification_required_fields(self):
        """P2-T05: Verify all required fields are present"""
        classification = Classification(
            review_id="review_123",
            theme_id="theme_456",
            theme_name="Test Theme",
            confidence=0.85
        )
        
        class_dict = classification.to_dict()
        required_fields = ['review_id', 'theme_id', 'theme_name', 'confidence']
        
        for field in required_fields:
            self.assertIn(field, class_dict)


def run_tests():
    """Run all Phase 2 model tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestThemeModel))
    suite.addTests(loader.loadTestsFromTestCase(TestClassificationModel))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeExtractionResult))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestClassificationValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
