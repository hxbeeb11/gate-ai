#!/usr/bin/env python
# deploy.py
# Entry point for Railway deployment that imports the original app
# This file preserves all existing functionality while adding deployment-specific settings

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("deploy")

# Create required directories if they don't exist
logger.info("Creating required directories...")
os.makedirs('data/processed/diagrams', exist_ok=True)
os.makedirs('data/adaptive_state', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Import the health check route
logger.info("Importing health check route...")
try:
    from src.health_check import add_health_check_route
except Exception as e:
    logger.error(f"Error importing health_check: {e}")
    sys.exit(1)

# Import the Flask app with better error handling
logger.info("Importing Flask app from src.app...")
try:
    from src.app import app
except Exception as e:
    logger.error(f"Error importing Flask app: {e}")
    sys.exit(1)

# Add health check endpoint for Railway
logger.info("Adding health check endpoint...")
app = add_health_check_route(app)
logger.info("Health check endpoint added successfully")

if __name__ == "__main__":
    # Use PORT environment variable provided by Railway
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting app on port {port}...")
    # Run with 0.0.0.0 to bind to all interfaces
    app.run(host="0.0.0.0", port=port) 