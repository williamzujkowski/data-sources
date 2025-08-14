#!/usr/bin/env python3
"""
Build and serve the MkDocs documentation locally.

This script builds the MkDocs site and serves it locally,
mimicking how it will appear on GitHub Pages.
"""

import os
import shutil
import subprocess
import webbrowser
from pathlib import Path

# Get project root directory
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE_DIR = ROOT_DIR / "site"


def main():
    """Build and serve MkDocs to preview documentation."""
    print("Building MkDocs site...")

    # Build the site
    subprocess.run(["mkdocs", "build", "--site-dir", str(SITE_DIR)], cwd=ROOT_DIR)

    # Create .nojekyll file
    (SITE_DIR / ".nojekyll").touch()

    print("Starting server to preview documentation...")
    print("Documentation will be available at http://127.0.0.1:8000")

    # Open browser after a short delay
    webbrowser.open_new_tab("http://127.0.0.1:8000")

    # Serve the site using Python's built-in HTTP server
    os.chdir(SITE_DIR)
    subprocess.run(["python", "-m", "http.server", "8000"])


if __name__ == "__main__":
    main()
