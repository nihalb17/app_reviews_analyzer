"""
Fee Explainer Generator Service

Generates bullet points about exit loads using Groq LLM.
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from groq import Groq
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.config import settings


def get_ist_timestamp() -> str:
    """Get current timestamp in IST (Indian Standard Time, UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None).isoformat()


class FeeExplainerGenerator:
    """Generates exit load bullet points using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY_FEE_EXPLAINER)
        self.model = settings.GROQ_MODEL_FEE_EXPLAINER
    
    def generate_bullet_points(self, scraped_data: Dict) -> Dict:
        """
        Generate 3-5 bullet points about exit loads from scraped data
        
        Args:
            scraped_data: Dictionary containing scraped exit load data from funds
            
        Returns:
            Dictionary with bullet points, sources, and timestamp
        """
        # Prepare the prompt
        prompt = self._build_prompt(scraped_data)
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial expert specializing in mutual funds. Generate clear, concise bullet points about exit loads that help users understand fee structures."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and format the result
            return self._format_result(result, scraped_data)
            
        except Exception as e:
            print(f"Error generating bullet points: {e}")
            # Return fallback content if LLM fails
            return self._get_fallback_result(scraped_data)
    
    def _build_prompt(self, scraped_data: Dict) -> str:
        """
        Build the prompt for Groq LLM
        
        Args:
            scraped_data: Scraped exit load data
            
        Returns:
            Formatted prompt string
        """
        # Format fund data for the prompt
        funds_text = []
        for fund in scraped_data.get("funds", []):
            exit_load = fund.get('exit_load', 'N/A')
            fund_info = f"""
Fund: {fund.get('fund_name', 'Unknown')}
Exit Load: {exit_load}
"""
            funds_text.append(fund_info)
        
        # Add static definition
        definition = """
Exit Load Definition:
Exit load is a fee charged when mutual fund units are redeemed before a specified holding period. 
This is typically 1% if redeemed within 1 year of investment.
"""
        
        prompt = f"""Based on the following exit load data from mutual fund schemes, generate 3-5 bullet points that explain key aspects of exit loads.

Exit Load Data:
{definition}

Scheme-Specific Data:
{''.join(funds_text)}

Requirements:
1. Generate 3-5 bullet points (not more than 5)
2. Each bullet point should be concise (1-2 sentences)
3. First 1-2 bullet points should be general exit load information
4. Remaining 2-3 bullet points must be scheme-specific, mentioning the actual fund names and their specific exit load terms
5. Use a neutral, facts-only tone - no recommendations, advice, or comparisons
6. Do not use words like "should", "recommended", "advisable", "better", "consider", "important to", "essential"
7. Simply state the facts about what exit loads exist and how they apply

Output JSON format:
{{
  "bullet_points": [
    {{
      "point": "string - the bullet point text",
      "type": "scheme_specific|general"
    }}
  ],
  "sources": [
    {{
      "name": "string - source name",
      "url": "string - source URL"
    }}
  ],
  "generated_at": "ISO8601 timestamp"
}}

Ensure the response is valid JSON."""
        
        return prompt
    
    def _format_result(self, result: Dict, scraped_data: Dict) -> Dict:
        """
        Format and validate the LLM result
        
        Args:
            result: Parsed JSON result from LLM
            scraped_data: Original scraped data
            
        Returns:
            Formatted result dictionary
        """
        # Ensure bullet_points exists and is a list
        bullet_points = result.get("bullet_points", [])
        if not isinstance(bullet_points, list):
            bullet_points = []
        
        # Limit to 5 bullet points
        bullet_points = bullet_points[:5]
        
        # Ensure each bullet point has required fields
        formatted_bullets = []
        for bp in bullet_points:
            if isinstance(bp, dict):
                formatted_bullets.append({
                    "point": bp.get("point", ""),
                    "type": bp.get("type", "general")
                })
        
        # Build sources from scraped data
        sources = []
        for src in scraped_data.get("sources", []):
            if isinstance(src, dict):
                sources.append({
                    "name": src.get("name", ""),
                    "url": src.get("url", "")
                })
        
        # Also include sources from LLM if provided
        llm_sources = result.get("sources", [])
        if isinstance(llm_sources, list):
            for src in llm_sources:
                if isinstance(src, dict):
                    # Avoid duplicates
                    src_url = src.get("url", "")
                    if not any(s.get("url") == src_url for s in sources):
                        sources.append({
                            "name": src.get("name", ""),
                            "url": src_url
                        })
        
        return {
            "bullet_points": formatted_bullets,
            "sources": sources,
            "last_checked": get_ist_timestamp(),
            "generated_at": get_ist_timestamp()
        }
    
    def _get_fallback_result(self, scraped_data: Dict) -> Dict:
        """
        Generate fallback result if LLM call fails
        
        Args:
            scraped_data: Scraped exit load data
            
        Returns:
            Fallback result dictionary
        """
        # Build sources
        sources = []
        for src in scraped_data.get("sources", []):
            if isinstance(src, dict):
                sources.append({
                    "name": src.get("name", ""),
                    "url": src.get("url", "")
                })
        
        # Build fallback bullets - general first, then scheme-specific
        fallback_bullets = []
        
        # Add general bullet first
        fallback_bullets.append({
            "point": "Exit load is a fee charged when mutual fund units are redeemed before a specified holding period.",
            "type": "general"
        })
        
        # Add scheme-specific bullets from scraped data
        for fund in scraped_data.get("funds", [])[:3]:  # Up to 3 scheme-specific bullets
            fund_name = fund.get('fund_name', 'Unknown')
            exit_load = fund.get('exit_load', '')
            if exit_load and len(exit_load) > 10:
                fallback_bullets.append({
                    "point": f"{fund_name}: {exit_load}",
                    "type": "scheme_specific"
                })
        
        return {
            "bullet_points": fallback_bullets,
            "sources": sources,
            "last_checked": get_ist_timestamp(),
            "generated_at": get_ist_timestamp()
        }
