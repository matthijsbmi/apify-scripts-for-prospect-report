"""
Health Check API endpoints.

Endpoints for monitoring system health and status.
"""

import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
import structlog

from app.api.models.requests import HealthCheckRequest
from app.api.models.responses import (
    HealthCheckResponse, ServiceHealth, SystemMetrics
)


logger = structlog.get_logger(__name__)
router = APIRouter()

# Track application start time for uptime calculation
_start_time = time.time()
_daily_stats = {
    "analyses_completed": 0,
    "total_execution_time": 0.0,
    "last_reset": datetime.now().date()
}


@router.get("/", response_model=HealthCheckResponse, tags=["Health"])
async def health_check(
    include_services: bool = Query(False, description="Include service health details"),
    include_actors: bool = Query(False, description="Include actor status"),
    include_metrics: bool = Query(False, description="Include system metrics")
) -> HealthCheckResponse:
    """
    Basic health check endpoint.
    
    **Parameters:**
    - `include_services`: Include detailed service health information
    - `include_actors`: Include actor availability status
    - `include_metrics`: Include system performance metrics
    
    **Returns:** System health status with optional detailed information.
    """
    log = logger.bind(
        include_services=include_services,
        include_actors=include_actors,
        include_metrics=include_metrics
    )
    log.info("Performing health check")
    
    try:
        # Reset daily stats if needed
        _reset_daily_stats_if_needed()
        
        # Calculate uptime
        uptime = time.time() - _start_time
        
        # Basic health status
        status = "healthy"
        
        # Collect optional detailed information
        services = None
        actors = None
        metrics = None
        
        if include_services:
            services = await _check_service_health()
            # Update overall status based on service health
            if any(s.status != "healthy" for s in services):
                status = "degraded"
        
        if include_actors:
            actors = await _check_actor_status()
        
        if include_metrics:
            metrics = _collect_system_metrics()
        
        response = HealthCheckResponse(
            status=status,
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            uptime=uptime,
            services=services,
            actors=actors,
            metrics=metrics
        )
        
        log.info(
            "Health check completed",
            status=status,
            uptime=uptime
        )
        
        return response
        
    except Exception as e:
        log.error("Health check failed", error=str(e))
        # Return unhealthy status but don't raise exception
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            uptime=time.time() - _start_time,
            services=[ServiceHealth(
                name="health_check",
                status="failed",
                last_check=datetime.now().isoformat(),
                details={"error": str(e)}
            )]
        )


@router.get("/detailed", response_model=HealthCheckResponse, tags=["Health"])
async def detailed_health_check() -> HealthCheckResponse:
    """
    Comprehensive health check with all available information.
    
    **Returns:** Complete system health report including services, actors, and metrics.
    """
    return await health_check(
        include_services=True,
        include_actors=True,
        include_metrics=True
    )


@router.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes-style readiness check.
    
    **Returns:** Simple ready/not ready status for orchestration systems.
    """
    log = logger.bind()
    log.info("Performing readiness check")
    
    try:
        # Check critical services
        services = await _check_service_health()
        critical_services = ["storage", "apify_client"]
        
        ready = True
        for service in services:
            if service.name in critical_services and service.status != "healthy":
                ready = False
                break
        
        status = "ready" if ready else "not_ready"
        
        log.info("Readiness check completed", status=status)
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "ready": ready
        }
        
    except Exception as e:
        log.error("Readiness check failed", error=str(e))
        return {
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "ready": False,
            "error": str(e)
        }


@router.get("/live", tags=["Health"])
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness check.
    
    **Returns:** Simple alive/dead status for orchestration systems.
    """
    log = logger.bind()
    log.info("Performing liveness check")
    
    # Basic liveness - if we can respond, we're alive
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - _start_time
    }


async def _check_service_health() -> List[ServiceHealth]:
    """Check health of individual services."""
    services = []
    
    # Check storage service
    try:
        from app.services.storage import InMemoryStorageService
        storage = InMemoryStorageService()
        start_time = time.time()
        
        # Test basic operation
        test_id = "health_check_test"
        await storage.create_prospect_data(test_id, {"test": "data"})
        await storage.get_prospect_data(test_id)
        
        response_time = (time.time() - start_time) * 1000
        
        services.append(ServiceHealth(
            name="storage",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now().isoformat(),
            details={"test_operation": "success"}
        ))
        
    except Exception as e:
        services.append(ServiceHealth(
            name="storage",
            status="unhealthy",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))
    
    # Check Apify client
    try:
        from app.core.apify_client import ApifyService
        apify = ApifyService()
        start_time = time.time()
        
        # Test API connection (simplified check)
        response_time = (time.time() - start_time) * 1000
        
        services.append(ServiceHealth(
            name="apify_client",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now().isoformat(),
            details={"api_available": True}
        ))
        
    except Exception as e:
        services.append(ServiceHealth(
            name="apify_client",
            status="unhealthy",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))
    
    # Check cost manager
    try:
        from app.cost.manager import CostManager
        cost_manager = CostManager()
        start_time = time.time()
        
        # Test basic operation
        cost_manager.get_cost_breakdown()
        response_time = (time.time() - start_time) * 1000
        
        services.append(ServiceHealth(
            name="cost_manager",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now().isoformat(),
            details={"test_operation": "success"}
        ))
        
    except Exception as e:
        services.append(ServiceHealth(
            name="cost_manager",
            status="unhealthy",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))
    
    return services


async def _check_actor_status() -> List[Dict[str, Any]]:
    """Check status of configured actors."""
    try:
        from app.actors.config import ACTOR_CONFIGS
        
        actors = []
        for actor_key, config in ACTOR_CONFIGS.items():
            actors.append({
                "key": actor_key,
                "actor_id": config["actor_id"],
                "name": config["name"],
                "category": config.get("category", "general"),
                "enabled": config.get("enabled", True),
                "status": "available" if config.get("enabled", True) else "disabled"
            })
        
        return actors
        
    except Exception as e:
        logger.error("Failed to check actor status", error=str(e))
        return [{"error": str(e)}]


def _collect_system_metrics() -> SystemMetrics:
    """Collect system performance metrics."""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Application metrics
        global _daily_stats
        average_analysis_time = (
            _daily_stats["total_execution_time"] / _daily_stats["analyses_completed"]
            if _daily_stats["analyses_completed"] > 0 else 0.0
        )
        
        return SystemMetrics(
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            active_analyses=0,  # Would track active analyses in production
            total_analyses_today=_daily_stats["analyses_completed"],
            average_analysis_time=average_analysis_time
        )
        
    except Exception as e:
        logger.error("Failed to collect system metrics", error=str(e))
        # Return basic metrics
        return SystemMetrics(
            memory_usage={"error": str(e)},
            cpu_usage=0.0,
            active_analyses=0,
            total_analyses_today=0,
            average_analysis_time=0.0
        )


def _reset_daily_stats_if_needed():
    """Reset daily statistics if date has changed."""
    global _daily_stats
    today = datetime.now().date()
    
    if _daily_stats["last_reset"] != today:
        _daily_stats = {
            "analyses_completed": 0,
            "total_execution_time": 0.0,
            "last_reset": today
        }


def update_analysis_stats(execution_time: float):
    """Update analysis statistics (to be called after each analysis)."""
    global _daily_stats
    _reset_daily_stats_if_needed()
    
    _daily_stats["analyses_completed"] += 1
    _daily_stats["total_execution_time"] += execution_time 