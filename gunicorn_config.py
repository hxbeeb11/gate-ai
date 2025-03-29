"""Gunicorn configuration for GATE AI"""
import os

# Use the PORT environment variable provided by Render
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker configuration
workers = 2  # Use 2 worker processes
worker_class = 'gevent'  # Use gevent for async support
worker_connections = 1000
timeout = 120  # 2 minute timeout

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Reload application on file changes
reload = False  # Set to True in development

# Process naming
proc_name = 'gate-ai'

# Recommended optimization settings
worker_tmp_dir = '/dev/shm'  # Use memory for temporary files
forwarded_allow_ips = '*'  # Trust X-Forwarded headers 