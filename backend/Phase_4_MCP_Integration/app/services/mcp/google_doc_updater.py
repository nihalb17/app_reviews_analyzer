"""
Google Doc Updater Service

Orchestrates the process of updating Google Doc with combined JSON data.
"""

from typing import Dict, Optional
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.config import settings
from services.formatter.json_formatter import JSONDataFormatter
from services.mcp.mcp_client import MCPClient


class GoogleDocUpdater:
    """Updates Google Doc with combined reviews and fee explainer data"""
    
    def __init__(self):
        self.formatter = JSONDataFormatter()
        self.mcp_client = MCPClient()
    
    def update_document(
        self,
        role: str = "Product",
        reviews_file: Path = None,
        fee_explainer_file: Path = None
    ) -> Dict:
        """
        Update Google Doc with combined JSON data
        
        Args:
            role: Role for which to load reviews data (Product, Support, UI/UX, Leadership)
            reviews_file: Optional custom path to reviews JSON file
            fee_explainer_file: Optional custom path to fee explainer JSON file
            
        Returns:
            Dictionary with operation result
        """
        # Check if Google Doc is configured
        if not self.mcp_client.is_configured():
            return {
                "success": False,
                "error": "Google Doc ID not configured",
                "message": "Please set GOOGLE_DOC_ID in .env file"
            }
        
        # Determine file paths
        if reviews_file is None:
            reviews_file = settings.PHASE3_DATA_DIR / f"insights_{role.lower().replace('/', '_')}.json"
        
        if fee_explainer_file is None:
            fee_explainer_file = settings.PHASE35_DATA_DIR / "fee_explainer.json"
        
        # Load data
        print(f"Loading reviews data from: {reviews_file}")
        reviews_data = self.formatter.load_reviews_data(reviews_file)
        
        print(f"Loading fee explainer data from: {fee_explainer_file}")
        fee_explainer_data = self.formatter.load_fee_explainer_data(fee_explainer_file)
        
        # Check if data was loaded
        if not reviews_data and not fee_explainer_data:
            return {
                "success": False,
                "error": "No data available",
                "message": "Both reviews and fee explainer data are missing"
            }
        
        # Format content for Google Doc
        formatted_content = self.formatter.format_for_google_doc(
            reviews_data=reviews_data,
            fee_explainer_data=fee_explainer_data,
            role=role
        )
        
        # Append to Google Doc via MCP
        result = self.mcp_client.append_to_document(formatted_content)
        
        # Add additional info to result
        if result.get("success"):
            result["data_summary"] = {
                "role": role,
                "reviews_loaded": reviews_data is not None,
                "fee_explainer_loaded": fee_explainer_data is not None,
                "document_url": self.mcp_client.get_document_url()
            }
        
        return result
    
    def get_document_url(self) -> str:
        """Get the Google Doc URL"""
        return self.mcp_client.get_document_url()
