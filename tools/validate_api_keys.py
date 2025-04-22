#!/usr/bin/env python3
"""
Validate API keys from .env file against relevant services.

This script loads API keys from the .env file and validates them
by making test requests to the corresponding services.
"""

import os
import sys
import requests
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("validate_api_keys")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = ROOT_DIR / ".env"
TIMEOUT = 10  # seconds

def load_environment():
    """Load environment variables from .env file."""
    if not ENV_FILE.exists():
        logger.error(f".env file not found at {ENV_FILE}")
        sys.exit(1)
    
    logger.info(f"Loading environment from {ENV_FILE}")
    load_dotenv(ENV_FILE)


def validate_nvd_api_key():
    """Validate NVD API key."""
    api_key = os.getenv("NVD_API_KEY")
    if not api_key:
        logger.warning("NVD_API_KEY not found in .env file")
        return False
    
    logger.info("Validating NVD API key...")
    try:
        # NVD API documentation: https://nvd.nist.gov/developers/vulnerabilities
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?apiKey={api_key}&resultsPerPage=1"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            logger.info("✅ NVD API key is valid")
            return True
        elif response.status_code == 403:
            logger.error("❌ NVD API key is invalid or unauthorized")
            return False
        else:
            logger.error(f"❌ NVD API request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating NVD API key: {e}")
        return False


def validate_otx_api_key():
    """Validate AlienVault OTX API key."""
    api_key = os.getenv("ALIENVAULT_OTX_API_KEY")
    if not api_key:
        logger.warning("ALIENVAULT_OTX_API_KEY not found in .env file")
        return False
    
    logger.info("Validating AlienVault OTX API key...")
    try:
        url = "https://otx.alienvault.com/api/v1/user/me"
        headers = {"X-OTX-API-KEY": api_key}
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"✅ AlienVault OTX API key is valid (user: {user_data.get('username', 'unknown')})")
            return True
        elif response.status_code == 401:
            logger.error("❌ AlienVault OTX API key is invalid or unauthorized")
            return False
        else:
            logger.error(f"❌ AlienVault OTX API request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating AlienVault OTX API key: {e}")
        return False


def validate_openai_api_key():
    """Validate OpenAI API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in .env file")
        return False
    
    logger.info("Validating OpenAI API key...")
    try:
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            logger.info("✅ OpenAI API key is valid")
            return True
        elif response.status_code in [401, 403]:
            logger.error("❌ OpenAI API key is invalid or unauthorized")
            return False
        else:
            logger.error(f"❌ OpenAI API request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating OpenAI API key: {e}")
        return False


def validate_google_api_key():
    """Validate Google API key for Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in .env file")
        return False
    
    logger.info("Validating Google Gemini API key...")
    try:
        # This is a simple model list request to check if the API key is valid
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            logger.info("✅ Google Gemini API key is valid")
            return True
        elif response.status_code in [400, 401, 403]:
            logger.error("❌ Google Gemini API key is invalid or unauthorized")
            return False
        else:
            logger.error(f"❌ Google Gemini API request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating Google Gemini API key: {e}")
        return False


def create_api_docs_file():
    """Create or update API documentation file."""
    api_docs_path = ROOT_DIR / "docs" / "API_KEYS.md"
    
    # Ensure docs directory exists
    api_docs_path.parent.mkdir(exist_ok=True)
    
    logger.info(f"Creating API documentation at {api_docs_path}")
    
    with open(api_docs_path, "w") as f:
        f.write("""# API Keys Documentation

This document provides information about the API keys used in this project, how to obtain them, and how to configure them.

## Configuration

API keys should be stored in a `.env` file in the root directory of the project. This file is not committed to the repository for security reasons.

Example `.env` file:
```
NVD_API_KEY=your_nvd_api_key_here
ALIENVAULT_OTX_API_KEY=your_otx_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

## API Key Sources

### National Vulnerability Database (NVD)
- **Environment Variable**: `NVD_API_KEY`
- **Purpose**: Access NVD APIs with higher rate limits
- **How to Obtain**: 
  1. Visit https://nvd.nist.gov/developers/request-an-api-key
  2. Fill out the form and submit
  3. You will receive the API key via email

### AlienVault Open Threat Exchange (OTX)
- **Environment Variable**: `ALIENVAULT_OTX_API_KEY`
- **Purpose**: Access OTX threat intelligence data
- **How to Obtain**: 
  1. Create an account at https://otx.alienvault.com/
  2. Navigate to your profile settings
  3. Find the API key section

### OpenAI
- **Environment Variable**: `OPENAI_API_KEY`
- **Purpose**: Access to GPT models for generation tasks
- **How to Obtain**: 
  1. Create an account at https://platform.openai.com/
  2. Navigate to API keys section: https://platform.openai.com/api-keys
  3. Generate a new API key

### Google (Gemini)
- **Environment Variable**: `GOOGLE_API_KEY`
- **Purpose**: Access to Gemini models
- **How to Obtain**: 
  1. Create or use an existing Google Cloud account
  2. Navigate to https://makersuite.google.com/app/apikey
  3. Create an API key

## Validation

You can validate your API keys using the `validate_api_keys.py` script:

```bash
python tools/validate_api_keys.py
```

This will check if your API keys are valid and have the necessary permissions.

## Security Best Practices

1. **Never commit your `.env` file or API keys to version control**
2. **Rotate your API keys periodically**
3. **Use API keys with the minimum necessary permissions**
4. **For CI/CD pipelines, use GitHub Secrets instead of hardcoded values**
""")
    
    logger.info(f"✅ API documentation created at {api_docs_path}")


def main():
    """Main validation function."""
    load_environment()
    
    # Track validation results
    results = {
        "valid": [],
        "invalid": [],
        "missing": []
    }
    
    # List of validation functions
    validators = [
        ("NVD", validate_nvd_api_key),
        ("AlienVault OTX", validate_otx_api_key),
        ("OpenAI", validate_openai_api_key),
        ("Google Gemini", validate_google_api_key),
    ]
    
    # Run all validators
    for name, validator in tqdm(validators, desc="Validating API keys"):
        try:
            if validator():
                results["valid"].append(name)
            else:
                results["invalid"].append(name)
        except Exception as e:
            logger.error(f"Error running {name} validator: {e}")
            results["invalid"].append(name)
    
    # Create API documentation
    create_api_docs_file()
    
    # Print summary
    print("\n" + "=" * 50)
    print("API Key Validation Summary")
    print("=" * 50)
    print(f"✅ Valid Keys:    {', '.join(results['valid']) if results['valid'] else 'None'}")
    print(f"❌ Invalid Keys:  {', '.join(results['invalid']) if results['invalid'] else 'None'}")
    print(f"⚠️ Missing Keys:  {', '.join(results['missing']) if results['missing'] else 'None'}")
    print("=" * 50)
    
    # Return exit code based on validity
    if results["invalid"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()