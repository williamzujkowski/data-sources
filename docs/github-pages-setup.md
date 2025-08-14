# GitHub Pages Setup Instructions

To properly display the MkDocs documentation on GitHub Pages, please follow these steps:

1. Go to your repository's Settings tab on GitHub.

2. In the left sidebar, click on "Pages" under "Code and automation".

3. Under "Build and deployment", set the following:
   - **Source**: "Deploy from a branch"
   - **Branch**: "gh-pages" (select this from the dropdown)
   - **Folder**: "/" (root)

4. Click "Save".

After completing these steps, GitHub Pages will automatically deploy your documentation from the gh-pages branch whenever it's updated by the GitHub Actions workflow.

## How It Works

The GitHub Actions workflow (`publish-docs.yml`) does the following:

1. It triggers when changes are pushed to the `docs/` directory or `mkdocs.yml` file on the main branch.

2. It builds the MkDocs site using the configuration in mkdocs.yml.

3. It uses the JamesIves/github-pages-deploy-action to deploy the built site to the gh-pages branch.

4. GitHub Pages then serves the content from the gh-pages branch.

## Troubleshooting

If you encounter issues with the GitHub Pages deployment:

1. Check the GitHub Actions workflow run to see if there were any errors during the build or deployment.

2. Verify that the gh-pages branch exists and contains the built documentation.

3. Ensure that GitHub Pages is configured to deploy from the gh-pages branch.

4. Check if the repository has the necessary permissions for GitHub Actions to push to the gh-pages branch.
