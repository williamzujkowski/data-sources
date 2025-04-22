# API Keys Documentation

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
