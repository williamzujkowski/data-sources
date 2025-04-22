#!/usr/bin/env python3
"""
Serve the MkDocs documentation locally.

This script runs `mkdocs serve` to preview the documentation locally.
"""

import os
import subprocess
import webbrowser
from pathlib import Path

# Get project root directory
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Run MkDocs serve to preview documentation."""
    print(f"Starting MkDocs server to preview documentation...")
    print(f"Documentation will be available at http://127.0.0.1:8000")
    
    # Open browser after a short delay
    webbrowser.open_new_tab("http://127.0.0.1:8000")
    
    # Run mkdocs serve
    subprocess.run(["mkdocs", "serve"], cwd=ROOT_DIR)

if __name__ == "__main__":
    main()