# Installation

This guide will help you set up the Data Sources Manager locally.

## Prerequisites

- Python 3.8 or higher
- Git
- pip (Python package installer)

## Clone the Repository

```bash
git clone https://github.com/williamzujkowski/data-sources.git
cd data-sources
```

## Set Up a Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r tools/requirements.txt
```

## Configure API Keys (Optional)

For features that require API access to external data sources:

1. Copy the sample environment file:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` to add your API keys:
   ```bash
   # Open in your favorite editor
   nano .env
   ```

3. Validate your API keys:
   ```bash
   python tools/validate_api_keys.py
   ```

## Running the Tools

Once installed, you can run the various tools:

```bash
# Fetch latest data from sources
python tools/fetch_sources.py

# Calculate quality scores
python tools/score_sources.py

# Build the search index
python tools/index_sources.py
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Learn how to use the Data Sources Manager
- [Configuration](configuration.md) - Customize the Data Sources Manager
- [API Keys](../development/api-keys.md) - Learn about obtaining and configuring API keys
