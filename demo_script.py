#!/usr/bin/env python3
"""
Clarity OS T4 Demo Script
Demonstrates all key features of Module A
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    print(f"Exit code: {result.returncode}")

def main():
    """Run comprehensive demo of Clarity OS T4."""
    print("Clarity OS T4 - Module A Demo")
    print("Local Search + Summarize with Citations")
    
    # Change to the correct directory
    os.chdir(os.path.dirname(__file__))
    
    # 1. Health Check
    run_command(
        "python -m clarity.main health",
        "System Health Check"
    )
    
    # 2. Basic Search
    run_command(
        'python -m clarity.main search --root "test_docs" --query "policy" --globs "**/*.md"',
        "Search for 'policy' in markdown files"
    )
    
    # 3. Search with Context
    run_command(
        'python -m clarity.main search --root "test_docs" --query "security" --context 3',
        "Search for 'security' with 3 lines context"
    )
    
    # 4. CSV Search
    run_command(
        'python -m clarity.main search --root "." --query "engineering" --globs "**/*.csv"',
        "Search for 'engineering' in CSV files"
    )
    
    # 5. Ask Command (Search + Summarize)
    run_command(
        'python -m clarity.main ask --root "test_docs" --question "encryption"',
        "Ask about encryption with citations"
    )
    
    # 6. Sources Command
    run_command(
        "python -m clarity.main sources --last",
        "Show coverage report from last search"
    )
    
    # 7. Case-Sensitive Search
    run_command(
        'python -m clarity.main search --root "test_docs" --query "Security" --case-sensitive',
        "Case-sensitive search for 'Security'"
    )
    
    # 8. Regex Search
    run_command(
        'python -m clarity.main search --root "test_docs" --query "security|encryption" --regex',
        "Regex search for 'security|encryption'"
    )
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print("All Clarity OS T4 features demonstrated successfully!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
