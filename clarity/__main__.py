#!/usr/bin/env python3

import argparse
import sys
import os
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from clarity.main import main

if __name__ == "__main__":
    sys.exit(main())
