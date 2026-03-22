"""
Phase 4 Test Cases - PDF Generator (P4-T05 to P4-T10)
"""
import pytest
import os
from datetime import datetime
from pathlib import Path

from app.services.report.pdf_generator import PDFGenerator, PLAYWRIGHT_AVAILABLE
from app.services.report.report_builder import ReportBuilder


class TestPDFGenerator:
    """P4-T05 to P4-T10: Test PDFGenerator"""
    
    @pytest.fixture
    def sample_report_data(self):
        """Create sample report data"""
        return {
            'report_id': 'test-123',
            'generated_at': datetime.now().isoformat(),
            'role': 'Product',
            'company_name': 'Groww',
            'report_title': 'Reviews Insights Report',
            'metadata': {
                'total_reviews': 100,
                'date_range': '2024-01-01 to 2024-01-31',
                'analysis_date': '2024-02-01'
            },
            'executive_summary': 'Test summary of insights',
            'themes': [
                {
                    'name': 'Test Theme',
                    'sentiment': 'positive',
                    'key_insights': ['Insight 1', 'Insight 2'],
                    'sample_reviews': [
                        {'review_id': 'r1', 'content': 'Great app!', 'rating': 5}
                    ],
                    'actionable_items': [
                        {
                            'action': 'Fix bug',
                            'priority': 'high',
                            'expected_impact': 'Better UX'
                        }
                    ]
                }
            ],
            'top_issues': ['Issue 1'],
            'recommendations': ['Recommendation 1']
        }
    
    def test_pdf_generator_initialization(self):
        """P4-T05-01: Initialize PDFGenerator"""
        generator = PDFGenerator()
        assert generator is not None
        assert generator.COLORS['primary'] == '#00D09C'
        assert generator.COLORS['secondary'] == '#5367FF'
    
    def test_groww_branding_colors(self):
        """P4-T05-02: Verify Groww brand colors are defined"""
        generator = PDFGenerator()
        
        assert generator.COLORS['primary'] == '#00D09C'  # Green
        assert generator.COLORS['secondary'] == '#5367FF'  # Blue
        assert generator.COLORS['background'] == '#FFFFFF'
        assert generator.COLORS['text_primary'] == '#1A1A1A'
        assert generator.COLORS['text_secondary'] == '#6C6C6C'
    
    def test_html_generation(self, sample_report_data, tmp_path):
        """P4-T06-01: Generate HTML report"""
        generator = PDFGenerator()
        
        # Override output dir for testing
        generator.output_dir = str(tmp_path)
        
        html_path = generator.generate_html_report(sample_report_data)
        
        assert os.path.exists(html_path)
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'Groww' in content
        assert 'Reviews Insights Report' in content
        assert 'Product' in content
        assert 'Test Theme' in content
    
    def test_html_template_structure(self, sample_report_data, tmp_path):
        """P4-T08-01: Verify template rendering with all variables"""
        generator = PDFGenerator()
        generator.output_dir = str(tmp_path)
        
        html_path = generator.generate_html_report(sample_report_data)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check all sections are present
        assert 'Executive Summary' in content
        assert 'Test summary of insights' in content
        assert 'Key Themes' in content
        assert 'Sample Reviews' in content
        assert 'Actionable Items' in content
        assert 'Strategic Recommendations' in content
    
    def test_large_content_handling(self, tmp_path):
        """P4-T06-02: Handle large content (multi-page)"""
        generator = PDFGenerator()
        generator.output_dir = str(tmp_path)
        
        # Create report with many themes
        large_report = {
            'report_id': 'large-test',
            'generated_at': datetime.now().isoformat(),
            'role': 'Product',
            'company_name': 'Groww',
            'report_title': 'Reviews Insights Report',
            'metadata': {
                'total_reviews': 1000,
                'date_range': '2024-01-01 to 2024-03-31',
                'analysis_date': '2024-04-01'
            },
            'executive_summary': 'Large report summary',
            'themes': [
                {
                    'name': f'Theme {i}',
                    'sentiment': 'positive',
                    'key_insights': [f'Insight {j}' for j in range(5)],
                    'sample_reviews': [
                        {'review_id': f'r{i}', 'content': f'Review content {i}', 'rating': 4}
                    ],
                    'actionable_items': [
                        {
                            'action': f'Action {i}',
                            'priority': 'high',
                            'expected_impact': f'Impact {i}'
                        }
                    ]
                }
                for i in range(10)
            ],
            'top_issues': [f'Issue {i}' for i in range(5)],
            'recommendations': [f'Rec {i}' for i in range(5)]
        }
        
        html_path = generator.generate_html_report(large_report)
        
        assert os.path.exists(html_path)
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain all themes
        assert 'Theme 0' in content
        assert 'Theme 9' in content
    
    def test_mobile_friendly_html(self, sample_report_data, tmp_path):
        """P4-T10-01: Verify mobile-friendly meta tags"""
        generator = PDFGenerator()
        generator.output_dir = str(tmp_path)
        
        html_path = generator.generate_html_report(sample_report_data)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for viewport meta tag (mobile-friendly)
        assert 'viewport' in content
        assert 'width=device-width' in content
    
    def test_file_size_optimization(self, sample_report_data, tmp_path):
        """P4-T09-01: Verify reasonable file size"""
        generator = PDFGenerator()
        generator.output_dir = str(tmp_path)
        
        html_path = generator.generate_html_report(sample_report_data)
        
        # Get file size
        file_size = os.path.getsize(html_path)
        
        # Should be under 1MB for this small report
        assert file_size < 1024 * 1024, f"File size {file_size} bytes is too large"
    
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    def test_pdf_generation(self, sample_report_data, tmp_path):
        """P4-T07-01: Generate PDF (if Playwright available)"""
        generator = PDFGenerator()
        generator.output_dir = str(tmp_path)
        
        pdf_path = generator.generate_pdf(sample_report_data)
        
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith('.pdf')
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        assert file_size > 0, "PDF file is empty"
    
    def test_pdf_generation_without_playwright(self, sample_report_data):
        """P4-T07-02: Handle missing Playwright gracefully"""
        import app.services.report.pdf_generator as pdf_module
        
        # Temporarily disable Playwright
        original_available = pdf_module.PLAYWRIGHT_AVAILABLE
        pdf_module.PLAYWRIGHT_AVAILABLE = False
        
        try:
            generator = PDFGenerator()
            
            with pytest.raises(ImportError) as exc_info:
                generator.generate_pdf(sample_report_data)
            
            assert "Playwright" in str(exc_info.value)
        finally:
            pdf_module.PLAYWRIGHT_AVAILABLE = original_available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
