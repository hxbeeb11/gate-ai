# GATE AI Deployment Guide for Render.com

This guide provides step-by-step instructions for deploying the GATE AI application on Render.com.

## Prerequisites

Before starting the deployment process, ensure you have:

- GATE AI repository on GitHub
- A Render.com account
- API keys for OpenAI or other services used by the application

## Deployment Steps

### 1. Sign up for Render

If you haven't already, sign up for a Render account at [render.com](https://render.com).

### 2. Create a New Web Service

1. From your Render dashboard, click "New" and select "Web Service".
2. Connect your GitHub repository.
3. Search for and select your GATE AI repository.

### 3. Configure the Web Service

Fill in the service details:

- **Name**: `gate-ai` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose the closest data center to your users
- **Branch**: `main` (or your deployment branch)
- **Build Command**: `pip install --upgrade pip && pip install -r modified_requirements.txt`
- **Start Command**: `gunicorn -c gunicorn_config.py deploy:app`
- **Plan**: Free (or choose a paid plan for better performance)

### 4. Set Environment Variables

Add the following environment variables:

- `PYTHON_VERSION`: `3.11.0`
- `OPENAI_API_KEY`: Your OpenAI API key
- `GOOGLE_API_KEY`: Your Google API key (if using)
- `OTHER_SERVICE_API_KEY`: Any other required API keys

Mark API keys as "Secret" to ensure they're not exposed in logs.

### 5. Deploy Your Application

Click "Create Web Service" to start the deployment process. Render will:

1. Clone your repository
2. Install dependencies as specified in `modified_requirements.txt`
3. Start the application using gunicorn with the optimized configuration

## Verifying Deployment

1. Once deployment is complete, Render will provide a URL for your application (e.g., `https://gate-ai.onrender.com`).
2. Visit this URL to ensure your application is running correctly.
3. Test the main functionality to confirm everything works as expected.

## Troubleshooting Common Issues

### Build Failures

- **Dependency Issues**: Check the build logs for specific error messages related to package installation.
- **Python Version**: Confirm that the Python version specified in `runtime.txt` is supported by Render.

### Runtime Errors

- **Configuration Issues**: Ensure your gunicorn configuration is correctly set up in `gunicorn_config.py`.
- **Missing Environment Variables**: Verify all required environment variables are correctly set.
- **Memory Limits**: If the application crashes, consider upgrading to a paid plan with more resources.

### Performance Issues

- The free plan has limited resources and may experience cold starts.
- For better performance, consider:
  - Optimizing your application code
  - Using caching mechanisms
  - Upgrading to a paid plan

## Maintenance and Updates

To update your application after deployment:

1. Push changes to your GitHub repository.
2. Render will automatically detect the changes and redeploy your application.
3. Monitor the deployment logs to ensure the update is successful.

If you need to manually trigger a deploy:

1. Go to the Render dashboard.
2. Select your GATE AI service.
3. Click "Manual Deploy" > "Deploy latest commit". 