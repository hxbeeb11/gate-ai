# Deploying GATE AI on Railway

This document provides instructions for deploying the GATE AI application on Railway.app.

## Preparation Files

The following files have been added to facilitate deployment without modifying the original application:

- `modified_requirements.txt`: Streamlined dependencies for deployment
- `src/health_check.py`: Adds a health check endpoint
- `deploy.py`: Entry point for Railway deployment
- `Procfile`: Tells Railway how to run the application
- `railway.json`: Configuration settings for Railway

## Required Environment Variables

When deploying, make sure to set the following environment variables in the Railway dashboard:

- `TOGETHER_API_KEY`: Your Together AI API key
- `SUPABASE_URL`: Your Supabase URL
- `SUPABASE_KEY`: Your Supabase key

## Deployment Steps

1. Log in to your Railway account
2. Create a new project and connect it to your GitHub repository
3. Railway will automatically detect the configuration files
4. Add the required environment variables in the Variables section
5. Wait for the deployment to complete
6. Access your application via the provided Railway URL

## Resource Configuration

For optimal performance, configure your Railway resources:

- CPU: At least 1 vCPU (2 vCPU recommended)
- Memory: At least 512MB (1GB recommended)

## Troubleshooting

- Check logs in the Railway dashboard for any errors
- Verify environment variables are set correctly
- Ensure all required dependencies are listed in modified_requirements.txt
- The health check endpoint (/health) should return a 200 status code

## Testing the Deployment

After deployment, test the following functionality:

1. User registration and login
2. Accessing questions and mock tests
3. Saving progress
4. Diagram rendering

## Maintenance

To update your application:
1. Push changes to your GitHub repository
2. Railway will automatically redeploy your application
3. Monitor deployment logs for any issues 