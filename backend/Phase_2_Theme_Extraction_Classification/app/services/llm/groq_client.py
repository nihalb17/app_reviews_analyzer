"""
Groq LLM Client for Theme Extraction and Classification
"""

import json
import time
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq LLM API with fallback support"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", fallback_api_key: str = None):
        self.api_key = api_key
        self.fallback_api_key = fallback_api_key
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2
        self.using_fallback = False
        
        # Import groq here to avoid dependency issues
        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
            # Pre-initialize fallback client if fallback key provided
            self.fallback_client = Groq(api_key=fallback_api_key) if fallback_api_key else None
        except ImportError:
            logger.error("groq package not installed. Run: pip install groq")
            raise
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error (429)"""
        error_str = str(error).lower()
        return '429' in error_str or 'rate_limit' in error_str or 'rate limit' in error_str
    
    def _switch_to_fallback(self):
        """Switch to fallback API key"""
        if self.fallback_client and not self.using_fallback:
            logger.warning("Rate limit hit on primary API key, switching to fallback key")
            self.client = self.fallback_client
            self.using_fallback = True
            return True
        return False
    
    def extract_themes(
        self,
        reviews: List[Dict[str, Any]],
        role: str,
        max_themes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract themes from reviews using Groq LLM
        
        Args:
            reviews: List of review dictionaries
            role: Target role (Product, Support, UI/UX, Leadership)
            max_themes: Maximum number of themes to extract (3-5)
        
        Returns:
            List of theme dictionaries
        """
        # Prepare review samples for the prompt
        review_samples = self._prepare_review_samples(reviews)
        
        # Build role-specific focus areas
        focus_areas = self._get_role_focus_areas(role)
        
        prompt = f"""You are analyzing Groww app reviews for a {role}.

Your task is to identify exactly 3-{max_themes} distinct themes that are most relevant to a {role}.

Focus areas for {role}:
{focus_areas}

Review the following user reviews and identify themes:

{review_samples}

For each theme, provide:
1. Theme name (short, descriptive, 2-4 words)
2. Description (what users are saying about this theme)
3. Sentiment (positive, negative, or mixed)
4. Keywords (3-5 keywords that identify this theme)

Output must be valid JSON in this exact format:
{{
  "themes": [
    {{
      "name": "Theme Name",
      "description": "Description of what users are saying",
      "sentiment": "positive|negative|mixed",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}

Important:
- Identify exactly 3-{max_themes} themes
- Themes must be specific and actionable for a {role}
- Do not include an "Other" category
- Ensure valid JSON output"""

        response = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            themes = result.get('themes', [])
            
            # Validate themes
            if not themes or len(themes) < 3:
                logger.warning(f"Extracted only {len(themes)} themes, expected 3-{max_themes}")
            
            if len(themes) > max_themes:
                logger.warning(f"Extracted {len(themes)} themes, limiting to {max_themes}")
                themes = themes[:max_themes]
            
            return themes
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            raise
    
    def classify_reviews(
        self,
        reviews: List[Dict[str, Any]],
        themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify reviews into themes using Groq LLM
        
        Args:
            reviews: List of review dictionaries
            themes: List of theme dictionaries with 'name' and 'theme_id'
        
        Returns:
            List of classification dictionaries
        """
        # Build theme list for prompt
        theme_list = "\n".join([f"- {t['name']} (ID: {t['theme_id']})" for t in themes])
        
        # Prepare reviews for classification
        review_texts = []
        for i, review in enumerate(reviews):
            review_id = review.get('review_id', f'review_{i}')
            content = review.get('cleaned_content', review.get('content', ''))
            review_texts.append(f"[{review_id}] {content}")
        
        reviews_text = "\n\n".join(review_texts)
        
        prompt = f"""Classify each review into one of the following themes:

{theme_list}

Reviews to classify:

{reviews_text}

For each review, provide:
1. The review ID
2. The theme name that best fits (must be from the list above)
3. Confidence score (0.0 to 1.0)

Output must be valid JSON in this exact format:
{{
  "classifications": [
    {{
      "review_id": "review_id_here",
      "theme_name": "Theme Name",
      "confidence": 0.95
    }}
  ]
}}

Important:
- Only use theme names from the provided list
- If a review doesn't fit any theme well, still assign the closest match
- Do NOT use "Other" as a theme
- Ensure valid JSON output"""

        response = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            classifications = result.get('classifications', [])
            return classifications
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            raise
    
    def _call_llm(self, prompt: str) -> str:
        """Call Groq LLM with retry logic and fallback support"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes app reviews and extracts themes. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                return content
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"Attempt {attempt + 1} failed: {error_str}")
                
                # Check if it's a rate limit error and try fallback
                if self._is_rate_limit_error(e):
                    if self._switch_to_fallback():
                        logger.info("Retrying with fallback API key...")
                        continue  # Retry immediately with fallback
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
        
        raise Exception("All retry attempts failed")
    
    def _prepare_review_samples(self, reviews: List[Dict[str, Any]], max_samples: int = 200) -> str:
        """Prepare review samples for the prompt"""
        # Limit to max_samples for theme extraction
        samples = reviews[:max_samples] if len(reviews) > max_samples else reviews
        
        review_texts = []
        for i, review in enumerate(samples):
            content = review.get('cleaned_content', review.get('content', ''))
            rating = review.get('rating', 'N/A')
            review_texts.append(f"{i+1}. [Rating: {rating}/5] {content}")
        
        return "\n\n".join(review_texts)
    
    def _get_role_focus_areas(self, role: str) -> str:
        """Get focus areas for specific role"""
        focus_areas = {
            "Product": """- Feature gaps and missing functionality
- Usability issues and user experience problems
- Feature requests and enhancement suggestions
- Product performance and reliability""",
            
            "Support": """- Common complaints and pain points
- User frustration with customer service
- Issues users face frequently
- Support response time and quality""",
            
            "UI/UX": """- Navigation issues and user flow problems
- Design feedback and visual appeal
- App interface and interaction issues
- User experience friction points""",
            
            "Leadership": """- Overall app sentiment and satisfaction
- Key metrics and performance indicators
- Strategic issues and opportunities
- Market positioning feedback"""
        }
        
        return focus_areas.get(role, "- General app feedback and issues")


class GroqAPIError(Exception):
    """Custom exception for Groq API errors"""
    pass
