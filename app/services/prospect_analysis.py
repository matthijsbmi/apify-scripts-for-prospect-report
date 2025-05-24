"""
Prospect Analysis Service.

This service orchestrates the entire prospect analysis workflow,
coordinating all actors and services to provide comprehensive 
prospect reports.
"""

import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

import structlog

from app.core.apify_client import ApifyService
from app.orchestration.orchestrator import ActorOrchestrator
from app.cost.manager import CostManager
from app.services.storage import InMemoryStorageService

# Import all actor services
from app.actors.linkedin import LinkedInService
from app.actors.social import SocialMediaService  
from app.actors.company import CompanyDataService

# Import validation if needed
try:
    from app.validation import ValidationService
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


logger = structlog.get_logger(__name__)


class ProspectAnalysisService:
    """
    Main service for conducting comprehensive prospect analysis.
    
    This service coordinates all data collection actors, manages costs,
    validates results, and generates comprehensive prospect reports.
    """
    
    def __init__(
        self,
        apify_service: ApifyService,
        storage_service: Optional[InMemoryStorageService] = None,
        cost_manager: Optional[CostManager] = None,
        orchestrator: Optional[ActorOrchestrator] = None,
        enable_validation: bool = False
    ):
        """Initialize the prospect analysis service."""
        self.apify_service = apify_service
        self.storage = storage_service or InMemoryStorageService()
        self.cost_manager = cost_manager or CostManager()
        self.orchestrator = orchestrator or ActorOrchestrator(apify_service, cost_manager)
        
        # Initialize actor services
        self.linkedin_service = LinkedInService(apify_service)
        self.social_media_service = SocialMediaService(apify_service)
        self.company_data_service = CompanyDataService(apify_service)
        
        # Initialize validation if available and requested
        self.validation_service = None
        if enable_validation and VALIDATION_AVAILABLE:
            self.validation_service = ValidationService()
        
        logger.info(
            "ProspectAnalysisService initialized",
            validation_enabled=self.validation_service is not None
        )
    
    async def analyze_prospect(
        self,
        prospect_data: Dict[str, Any],
        analysis_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single prospect using all available data sources.
        
        Args:
            prospect_data: Basic prospect information (name, LinkedIn URL, company, etc.)
            analysis_params: Analysis configuration and preferences
            
        Returns:
            Comprehensive prospect analysis report
        """
        analysis_params = analysis_params or {}
        prospect_id = str(uuid.uuid4())
        
        log = logger.bind(prospect_id=prospect_id)
        log.info("Starting prospect analysis", prospect_data=prospect_data)
        
        start_time = time.time()
        
        try:
            # Validate input data
            self._validate_prospect_data(prospect_data)
            self._validate_analysis_params(analysis_params)
            
            # Set budget constraints if provided
            if "max_budget" in analysis_params:
                self.cost_manager.set_budget(analysis_params["max_budget"])
                log.info("Budget set", budget=analysis_params["max_budget"])
            
            # Check cache for existing results
            cache_key = self._generate_cache_key(prospect_data)
            if analysis_params.get("use_cache", True):
                cached_result = await self._check_cache(cache_key)
                if cached_result:
                    log.info("Returning cached result")
                    return cached_result
            
            # Store initial prospect data
            await self.storage.create_prospect_data(prospect_id, prospect_data)
            
            # Build execution plan based on available inputs
            execution_plan = self._build_execution_plan(prospect_data, analysis_params)
            log.info("Execution plan created", plan_summary=execution_plan["summary"])
            
            # Execute data collection plan
            raw_results = await self._execute_data_collection(execution_plan)
            
            # Process and validate results
            processed_results = await self._process_results(raw_results)
            
            # Generate analysis summary and insights
            analysis_summary = self._generate_analysis_summary(processed_results)
            
            # Calculate total costs
            cost_breakdown = self.cost_manager.get_cost_breakdown()
            
            # Prepare final report
            execution_time = time.time() - start_time
            report = self._prepare_final_report(
                prospect_id=prospect_id,
                prospect_data=prospect_data,
                results=processed_results,
                summary=analysis_summary,
                cost_breakdown=cost_breakdown,
                execution_time=execution_time,
                analysis_params=analysis_params
            )
            
            # Store final report
            await self.storage.create_analysis_result(prospect_id, report)
            
            # Cache results
            if analysis_params.get("cache_results", True):
                await self._cache_result(cache_key, report)
            
            log.info(
                "Prospect analysis completed",
                execution_time=execution_time,
                total_cost=cost_breakdown.get("total_cost", 0)
            )
            
            return report
            
        except Exception as e:
            log.error("Prospect analysis failed", error=str(e))
            
            # Create error report
            error_report = {
                "prospect_id": prospect_id,
                "status": "failed",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "partial_results": getattr(self, '_partial_results', {}),
                "cost_breakdown": self.cost_manager.get_cost_breakdown()
            }
            
            # Store error report
            await self.storage.create_analysis_result(prospect_id, error_report)
            
            raise
    
    async def analyze_batch(
        self,
        prospects: List[Dict[str, Any]],
        global_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple prospects in batch mode.
        
        Args:
            prospects: List of prospect data dictionaries
            global_params: Global analysis parameters applied to all prospects
            
        Returns:
            Batch analysis results with individual prospect reports
        """
        global_params = global_params or {}
        batch_id = str(uuid.uuid4())
        
        log = logger.bind(batch_id=batch_id, prospect_count=len(prospects))
        log.info("Starting batch prospect analysis")
        
        start_time = time.time()
        results = []
        successful_analyses = 0
        failed_analyses = 0
        
        for i, prospect in enumerate(prospects):
            prospect_log = log.bind(prospect_index=i+1)
            
            try:
                # Merge global and prospect-specific parameters
                prospect_data = prospect.get("data", prospect)
                prospect_params = prospect.get("params", {})
                merged_params = {**global_params, **prospect_params}
                
                # Analyze individual prospect
                result = await self.analyze_prospect(prospect_data, merged_params)
                
                results.append({
                    "index": i + 1,
                    "prospect_id": result["prospect_id"],
                    "status": "completed",
                    "result": result
                })
                
                successful_analyses += 1
                prospect_log.info("Prospect analysis completed")
                
            except Exception as e:
                prospect_log.error("Prospect analysis failed", error=str(e))
                
                results.append({
                    "index": i + 1,
                    "prospect_id": str(uuid.uuid4()),
                    "status": "failed",
                    "error": str(e),
                    "prospect_data": prospect.get("data", prospect)
                })
                
                failed_analyses += 1
        
        # Generate batch summary
        execution_time = time.time() - start_time
        batch_report = {
            "batch_id": batch_id,
            "status": "completed",
            "execution_time": execution_time,
            "statistics": {
                "total_prospects": len(prospects),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "success_rate": successful_analyses / len(prospects) if prospects else 0
            },
            "total_cost": sum(
                r.get("result", {}).get("cost_breakdown", {}).get("total_cost", 0)
                for r in results if r["status"] == "completed"
            ),
            "results": results,
            "generated_at": datetime.now().isoformat()
        }
        
        log.info(
            "Batch analysis completed",
            successful=successful_analyses,
            failed=failed_analyses,
            execution_time=execution_time
        )
        
        return batch_report
    
    def _validate_prospect_data(self, prospect_data: Dict[str, Any]) -> None:
        """Validate prospect input data."""
        if not isinstance(prospect_data, dict):
            raise ValueError("Prospect data must be a dictionary")
        
        # At minimum, we need some identifier (name, LinkedIn URL, or company)
        identifiers = ["name", "linkedin_url", "profile_url", "company", "email"]
        if not any(prospect_data.get(field) for field in identifiers):
            raise ValueError(
                f"Prospect data must contain at least one identifier: {identifiers}"
            )
    
    def _validate_analysis_params(self, params: Dict[str, Any]) -> None:
        """Validate analysis parameters."""
        valid_params = {
            "max_budget", "use_cache", "cache_results", "data_freshness",
            "include_linkedin", "include_social_media", "include_company_data",
            "detail_level", "timeout"
        }
        
        invalid_params = set(params.keys()) - valid_params
        if invalid_params:
            raise ValueError(f"Invalid analysis parameters: {invalid_params}")
        
        # Validate specific parameter values
        if "max_budget" in params and (not isinstance(params["max_budget"], (int, float)) or params["max_budget"] <= 0):
            raise ValueError("max_budget must be a positive number")
        
        if "detail_level" in params and params["detail_level"] not in ["basic", "standard", "comprehensive"]:
            raise ValueError("detail_level must be 'basic', 'standard', or 'comprehensive'")
    
    def _build_execution_plan(
        self,
        prospect_data: Dict[str, Any],
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build execution plan based on available data and parameters."""
        plan = {
            "actors": [],
            "dependencies": {},
            "estimated_cost": 0.0,
            "estimated_time": 0.0,
            "summary": {}
        }
        
        # Determine which actors to use based on available data and preferences
        if analysis_params.get("include_linkedin", True):
            if prospect_data.get("linkedin_url") or prospect_data.get("profile_url"):
                plan["actors"].extend(["linkedin_profile", "linkedin_posts"])
                plan["summary"]["linkedin"] = "Profile and posts data"
            
            if prospect_data.get("company"):
                plan["actors"].append("linkedin_company")
                plan["summary"]["linkedin_company"] = "Company data from LinkedIn"
        
        if analysis_params.get("include_social_media", True):
            if prospect_data.get("company") or prospect_data.get("name"):
                plan["actors"].extend(["facebook_pages", "twitter_scraper"])
                plan["summary"]["social_media"] = "Facebook and Twitter data"
        
        if analysis_params.get("include_company_data", True):
            if prospect_data.get("company") or prospect_data.get("company_domain"):
                plan["actors"].extend(["crunchbase", "duns", "zoominfo"])
                plan["summary"]["company_data"] = "Financial and company data"
        
        # Set dependencies - company actors can run in parallel after basic profile data
        if "linkedin_profile" in plan["actors"]:
            for actor in ["linkedin_company", "facebook_pages", "twitter_scraper"]:
                if actor in plan["actors"]:
                    plan["dependencies"][actor] = ["linkedin_profile"]
        
        # Estimate costs and time
        plan["estimated_cost"] = len(plan["actors"]) * 0.05  # Rough estimate
        plan["estimated_time"] = len(plan["actors"]) * 30  # Rough estimate in seconds
        
        return plan
    
    async def _execute_data_collection(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the data collection plan using the orchestrator."""
        results = {}
        
        for actor_type in execution_plan["actors"]:
            try:
                if actor_type == "linkedin_profile":
                    # This would normally use the orchestrator, but for now direct call
                    result = await self.linkedin_service.get_profile_data(
                        self._get_linkedin_url_from_plan()
                    )
                    results["linkedin_profile"] = result
                
                elif actor_type == "linkedin_posts":
                    result = await self.linkedin_service.get_posts_data(
                        self._get_linkedin_url_from_plan()
                    )
                    results["linkedin_posts"] = result
                
                elif actor_type == "linkedin_company":
                    result = await self.linkedin_service.get_company_data(
                        self._get_company_url_from_plan()
                    )
                    results["linkedin_company"] = result
                
                elif actor_type in ["facebook_pages", "twitter_scraper"]:
                    result = await self.social_media_service.collect_social_data(
                        self._get_social_inputs_from_plan()
                    )
                    results["social_media"] = result
                
                elif actor_type in ["crunchbase", "duns", "zoominfo"]:
                    result = await self.company_data_service.collect_company_data(
                        self._get_company_inputs_from_plan()
                    )
                    results["company_data"] = result
                    
            except Exception as e:
                logger.warning(f"Actor {actor_type} failed", error=str(e))
                results[actor_type] = {"error": str(e)}
        
        return results
    
    async def _process_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate raw results from actors."""
        processed = {}
        
        for data_type, raw_data in raw_results.items():
            if "error" in raw_data:
                processed[data_type] = raw_data
                continue
            
            try:
                # Apply validation if available
                if self.validation_service:
                    validation_result = self.validation_service.validate_and_score(
                        data=raw_data,
                        data_type=data_type
                    )
                    processed[data_type] = {
                        "data": raw_data,
                        "validation": validation_result
                    }
                else:
                    processed[data_type] = {"data": raw_data}
                    
            except Exception as e:
                logger.warning(f"Failed to process {data_type}", error=str(e))
                processed[data_type] = {
                    "data": raw_data,
                    "processing_error": str(e)
                }
        
        return processed
    
    def _generate_analysis_summary(self, processed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level analysis summary and insights."""
        summary = {
            "data_sources_found": [],
            "data_completeness": {},
            "key_insights": [],
            "data_quality_overview": {},
            "recommendations": []
        }
        
        # Count successful data sources
        for source, result in processed_results.items():
            if "error" not in result and result.get("data"):
                summary["data_sources_found"].append(source)
        
        # Calculate data completeness
        total_sources = len(processed_results)
        successful_sources = len(summary["data_sources_found"])
        summary["data_completeness"] = {
            "percentage": (successful_sources / total_sources * 100) if total_sources > 0 else 0,
            "sources_found": successful_sources,
            "total_sources": total_sources
        }
        
        # Generate insights based on available data
        if "linkedin_profile" in summary["data_sources_found"]:
            summary["key_insights"].append("Professional profile data available")
        
        if "social_media" in summary["data_sources_found"]:
            summary["key_insights"].append("Social media presence identified")
        
        if "company_data" in summary["data_sources_found"]:
            summary["key_insights"].append("Company financial data available")
        
        # Add recommendations
        if successful_sources < total_sources:
            summary["recommendations"].append("Consider alternative data sources for missing information")
        
        if successful_sources >= 3:
            summary["recommendations"].append("High data availability - proceed with confidence")
        
        return summary
    
    def _prepare_final_report(
        self,
        prospect_id: str,
        prospect_data: Dict[str, Any],
        results: Dict[str, Any],
        summary: Dict[str, Any],
        cost_breakdown: Dict[str, Any],
        execution_time: float,
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare the final comprehensive prospect report."""
        return {
            "prospect_id": prospect_id,
            "status": "completed",
            "prospect_data": prospect_data,
            "analysis_params": analysis_params,
            "results": results,
            "summary": summary,
            "cost_breakdown": cost_breakdown,
            "execution_metadata": {
                "execution_time": execution_time,
                "generated_at": datetime.now().isoformat(),
                "data_sources_used": list(results.keys()),
                "validation_enabled": self.validation_service is not None
            }
        }
    
    def _generate_cache_key(self, prospect_data: Dict[str, Any]) -> str:
        """Generate cache key for prospect data."""
        # Use the most stable identifiers for caching
        key_parts = []
        for field in ["linkedin_url", "profile_url", "email", "name", "company"]:
            if prospect_data.get(field):
                key_parts.append(f"{field}:{prospect_data[field]}")
        
        if not key_parts:
            key_parts.append(f"data_hash:{hash(str(sorted(prospect_data.items())))}")
        
        return "|".join(key_parts)
    
    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if cached result exists for the prospect."""
        # For now, return None - cache implementation would go here
        return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache the analysis result."""
        # Cache implementation would go here
        pass
    
    def _get_linkedin_url_from_plan(self) -> str:
        """Extract LinkedIn URL from current execution context."""
        # This would be populated from the current prospect data
        return "https://linkedin.com/in/sample"
    
    def _get_company_url_from_plan(self) -> str:
        """Extract company URL from current execution context."""
        return "https://linkedin.com/company/sample"
    
    def _get_social_inputs_from_plan(self) -> Dict[str, Any]:
        """Extract social media inputs from current execution context."""
        return {"company_name": "Sample Company"}
    
    def _get_company_inputs_from_plan(self) -> Dict[str, Any]:
        """Extract company data inputs from current execution context."""
        return {"company_name": "Sample Company"} 