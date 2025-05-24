"""
Main API router for version 1.

Includes all endpoint routers and provides API structure.
"""

from fastapi import APIRouter

# Import routers
from app.api.v1.endpoints import prospect, actors, health, linkedin, company, social
# from app.api.v1.endpoints import validation  # Disabled - not essential

api_router = APIRouter()

# Include routers with prefixes and tags
api_router.include_router(prospect.router, prefix="/prospect", tags=["Prospect Analysis"])
api_router.include_router(actors.router, prefix="/actors", tags=["Actors"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(linkedin.router, prefix="/linkedin", tags=["LinkedIn"])
api_router.include_router(company.router, prefix="/company", tags=["Company"])
api_router.include_router(social.router, prefix="/social", tags=["Social"])
# api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])  # Disabled

# Root endpoint for API information
@api_router.get("/", tags=["API Info"])
async def api_info():
    """
    Get API information and available endpoints.
    
    **Returns:** API version, available endpoints, and system status.
    """
    return {
        "name": "Apify Prospect Analyzer API",
        "version": "1.0.0",
        "description": "API for comprehensive prospect analysis using Apify actors",
        "endpoints": {
            "prospect": "/api/v1/prospect",
            "actors": "/api/v1/actors", 
            "health": "/api/v1/health",
            "linkedin": "/api/v1/linkedin",
            "company": "/api/v1/company",
            "social": "/api/v1/social",
            # "validation": "/api/v1/validation"  # Disabled
        },
        "actor_endpoints": {
            "linkedin": {
                "profiles": "/api/v1/linkedin/profiles",
                "posts": "/api/v1/linkedin/posts", 
                "companies": "/api/v1/linkedin/companies",
                "pricing": "/api/v1/linkedin/pricing",
                "test": "/api/v1/linkedin/test"
            },
            "company": {
                "erasmus_domain": "/api/v1/company/erasmus/domain",
                "erasmus_name": "/api/v1/company/erasmus/name",
                "crunchbase": "/api/v1/company/crunchbase",
                "zoominfo": "/api/v1/company/zoominfo", 
                "duns": "/api/v1/company/duns",
                "erasmus_pricing": "/api/v1/company/erasmus/pricing",
                "test": "/api/v1/company/test"
            },
            "social": {
                "twitter_handles": "/api/v1/social/twitter/handles",
                "twitter_search": "/api/v1/social/twitter/search",
                "twitter_combined": "/api/v1/social/twitter/combined",
                "facebook": "/api/v1/social/facebook",
                "twitter_pricing": "/api/v1/social/twitter/pricing",
                "test": "/api/v1/social/test"
            }
        },
        "docs": "/docs",
        "redoc": "/redoc"
    } 