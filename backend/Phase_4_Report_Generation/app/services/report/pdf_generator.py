"""
PDF Generator Service

Generates PDF reports with Groww branding using Playwright.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

# Try to import Playwright for PDF generation
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not available.")

from app.core.config import settings


class PDFGenerator:
    """Generates PDF reports with Groww branding"""
    
    # Groww Brand Colors
    COLORS = {
        'primary': '#00D09C',
        'secondary': '#5367FF',
        'background': '#FFFFFF',
        'text_primary': '#1A1A1A',
        'text_secondary': '#6C6C6C',
        'border': '#E5E5E5',
        'success': '#00D09C',
        'warning': '#FFB800',
        'danger': '#FF5252'
    }
    
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader(settings.TEMPLATES_DIR)
        )
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists"""
        Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        output_filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate PDF from report data using Playwright
        
        Args:
            report_data: Report data dictionary from ReportBuilder
            output_filename: Optional custom filename
            output_dir: Optional custom output directory
            
        Returns:
            Path to generated PDF file
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for PDF generation. "
                "Install with: pip install playwright"
            )
        
        # Generate HTML content first
        html_content = self._generate_html(report_data)
        
        # Generate filename (overwrites existing)
        if not output_filename:
            role = report_data.get('role', 'report').lower()
            # Sanitize role name for filename
            safe_role = role.replace('/', '_').replace('\\', '_')
            output_filename = f"groww_insights_{safe_role}.pdf"
        
        dest_dir = output_dir or settings.OUTPUT_DIR
        os.makedirs(dest_dir, exist_ok=True)
        output_path = os.path.join(dest_dir, output_filename)
        
        # Generate PDF using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            page.pdf(
                path=output_path,
                format='A4',
                margin={
                    'top': '20mm',
                    'right': '20mm',
                    'bottom': '20mm',
                    'left': '20mm'
                },
                print_background=True
            )
            browser.close()
        
        return output_path
    
    def generate_html_report(
        self,
        report_data: Dict[str, Any],
        output_filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate HTML report (for email body or preview)
        
        Args:
            report_data: Report data dictionary
            output_filename: Optional custom filename
            output_dir: Optional custom output directory
            
        Returns:
            Path to generated HTML file
        """
        html_content = self._generate_email_html(report_data)
        
        if not output_filename:
            role = report_data.get('role', 'report').lower()
            # Sanitize role name for filename
            safe_role = role.replace('/', '_').replace('\\', '_')
            output_filename = f"groww_insights_{safe_role}.html"
        
        dest_dir = output_dir or settings.OUTPUT_DIR
        os.makedirs(dest_dir, exist_ok=True)
        output_path = os.path.join(dest_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content from report data"""
        # Use inline template if file not found
        try:
            template = self.template_env.get_template('report_template.html')
        except:
            template = Template(self._get_default_template())
        
        # Add colors to report data
        report_data['colors'] = self.COLORS
        
        return template.render(**report_data)
    
    def _get_default_template(self) -> str:
        """Get default HTML template"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} - {{ report_title }}</title>
    <style>
        @page {
            size: A4;
            margin: 20mm;
            @bottom-center {
                content: "Confidential - {{ company_name }} | Page " counter(page);
                font-size: 9pt;
                color: #6C6C6C;
            }
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: {{ colors.text_primary }};
            background: {{ colors.background }};
            max-width: 600px;
            margin: 0 auto;
            padding: 15px;
        }
        
        .header {
            background: white;
            color: {{ colors.text_primary }};
            padding: 10px 0;
            margin-bottom: 10px;
            text-align: left;
            border-bottom: 1px solid #E0E0E0;
        }

        .header-brand {
            font-size: 20pt;
            font-weight: 700;
            color: {{ colors.primary }};
            margin: 0 0 4px 0;
        }

        .header-title {
            font-size: 12pt;
            font-weight: 500;
            color: {{ colors.text_primary }};
            margin: 0 0 8px 0;
        }

        .header-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 8pt;
            color: {{ colors.text_secondary }};
            margin-top: 8px;
        }

        .header-stats {
            display: flex;
        }

        .stat-item {
            color: {{ colors.text_primary }};
            font-weight: 500;
            padding: 0 12px;
            border-right: 1px solid #E0E0E0;
        }

        .stat-item:first-child {
            padding-left: 0;
        }

        .stat-item:last-child {
            border-right: none;
            padding-right: 0;
        }

        .section {
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 14pt;
            font-weight: 700;
            color: {{ colors.primary }};
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid {{ colors.primary }};
        }
        
        .executive-summary {
            background: #F0FDF9;
            border-left: 4px solid {{ colors.primary }};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: {{ colors.text_primary }};
            font-size: 10pt;
            line-height: 1.5;
        }

        .theme {
            background: white;
            border: 1px solid {{ colors.border }};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .theme-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            gap: 15px;
        }

        .theme-name {
            font-size: 12pt;
            font-weight: 700;
            color: {{ colors.text_primary }};
        }
        
        .sentiment-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .sentiment-highly-positive {
            background: #D1FAE5;
            color: #065F46;
        }

        .sentiment-positive {
            background: #D1FAE5;
            color: #065F46;
        }

        .sentiment-highly-negative {
            background: #FEE2E2;
            color: #991B1B;
        }

        .sentiment-negative {
            background: #FEE2E2;
            color: #991B1B;
        }

        .sentiment-mixed {
            background: #FEF3C7;
            color: #92400E;
        }

        .sentiment-neutral {
            background: #E5E7EB;
            color: #374151;
        }
        
        .key-insights {
            margin-bottom: 10px;
        }

        .key-insights h4 {
            font-size: 8pt;
            color: {{ colors.text_secondary }};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .key-insights ul {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }

        .key-insights li {
            padding: 3px 0;
            padding-left: 16px;
            position: relative;
            font-size: 9.5pt;
            line-height: 1.4;
        }

        .key-insights li:before {
            content: "▸";
            color: {{ colors.primary }};
            position: absolute;
            left: 0;
            font-weight: bold;
        }

        .sample-reviews {
            background: #F8F9FA;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 10px;
        }

        .sample-reviews h4 {
            font-size: 8pt;
            color: {{ colors.text_secondary }};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .review {
            padding: 6px 8px;
            background: white;
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 9pt;
            border-left: 3px solid {{ colors.secondary }};
            line-height: 1.4;
        }

        .review-rating {
            color: #F59E0B;
            font-size: 9pt;
            margin-bottom: 2px;
            letter-spacing: 1px;
        }
        
        .actionable-items {
            margin-top: 10px;
        }

        .actionable-items h4 {
            font-size: 8pt;
            color: {{ colors.text_secondary }};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .action-item {
            background: #EFF6FF;
            border-left: 3px solid {{ colors.secondary }};
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 0 6px 6px 0;
        }

        .action-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }

        .action-item-text {
            font-weight: 600;
            color: {{ colors.text_primary }};
            font-size: 9.5pt;
            line-height: 1.3;
        }

        .priority-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 7pt;
            font-weight: 700;
            text-transform: uppercase;
            margin-left: 8px;
        }

        .priority-high {
            background: {{ colors.danger }};
            color: white;
        }

        .priority-medium {
            background: {{ colors.warning }};
            color: {{ colors.text_primary }};
        }

        .priority-low {
            background: #6C6C6C;
            color: white;
        }

        .action-item-impact {
            font-size: 8.5pt;
            color: {{ colors.text_secondary }};
            line-height: 1.3;
        }
        
        .recommendations-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .recommendations-list li {
            padding: 8px;
            background: #F0FDF9;
            border-left: 3px solid {{ colors.primary }};
            margin-bottom: 6px;
            border-radius: 0 6px 6px 0;
            font-size: 9.5pt;
            line-height: 1.4;
        }
        
        .confidentiality {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid {{ colors.border }};
            font-size: 9pt;
            color: {{ colors.text_secondary }};
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-brand">{{ company_name }}</div>
        <div class="header-title">Playstore Reviews Insights for {{ role }} Team</div>
        <div class="header-meta">
            <table cellpadding="0" cellspacing="0" border="0" style="display: inline-table;">
                <tr>
                    <td style="padding-right: 15px; border-right: 1px solid #E0E0E0;">{{ metadata.total_reviews }} reviews</td>
                    <td style="padding-left: 15px; padding-right: 15px; border-right: 1px solid #E0E0E0;">Last {{ metadata.weeks_covered }} weeks</td>
                    <td style="padding-left: 15px;">Generated on {{ metadata.analysis_date }}</td>
                </tr>
            </table>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">Executive Summary</h2>
        <div class="executive-summary">
            {{ executive_summary }}
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">Key Themes</h2>
        {% for theme in themes %}
        <div class="theme">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 10px;">
                <tr>
                    <td style="font-size: 12pt; font-weight: 700; color: {{ colors.text_primary }};">{{ theme.name }}</td>
                    <td align="right">
                        <span class="sentiment-badge sentiment-{{ theme.sentiment|replace(' ', '-')|replace('to-', '-') }}">
                            {{ theme.sentiment }}
                        </span>
                    </td>
                </tr>
            </table>
            
            <div class="key-insights">
                <h4>Key Insights</h4>
                <ul>
                    {% for insight in theme.key_insights[:2] %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            {% if theme.sample_reviews %}
            <div class="sample-reviews">
                <h4>Sample Reviews</h4>
                {% for review in theme.sample_reviews %}
                <div class="review">
                    <div class="review-rating">{% for i in range(review.rating|int) %}★{% endfor %}{% for i in range(5 - review.rating|int) %}☆{% endfor %}</div>
                    <div>{{ review.content[:150] }}{% if review.content|length > 150 %}...{% endif %}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if theme.actionable_items %}
            <div class="actionable-items">
                <h4>Actionable Items</h4>
                {% for item in theme.actionable_items[:3] %}
                <div class="action-item">
                    <div class="action-item-header">
                        <span class="action-item-text">{{ item.action }}</span>
                        <span class="priority-badge priority-{{ item.priority }}">{{ item.priority }}</span>
                    </div>
                    <div class="action-item-impact">Impact: {{ item.expected_impact }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    {% if recommendations %}
    <div class="section">
        <h2 class="section-title">Strategic Recommendations</h2>
        <ul class="recommendations-list">
            {% for rec in recommendations[:3] %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <div class="confidentiality">
        This report contains confidential information intended solely for the {{ role }} team.<br>
        Generated on {{ metadata.analysis_date }} | {{ company_name }} Reviews Insights
    </div>
</body>
</html>
'''
    
    def _generate_email_html(self, report_data: Dict[str, Any]) -> str:
        """Generate email-friendly HTML with card-based layout"""
        colors = self.COLORS
        company_name = report_data.get('company_name', 'Groww')
        role = report_data.get('role', 'UI/UX')
        metadata = report_data.get('metadata', {})
        executive_summary = report_data.get('executive_summary', '')
        themes = report_data.get('themes', [])[:5]  # Top 5 themes
        actionable_items = report_data.get('actionable_items', [])[:5]  # Top 5 items
        
        # Sentiment colors
        sentiment_colors = {
            'highly-negative': '#DC2626',
            'negative': '#EF4444',
            'neutral': '#6B7280',
            'positive': '#10B981',
            'highly-positive': '#059669',
            'mixed': '#F59E0B'
        }
        
        # Build themes HTML
        themes_html = ""
        for theme in themes:
            sentiment = theme.get('sentiment', theme.get('user_sentiment', 'neutral')).lower().replace(' ', '-').replace('to-', '-')
            sentiment_color = sentiment_colors.get(sentiment, '#6B7280')
            
            # Get description from key_insights[0] or description field
            key_insights = theme.get('key_insights', [])
            description = key_insights[0] if key_insights else theme.get('description', '')
            
            # Get actionable from actionable_items[0] or actionable field
            actionable_items_list = theme.get('actionable_items', [])
            if actionable_items_list:
                actionable = actionable_items_list[0].get('action', '')
            else:
                actionable = theme.get('actionable', '')
            
            themes_html += f'''
        <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; margin-bottom: 12px; overflow: hidden;">
            <div style="padding: 16px;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="font-size: 14px; font-weight: 600; color: #1F2937;">{theme.get('name', theme.get('theme_name', ''))}</td>
                        <td align="right">
                            <span style="background: {sentiment_color}15; color: {sentiment_color}; padding: 4px 12px; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase;">{theme.get('sentiment', theme.get('user_sentiment', '')).upper()}</span>
                        </td>
                    </tr>
                </table>
                <p style="font-size: 12px; color: #4B5563; margin: 8px 0 0 0; line-height: 1.5;">{description}</p>
            </div>
            <div style="background: #F9FAFB; padding: 12px 16px; border-top: 1px solid #E5E7EB;">
                <p style="font-size: 10px; color: #6B7280; margin: 0 0 4px 0; text-transform: uppercase; font-weight: 600;">Action Required</p>
                <p style="font-size: 11px; color: #374151; margin: 0; line-height: 1.5;">{actionable}</p>
            </div>
        </div>'''
        
        # Build strategic recommendations HTML from top-level recommendations
        recommendations = report_data.get('recommendations', [])
        
        strategic_html = ""
        for i, rec in enumerate(recommendations[:3], 1):
            # Split recommendation into title and description if it contains a colon
            if ': ' in rec:
                title, desc = rec.split(': ', 1)
            else:
                title = rec
                desc = ""
            
            if desc:
                strategic_html += f'''
        <div style="margin-bottom: 12px; line-height: 1.5;">
            <span style="color: {colors['primary']}; font-weight: 700; margin-right: 4px;">{i}.</span>
            <span style="font-weight: 600; color: #1F2937;">{title}</span>
            <span style="color: #6B7280; font-size: 12px;"> — {desc}</span>
        </div>'''
            else:
                strategic_html += f'''
        <div style="margin-bottom: 12px; line-height: 1.5;">
            <span style="color: {colors['primary']}; font-weight: 700; margin-right: 4px;">{i}.</span>
            <span style="color: #374151;">{title}</span>
        </div>'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - Playstore Reviews Insights</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F3F4F6;">
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: #F3F4F6;">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table cellpadding="0" cellspacing="0" border="0" width="600" style="background: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: {colors['primary']}; padding: 24px 24px 20px 24px;">
                            <div style="font-size: 24px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">{company_name}</div>
                            <div style="font-size: 14px; color: #FFFFFF; opacity: 0.95; margin-bottom: 12px;">Playstore Reviews Insights for {role} Team</div>
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="color: #FFFFFF; opacity: 0.85; font-size: 11px; padding-right: 12px; border-right: 1px solid rgba(255,255,255,0.3);">{metadata.get('total_reviews', 0)} reviews</td>
                                    <td style="color: #FFFFFF; opacity: 0.85; font-size: 11px; padding: 0 12px; border-right: 1px solid rgba(255,255,255,0.3);">Last {metadata.get('weeks_covered', 0)} weeks</td>
                                    <td style="color: #FFFFFF; opacity: 0.85; font-size: 11px; padding-left: 12px;">{metadata.get('analysis_date', '')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Executive Summary -->
                    <tr>
                        <td style="padding: 24px 24px 0 24px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="border-left: 3px solid {colors['primary']}; padding-left: 12px;">
                                        <div style="font-size: 14px; font-weight: 700; color: #1F2937; margin-bottom: 8px;">Executive Summary</div>
                                    </td>
                                </tr>
                            </table>
                            <p style="font-size: 12px; color: #4B5563; line-height: 1.6; margin: 12px 0 0 0;">{executive_summary}</p>
                        </td>
                    </tr>
                    
                    <!-- Key Themes -->
                    <tr>
                        <td style="padding: 24px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="border-left: 3px solid {colors['primary']}; padding-left: 12px;">
                                        <div style="font-size: 14px; font-weight: 700; color: #1F2937;">Key Themes</div>
                                    </td>
                                </tr>
                            </table>
                            <div style="margin-top: 16px;">
                                {themes_html}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Strategic Recommendations -->
                    <tr>
                        <td style="padding: 0 24px 24px 24px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="border-left: 3px solid {colors['primary']}; padding-left: 12px;">
                                        <div style="font-size: 14px; font-weight: 700; color: #1F2937; margin-bottom: 16px;">Strategic Recommendations</div>
                                    </td>
                                </tr>
                            </table>
                            {strategic_html}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 16px 24px; border-top: 1px solid #E5E7EB; text-align: center;">
                            <p style="font-size: 10px; color: #9CA3AF; margin: 0;">Confidential — {company_name} | Full report attached as PDF</p>
                            <p style="font-size: 10px; color: #9CA3AF; margin: 4px 0 0 0;">Generated on {metadata.get('analysis_date', '')}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
