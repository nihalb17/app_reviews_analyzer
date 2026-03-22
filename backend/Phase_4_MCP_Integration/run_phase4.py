#!/usr/bin/env python3
"""
Phase 4: MCP Integration (Google Doc Update)

This script runs the MCP integration pipeline:
1. Load reviews JSON from Phase 3
2. Load fee explainer JSON from Phase 3.5
3. Format combined data for Google Doc
4. Append to Google Doc via MCP

Usage:
    python run_phase4.py
    python run_phase4.py --role Product
    python run_phase4.py --role Leadership
"""

import argparse
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.mcp import GoogleDocUpdater
from app.core.config import settings


def run_mcp_integration(role: str = "Product") -> dict:
    """
    Run the complete MCP integration pipeline
    
    Args:
        role: Role for which to load reviews data (Product, Support, UI/UX, Leadership)
        
    Returns:
        Dictionary with results
    """
    print("=" * 60)
    print("Phase 4: MCP Integration (Google Doc Update)")
    print("=" * 60)
    print()
    
    # Initialize updater
    updater = GoogleDocUpdater()
    
    # Check if Google Doc is configured
    if not updater.mcp_client.is_configured():
        print("ERROR: Google Doc ID not configured!")
        print(f"Please set GOOGLE_DOC_ID in {settings.ENV_FILE}")
        return {
            "success": False,
            "error": "Google Doc ID not configured"
        }
    
    print(f"Google Doc ID: {settings.GOOGLE_DOC_ID}")
    print(f"Document URL: {updater.get_document_url()}")
    print(f"Role: {role}")
    print()
    
    # Update document
    print("Step 1: Loading and formatting data...")
    print("-" * 60)
    
    result = updater.update_document(role=role)
    
    print()
    
    if result.get("success"):
        print("=" * 60)
        print("Phase 4 Complete!")
        print("=" * 60)
        print(f"[OK] Content prepared for Google Doc")
        print(f"[OK] Document URL: {result.get('document_url')}")
        
        if result.get("local_file"):
            print(f"[OK] Local file: {result.get('local_file')}")
        
        data_summary = result.get("data_summary", {})
        print(f"[OK] Reviews data loaded: {data_summary.get('reviews_loaded', False)}")
        print(f"[OK] Fee explainer data loaded: {data_summary.get('fee_explainer_loaded', False)}")
        print()
        
        if result.get("note"):
            print(f"Note: {result.get('note')}")
            print()
        
        return result
    else:
        print("=" * 60)
        print("Phase 4 Failed!")
        print("=" * 60)
        print(f"Error: {result.get('error')}")
        print(f"Message: {result.get('message')}")
        print()
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4: MCP Integration (Google Doc Update)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_phase4.py
  python run_phase4.py --role Product
  python run_phase4.py --role Support
  python run_phase4.py --role UI/UX
  python run_phase4.py --role Leadership
        """
    )
    
    parser.add_argument(
        "--role",
        type=str,
        default="Product",
        choices=["Product", "Support", "UI/UX", "Leadership"],
        help="Role for which to load reviews data (default: Product)"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_mcp_integration(role=args.role)
        return 0 if result.get("success") else 1
        
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
