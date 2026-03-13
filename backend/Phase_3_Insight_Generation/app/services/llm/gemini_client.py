"""
Gemini LLM Client for Insight Generation
"""

import json
import time
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini LLM API"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2
        
        # Import google.generativeai here to avoid dependency issues
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai
            self.model_instance = genai.GenerativeModel(model)
        except ImportError:
            logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
            raise
    
    def generate_role_insights(
        self,
        role: str,
        themes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate all insights for a role in ONE API call
        
        Args:
            role: Target role (Product, Support, UI/UX, Leadership)
            themes: List of themes with their reviews, each containing:
                - name: Theme name
                - description: Theme description
                - reviews: List of reviews for this theme
        
        Returns:
            Dictionary with themes insights, summary, top_issues, recommendations
        """
        # Prepare themes data for the prompt
        themes_data = []
        for theme in themes:
            review_samples = self._prepare_review_samples(theme['reviews'], max_samples=20)
            themes_data.append(f"""
THEME: {theme['name']}
DESCRIPTION: {theme['description']}
REVIEWS ({len(theme['reviews'])} total):
{review_samples}
""")
        
        all_themes_text = "\n---\n".join(themes_data)
        
        prompt = f"""You are a senior analyst generating insights for a {role}.

Based on the following themes and user reviews, generate comprehensive insights:

{all_themes_text}

For EACH theme above, provide:
1. Theme name
2. Key insights (3-5 bullet points about what users are saying)
3. User sentiment (highly negative/negative/mixed/positive/highly positive)
4. Actionable items (2-4 items with action, priority high/medium/low, expected impact)

Then provide:
5. Executive Summary (2-3 sentences on main takeaways for {role})
6. Top Issues (3-5 most critical issues across all themes)
7. Recommendations (3-5 specific actions for {role})

Output must be valid JSON in this exact format:
{{
  "themes": [
    {{
      "theme_name": "Theme Name",
      "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
      "user_sentiment": "negative",
      "actionable_items": [
        {{
          "action": "Fix the issue",
          "priority": "high",
          "expected_impact": "Reduce complaints by 80%"
        }}
      ]
    }}
  ],
  "summary": "Executive summary here...",
  "top_issues": ["Issue 1", "Issue 2", "Issue 3"],
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

Important:
- Generate insights for ALL themes provided
- Be specific and actionable
- Focus on insights relevant to a {role}
- Ensure valid JSON output"""

        response = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            raise
    
    def _call_llm(self, prompt: str) -> str:
        """Call Gemini LLM with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.model_instance.generate_content(prompt)
                content = response.text
                
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                return content
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
        
        raise Exception("All retry attempts failed")
    
    def _prepare_review_samples(self, reviews: List[Dict[str, Any]], max_samples: int = 50) -> str:
        """Prepare review samples for the prompt"""
        samples = reviews[:max_samples] if len(reviews) > max_samples else reviews
        
        review_texts = []
        for i, review in enumerate(samples):
            content = review.get('cleaned_content', review.get('content', ''))
            rating = review.get('rating', 'N/A')
            review_texts.append(f"{i+1}. [Rating: {rating}/5] {content}")
        
        return "\n\n".join(review_texts)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors"""
    pass
