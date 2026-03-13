"""
Run Phase 2: Theme Extraction & Classification

This script loads reviews from Phase 1 and extracts themes using Groq LLM.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.themes.theme_service import run_phase2
import argparse


def main():
    parser = argparse.ArgumentParser(description='Phase 2: Theme Extraction & Classification')
    parser.add_argument(
        '--reviews-file',
        type=str,
        default='..\\Phase_1_Data_Ingestion_Layer\\data\\groww_reviews.json',
        help='Path to reviews JSON file from Phase 1'
    )
    parser.add_argument(
        '--role',
        type=str,
        default='Product',
        choices=['Product', 'Support', 'UI/UX', 'Leadership'],
        help='Target role for theme extraction'
    )
    parser.add_argument(
        '--max-themes',
        type=int,
        default=5,
        help='Maximum number of themes to extract (3-5)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Directory to save theme results'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PHASE 2: THEME EXTRACTION & CLASSIFICATION")
    print("="*60)
    print()
    print(f"Configuration:")
    print(f"  - Reviews file: {args.reviews_file}")
    print(f"  - Role: {args.role}")
    print(f"  - Max themes: {args.max_themes}")
    print()
    
    # Check if file exists
    if not os.path.exists(args.reviews_file):
        print(f"ERROR: Error: Reviews file not found: {args.reviews_file}")
        print()
        print("Please run Phase 1 first to fetch reviews:")
        print("  cd Phase_1_Data_Ingestion_Layer")
        print("  python fetch_reviews_to_file.py")
        return 1
    
    # Run Phase 2
    try:
        results = run_phase2(
            reviews_file=args.reviews_file,
            role=args.role,
            max_themes=args.max_themes,
            output_dir=args.output_dir
        )
        
        if results['status'] == 'success':
            print()
            print("="*60)
            print("RESULTS SUMMARY")
            print("="*60)
            print()
            
            # Display themes
            print(f"Extracted Themes for {args.role}:")
            for i, theme in enumerate(results['themes'], 1):
                print(f"\n{i}. {theme['name']} ({theme['sentiment']})")
                print(f"   Description: {theme['description']}")
                print(f"   Keywords: {', '.join(theme['keywords'])}")
                print(f"   Reviews: {len(theme['review_ids'])}")
            
            print()
            print(f"Classification Stats:")
            print(f"  - Total reviews: {results['stats']['total']}")
            print(f"  - Classified: {results['stats']['classified']}")
            print(f"  - Excluded: {results['stats']['excluded']}")
            print()
            print("OK: Phase 2 completed successfully!")
            print()
            
            return 0
        else:
            print(f"ERROR: Phase 2 failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"ERROR: Error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
