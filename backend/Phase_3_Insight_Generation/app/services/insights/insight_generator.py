"""
Insight Generation Service

Generates actionable insights from themes using Gemini LLM.
Creates role-based insights and actionable items.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.insight import (
    ActionItem, ThemeInsight, RoleInsights, OnePagerReport
)
from app.services.llm.gemini_client import GeminiClient
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightGenerator:
    """Service for generating insights from themes"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env file")
        
        self.gemini_client = GeminiClient(
            api_key=self.api_key,
            model=settings.GEMINI_MODEL
        )
    
    def generate_role_insights(
        self,
        role: str,
        themes: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
        classifications: List[Dict[str, Any]]
    ) -> RoleInsights:
        """
        Generate insights for a specific role in ONE API call
        
        Args:
            role: Target role (Product, Support, UI/UX, Leadership)
            themes: List of theme dictionaries
            reviews: List of all review dictionaries
            classifications: List of classification dictionaries
        
        Returns:
            RoleInsights object
        """
        logger.info(f"Generating insights for role: {role}")
        
        # Build review lookup by ID
        reviews_by_id = {r['review_id']: r for r in reviews}
        
        # Prepare themes with their reviews for the single API call
        themes_with_reviews = []
        for theme in themes:
            theme_name = theme['name']
            theme_description = theme['description']
            
            # Get reviews for this theme
            theme_review_ids = [
                c['review_id'] for c in classifications
                if c['theme_name'] == theme_name
            ]
            theme_reviews = [reviews_by_id[rid] for rid in theme_review_ids if rid in reviews_by_id]
            
            if not theme_reviews:
                logger.warning(f"No reviews found for theme: {theme_name}")
                continue
            
            themes_with_reviews.append({
                'name': theme_name,
                'description': theme_description,
                'reviews': theme_reviews
            })
        
        if not themes_with_reviews:
            logger.error(f"No themes with reviews found for role: {role}")
            raise ValueError(f"No themes with reviews for role: {role}")
        
        logger.info(f"Calling Gemini API once for {role} with {len(themes_with_reviews)} themes")
        
        # SINGLE API CALL for all themes
        result = self.gemini_client.generate_role_insights(
            role=role,
            themes=themes_with_reviews
        )
        
        # Parse the result into ThemeInsight objects
        theme_insights = []
        for theme_data in result.get('themes', []):
            theme_name = theme_data['theme_name']
            
            actionable_items = [
                ActionItem(
                    action=item['action'],
                    priority=item['priority'],
                    expected_impact=item['expected_impact']
                )
                for item in theme_data.get('actionable_items', [])
            ]
            
            # Get sample reviews for this theme (2-3 reviews)
            sample_reviews = []
            for twr in themes_with_reviews:
                if twr['name'] == theme_name:
                    # Get first 2-3 reviews as samples
                    for review in twr['reviews'][:3]:
                        sample_reviews.append({
                            'review_id': review.get('review_id', ''),
                            'content': review.get('cleaned_content', review.get('content', '')),
                            'rating': review.get('rating', 0)
                        })
                    break
            
            theme_insight = ThemeInsight(
                theme_name=theme_name,
                key_insights=theme_data.get('key_insights', []),
                user_sentiment=theme_data.get('user_sentiment', 'mixed'),
                actionable_items=actionable_items,
                sample_reviews=sample_reviews
            )
            
            theme_insights.append(theme_insight)
        
        role_insights = RoleInsights(
            role=role,
            summary=result.get('summary', ''),
            themes=theme_insights,
            top_issues=result.get('top_issues', []),
            recommendations=result.get('recommendations', [])
        )
        
        logger.info(f"✓ Generated insights for {role}: {len(theme_insights)} themes in 1 API call")
        
        return role_insights
    
    def generate_one_pager_report(
        self,
        roles: List[str],
        themes_by_role: Dict[str, List[Dict[str, Any]]],
        reviews: List[Dict[str, Any]],
        classifications_by_role: Dict[str, List[Dict[str, Any]]],
        period_covered: str
    ) -> OnePagerReport:
        """
        Generate complete 1-pager report for all roles
        
        Args:
            roles: List of roles to generate insights for
            themes_by_role: Dictionary mapping role to themes
            reviews: List of all reviews
            classifications_by_role: Dictionary mapping role to classifications
            period_covered: Period string (e.g., "Last 10 weeks")
        
        Returns:
            OnePagerReport object
        """
        logger.info("="*60)
        logger.info("GENERATING 1-PAGER REPORT")
        logger.info("="*60)
        
        role_insights = {}
        
        # Generate insights for each role
        for role in roles:
            themes = themes_by_role.get(role, [])
            classifications = classifications_by_role.get(role, [])
            
            if not themes:
                logger.warning(f"No themes found for role: {role}")
                continue
            
            role_insight = self.generate_role_insights(
                role=role,
                themes=themes,
                reviews=reviews,
                classifications=classifications
            )
            
            role_insights[role] = role_insight
        
        # Create executive summary from role summaries
        logger.info("Creating executive summary")
        role_summaries = [f"{role}: {insight.summary}" for role, insight in role_insights.items()]
        executive_summary = " ".join(role_summaries)
        
        # Create report
        report = OnePagerReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            period_covered=period_covered,
            total_reviews=len(reviews),
            role_insights=role_insights,
            executive_summary=executive_summary
        )
        
        logger.info("✓ 1-pager report generated successfully")
        
        return report


class InsightGenerationError(Exception):
    """Custom exception for insight generation errors"""
    pass
