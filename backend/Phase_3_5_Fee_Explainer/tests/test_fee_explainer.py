"""
Tests for Phase 3.5 Fee Explainer Generation
"""

import unittest
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.scraper import ExitLoadScraper
from app.services.llm import FeeExplainerGenerator
from app.services.repository import FeeExplainerRepository


class TestExitLoadScraper(unittest.TestCase):
    """Test cases for ExitLoadScraper"""
    
    def setUp(self):
        self.scraper = ExitLoadScraper()
    
    def test_fund_urls_configured(self):
        """Test that fund URLs are configured"""
        self.assertEqual(len(self.scraper.FUND_URLS), 3)
        self.assertIn("Axis Flexi Cap Fund", self.scraper.FUND_URLS)
        self.assertIn("Nippon India Large Cap Fund", self.scraper.FUND_URLS)
        self.assertIn("ICICI Prudential Indo Asia Equity Fund", self.scraper.FUND_URLS)
    
    def test_static_definition_source(self):
        """Test static definition source"""
        definition = self.scraper.get_static_exit_load_definition()
        self.assertIn("definition", definition)
        self.assertIn("source", definition)
        self.assertEqual(definition["source"]["name"], "Mirae Asset - Exit Load Guide")
    
    @patch('app.services.scraper.exit_load_scraper.requests.Session.get')
    def test_scrape_fund_page_success(self, mock_get):
        """Test successful fund page scraping"""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <body>
                <div>Exit Load: 1% if redeemed within 365 days</div>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = self.scraper._scrape_fund_page("Test Fund", "https://test.com")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["fund_name"], "Test Fund")
        self.assertIn("exit_load", result)
    
    @patch('app.services.scraper.exit_load_scraper.requests.Session.get')
    def test_scrape_fund_page_failure(self, mock_get):
        """Test fund page scraping failure handling"""
        mock_get.side_effect = Exception("Connection error")
        
        result = self.scraper._scrape_fund_page("Test Fund", "https://test.com")
        
        self.assertIsNone(result)


class TestFeeExplainerGenerator(unittest.TestCase):
    """Test cases for FeeExplainerGenerator"""
    
    @patch('app.services.llm.fee_explainer_generator.Groq')
    def setUp(self, mock_groq):
        self.generator = FeeExplainerGenerator()
    
    def test_build_prompt(self):
        """Test prompt building"""
        scraped_data = {
            "funds": [
                {
                    "fund_name": "Test Fund",
                    "exit_load": {
                        "details": "1% within 1 year",
                        "percentage": "1%",
                        "holding_period": "1 year"
                    }
                }
            ],
            "sources": [{"name": "Test", "url": "https://test.com"}]
        }
        
        prompt = self.generator._build_prompt(scraped_data)
        
        self.assertIn("Exit Load Data:", prompt)
        self.assertIn("Test Fund", prompt)
        self.assertIn("Output JSON format:", prompt)
    
    def test_format_result(self):
        """Test result formatting"""
        llm_result = {
            "bullet_points": [
                {"point": "Test point 1", "type": "general"},
                {"point": "Test point 2", "type": "scheme_specific"}
            ],
            "sources": [{"name": "Test Source", "url": "https://test.com"}]
        }
        
        scraped_data = {
            "sources": [{"name": "Scraped Source", "url": "https://scraped.com"}]
        }
        
        result = self.generator._format_result(llm_result, scraped_data)
        
        self.assertEqual(len(result["bullet_points"]), 2)
        self.assertIn("last_checked", result)
        self.assertIn("generated_at", result)
    
    def test_get_fallback_result(self):
        """Test fallback result generation"""
        scraped_data = {"sources": []}
        
        result = self.generator._get_fallback_result(scraped_data)
        
        self.assertEqual(len(result["bullet_points"]), 3)
        self.assertIn("sources", result)
        self.assertIn("last_checked", result)


class TestFeeExplainerRepository(unittest.TestCase):
    """Test cases for FeeExplainerRepository"""
    
    def setUp(self):
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        self.repository = FeeExplainerRepository(data_dir=self.test_dir)
    
    def tearDown(self):
        # Clean up test files
        if self.repository.output_file.exists():
            self.repository.output_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()
    
    def test_save_and_load(self):
        """Test saving and loading data"""
        test_data = {
            "bullet_points": [{"point": "Test", "type": "general"}],
            "sources": [{"name": "Test", "url": "https://test.com"}],
            "last_checked": datetime.now().isoformat()
        }
        
        # Save
        file_path = self.repository.save(test_data)
        self.assertTrue(Path(file_path).exists())
        
        # Load
        loaded_data = self.repository.load()
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data["bullet_points"]), 1)
    
    def test_load_nonexistent_file(self):
        """Test loading when file doesn't exist"""
        result = self.repository.load()
        self.assertIsNone(result)
    
    def test_file_exists(self):
        """Test file existence check"""
        self.assertFalse(self.repository.file_exists())
        
        # Create file
        test_data = {"bullet_points": [], "sources": []}
        self.repository.save(test_data)
        
        self.assertTrue(self.repository.file_exists())


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline"""
    
    @patch('app.services.scraper.exit_load_scraper.requests.Session.get')
    @patch('app.services.llm.fee_explainer_generator.Groq')
    def test_full_pipeline(self, mock_groq, mock_get):
        """Test the complete pipeline"""
        # Mock scraper response
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <body>
                <div>Exit Load: 1% if redeemed within 365 days</div>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock Groq response
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = json.dumps({
            "bullet_points": [
                {"point": "Test bullet point", "type": "general"}
            ],
            "sources": [{"name": "Test", "url": "https://test.com"}]
        })
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        # Run pipeline
        from run_phase35 import run_fee_explainer_generation
        
        test_dir = Path(__file__).parent / "test_output"
        test_dir.mkdir(exist_ok=True)
        
        try:
            result = run_fee_explainer_generation(output_dir=test_dir)
            
            self.assertTrue(result["success"])
            self.assertIn("file_path", result)
            self.assertIn("data", result)
            
        finally:
            # Cleanup
            output_file = test_dir / "fee_explainer.json"
            if output_file.exists():
                output_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()


if __name__ == '__main__':
    unittest.main()
