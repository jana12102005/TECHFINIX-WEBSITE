import os
import sys

# Ensure root directory is in sys.path for Vercel serverless execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()


class VercelWSGIMiddleware:
    """
    WSGI Middleware for Vercel Serverless Functions.
    Ensures PATH_INFO is cleanly formatted even if Vercel internal rewrites prepend /api/index.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/api/index"):
            environ["PATH_INFO"] = path[10:] or "/"
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
