"""
Main FastAPI application for Apify Prospect Analyzer.

This is the entry point for the API server.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.v1.api import api_router
from app.core.config import settings
from app.api.models.responses import ErrorResponse


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Apify Prospect Analyzer API")
    
    # Initialize services here if needed
    # e.g., database connections, external service clients, etc.
    
    yield
    
    # Shutdown
    logger.info("Shutting down Apify Prospect Analyzer API")


# Create FastAPI application
app = FastAPI(
    title="Apify Prospect Analyzer API",
    description="""
    ## Comprehensive Prospect Analysis API
    
    This API provides comprehensive prospect analysis capabilities using Apify actors to collect data from:
    
    * **LinkedIn** - Profile data, posts, company information
    * **Social Media** - Facebook pages, Twitter/X profiles  
    * **Company Data** - Financial data from Crunchbase, D&B, ZoomInfo
    * **Data Validation** - Quality scoring and validation
    
    ### Key Features
    
    * Single prospect analysis with detailed reporting
    * Batch processing for multiple prospects
    * Cost estimation and budget management
    * Real-time health monitoring
    * Data validation and quality scoring
    * Comprehensive actor management
    
    ### Getting Started
    
    1. Use `/api/v1/prospect/analyze` for single prospect analysis
    2. Use `/api/v1/prospect/batch` for bulk processing
    3. Check `/api/v1/health` for system status
    4. View `/api/v1/actors` for available data sources
    
    ### Cost Management
    
    * Get cost estimates with `/api/v1/prospect/estimate-cost`
    * Set budget limits in analysis parameters
    * Monitor spending with detailed cost breakdowns
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Prospect Analysis",
            "description": "Core prospect analysis operations including single and batch processing"
        },
        {
            "name": "Actors", 
            "description": "Apify actor management and configuration"
        },
        {
            "name": "Health",
            "description": "System health monitoring and status checks"
        },
        {
            "name": "Validation",
            "description": "Data validation and quality scoring"
        },
        {
            "name": "API Info",
            "description": "API information and metadata"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header to all requests."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Incoming request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            timestamp=time.time(),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled exceptions."""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            details={"error_type": type(exc).__name__},
            timestamp=time.time(),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.
    
    **Returns:** Basic API information and links to documentation.
    """
    return {
        "message": "Welcome to the Apify Prospect Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/api/v1/health",
        "api_info": "/api/v1/"
    }


@app.get("/ping", tags=["Root"])
async def ping():
    """Simple ping endpoint for basic connectivity testing."""
    return {"message": "pong"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom logging configuration
    ) 