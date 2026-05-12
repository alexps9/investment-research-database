"""
Vercel entry point for FastAPI backend
"""
from app.main import app

# Vercel serverless handler
handler = app
