#!/usr/bin/env python3
"""
Phase 3.5: Fee Explainer Generation

This script runs the fee explainer generation pipeline:
1. Scrape exit load data from mutual fund pages
2. Generate bullet points using Groq LLM
3. Save results to JSON file

Usage:
    python run_phase35.py
    python run_phase35.py --output-dir ./custom_data
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.scraper import ExitLoadScraper
from app.services.llm import FeeExplainerGenerator
from app.services.repository import FeeExplainerRepository
from app.core.config import settings


def run_fee_explainer_generation(output_dir: Path = None) -> dict:
    """
    Run the complete fee explainer generation pipeline
    
    Args:
        output_dir: Optional custom output directory
        
    Returns:
        Dictionary with results and file path
    """
    print("=" * 60)
    print("Phase 3.5: Fee Explainer Generation")
    print("=" * 60)
    print()
    
    # Step 1: Scrape exit load data
    print("Step 1: Scraping exit load data from mutual fund pages...")
    print("-" * 60)
    
    scraper = ExitLoadScraper()
    scraped_data = scraper.scrape_all_funds()
    
    print(f"[OK] Scraped data from {len(scraped_data.get('funds', []))} funds")
    for fund in scraped_data.get('funds', []):
        exit_load = fund.get('exit_load', 'N/A')
        print(f"  - {fund.get('fund_name')}")
        # Truncate long exit load text for display
        display_text = exit_load[:80] + "..." if len(exit_load) > 80 else exit_load
        print(f"    Exit Load: {display_text}")
    print()
    
    # Step 2: Generate bullet points using Groq
    print("Step 2: Generating bullet points using Groq LLM...")
    print("-" * 60)
    
    generator = FeeExplainerGenerator()
    fee_explainer_data = generator.generate_bullet_points(scraped_data)
    
    print(f"[OK] Generated {len(fee_explainer_data.get('bullet_points', []))} bullet points")
    for i, bp in enumerate(fee_explainer_data.get('bullet_points', []), 1):
        point_text = bp.get('point', '')[:80]
        if len(bp.get('point', '')) > 80:
            point_text += "..."
        print(f"  {i}. {point_text}")
    print()
    
    # Step 3: Save to repository
    print("Step 3: Saving fee explainer data...")
    print("-" * 60)
    
    if output_dir:
        repository = FeeExplainerRepository(data_dir=output_dir)
    else:
        repository = FeeExplainerRepository()
    
    # Save generated fee explainer
    file_path = repository.save(fee_explainer_data)
    print(f"[OK] Fee explainer saved to: {file_path}")
    
    # Save raw scraped data
    scraped_data_path = repository.save_scraped_data(scraped_data)
    print(f"[OK] Scraped data saved to: {scraped_data_path}")
    print()
    
    # Summary
    print("=" * 60)
    print("Phase 3.5 Complete!")
    print("=" * 60)
    print(f"Output file: {file_path}")
    print(f"Bullet points: {len(fee_explainer_data.get('bullet_points', []))}")
    print(f"Sources: {len(fee_explainer_data.get('sources', []))}")
    print(f"Last checked: {fee_explainer_data.get('last_checked', 'N/A')}")
    print()
    
    return {
        "success": True,
        "file_path": file_path,
        "data": fee_explainer_data
    }


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.5: Fee Explainer Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_phase35.py
  python run_phase35.py --output-dir ./custom_data
  python run_phase35.py --test
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for fee_explainer.json"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (uses mock data)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Set output directory if provided
        output_dir = None
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run the pipeline
        result = run_fee_explainer_generation(output_dir)
        
        if args.verbose:
            print("\nFull output data:")
            print(json.dumps(result["data"], indent=2))
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
