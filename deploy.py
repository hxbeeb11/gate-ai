#!/usr/bin/env python
# deploy.py
# Entry point for Railway deployment that imports the original app
# This file preserves all existing functionality while adding deployment-specific settings

import os
import sys
from src.app import app
from src.health_check import add_health_check_route

# Create required directories if they don't exist
os.makedirs('data/processed/diagrams', exist_ok=True)
os.makedirs('data/adaptive_state', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Add health check endpoint for Railway
app = add_health_check_route(app)

if __name__ == "__main__":
    # Use PORT environment variable provided by Railway
    port = int(os.environ.get("PORT", 5000))
    # Run with 0.0.0.0 to bind to all interfaces
    app.run(host="0.0.0.0", port=port) 