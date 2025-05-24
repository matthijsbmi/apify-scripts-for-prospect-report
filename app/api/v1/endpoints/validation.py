"""
Validation API endpoints.

Provides endpoints for validating data quality and scoring
across all supported data types.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import structlog

from app.validation import ValidationService
from app.models.data import (
    LinkedInProfileData, LinkedInPostsData, LinkedInCompanyData,
    FacebookData, TwitterData, SocialMediaData, CompanyData
)


logger = structlog.get_logger(__name__)
router = APIRouter()


class ValidationRequest(BaseModel):
    """Request model for single data validation."""
    data: Dict[str, Any] = Field(..., description="Data to validate")
    data_type: str = Field(..., description="Type of data (linkedin_profile, company_data, etc.)")
    strict_mode: bool = Field(False, description="Use strict validation rules")
    include_quality_analysis: bool = Field(True, description="Include detailed quality analysis")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for validation")


class BatchValidationRequest(BaseModel):
    """Request model for batch data validation."""
    items: List[Dict[str, Any]] = Field(..., description="List of data items to validate")
    strict_mode: bool = Field(False, description="Use strict validation rules")
    include_quality_analysis: bool = Field(True, description="Include detailed quality analysis")


class QualityComparisonRequest(BaseModel):
    """Request model for data quality comparison."""
    items: List[Dict[str, Any]] = Field(..., description="List of data items to compare")
    criteria: Optional[List[str]] = Field(None, description="Comparison criteria")


class QualityReportRequest(BaseModel):
    """Request model for quality report generation."""
    items: List[Dict[str, Any]] = Field(..., description="List of data items to include")
    format: str = Field("detailed", description="Report format (summary, detailed, executive)")


# Initialize validation service
validation_service = ValidationService()


@router.post("/validate", tags=["Validation"])
async def validate_data(request: ValidationRequest) -> Dict[str, Any]:
    """
    Validate a single data item and return quality assessment.
    
    Performs comprehensive validation including:
    - Schema validation
    - Completeness assessment
    - Quality scoring
    - Anomaly detection
    - Recommendations
    """
    log = logger.bind(
        data_type=request.data_type,
        strict_mode=request.strict_mode,
        include_quality=request.include_quality_analysis
    )
    log.info("Validating single data item")
    
    try:
        result = validation_service.validate_and_score(
            data=request.data,
            data_type=request.data_type,
            strict_mode=request.strict_mode,
            include_quality_analysis=request.include_quality_analysis,
            context=request.context,
        )
        
        log.info(
            "Validation completed",
            is_valid=result.get("validation", {}).get("is_valid", False),
            confidence_score=result.get("validation", {}).get("confidence_score", 0.0),
        )
        
        return result
        
    except Exception as e:
        log.error("Validation failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/validate/batch", tags=["Validation"])
async def validate_batch(request: BatchValidationRequest) -> Dict[str, Any]:
    """
    Validate multiple data items and return batch analysis.
    
    Provides:
    - Individual validation results
    - Aggregate statistics
    - Common issues identification
    - Batch recommendations
    """
    log = logger.bind(
        item_count=len(request.items),
        strict_mode=request.strict_mode,
        include_quality=request.include_quality_analysis
    )
    log.info("Starting batch validation")
    
    try:
        result = validation_service.validate_multiple(
            data_items=request.items,
            strict_mode=request.strict_mode,
            include_quality_analysis=request.include_quality_analysis,
        )
        
        log.info(
            "Batch validation completed",
            total_items=result["statistics"]["total_items"],
            valid_items=result["statistics"]["valid_items"],
            invalid_items=result["statistics"]["invalid_items"],
        )
        
        return result
        
    except Exception as e:
        log.error("Batch validation failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Batch validation failed: {str(e)}"
        )


@router.post("/compare", tags=["Validation"])
async def compare_quality(request: QualityComparisonRequest) -> Dict[str, Any]:
    """
    Compare data quality across multiple items.
    
    Provides:
    - Quality rankings
    - Comparative analysis
    - Best/worst item identification
    - Improvement recommendations
    """
    log = logger.bind(
        item_count=len(request.items),
        criteria=request.criteria
    )
    log.info("Starting quality comparison")
    
    try:
        result = validation_service.compare_data_quality(
            data_items=request.items,
            comparison_criteria=request.criteria,
        )
        
        log.info(
            "Quality comparison completed",
            total_items=result["statistics"]["total_items"],
            avg_score=result["statistics"]["average_score"],
        )
        
        return result
        
    except Exception as e:
        log.error("Quality comparison failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Quality comparison failed: {str(e)}"
        )


@router.post("/report", tags=["Validation"])
async def generate_report(request: QualityReportRequest) -> Dict[str, Any]:
    """
    Generate comprehensive quality report.
    
    Available formats:
    - summary: High-level overview
    - detailed: Full analysis with recommendations
    - executive: Business-focused summary
    """
    log = logger.bind(
        item_count=len(request.items),
        format=request.format
    )
    log.info("Generating quality report")
    
    if request.format not in ["summary", "detailed", "executive"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid report format. Must be 'summary', 'detailed', or 'executive'"
        )
    
    try:
        result = validation_service.generate_quality_report(
            data_items=request.items,
            report_format=request.format,
        )
        
        log.info(
            "Quality report generated",
            format=request.format,
            total_items=len(request.items),
        )
        
        return result
        
    except Exception as e:
        log.error("Report generation failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/supported-types", tags=["Validation"])
async def get_supported_types() -> Dict[str, Any]:
    """
    Get list of supported data types for validation.
    
    Returns information about each supported data type including
    required fields, validation rules, and examples.
    """
    return {
        "supported_types": {
            "linkedin_profile": {
                "description": "LinkedIn profile data",
                "required_fields": ["full_name", "profile_url"],
                "optional_fields": [
                    "headline", "location", "summary", "experience",
                    "education", "skills", "profile_image", "connections_count"
                ],
                "validation_rules": [
                    "Valid LinkedIn profile URL format",
                    "Name must contain at least first and last name",
                    "Experience entries must have title and company"
                ]
            },
            "linkedin_posts": {
                "description": "LinkedIn posts data",
                "required_fields": ["profile_url", "posts"],
                "optional_fields": ["author_name", "post_count"],
                "validation_rules": [
                    "Valid LinkedIn profile URL",
                    "Posts must contain content or text",
                    "Recent activity within 6 months preferred"
                ]
            },
            "linkedin_company": {
                "description": "LinkedIn company data",
                "required_fields": ["name", "company_url"],
                "optional_fields": [
                    "description", "industry", "company_size",
                    "location", "website", "employee_count", "specialties"
                ],
                "validation_rules": [
                    "Valid LinkedIn company URL format",
                    "Company size should follow standard formats",
                    "Employee count must be positive"
                ]
            },
            "facebook_data": {
                "description": "Facebook page data",
                "required_fields": ["page_url", "name"],
                "optional_fields": ["posts", "page_info"],
                "validation_rules": [
                    "Valid Facebook page URL",
                    "Posts should have engagement metrics",
                    "Recent activity preferred"
                ]
            },
            "twitter_data": {
                "description": "Twitter/X profile data",
                "required_fields": ["handle"],
                "optional_fields": [
                    "profile_info", "tweets", "followers_count",
                    "following_count"
                ],
                "validation_rules": [
                    "Valid Twitter handle format",
                    "Follower counts must be non-negative",
                    "Tweet content should be present"
                ]
            },
            "social_media_data": {
                "description": "Combined social media data",
                "required_fields": ["has_data"],
                "optional_fields": ["facebook", "twitter"],
                "validation_rules": [
                    "At least one social media platform required",
                    "Multiple platforms increase quality score"
                ]
            },
            "company_data": {
                "description": "Company information data",
                "required_fields": ["name", "sources"],
                "optional_fields": [
                    "website", "financial", "funding", "industry",
                    "employees", "technologies"
                ],
                "validation_rules": [
                    "Valid data sources specified",
                    "Website URL format validation",
                    "Financial data consistency checks",
                    "Multiple sources increase confidence"
                ]
            }
        },
        "validation_levels": {
            "strict": "Enforces all optional fields and additional consistency checks",
            "standard": "Validates required fields and common optional fields"
        },
        "quality_scoring": {
            "components": [
                "completeness_score",
                "consistency_score", 
                "freshness_score",
                "validity_score"
            ],
            "overall_calculation": "Weighted average with validity (30%), completeness (30%), consistency (25%), freshness (15%)"
        }
    } 