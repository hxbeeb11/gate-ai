# src/health_check.py
# Health check endpoint for Railway deployment
# Import this into app.py without modifying existing functionality

def add_health_check_route(app):
    """
    Add a health check endpoint to the Flask app.
    This function should be called after the app is created.
    """
    @app.route('/health')
    def health_check():
        return {"status": "healthy", "message": "GATE AI is running"}
    
    return app 