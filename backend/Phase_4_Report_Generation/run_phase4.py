#!/usr/bin/env python3
"""
Phase 4: Report Generation & Distribution

Generates PDF reports from Phase 3 insights with Groww branding.

Usage:
    python run_phase4.py --insights-file path/to/insights.json --role Product
    python run_phase4.py --insights-file path/to/insights.json --role Product --html-only
"""

import argparse
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.report.report_builder import ReportBuilder
from app.services.report.pdf_generator import PDFGenerator, PLAYWRIGHT_AVAILABLE


def main():
    parser = argparse.ArgumentParser(
        description='Generate PDF reports from insights (Phase 4)'
    )
    parser.add_argument(
        '--insights-file',
        type=str,
        required=True,
        help='Path to Phase 3 insights JSON file'
    )
    parser.add_argument(
        '--reviews-file',
        type=str,
        default='..\\Phase_1_Data_Ingestion_Layer\\data\\groww_reviews.json',
        help='Path to reviews file for metadata (default: Phase 1 data)'
    )
    parser.add_argument(
        '--role',
        type=str,
        required=True,
        choices=['Product', 'Support', 'UI/UX', 'Leadership'],
        help='Target role for the report'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for generated reports'
    )
    parser.add_argument(
        '--html-only',
        action='store_true',
        help='Generate HTML only (no PDF) - useful when WeasyPrint is not installed'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PHASE 4: REPORT GENERATION")
    print("="*60)
    print()
    
    # Validate inputs
    if not os.path.exists(args.insights_file):
        print(f"ERROR: Error: Insights file not found: {args.insights_file}")
        return 1
    
    # Check Playwright availability
    if not args.html_only and not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Warning: Playwright not available. Install with: pip install playwright")
        print("  Falling back to HTML-only generation.")
        print()
        args.html_only = True
    
    try:
        # Step 1: Build report data
        print("Step 1: Building report data...")
        report_builder = ReportBuilder()
        report_data = report_builder.build_report(
            role=args.role,
            insights_file=args.insights_file,
            reviews_file=args.reviews_file
        )
        print(f"  OK: Report data built for role: {args.role}")
        print(f"  OK: Total reviews: {report_data['metadata']['total_reviews']}")
        print(f"  OK: Themes: {len(report_data['themes'])}")
        print()
        
        # Step 2: Generate output
        pdf_generator = PDFGenerator()
        
        if args.html_only:
            # Generate HTML only
            print("Step 2: Generating HTML report...")
            html_path = pdf_generator.generate_html_report(report_data, output_dir=args.output_dir)
            print(f"  OK: HTML report generated: {html_path}")
            
            print()
            print("="*60)
            print("REPORT GENERATION COMPLETE (HTML ONLY)")
            print("="*60)
            print()
            print(f"Output: {html_path}")
            print()
            print("Note: Install Playwright for PDF generation:")
            print("  pip install playwright")
            
        else:
            # Generate PDF
            print("Step 2: Generating PDF report...")
            pdf_path = pdf_generator.generate_pdf(report_data, output_dir=args.output_dir)
            print(f"  OK: PDF report generated: {pdf_path}")
            
            # Also generate HTML for email
            print("Step 3: Generating HTML version for email...")
            html_path = pdf_generator.generate_html_report(report_data, output_dir=args.output_dir)
            print(f"  OK: HTML report generated: {html_path}")
            
            print()
            print("="*60)
            print("REPORT GENERATION COMPLETE")
            print("="*60)
            print()
            print(f"PDF:  {pdf_path}")
            print(f"HTML: {html_path}")
        
        print()
        print("Report Contents:")
        print(f"  - Executive Summary")
        print(f"  - {len(report_data['themes'])} Themes with sample reviews")
        print(f"  - Actionable Items")
        if report_data.get('recommendations'):
            print(f"  - Strategic Recommendations")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
