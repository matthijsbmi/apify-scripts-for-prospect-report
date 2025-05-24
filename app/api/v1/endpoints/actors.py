"""
Actors API endpoints.

Endpoints for managing and retrieving information about Apify actors.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
import structlog

from app.api.models.responses import ActorsResponse, ActorConfiguration
from app.actors.config import ACTOR_CONFIGS


logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=ActorsResponse, tags=["Actors"])
async def list_actors(
    category: Optional[str] = Query(None, description="Filter by actor category"),
    enabled_only: bool = Query(True, description="Show only enabled actors")
) -> ActorsResponse:
    """
    List all available Apify actors with their configurations.
    
    **Parameters:**
    - `category`: Filter actors by category (linkedin, social, company, etc.)
    - `enabled_only`: Whether to show only enabled actors
    
    **Returns:** List of actors with detailed configuration information.
    """
    log = logger.bind(category=category, enabled_only=enabled_only)
    log.info("Listing actors")
    
    try:
        actors = []
        categories = set()
        total_cost = 0.0
        
        for actor_key, config in ACTOR_CONFIGS.items():
            # Apply category filter
            if category and config.get("category", "").lower() != category.lower():
                continue
            
            # Apply enabled filter
            if enabled_only and not config.get("enabled", True):
                continue
            
            actor_config = ActorConfiguration(
                actor_id=config["actor_id"],
                name=config["name"],
                description=config.get("description", ""),
                category=config.get("category", "general"),
                cost_per_run=config.get("cost_per_run", 0.05),
                average_runtime=config.get("average_runtime"),
                input_schema=config.get("input_schema", {}),
                output_format=config.get("output_format", "json"),
                is_enabled=config.get("enabled", True)
            )
            
            actors.append(actor_config)
            categories.add(actor_config.category)
            total_cost += actor_config.cost_per_run
        
        response = ActorsResponse(
            actors=actors,
            total_count=len(actors),
            categories=sorted(list(categories)),
            total_estimated_cost=round(total_cost, 4)
        )
        
        log.info(
            "Actors listed successfully",
            count=len(actors),
            categories=len(categories),
            total_cost=total_cost
        )
        
        return response
        
    except Exception as e:
        log.error("Failed to list actors", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list actors: {str(e)}"
        )


@router.get("/{actor_id}", response_model=ActorConfiguration, tags=["Actors"])
async def get_actor(actor_id: str) -> ActorConfiguration:
    """
    Get detailed information about a specific actor.
    
    **Returns:** Complete actor configuration and metadata.
    """
    log = logger.bind(actor_id=actor_id)
    log.info("Getting actor details")
    
    try:
        # Find actor in configs
        actor_config = None
        for config in ACTOR_CONFIGS.values():
            if config["actor_id"] == actor_id:
                actor_config = config
                break
        
        if not actor_config:
            log.warning("Actor not found")
            raise HTTPException(
                status_code=404,
                detail=f"Actor {actor_id} not found"
            )
        
        response = ActorConfiguration(
            actor_id=actor_config["actor_id"],
            name=actor_config["name"],
            description=actor_config.get("description", ""),
            category=actor_config.get("category", "general"),
            cost_per_run=actor_config.get("cost_per_run", 0.05),
            average_runtime=actor_config.get("average_runtime"),
            input_schema=actor_config.get("input_schema", {}),
            output_format=actor_config.get("output_format", "json"),
            is_enabled=actor_config.get("enabled", True)
        )
        
        log.info("Actor details retrieved successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to get actor details", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get actor details: {str(e)}"
        )


@router.get("/categories", tags=["Actors"])
async def list_categories() -> Dict[str, List[str]]:
    """
    Get all available actor categories with their actors.
    
    **Returns:** Dictionary mapping categories to lists of actor names.
    """
    log = logger.bind()
    log.info("Listing actor categories")
    
    try:
        categories = {}
        
        for config in ACTOR_CONFIGS.values():
            category = config.get("category", "general")
            actor_name = config["name"]
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(actor_name)
        
        # Sort actors within each category
        for category in categories:
            categories[category].sort()
        
        log.info(
            "Categories listed successfully",
            category_count=len(categories)
        )
        
        return categories
        
    except Exception as e:
        log.error("Failed to list categories", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list categories: {str(e)}"
        ) 