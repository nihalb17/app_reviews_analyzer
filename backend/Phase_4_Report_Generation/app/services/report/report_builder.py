"""
Report Builder Service

Assembles report data from Phase 3 insights for PDF generation.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class ReportBuilder:
    """Builds report data structure from insights"""
    
    def __init__(self):
        self.report_data = {}
    
    def build_report(
        self,
        role: str,
        insights_file: str,
        reviews_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete report data from insights file
        
        Args:
            role: Target role (Product, Support, UI/UX, Leadership)
            insights_file: Path to Phase 3 insights JSON file
            reviews_file: Optional path to reviews file for metadata
            
        Returns:
            Complete report data dictionary
        """
        # Load insights
        with open(insights_file, 'r', encoding='utf-8') as f:
            insights = json.load(f)
        
        # Get metadata from reviews if available
        metadata = self._extract_metadata(reviews_file)
        
        # Build report structure
        report_data = {
            'report_id': insights.get('insight_id', 'unknown'),
            'generated_at': insights.get('created_at', datetime.now().isoformat()),
            'role': role,
            'company_name': 'Groww',
            'report_title': 'Reviews Insights Report',
            'metadata': {
                'total_reviews': metadata.get('total_reviews', 0),
                'date_range': metadata.get('date_range', 'N/A'),
                'analysis_date': datetime.now().strftime('%d-%m-%Y %H:%M'),
                'weeks_covered': metadata.get('weeks_covered', '10')
            },
            'executive_summary': insights.get('summary', ''),
            'themes': self._process_themes(insights.get('themes', [])),
            'top_issues': insights.get('top_issues', []),
            'recommendations': insights.get('recommendations', [])
        }
        
        return report_data
    
    def _extract_metadata(self, reviews_file: Optional[str]) -> Dict[str, Any]:
        """Extract metadata from reviews file"""
        metadata = {
            'total_reviews': 0,
            'date_range': 'N/A',
            'weeks_covered': '10'
        }
        
        if reviews_file and Path(reviews_file).exists():
            try:
                with open(reviews_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both list and dict formats
                if isinstance(data, dict) and 'reviews' in data:
                    reviews = data['reviews']
                    # Use metadata.count if available (from Phase 1 structure)
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        metadata['total_reviews'] = data['metadata'].get('count', len(reviews))
                    else:
                        metadata['total_reviews'] = len(reviews)
                elif isinstance(data, list):
                    reviews = data
                    metadata['total_reviews'] = len(reviews)
                else:
                    reviews = []
                    
                    # Extract date range if dates available
                    dates = []
                    for review in reviews:
                        if isinstance(review, dict):
                            # Try different date field names
                            date_field = review.get('review_date') or review.get('at') or review.get('date')
                            if date_field:
                                dates.append(str(date_field))
                    
                    if dates:
                        dates.sort()
                        # Format dates nicely
                        start_date = dates[0][:10] if len(dates[0]) >= 10 else dates[0]
                        end_date = dates[-1][:10] if len(dates[-1]) >= 10 else dates[-1]
                        metadata['date_range'] = f"{start_date} to {end_date}"
                        
            except Exception as e:
                print(f"Warning: Could not extract metadata: {e}")
        
        return metadata
    
    def _process_themes(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process themes for report display - limit to 1-2 reviews, 1 insight, 1 action item"""
        processed_themes = []
        
        for theme in themes:
            processed_theme = {
                'name': theme.get('theme_name', 'Unknown'),
                'sentiment': theme.get('user_sentiment', 'neutral'),
                'key_insights': theme.get('key_insights', [])[:1],  # Only 1 key insight
                'sample_reviews': theme.get('sample_reviews', [])[:2],  # Max 2 reviews
                'actionable_items': theme.get('actionable_items', [])[:1]  # Only 1 actionable item
            }
            processed_themes.append(processed_theme)
        
        return processed_themes
    
    def get_role_badge(self, role: str) -> str:
        """Get role badge text"""
        badges = {
            'Product': 'Product Team',
            'Support': 'Support Team',
            'UI/UX': 'Design Team',
            'Leadership': 'Leadership'
        }
        return badges.get(role, role)
