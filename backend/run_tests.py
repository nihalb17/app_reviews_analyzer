import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now run the tests
from app.tests.test_phase1 import run_all_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
