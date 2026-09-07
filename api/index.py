import sys
import os

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set VERCEL marker so config/database can detect serverless env
os.environ.setdefault("VERCEL", "1")

from app.main import app
