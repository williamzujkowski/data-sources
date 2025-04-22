# Secrets Management Guide

This document outlines how API keys and other secrets are managed in the data-sources-manager project.

## Local Development

For local development, secrets are stored in a `.env` file in the root directory. This file is **not** committed to the repository.

Example `.env` file:
```
NVD_API_KEY=your_nvd_api_key_here
ALIENVAULT_OTX_API_KEY=your_otx_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### Validating API Keys

Use the included validation tool to verify your API keys are working:

```bash
python tools/validate_api_keys.py
```

## CI/CD Environment

For GitHub Actions and other CI/CD environments, secrets should be stored as GitHub Secrets and accessed as environment variables.

### Setting up GitHub Secrets

1. Navigate to your repository on GitHub
2. Go to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each API key with the same name as in your local `.env` file

### Using Secrets in GitHub Actions

In your workflow files (`.github/workflows/*.yml`), you can access the secrets like this:

```yaml
jobs:
  update-sources:
    runs-on: ubuntu-latest
    env:
      NVD_API_KEY: ${{ secrets.NVD_API_KEY }}
      ALIENVAULT_OTX_API_KEY: ${{ secrets.ALIENVAULT_OTX_API_KEY }}
    steps:
      - uses: actions/checkout@v3
      - name: Run update
        run: python tools/fetch_sources.py
```

## Adding New Secrets

When adding new API keys or other secrets:

1. Update the `.env.sample` file with the new variable name (but not the value)
2. Add validation in `tools/validate_api_keys.py` if appropriate
3. Update the documentation in `docs/API_KEYS.md`
4. Add the secret to GitHub Secrets for CI/CD workflows

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Rotate API keys** periodically
3. Use **least privilege** when creating API keys
4. **Audit access** to secrets regularly
5. **Revoke compromised keys** immediately

## Troubleshooting

If you encounter issues with API keys:

1. Verify the key is correctly copied (no extra spaces or characters)
2. Run the validation tool to check if the key is valid
3. Check the API provider's documentation for any rate limits or restrictions
4. Regenerate the key if necessary