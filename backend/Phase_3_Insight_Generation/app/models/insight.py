from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ActionItem:
    """Represents an actionable item derived from insights"""
    action: str
    priority: str  # high, medium, low
    expected_impact: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'priority': self.priority,
            'expected_impact': self.expected_impact
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        return cls(
            action=data['action'],
            priority=data['priority'],
            expected_impact=data['expected_impact']
        )


@dataclass
class ThemeInsight:
    """Represents insights for a specific theme"""
    theme_name: str
    key_insights: List[str]
    user_sentiment: str
    actionable_items: List[ActionItem]
    sample_reviews: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'theme_name': self.theme_name,
            'key_insights': self.key_insights,
            'user_sentiment': self.user_sentiment,
            'actionable_items': [a.to_dict() for a in self.actionable_items],
            'sample_reviews': self.sample_reviews
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeInsight':
        return cls(
            theme_name=data['theme_name'],
            key_insights=data['key_insights'],
            user_sentiment=data['user_sentiment'],
            actionable_items=[ActionItem.from_dict(a) for a in data.get('actionable_items', [])],
            sample_reviews=data.get('sample_reviews', [])
        )


@dataclass
class RoleInsights:
    """Represents all insights for a specific role"""
    role: str
    summary: str
    themes: List[ThemeInsight]
    top_issues: List[str]
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_id': self.insight_id,
            'role': self.role,
            'summary': self.summary,
            'themes': [t.to_dict() for t in self.themes],
            'top_issues': self.top_issues,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat()
        }
    
    def save_to_file(self, filepath: str):
        """Save insights to JSON file"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'RoleInsights':
        """Load insights from JSON file"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            insight_id=data.get('insight_id', str(uuid.uuid4())),
            role=data['role'],
            summary=data['summary'],
            themes=[ThemeInsight.from_dict(t) for t in data['themes']],
            top_issues=data['top_issues'],
            recommendations=data['recommendations'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class OnePagerReport:
    """Represents the final 1-pager report with all role insights"""
    report_id: str
    generated_at: datetime
    period_covered: str
    total_reviews: int
    role_insights: Dict[str, RoleInsights]
    executive_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'period_covered': self.period_covered,
            'total_reviews': self.total_reviews,
            'role_insights': {role: insight.to_dict() for role, insight in self.role_insights.items()},
            'executive_summary': self.executive_summary
        }
    
    def save_to_file(self, filepath: str):
        """Save report to JSON file"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'OnePagerReport':
        """Load report from JSON file"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            report_id=data['report_id'],
            generated_at=datetime.fromisoformat(data['generated_at']),
            period_covered=data['period_covered'],
            total_reviews=data['total_reviews'],
            role_insights={
                role: RoleInsights.from_dict(insight_data)
                for role, insight_data in data['role_insights'].items()
            },
            executive_summary=data['executive_summary']
        )
