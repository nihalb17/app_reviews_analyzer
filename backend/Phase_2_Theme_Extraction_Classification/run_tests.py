"""
Phase 2 Test Runner

Runs all test cases for Phase 2: Theme Extraction & Classification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tests.test_theme_models import run_tests as run_model_tests
from app.tests.test_theme_extractor import run_tests as run_extractor_tests
from app.tests.test_theme_classifier import run_tests as run_classifier_tests


def main():
    print("="*70)
    print("PHASE 2: THEME EXTRACTION & CLASSIFICATION - TEST SUITE")
    print("="*70)
    print()
    
    results = {}
    
    # Run Theme Model Tests (P2-T01 to P2-T05)
    print("Running Theme Model Tests (P2-T01 to P2-T05)...")
    print("-"*70)
    results['models'] = run_model_tests()
    print()
    
    # Run Theme Extractor Tests (P2-T06 to P2-T10)
    print("Running Theme Extractor Tests (P2-T06 to P2-T10)...")
    print("-"*70)
    results['extractor'] = run_extractor_tests()
    print()
    
    # Run Theme Classifier Tests (P2-T11 to P2-T15)
    print("Running Theme Classifier Tests (P2-T11 to P2-T15)...")
    print("-"*70)
    results['classifier'] = run_classifier_tests()
    print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print()
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name.capitalize():12} {status}")
    
    print()
    
    all_passed = all(results.values())
    
    if all_passed:
        print("✓ All Phase 2 tests passed!")
        return 0
    else:
        print("✗ Some Phase 2 tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
