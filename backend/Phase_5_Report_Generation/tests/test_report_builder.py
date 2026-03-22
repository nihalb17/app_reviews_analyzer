"""
Phase 4 Test Cases - Report Builder (P4-T01 to P4-T04)
"""
import pytest
import json
import os
from datetime import datetime
from pathlib import Path

from app.services.report.report_builder import ReportBuilder


class TestReportBuilder:
    """P4-T01 to P4-T04: Test ReportBuilder"""
    
    @pytest.fixture
    def sample_insights(self, tmp_path):
        """Create sample insights file"""
        insights = {
            'insight_id': 'test-123',
            'created_at': datetime.now().isoformat(),
            'role': 'Product',
            'summary': 'Test executive summary',
            'themes': [
                {
                    'theme_name': 'Test Theme',
                    'user_sentiment': 'positive',
                    'key_insights': ['Insight 1', 'Insight 2'],
                    'sample_reviews': [
                        {'review_id': 'r1', 'content': 'Great app!', 'rating': 5}
                    ],
                    'actionable_items': [
                        {
                            'action': 'Fix bug',
                            'priority': 'high',
                            'expected_impact': 'Better UX'
                        }
                    ]
                }
            ],
            'top_issues': ['Issue 1'],
            'recommendations': ['Rec 1']
        }
        
        file_path = tmp_path / "test_insights.json"
        with open(file_path, 'w') as f:
            json.dump(insights, f)
        
        return str(file_path)
    
    @pytest.fixture
    def sample_reviews(self, tmp_path):
        """Create sample reviews file"""
        reviews = [
            {
                'review_id': 'r1',
                'content': 'Great app!',
                'review_date': '2024-01-15T10:00:00',
                'rating': 5
            },
            {
                'review_id': 'r2',
                'content': 'Good but buggy',
                'review_date': '2024-01-20T10:00:00',
                'rating': 3
            }
        ]
        
        file_path = tmp_path / "test_reviews.json"
        with open(file_path, 'w') as f:
            json.dump(reviews, f)
        
        return str(file_path)
    
    def test_report_builder_initialization(self):
        """P4-T01-01: Initialize ReportBuilder"""
        builder = ReportBuilder()
        assert builder is not None
    
    def test_build_report_product_role(self, sample_insights, sample_reviews):
        """P4-T01-02: Build report for Product role"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='Product',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        assert report['role'] == 'Product'
        assert report['company_name'] == 'Groww'
        assert report['report_title'] == 'Reviews Insights Report'
        assert 'executive_summary' in report
        assert 'themes' in report
        assert len(report['themes']) == 1
    
    def test_build_report_support_role(self, sample_insights, sample_reviews):
        """P4-T02-01: Build report for Support role"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='Support',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        assert report['role'] == 'Support'
        assert len(report['themes']) > 0
    
    def test_build_report_ui_ux_role(self, sample_insights, sample_reviews):
        """P4-T03-01: Build report for UI/UX role"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='UI/UX',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        assert report['role'] == 'UI/UX'
    
    def test_build_report_leadership_role(self, sample_insights, sample_reviews):
        """P4-T04-01: Build report for Leadership role"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='Leadership',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        assert report['role'] == 'Leadership'
    
    def test_report_metadata_extraction(self, sample_insights, sample_reviews):
        """P4-T01-03: Verify metadata extraction from reviews"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='Product',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        assert report['metadata']['total_reviews'] == 2
        assert '2024-01-15' in report['metadata']['date_range']
        assert '2024-01-20' in report['metadata']['date_range']
    
    def test_themes_processing(self, sample_insights, sample_reviews):
        """P4-T01-04: Verify themes are processed correctly"""
        builder = ReportBuilder()
        report = builder.build_report(
            role='Product',
            insights_file=sample_insights,
            reviews_file=sample_reviews
        )
        
        theme = report['themes'][0]
        assert theme['name'] == 'Test Theme'
        assert theme['sentiment'] == 'positive'
        assert len(theme['sample_reviews']) == 1
        assert len(theme['actionable_items']) == 1
    
    def test_role_badge(self):
        """P4-T01-05: Test role badge generation"""
        builder = ReportBuilder()
        
        assert builder.get_role_badge('Product') == 'Product Team'
        assert builder.get_role_badge('Support') == 'Support Team'
        assert builder.get_role_badge('UI/UX') == 'Design Team'
        assert builder.get_role_badge('Leadership') == 'Leadership'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
