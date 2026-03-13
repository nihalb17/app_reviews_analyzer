"""
Phase 3 Test Cases - Insight Models (P3-T01 to P3-T04)
"""
import pytest
import json
from datetime import datetime
from app.models.insight import ActionItem, ThemeInsight, RoleInsights, OnePagerReport


class TestActionItem:
    """P3-T01: Test ActionItem model creation and serialization"""
    
    def test_action_item_creation(self):
        """P3-T01-01: Create ActionItem with valid data"""
        action = ActionItem(
            action="Fix critical bug",
            priority="high",
            expected_impact="Reduce errors by 50%"
        )
        assert action.action == "Fix critical bug"
        assert action.priority == "high"
        assert action.expected_impact == "Reduce errors by 50%"
    
    def test_action_item_to_dict(self):
        """P3-T01-02: Convert ActionItem to dictionary"""
        action = ActionItem(
            action="Improve UI",
            priority="medium",
            expected_impact="Better UX"
        )
        data = action.to_dict()
        assert data['action'] == "Improve UI"
        assert data['priority'] == "medium"
        assert data['expected_impact'] == "Better UX"
    
    def test_action_item_from_dict(self):
        """P3-T01-03: Create ActionItem from dictionary"""
        data = {
            'action': 'Test action',
            'priority': 'low',
            'expected_impact': 'Minor improvement'
        }
        action = ActionItem.from_dict(data)
        assert action.action == 'Test action'
        assert action.priority == 'low'


class TestThemeInsight:
    """P3-T02: Test ThemeInsight model"""
    
    def test_theme_insight_creation(self):
        """P3-T02-01: Create ThemeInsight with sample reviews"""
        action_items = [
            ActionItem("Fix bug", "high", "Reduce errors"),
            ActionItem("Add feature", "medium", "Improve UX")
        ]
        
        sample_reviews = [
            {'review_id': 'r1', 'content': 'Great app!', 'rating': 5},
            {'review_id': 'r2', 'content': 'Needs work', 'rating': 3}
        ]
        
        theme = ThemeInsight(
            theme_name="Usability",
            key_insights=["Easy to use", "Clean UI"],
            user_sentiment="positive",
            actionable_items=action_items,
            sample_reviews=sample_reviews
        )
        
        assert theme.theme_name == "Usability"
        assert len(theme.sample_reviews) == 2
        assert theme.sample_reviews[0]['rating'] == 5
    
    def test_theme_insight_to_dict(self):
        """P3-T02-02: Convert ThemeInsight to dictionary"""
        theme = ThemeInsight(
            theme_name="Performance",
            key_insights=["Fast", "Reliable"],
            user_sentiment="positive",
            actionable_items=[],
            sample_reviews=[]
        )
        
        data = theme.to_dict()
        assert data['theme_name'] == "Performance"
        assert 'sample_reviews' in data
    
    def test_theme_insight_from_dict(self):
        """P3-T02-03: Create ThemeInsight from dictionary"""
        data = {
            'theme_name': 'Bugs',
            'key_insights': ['Many crashes'],
            'user_sentiment': 'negative',
            'actionable_items': [],
            'sample_reviews': [
                {'review_id': 'r1', 'content': 'Crashes often', 'rating': 1}
            ]
        }
        
        theme = ThemeInsight.from_dict(data)
        assert theme.theme_name == 'Bugs'
        assert len(theme.sample_reviews) == 1


class TestRoleInsights:
    """P3-T03: Test RoleInsights model"""
    
    def test_role_insights_creation(self):
        """P3-T03-01: Create RoleInsights for Product manager"""
        theme_insights = [
            ThemeInsight(
                theme_name="Technical Issues",
                key_insights=["App crashes"],
                user_sentiment="negative",
                actionable_items=[ActionItem("Fix crash", "high", "Stability")],
                sample_reviews=[]
            )
        ]
        
        role_insights = RoleInsights(
            role="Product",
            summary="App has stability issues",
            themes=theme_insights,
            top_issues=["Crashes", "Slow performance"],
            recommendations=["Fix bugs", "Optimize"]
        )
        
        assert role_insights.role == "Product"
        assert len(role_insights.themes) == 1
    
    def test_role_insights_to_dict(self):
        """P3-T03-02: Convert RoleInsights to dictionary"""
        role_insights = RoleInsights(
            role="Support",
            summary="Support needs improvement",
            themes=[],
            top_issues=["Slow response"],
            recommendations=["Hire more staff"]
        )
        
        data = role_insights.to_dict()
        assert data['role'] == "Support"
        assert data['summary'] == "Support needs improvement"


class TestOnePagerReport:
    """P3-T04: Test OnePagerReport model"""
    
    def test_one_pager_report_creation(self):
        """P3-T04-01: Create OnePagerReport with all roles"""
        product_insights = RoleInsights(
            role="Product",
            summary="Product summary",
            themes=[],
            top_issues=[],
            recommendations=[]
        )
        
        report = OnePagerReport(
            report_id="rpt-001",
            generated_at=datetime.now(),
            period_covered="2024-01-01 to 2024-01-31",
            total_reviews=100,
            role_insights={"Product": product_insights},
            executive_summary="Overall summary of all insights"
        )
        
        assert report.report_id == "rpt-001"
        assert report.total_reviews == 100
        assert report.period_covered == "2024-01-01 to 2024-01-31"
        assert "Product" in report.role_insights
    
    def test_one_pager_report_to_dict(self):
        """P3-T04-02: Convert OnePagerReport to dictionary"""
        report = OnePagerReport(
            report_id="rpt-002",
            generated_at=datetime.now(),
            period_covered="2024-02-01 to 2024-02-28",
            total_reviews=50,
            role_insights={},
            executive_summary="Test summary"
        )
        
        data = report.to_dict()
        assert data['report_id'] == "rpt-002"
        assert data['total_reviews'] == 50
        assert data['period_covered'] == "2024-02-01 to 2024-02-28"
        assert data['executive_summary'] == "Test summary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
