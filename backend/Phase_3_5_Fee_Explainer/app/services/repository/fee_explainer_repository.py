"""
Fee Explainer Repository Service

Handles storage and retrieval of fee explainer data.
"""

import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys


def get_ist_timestamp() -> str:
    """Get current timestamp in IST (Indian Standard Time, UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None).isoformat()

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.config import settings


class FeeExplainerRepository:
    """Repository for fee explainer data storage"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.data_dir / "fee_explainer.json"
        self.scraped_data_file = self.data_dir / "exit_load_scraped_data.json"
    
    def save(self, fee_explainer_data: Dict) -> str:
        """
        Save fee explainer data to JSON file
        
        Args:
            fee_explainer_data: Dictionary containing bullet points, sources, etc.
            
        Returns:
            Path to saved file
        """
        # Add metadata
        data_to_save = {
            "fee_explainer": fee_explainer_data,
            "metadata": {
                "saved_at": get_ist_timestamp(),
                "version": "1.0"
            }
        }
        
        # Write to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        return str(self.output_file)
    
    def load(self) -> Optional[Dict]:
        """
        Load fee explainer data from JSON file
        
        Returns:
            Dictionary containing fee explainer data or None if file doesn't exist
        """
        if not self.output_file.exists():
            return None
        
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("fee_explainer", data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading fee explainer data: {e}")
            return None
    
    def get_raw_data(self) -> Optional[Dict]:
        """
        Get raw data including metadata
        
        Returns:
            Complete data dictionary or None
        """
        if not self.output_file.exists():
            return None
        
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading fee explainer data: {e}")
            return None
    
    def file_exists(self) -> bool:
        """Check if fee explainer file exists"""
        return self.output_file.exists()
    
    def get_file_path(self) -> str:
        """Get the path to the fee explainer JSON file"""
        return str(self.output_file)
    
    def save_scraped_data(self, scraped_data: Dict) -> str:
        """
        Save raw scraped exit load data to JSON file
        
        Args:
            scraped_data: Dictionary containing scraped data from all funds
            
        Returns:
            Path to saved file
        """
        data_to_save = {
            "scraped_data": scraped_data,
            "metadata": {
                "saved_at": get_ist_timestamp(),
                "version": "1.0"
            }
        }
        
        with open(self.scraped_data_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        return str(self.scraped_data_file)
    
    def load_scraped_data(self) -> Optional[Dict]:
        """
        Load raw scraped exit load data from JSON file
        
        Returns:
            Dictionary containing scraped data or None if file doesn't exist
        """
        if not self.scraped_data_file.exists():
            return None
        
        try:
            with open(self.scraped_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("scraped_data", data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading scraped data: {e}")
            return None
    
    def get_scraped_data_file_path(self) -> str:
        """Get the path to the scraped data JSON file"""
        return str(self.scraped_data_file)
