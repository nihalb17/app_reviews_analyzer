from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Theme:
    """Represents a theme extracted from reviews"""
    name: str
    description: str
    sentiment: str  # positive, negative, mixed
    keywords: List[str] = field(default_factory=list)
    review_ids: List[str] = field(default_factory=list)
    theme_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'theme_id': self.theme_id,
            'name': self.name,
            'description': self.description,
            'sentiment': self.sentiment,
            'keywords': self.keywords,
            'review_ids': self.review_ids,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        return cls(
            theme_id=data.get('theme_id', str(uuid.uuid4())),
            name=data['name'],
            description=data['description'],
            sentiment=data['sentiment'],
            keywords=data.get('keywords', []),
            review_ids=data.get('review_ids', []),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        )


@dataclass
class Classification:
    """Represents a review classification"""
    review_id: str
    theme_id: str
    theme_name: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'review_id': self.review_id,
            'theme_id': self.theme_id,
            'theme_name': self.theme_name,
            'confidence': self.confidence
        }


@dataclass
class ThemeExtractionResult:
    """Result of theme extraction"""
    themes: List[Theme]
    role: str
    sample_size: int
    total_reviews: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'themes': [t.to_dict() for t in self.themes],
            'role': self.role,
            'sample_size': self.sample_size,
            'total_reviews': self.total_reviews,
            'created_at': self.created_at.isoformat()
        }
    
    def save_to_file(self, filepath: str):
        """Save result to JSON file"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'ThemeExtractionResult':
        """Load result from JSON file"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            themes=[Theme.from_dict(t) for t in data['themes']],
            role=data['role'],
            sample_size=data['sample_size'],
            total_reviews=data['total_reviews'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
