"""
JSON Data Formatter Service

Formats reviews and fee explainer JSON data for Google Doc.
"""

import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime


class JSONDataFormatter:
    """Formats JSON data for Google Doc output"""
    
    def __init__(self):
        pass
    
    def load_reviews_data(self, file_path: Path) -> Optional[Dict]:
        """
        Load reviews data from Phase 3 JSON file
        
        Args:
            file_path: Path to the reviews insights JSON file
            
        Returns:
            Dictionary containing reviews data or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading reviews data: {e}")
            return None
    
    def load_fee_explainer_data(self, file_path: Path) -> Optional[Dict]:
        """
        Load fee explainer data from Phase 3.5 JSON file
        
        Args:
            file_path: Path to the fee explainer JSON file
            
        Returns:
            Dictionary containing fee explainer data or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Return the fee_explainer section if present
                return data.get("fee_explainer", data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading fee explainer data: {e}")
            return None
    
    def format_for_google_doc(
        self,
        reviews_data: Dict,
        fee_explainer_data: Dict,
        role: str = "Product"
    ) -> str:
        """
        Format combined JSON data for Google Doc with proper Markdown formatting
        
        Args:
            reviews_data: Reviews insights data from Phase 3
            fee_explainer_data: Fee explainer data from Phase 3.5
            role: Role for which the reviews data is (Product, Support, UI/UX, Leadership)
            
        Returns:
            Formatted text string for Google Doc with Markdown headings
        """
        formatted_text = []
        
        # Document Header - Heading 1
        formatted_text.append("# Groww Reviews Analysis - Raw Data")
        formatted_text.append("")
        formatted_text.append(f"**Generated:** {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
        formatted_text.append("")
        
        # Section 1: Reviews Data - Heading 2
        formatted_text.append(f"## Section 1: Reviews Data ({role})")
        formatted_text.append("")
        
        if reviews_data:
            formatted_text.append("```json")
            formatted_text.append(json.dumps(reviews_data, indent=2, ensure_ascii=False))
            formatted_text.append("```")
        else:
            formatted_text.append("No reviews data available.")
        
        formatted_text.append("")
        
        # Section 2: Fee Explainer Data - Heading 2
        formatted_text.append("## Section 2: Fee Explainer Data")
        formatted_text.append("")
        
        if fee_explainer_data:
            formatted_text.append("```json")
            formatted_text.append(json.dumps(fee_explainer_data, indent=2, ensure_ascii=False))
            formatted_text.append("```")
        else:
            formatted_text.append("No fee explainer data available.")
        
        formatted_text.append("")
        formatted_text.append("---")
        formatted_text.append("*End of Document*")
        
        return "\n".join(formatted_text)
    
    def get_combined_json(
        self,
        reviews_data: Dict,
        fee_explainer_data: Dict
    ) -> Dict:
        """
        Get combined JSON structure
        
        Args:
            reviews_data: Reviews insights data
            fee_explainer_data: Fee explainer data
            
        Returns:
            Combined dictionary
        """
        return {
            "reviews_data": reviews_data,
            "fee_explainer_data": fee_explainer_data,
            "generated_at": datetime.now().isoformat()
        }
