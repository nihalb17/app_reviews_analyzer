"""
Report Builder Service

Assembles report data from Phase 3 insights for PDF generation.
Includes Fee Explainer data from Phase 3.5 for email body.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

# IST timezone offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)

def get_ist_datetime() -> datetime:
    """Get current datetime in IST timezone"""
    return datetime.now(timezone.utc) + IST_OFFSET

def format_ist_datetime(dt: datetime = None) -> str:
    """Format datetime as DD-MM-YYYY HH:MM in IST"""
    if dt is None:
        dt = get_ist_datetime()
    return dt.strftime("%d-%m-%Y %H:%M")


class ReportBuilder:
    """Builds report data structure from insights"""
    
    # Default path to Fee Explainer data
    DEFAULT_FEE_EXPLAINER_PATH = Path(__file__).parent.parent.parent.parent.parent / "Phase_3_5_Fee_Explainer" / "data" / "fee_explainer.json"
    
    def __init__(self):
        self.report_data = {}
    
    def build_report(
        self,
        role: str,
        insights_file: str,
        reviews_file: Optional[str] = None,
        fee_explainer_file: Optional[str] = None,
        weeks: int = 10
    ) -> Dict[str, Any]:
        """
        Build complete report data from insights file
        
        Args:
            role: Target role (Product, Support, UI/UX, Leadership)
            insights_file: Path to Phase 3 insights JSON file
            reviews_file: Optional path to reviews file for metadata
            fee_explainer_file: Optional path to fee explainer JSON file
            weeks: Number of weeks covered by the analysis
            
        Returns:
            Complete report data dictionary
        """
        # Load insights
        with open(insights_file, 'r', encoding='utf-8') as f:
            insights = json.load(f)
        
        # Load fee explainer data
        fee_explainer_data = self._load_fee_explainer(fee_explainer_file)
        
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
                'analysis_date': format_ist_datetime(),
                'weeks_covered': str(weeks)  # Use passed weeks parameter
            },
            'executive_summary': insights.get('summary', ''),
            'themes': self._process_themes(insights.get('themes', [])),
            'top_issues': insights.get('top_issues', []),
            'recommendations': insights.get('recommendations', []),
            # Fee Explainer data for email body (NOT included in PDF)
            'fee_explainer': fee_explainer_data
        }
        
        return report_data
    
    def _load_fee_explainer(self, fee_explainer_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load fee explainer data from Phase 3.5
        
        Args:
            fee_explainer_file: Optional custom path to fee explainer JSON
            
        Returns:
            Fee explainer data dictionary or empty dict if not found
        """
        # Determine file path
        if fee_explainer_file:
            file_path = Path(fee_explainer_file)
        else:
            file_path = self.DEFAULT_FEE_EXPLAINER_PATH
        
        if not file_path.exists():
            print(f"Warning: Fee explainer file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Return the fee_explainer section
            return data.get('fee_explainer', data)
        except Exception as e:
            print(f"Warning: Could not load fee explainer data: {e}")
            return {}
    
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
