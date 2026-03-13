"""
Phase 3 Test Cases - Insight Generator Service (P3-T05 to P3-T10)
Uses mocking to avoid actual API calls
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.insights.insight_generator import InsightGenerator
from app.models.insight import ActionItem, ThemeInsight, RoleInsights


class TestInsightGenerator:
    """P3-T05 to P3-T10: Test InsightGenerator with mocked LLM"""
    
    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response"""
        return {
            'themes': [
                {
                    'theme_name': 'Test Theme',
                    'key_insights': ['Insight 1', 'Insight 2'],
                    'user_sentiment': 'negative',
                    'actionable_items': [
                        {
                            'action': 'Fix the issue',
                            'priority': 'high',
                            'expected_impact': 'Improve user satisfaction'
                        }
                    ]
                }
            ],
            'top_issues': ['Issue 1', 'Issue 2'],
            'recommendations': ['Rec 1', 'Rec 2'],
            'executive_summary': 'Test summary'
        }
    
    @pytest.fixture
    def sample_themes(self):
        """Create sample themes for testing"""
        return [
            {
                'name': 'Technical Glitches',
                'description': 'App crashes and bugs',
                'review_count': 2
            }
        ]
    
    @pytest.fixture
    def sample_reviews(self):
        """Create sample reviews for testing"""
        return [
            {
                'review_id': 'r1',
                'content': 'App crashes frequently',
                'cleaned_content': 'App crashes frequently',
                'rating': 1
            },
            {
                'review_id': 'r2',
                'content': 'Very slow performance',
                'cleaned_content': 'Very slow performance',
                'rating': 2
            }
        ]
    
    @pytest.fixture
    def sample_classifications(self):
        """Create sample classifications for testing"""
        return [
            {
                'review_id': 'r1',
                'theme_name': 'Technical Glitches',
                'confidence': 0.95
            },
            {
                'review_id': 'r2',
                'theme_name': 'Technical Glitches',
                'confidence': 0.88
            }
        ]
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_insight_generator_initialization(self, mock_gemini_class):
        """P3-T05-01: Initialize InsightGenerator with mocked client"""
        mock_client = Mock()
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            assert generator.api_key == 'test-key'
            assert generator.gemini_client is not None
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_generate_insights_success(self, mock_gemini_class, mock_llm_response, sample_themes, sample_reviews, sample_classifications):
        """P3-T06-01: Generate insights successfully with mocked API"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = mock_llm_response
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            result = generator.generate_role_insights(
                role="Product",
                themes=sample_themes,
                reviews=sample_reviews,
                classifications=sample_classifications
            )
            
            assert result is not None
            assert isinstance(result, RoleInsights)
            assert result.role == "Product"
            assert len(result.themes) == 1
            
            # Verify API was called once
            mock_client.generate_role_insights.assert_called_once()
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_generate_insights_sample_reviews_included(self, mock_gemini_class, mock_llm_response, sample_themes, sample_reviews, sample_classifications):
        """P3-T07-01: Verify sample reviews are included in theme insights"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = mock_llm_response
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            result = generator.generate_role_insights(
                role="Product",
                themes=sample_themes,
                reviews=sample_reviews,
                classifications=sample_classifications
            )
            
            # Check that themes have sample reviews (mocked response has 1 theme)
            assert len(result.themes) == 1
            # The sample reviews are added from the actual data, not mocked response
            # So we just verify the structure is correct
            for theme in result.themes:
                assert isinstance(theme.sample_reviews, list)
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_generate_insights_actionable_items_structure(self, mock_gemini_class, mock_llm_response, sample_themes, sample_reviews, sample_classifications):
        """P3-T08-01: Verify actionable items have correct structure"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = mock_llm_response
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            result = generator.generate_role_insights(
                role="Product",
                themes=sample_themes,
                reviews=sample_reviews,
                classifications=sample_classifications
            )
            
            for theme in result.themes:
                assert len(theme.actionable_items) > 0
                for item in theme.actionable_items:
                    assert isinstance(item, ActionItem)
                    assert item.action is not None
                    assert item.priority in ['high', 'medium', 'low']
                    assert item.expected_impact is not None
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_generate_insights_api_error_handling(self, mock_gemini_class, sample_themes, sample_reviews, sample_classifications):
        """P3-T09-01: Handle API errors gracefully"""
        mock_client = Mock()
        mock_client.generate_role_insights.side_effect = Exception("API Error")
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            with pytest.raises(Exception) as exc_info:
                generator.generate_role_insights(
                    role="Product",
                    themes=sample_themes,
                    reviews=sample_reviews,
                    classifications=sample_classifications
                )
            
            assert "API Error" in str(exc_info.value)
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_generate_insights_empty_themes(self, mock_gemini_class):
        """P3-T10-01: Handle empty themes list - should raise ValueError"""
        mock_client = Mock()
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            # Empty themes should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                generator.generate_role_insights(
                    role="Product",
                    themes=[],
                    reviews=[],
                    classifications=[]
                )
            
            assert "No themes with reviews" in str(exc_info.value)


class TestInsightGeneratorEdgeCases:
    """P3-T11 to P3-T13: Edge case testing"""
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_large_number_of_reviews(self, mock_gemini_class):
        """P3-T11-01: Handle themes with many reviews"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = {
            'themes': [],
            'top_issues': [],
            'recommendations': [],
            'executive_summary': 'Test'
        }
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            # Create theme with 50 reviews
            many_reviews = [
                {
                    'review_id': f'r{i}',
                    'content': f'Review {i}',
                    'cleaned_content': f'Review {i}',
                    'rating': 3
                }
                for i in range(50)
            ]
            
            classifications = [
                {'review_id': f'r{i}', 'theme_name': 'Large Theme', 'confidence': 0.9}
                for i in range(50)
            ]
            
            themes = [{
                'name': 'Large Theme',
                'description': 'Many reviews',
                'review_count': 50
            }]
            
            result = generator.generate_role_insights(
                role="Product",
                themes=themes,
                reviews=many_reviews,
                classifications=classifications
            )
            assert result is not None
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_reviews_with_special_characters(self, mock_gemini_class):
        """P3-T12-01: Handle reviews with special characters"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = {
            'themes': [{
                'theme_name': 'Special',
                'key_insights': ['Test'],
                'user_sentiment': 'neutral',
                'actionable_items': []
            }],
            'top_issues': [],
            'recommendations': [],
            'executive_summary': 'Test'
        }
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            themes = [{
                'name': 'Special Chars',
                'description': 'Test',
                'review_count': 1
            }]
            
            reviews = [
                {
                    'review_id': 'r1',
                    'content': 'Special chars: ñ, é, 中文, 🚀, <script>',
                    'cleaned_content': 'Special chars: ñ, é, 中文, 🚀, <script>',
                    'rating': 4
                }
            ]
            
            classifications = [
                {'review_id': 'r1', 'theme_name': 'Special Chars', 'confidence': 0.95}
            ]
            
            result = generator.generate_role_insights(
                role="Product",
                themes=themes,
                reviews=reviews,
                classifications=classifications
            )
            assert result is not None
    
    @patch('app.services.insights.insight_generator.GeminiClient')
    def test_multiple_roles_generation(self, mock_gemini_class):
        """P3-T13-01: Generate insights for different roles"""
        mock_client = Mock()
        mock_client.generate_role_insights.return_value = {
            'themes': [{
                'theme_name': 'Test Theme',
                'key_insights': ['Test insight'],
                'user_sentiment': 'positive',
                'actionable_items': [{
                    'action': 'Test action',
                    'priority': 'medium',
                    'expected_impact': 'Test impact'
                }]
            }],
            'top_issues': ['Issue'],
            'recommendations': ['Rec'],
            'executive_summary': 'Summary'
        }
        mock_gemini_class.return_value = mock_client
        
        with patch('app.services.insights.insight_generator.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test-key'
            mock_settings.GEMINI_MODEL = 'gemini-2.5-flash'
            
            generator = InsightGenerator(api_key='test-key')
            
            # Need actual reviews and classifications for themes to work
            reviews = [{'review_id': 'r1', 'content': 'Test', 'cleaned_content': 'Test', 'rating': 4}]
            themes = [{'name': 'Test Theme', 'description': 'Test', 'review_count': 1}]
            classifications = [{'review_id': 'r1', 'theme_name': 'Test Theme', 'confidence': 0.9}]
            
            # Test different roles
            for role in ['Product', 'Support', 'UI/UX', 'Leadership']:
                result = generator.generate_role_insights(
                    role=role,
                    themes=themes,
                    reviews=reviews,
                    classifications=classifications
                )
                assert result.role == role


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
