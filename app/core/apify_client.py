"""
Apify service wrapper.

Provides a simplified interface to the Apify client for the prospect analyzer.
"""

from typing import Dict, Any, Optional, List
import structlog

try:
    from apify_client import ApifyClient
    from apify_client import ApifyClientAsync
    APIFY_CLIENT_AVAILABLE = True
except ImportError:
    APIFY_CLIENT_AVAILABLE = False

from app.core.config import settings


logger = structlog.get_logger(__name__)


class ApifyService:
    """
    Service wrapper for Apify client operations.
    
    Provides a simplified interface for common Apify operations
    used throughout the prospect analyzer.
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the Apify service.
        
        Args:
            api_token: Apify API token. If not provided, uses config.
        """
        if not APIFY_CLIENT_AVAILABLE:
            logger.warning("Apify client not available, running in mock mode")
            self.client = None
            self.async_client = None
            return
        
        self.api_token = api_token or settings.apify_api_token
        
        if not self.api_token:
            logger.warning("No Apify API token provided, running in mock mode")
            self.client = None
            self.async_client = None
            return
        
        try:
            self.client = ApifyClient(token=self.api_token)
            self.async_client = ApifyClientAsync(token=self.api_token)
            logger.info("Apify service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Apify client", error=str(e))
            self.client = None
            self.async_client = None
    
    def is_available(self) -> bool:
        """Check if Apify client is available and configured."""
        return self.client is not None
    
    async def run_actor_async(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        timeout_secs: Optional[int] = None,
        memory_mbytes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run an actor asynchronously.
        
        Args:
            actor_id: ID of the actor to run
            input_data: Input data for the actor
            timeout_secs: Timeout in seconds
            memory_mbytes: Memory limit in MB
            
        Returns:
            Actor run result
        """
        if not self.is_available():
            logger.warning("Apify client not available, returning mock data")
            return self._mock_actor_result(actor_id, input_data)
        
        try:
            # Use the correct parameter names based on latest Apify client API
            call_params = {
                "run_input": input_data
            }
            
            if timeout_secs:
                call_params["timeout_secs"] = timeout_secs
            else:
                call_params["timeout_secs"] = settings.default_timeout
                
            if memory_mbytes:
                call_params["memory_mbytes"] = memory_mbytes
            
            run = await self.async_client.actor(actor_id).call(**call_params)
            
            # Get dataset items
            items = []
            if run.get("defaultDatasetId"):
                dataset_client = self.async_client.dataset(run["defaultDatasetId"])
                items_result = await dataset_client.list_items()
                
                # Handle different types of responses from the Apify client
                if hasattr(items_result, 'items'):
                    # If it's a paginated response object with an items attribute
                    items = list(items_result.items)
                elif hasattr(items_result, '__iter__') and not isinstance(items_result, (str, bytes)):
                    # If it's iterable (like ListPage), convert to list
                    items = list(items_result)
                elif isinstance(items_result, dict) and "items" in items_result:
                    # If it's a dict with items key
                    items = items_result["items"]
                else:
                    # Fallback: assume it's already a list or convert to list
                    items = list(items_result) if items_result else []
            
            return {
                "run": run,
                "items": items or [],
                "success": True
            }
            
        except Exception as e:
            logger.error("Actor run failed", actor_id=actor_id, error=str(e))
            return {
                "run": {"id": "error", "status": "FAILED"},
                "items": [],
                "success": False,
                "error": str(e)
            }
    
    def run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        timeout_secs: Optional[int] = None,
        memory_mbytes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run an actor synchronously.
        
        Args:
            actor_id: ID of the actor to run
            input_data: Input data for the actor
            timeout_secs: Timeout in seconds
            memory_mbytes: Memory limit in MB
            
        Returns:
            Actor run result
        """
        if not self.is_available():
            logger.warning("Apify client not available, returning mock data")
            return self._mock_actor_result(actor_id, input_data)
        
        try:
            # Use the correct parameter names based on latest Apify client API
            call_params = {
                "run_input": input_data
            }
            
            if timeout_secs:
                call_params["timeout_secs"] = timeout_secs
            else:
                call_params["timeout_secs"] = settings.default_timeout
                
            if memory_mbytes:
                call_params["memory_mbytes"] = memory_mbytes
            
            run = self.client.actor(actor_id).call(**call_params)
            
            # Get dataset items
            items = []
            if run.get("defaultDatasetId"):
                dataset_client = self.client.dataset(run["defaultDatasetId"])
                items_result = dataset_client.list_items()
                
                # Handle different types of responses from the Apify client
                if hasattr(items_result, 'items'):
                    # If it's a paginated response object with an items attribute
                    items = list(items_result.items)
                elif hasattr(items_result, '__iter__') and not isinstance(items_result, (str, bytes)):
                    # If it's iterable (like ListPage), convert to list
                    items = list(items_result)
                elif isinstance(items_result, dict) and "items" in items_result:
                    # If it's a dict with items key
                    items = items_result["items"]
                else:
                    # Fallback: assume it's already a list or convert to list
                    items = list(items_result) if items_result else []
            
            return {
                "run": run,
                "items": items or [],
                "success": True
            }
            
        except Exception as e:
            logger.error("Actor run failed", actor_id=actor_id, error=str(e))
            return {
                "run": {"id": "error", "status": "FAILED"},
                "items": [],
                "success": False,
                "error": str(e)
            }
    
    def get_actor_info(self, actor_id: str) -> Dict[str, Any]:
        """
        Get information about an actor.
        
        Args:
            actor_id: ID of the actor
            
        Returns:
            Actor information
        """
        if not self.is_available():
            return {
                "id": actor_id,
                "name": f"Mock Actor {actor_id}",
                "description": "Mock actor for testing",
                "isPublic": False
            }
        
        try:
            return self.client.actor(actor_id).get()
        except Exception as e:
            logger.error("Failed to get actor info", actor_id=actor_id, error=str(e))
            return {"error": str(e)}
    
    def _mock_actor_result(self, actor_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock actor result for testing.
        
        Args:
            actor_id: ID of the actor
            input_data: Input data
            
        Returns:
            Mock result
        """
        # Basic mock result structure
        mock_run = {
            "id": f"mock-run-{actor_id}",
            "status": "SUCCEEDED",
            "statusMessage": "Mock run completed",
            "computeUnits": 0.1,
            "defaultDatasetId": f"mock-dataset-{actor_id}"
        }
        
        # Mock items based on input
        mock_items = []
        if "profileUrls" in input_data:
            for url in input_data["profileUrls"]:
                mock_items.append({
                    "profile": {
                        "fullName": "Mock User",
                        "headline": "Mock Professional",
                        "location": "Mock City",
                        "connectionsCount": 500
                    },
                    "experience": [
                        {
                            "title": "Mock Position",
                            "company": "Mock Company",
                            "duration": "2+ years"
                        }
                    ],
                    "education": [
                        {
                            "school": "Mock University",
                            "degree": "Mock Degree"
                        }
                    ],
                    "skills": [
                        {"name": "Mock Skill 1", "endorsements": 15},
                        {"name": "Mock Skill 2", "endorsements": 12}
                    ]
                })
        
        return {
            "run": mock_run,
            "items": mock_items,
            "success": True
        } 