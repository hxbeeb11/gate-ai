# Gunicorn Configuration for GATE AI

This document explains the gunicorn configuration used for deploying GATE AI on Render.com and other platforms.

## Overview

We use [Gunicorn](https://gunicorn.org/) (Green Unicorn) as our WSGI HTTP server to run our Flask application in production. The configuration in `gunicorn_config.py` is optimized for cloud deployment environments like Render.com.

## Key Configuration Parameters

### Basic Settings

- **bind**: `0.0.0.0:{PORT}` - Binds to all network interfaces on the port specified by the environment variable
- **workers**: `2` - Number of worker processes
- **worker_class**: `gevent` - Uses gevent for asynchronous processing
- **worker_connections**: `1000` - Maximum number of simultaneous connections per worker
- **timeout**: `120` - Worker timeout in seconds (2 minutes)

### Logging

- **accesslog**: `-` - Access logs to stdout
- **errorlog**: `-` - Error logs to stdout  
- **loglevel**: `info` - Log level

### Performance Optimizations

- **worker_tmp_dir**: `/dev/shm` - Uses memory for temporary files
- **forwarded_allow_ips**: `*` - Trust X-Forwarded headers from all IPs

## When to Modify This Configuration

You might need to modify the gunicorn configuration when:

1. **Scaling up**: Increase the number of workers (typically 2-4× the number of CPU cores)
2. **Memory issues**: Decrease the number of workers if you're experiencing out-of-memory errors
3. **Long-running requests**: Adjust the timeout value if your application has endpoints that take longer to process
4. **Development**: Set `reload = True` for automatic reloading during development

## Usage

This configuration is applied when starting the server with:

```
gunicorn -c gunicorn_config.py deploy:app
```

## Recommended Production Settings

For production deployments with higher traffic:

1. Increase workers to 4-12 depending on available CPU cores
2. Consider using a reverse proxy like Nginx in front of gunicorn
3. Implement proper rate limiting
4. Use a CDN for static assets 