#!/usr/bin/env python3
"""
Start script for the Apify Prospect Analyzer API.

Simple script to run the API server with proper configuration.
"""

import os
import sys
import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Set environment variables for development
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    print("🚀 Starting Apify Prospect Analyzer API...")
    print("📖 API Documentation: http://localhost:8005/docs")
    print("🔍 Alternative Docs: http://localhost:8005/redoc")
    print("🏥 Health Check: http://localhost:8005/api/v1/health")
    print("⚡ Quick Test: http://localhost:8005/ping")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info",
        access_log=True
    ) 