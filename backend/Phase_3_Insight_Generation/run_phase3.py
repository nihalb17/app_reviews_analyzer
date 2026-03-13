"""
Run Phase 3: Insight Generation

This script generates insights from themes using Gemini LLM.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.insights.insight_service import run_phase3_for_role, run_phase3_one_pager
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description='Phase 3: Insight Generation')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['single', 'onepager'],
        default='single',
        help='Mode: single role or full 1-pager report'
    )
    parser.add_argument(
        '--role',
        type=str,
        default='Product',
        choices=['Product', 'Support', 'UI/UX', 'Leadership'],
        help='Target role (for single mode)'
    )
    parser.add_argument(
        '--themes-file',
        type=str,
        default='..\\Phase_2_Theme_Extraction_Classification\\data\\themes_product_20260309_024908.json',
        help='Path to themes JSON file from Phase 2'
    )
    parser.add_argument(
        '--reviews-file',
        type=str,
        default='..\\Phase_1_Data_Ingestion_Layer\\data\\groww_reviews.json',
        help='Path to reviews JSON file from Phase 1'
    )
    parser.add_argument(
        '--period',
        type=str,
        default='Last 10 weeks',
        help='Period covered by the analysis'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Directory to save insights'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PHASE 3: INSIGHT GENERATION")
    print("="*60)
    print()
    
    # Check if files exist
    if not os.path.exists(args.themes_file):
        print(f"ERROR: Error: Themes file not found: {args.themes_file}")
        print()
        print("Please run Phase 2 first to extract themes:")
        print("  cd Phase_2_Theme_Extraction_Classification")
        print("  python run_phase2.py")
        return 1
    
    if not os.path.exists(args.reviews_file):
        print(f"ERROR: Error: Reviews file not found: {args.reviews_file}")
        return 1
    
    try:
        if args.mode == 'single':
            # Generate insights for single role
            print(f"Generating insights for role: {args.role}")
            print(f"Themes file: {args.themes_file}")
            print(f"Reviews file: {args.reviews_file}")
            print()
            
            results = run_phase3_for_role(
                role=args.role,
                themes_file=args.themes_file,
                reviews_file=args.reviews_file,
                output_dir=args.output_dir
            )
            
            if results['status'] == 'success':
                print()
                print("="*60)
                print("INSIGHTS SUMMARY")
                print("="*60)
                print()
                
                insights = results['insights']
                
                print(f"Role: {insights['role']}")
                print()
                print(f"Executive Summary:")
                print(f"  {insights['summary']}")
                print()
                
                print(f"Themes Analyzed: {len(insights['themes'])}")
                for theme in insights['themes']:
                    print(f"\n  • {theme['theme_name']} ({theme['user_sentiment']})")
                    print(f"    Key Insights:")
                    for ki in theme['key_insights'][:2]:
                        # Encode to handle Unicode characters on Windows
                        try:
                            print(f"      - {ki}")
                        except UnicodeEncodeError:
                            print(f"      - {ki.encode('ascii', 'ignore').decode('ascii')}")
                    
                    # Show sample reviews
                    if theme.get('sample_reviews'):
                        print(f"    Sample Reviews:")
                        for i, review in enumerate(theme['sample_reviews'][:3], 1):
                            content = review['content'][:100] + "..." if len(review['content']) > 100 else review['content']
                            try:
                                print(f"      {i}. [Rating: {review['rating']}/5] {content}")
                            except UnicodeEncodeError:
                                content = content.encode('ascii', 'ignore').decode('ascii')
                                print(f"      {i}. [Rating: {review['rating']}/5] {content}")
                    
                    # Show actionable items
                    if theme.get('actionable_items'):
                        print(f"    Actionable Items:")
                        for i, item in enumerate(theme['actionable_items'], 1):
                            try:
                                print(f"      {i}. [{item['priority'].upper()}] {item['action']}")
                                print(f"         Impact: {item['expected_impact']}")
                            except UnicodeEncodeError:
                                action = item['action'].encode('ascii', 'ignore').decode('ascii')
                                impact = item['expected_impact'].encode('ascii', 'ignore').decode('ascii')
                                print(f"      {i}. [{item['priority'].upper()}] {action}")
                                print(f"         Impact: {impact}")
                
                print()
                print(f"Top Issues:")
                for issue in insights['top_issues'][:3]:
                    print(f"  - {issue}")
                
                print()
                print(f"Recommendations:")
                for rec in insights['recommendations'][:3]:
                    print(f"  - {rec}")
                
                print()
                print(f"OK: Insights saved to: {results['saved_to']}")
                print()
                
                return 0
            else:
                print(f"ERROR: Phase 3 failed")
                return 1
        
        else:
            # Generate full 1-pager
            print("Generating full 1-pager report")
            print(f"Reviews file: {args.reviews_file}")
            print(f"Period: {args.period}")
            print()
            
            # For one-pager, we need themes for all roles
            # This is a simplified version - in practice you'd have themes for each role
            themes_files = {
                'Product': args.themes_file
            }
            
            results = run_phase3_one_pager(
                roles=['Product'],
                themes_files=themes_files,
                reviews_file=args.reviews_file,
                period_covered=args.period,
                output_dir=args.output_dir
            )
            
            if results['status'] == 'success':
                print()
                print("="*60)
                print("1-PAGER REPORT GENERATED")
                print("="*60)
                print()
                
                report = results['report']
                
                print(f"Report ID: {report['report_id']}")
                print(f"Period: {report['period_covered']}")
                print(f"Total Reviews: {report['total_reviews']}")
                print()
                
                print("Executive Summary:")
                print(f"  {report['executive_summary']}")
                print()
                
                print(f"Roles Covered: {len(report['role_insights'])}")
                for role, insights in report['role_insights'].items():
                    print(f"  - {role}: {len(insights['themes'])} themes")
                
                print()
                print(f"OK: Report saved to: {results['saved_to']}")
                print()
                
                return 0
            else:
                print(f"ERROR: Phase 3 failed")
                return 1
                
    except Exception as e:
        print(f"ERROR: Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
