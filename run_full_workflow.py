import subprocess
import sys
import glob
import os
from datetime import datetime

def run_script(script_name):
    print(f"\nRunning {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    # Step 1: Run the main scraper
    run_script("scraper.py")

    # Step 2: Run the Reddit cultural events finder
    run_script("find_reddit_cultural_events.py")

    # Step 3: Run the combiner
    run_script("combine_summaries.py")

    # Find the latest combined markdown file
    combined_files = glob.glob("nyc_events_combined_*.md")
    if not combined_files:
        print("No combined markdown file found.")
        sys.exit(1)
    latest_file = max(combined_files, key=os.path.getctime)
    print(f"\nWorkflow complete! Combined summary saved to: {latest_file}") 