import os
import sys

# Ensure project root directory is in sys.path for Vercel serverless execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()
