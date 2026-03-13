"""
Local Scheduler Test Script
Runs the scheduler every 5 minutes locally for testing
"""
import time
import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8001/api/triggers/scheduled"
API_TOKEN = "local-scheduler-test-token-2024"

# Fixed parameters
SCHEDULER_CONFIG = {
    "weeks": 9,
    "reviews_count": 1000,
    "role": "Product",
    "recipient_name": "Nihal",
    "recipient_email": "nihalreddyb1997@gmail.com",
    "mode": "email",
    "type": "Scheduler"
}

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def trigger_scheduler():
    """Trigger the scheduler endpoint"""
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering scheduler...")
        response = requests.post(API_URL, headers=HEADERS, json=SCHEDULER_CONFIG, timeout=10)
        
        if response.status_code in [200, 202]:
            data = response.json()
            print(f"Success! Trigger ID: {data.get('id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"Failed! Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to server at {API_URL}")
        print("   Make sure the backend server is running!")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_scheduler_loop(max_runs=None, interval_minutes=5):
    """
    Run the scheduler in a loop
    
    Args:
        max_runs: Number of times to run (None for infinite)
        interval_minutes: Minutes between runs
    """
    run_count = 0
    interval_seconds = interval_minutes * 60
    
    print("=" * 60)
    print("LOCAL SCHEDULER TEST")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Interval: {interval_minutes} minutes")
    print(f"Max runs: {'Unlimited' if max_runs is None else max_runs}")
    print(f"Config: {json.dumps(SCHEDULER_CONFIG, indent=2)}")
    print("=" * 60)
    
    try:
        while max_runs is None or run_count < max_runs:
            run_count += 1
            print(f"\n--- Run #{run_count} ---")
            
            success = trigger_scheduler()
            
            if max_runs and run_count >= max_runs:
                print(f"\nCompleted {max_runs} runs. Exiting.")
                break
            
            # Wait for next run
            next_run = datetime.now().timestamp() + interval_seconds
            next_run_str = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
            print(f"\nNext run at {next_run_str} (in {interval_minutes} minutes)")
            print("Press Ctrl+C to stop")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n\nStopped by user. Total runs: {run_count}")

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            # Run once and exit
            print("Running scheduler once...")
            trigger_scheduler()
        elif sys.argv[1].isdigit():
            # Run N times
            run_scheduler_loop(max_runs=int(sys.argv[1]))
        else:
            print("Usage:")
            print("  python test_scheduler_local.py        # Run continuously every 5 mins")
            print("  python test_scheduler_local.py once   # Run once")
            print("  python test_scheduler_local.py 3      # Run 3 times")
    else:
        # Default: run continuously
        run_scheduler_loop(max_runs=5, interval_minutes=5)  # Run 5 times for testing
