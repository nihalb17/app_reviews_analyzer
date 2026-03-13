"""
Phase 3: Insight Generation Service

Main service that orchestrates insight generation from themes.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.insight import RoleInsights, OnePagerReport
from app.services.insights.insight_generator import InsightGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightService:
    """Main service for Phase 3 - Insight Generation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.generator = InsightGenerator()
    
    def generate_insights_for_role(
        self,
        role: str,
        themes_file: str,
        reviews_file: str
    ) -> Dict[str, Any]:
        """
        Generate insights for a single role
        
        Args:
            role: Target role
            themes_file: Path to themes JSON file from Phase 2
            reviews_file: Path to reviews JSON file from Phase 1
        
        Returns:
            Dictionary with insights and metadata
        """
        logger.info(f"Generating insights for role: {role}")
        
        # Load themes and classifications
        with open(themes_file, 'r', encoding='utf-8') as f:
            themes_data = json.load(f)
        
        themes = themes_data.get('themes', [])
        classifications = themes_data.get('classifications', [])
        
        # Load reviews
        with open(reviews_file, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)
        
        if isinstance(reviews_data, dict) and 'reviews' in reviews_data:
            reviews = reviews_data['reviews']
        elif isinstance(reviews_data, list):
            reviews = reviews_data
        else:
            reviews = []
        
        # Generate insights
        role_insights = self.generator.generate_role_insights(
            role=role,
            themes=themes,
            reviews=reviews,
            classifications=classifications
        )
        
        # Save results
        filepath = self._save_role_insights(role_insights)
        
        results = {
            'status': 'success',
            'role': role,
            'insights': role_insights.to_dict(),
            'saved_to': filepath
        }
        
        return results
    
    def generate_one_pager(
        self,
        roles: List[str],
        themes_files: Dict[str, str],
        reviews_file: str,
        period_covered: str
    ) -> Dict[str, Any]:
        """
        Generate complete 1-pager report for all roles
        
        Args:
            roles: List of roles to include
            themes_files: Dictionary mapping role to themes file path
            reviews_file: Path to reviews file
            period_covered: Period description
        
        Returns:
            Dictionary with report and metadata
        """
        logger.info("="*60)
        logger.info("PHASE 3: INSIGHT GENERATION - 1-PAGER REPORT")
        logger.info("="*60)
        
        # Load data for all roles
        themes_by_role = {}
        classifications_by_role = {}
        
        for role in roles:
            themes_file = themes_files.get(role)
            if not themes_file or not os.path.exists(themes_file):
                logger.warning(f"Themes file not found for role: {role}")
                continue
            
            with open(themes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            themes_by_role[role] = data.get('themes', [])
            classifications_by_role[role] = data.get('classifications', [])
        
        # Load reviews
        with open(reviews_file, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)
        
        if isinstance(reviews_data, dict) and 'reviews' in reviews_data:
            reviews = reviews_data['reviews']
        elif isinstance(reviews_data, list):
            reviews = reviews_data
        else:
            reviews = []
        
        # Generate report
        report = self.generator.generate_one_pager_report(
            roles=roles,
            themes_by_role=themes_by_role,
            reviews=reviews,
            classifications_by_role=classifications_by_role,
            period_covered=period_covered
        )
        
        # Save report
        filepath = self._save_report(report)
        
        results = {
            'status': 'success',
            'report': report.to_dict(),
            'saved_to': filepath
        }
        
        logger.info("✓ Phase 3 complete!")
        
        return results
    
    def _save_role_insights(self, role_insights: RoleInsights) -> str:
        """Save role insights to file (overwrites existing)"""
        # Sanitize role name for filename
        safe_role = role_insights.role.lower().replace('/', '_').replace('\\', '_')
        filename = f"insights_{safe_role}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        role_insights.save_to_file(filepath)
        
        logger.info(f"✓ Insights saved to: {filepath}")
        return filepath
    
    def _save_report(self, report: OnePagerReport) -> str:
        """Save 1-pager report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"onepager_report_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        report.save_to_file(filepath)
        
        logger.info(f"✓ Report saved to: {filepath}")
        return filepath


def run_phase3_for_role(
    role: str,
    themes_file: str,
    reviews_file: str,
    output_dir: str = "data"
) -> Dict[str, Any]:
    """
    Run Phase 3 for a single role
    
    Args:
        role: Target role
        themes_file: Path to themes file
        reviews_file: Path to reviews file
        output_dir: Directory to save results
    
    Returns:
        Results dictionary
    """
    service = InsightService(data_dir=output_dir)
    results = service.generate_insights_for_role(role, themes_file, reviews_file)
    return results


def run_phase3_one_pager(
    roles: List[str],
    themes_files: Dict[str, str],
    reviews_file: str,
    period_covered: str = "Last 10 weeks",
    output_dir: str = "data"
) -> Dict[str, Any]:
    """
    Run Phase 3 to generate complete 1-pager
    
    Args:
        roles: List of roles
        themes_files: Dictionary of role to themes file
        reviews_file: Path to reviews file
        period_covered: Period description
        output_dir: Directory to save results
    
    Returns:
        Results dictionary
    """
    service = InsightService(data_dir=output_dir)
    results = service.generate_one_pager(roles, themes_files, reviews_file, period_covered)
    return results


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python insight_service.py <role> <themes_file> <reviews_file>")
        sys.exit(1)
    
    role = sys.argv[1]
    themes_file = sys.argv[2]
    reviews_file = sys.argv[3]
    
    results = run_phase3_for_role(role, themes_file, reviews_file)
    print(f"\nResults: {json.dumps(results, indent=2)}")
