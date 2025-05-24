"""
Data validation and quality scoring system.

This module provides comprehensive validation for all data types collected
from LinkedIn, social media, and company data sources.
"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse

import structlog

from app.models.data import (
    LinkedInProfileData, LinkedInPostsData, LinkedInCompanyData,
    FacebookData, TwitterData, SocialMediaData,
    CompanyData, CompanyFinancialData, CompanyEmployeeData
)


logger = structlog.get_logger(__name__)


class ValidationResult:
    """Container for validation results with detailed scoring."""
    
    def __init__(
        self,
        is_valid: bool,
        confidence_score: float,
        required_fields: Dict[str, Any],
        optional_fields: Dict[str, Any],
        issues: List[str],
        recommendations: List[str],
    ):
        self.is_valid = is_valid
        self.confidence_score = confidence_score
        self.required_fields = required_fields
        self.optional_fields = optional_fields
        self.issues = issues
        self.recommendations = recommendations
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "confidence_score": self.confidence_score,
            "confidence_level": self._interpret_score(self.confidence_score),
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def _interpret_score(self, score: float) -> str:
        """Interpret confidence score into human-readable levels."""
        if score >= 0.9:
            return "very high"
        elif score >= 0.75:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very low"


class DataValidator:
    """
    Comprehensive data validator for all collected data types.
    
    Validates data quality, completeness, and consistency across sources.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        self.validators = {
            "linkedin_profile": self._validate_linkedin_profile,
            "linkedin_posts": self._validate_linkedin_posts,
            "linkedin_company": self._validate_linkedin_company,
            "facebook_data": self._validate_facebook_data,
            "twitter_data": self._validate_twitter_data,
            "social_media_data": self._validate_social_media_data,
            "company_data": self._validate_company_data,
        }
    
    def validate_data(
        self,
        data: Any,
        data_type: str,
        strict_mode: bool = False
    ) -> ValidationResult:
        """
        Validate data based on its type.
        
        Args:
            data: Data to validate.
            data_type: Type of data being validated.
            strict_mode: Whether to use strict validation rules.
            
        Returns:
            ValidationResult with detailed scoring and recommendations.
            
        Raises:
            ValueError: If data type is not supported.
        """
        if data_type not in self.validators:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        log = logger.bind(data_type=data_type, strict_mode=strict_mode)
        log.info("Validating data")
        
        try:
            return self.validators[data_type](data, strict_mode)
        except Exception as e:
            log.error("Validation failed", error=str(e))
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                required_fields={"total": 0, "valid": 0, "details": {}},
                optional_fields={"total": 0, "valid": 0, "details": {}},
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Check data format and try again"],
            )
    
    def _validate_linkedin_profile(
        self,
        profile: LinkedInProfileData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate LinkedIn profile data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "full_name": self._validate_person_name(profile.full_name),
            "profile_url": self._validate_linkedin_url(profile.profile_url),
        }
        
        # Optional fields validation
        optional_fields = {
            "headline": self._validate_non_empty_string(profile.headline),
            "location": self._validate_location(profile.location),
            "summary": self._validate_text_content(profile.summary),
            "experience": self._validate_experience_list(profile.experience),
            "education": self._validate_education_list(profile.education),
            "skills": self._validate_skills_list(profile.skills),
            "profile_image": self._validate_image_url(profile.profile_image),
            "connections_count": self._validate_positive_number(profile.connections_count),
        }
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        # Check for issues
        if not required_fields["full_name"]["valid"]:
            issues.append("Missing or invalid full name")
            recommendations.append("Ensure profile has a valid full name")
        
        if not required_fields["profile_url"]["valid"]:
            issues.append("Missing or invalid LinkedIn profile URL")
            recommendations.append("Verify LinkedIn profile URL format")
        
        if strict_mode:
            if not optional_fields["experience"]["valid"]:
                issues.append("No work experience data")
                recommendations.append("Add work experience for better profile completeness")
            
            if not optional_fields["education"]["valid"]:
                issues.append("No education data")
                recommendations.append("Add education information")
        
        # Overall confidence calculation
        confidence_score = (required_score * 0.7) + (optional_score * 0.3)
        
        # Adjust for data richness
        if profile.experience and len(profile.experience) >= 3:
            confidence_score += 0.05
        if profile.skills and len(profile.skills) >= 5:
            confidence_score += 0.05
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_linkedin_posts(
        self,
        posts_data: LinkedInPostsData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate LinkedIn posts data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "profile_url": self._validate_linkedin_url(posts_data.profile_url),
            "posts_exist": {"valid": bool(posts_data.posts), "value": len(posts_data.posts or [])},
        }
        
        # Optional fields validation  
        optional_fields = {
            "author_name": self._validate_person_name(posts_data.author_name),
            "post_count": self._validate_positive_number(len(posts_data.posts or [])),
            "recent_activity": self._validate_recent_posts(posts_data.posts),
        }
        
        # Validate individual posts
        if posts_data.posts:
            post_validation = self._validate_post_list(posts_data.posts)
            optional_fields["post_quality"] = post_validation
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        # Check for issues
        if not posts_data.posts:
            issues.append("No posts found")
            recommendations.append("Verify profile has public posts or increase scraping limits")
        
        if posts_data.posts and len(posts_data.posts) < 5 and strict_mode:
            issues.append("Limited post data")
            recommendations.append("Consider increasing post scraping limit for better insights")
        
        confidence_score = (required_score * 0.6) + (optional_score * 0.4)
        
        return ValidationResult(
            is_valid=required_score >= 0.5,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_linkedin_company(
        self,
        company_data: LinkedInCompanyData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate LinkedIn company data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "name": self._validate_non_empty_string(company_data.name),
            "company_url": self._validate_linkedin_company_url(company_data.company_url),
        }
        
        # Optional fields validation
        optional_fields = {
            "description": self._validate_text_content(company_data.description),
            "industry": self._validate_non_empty_string(company_data.industry),
            "company_size": self._validate_company_size(company_data.company_size),
            "location": self._validate_location(company_data.location),
            "website": self._validate_website_url(company_data.website),
            "employee_count": self._validate_positive_number(company_data.employee_count),
            "specialties": self._validate_list_content(company_data.specialties),
        }
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        # Check for issues
        if not required_fields["name"]["valid"]:
            issues.append("Missing or invalid company name")
            recommendations.append("Verify company name is properly extracted")
        
        if not optional_fields["website"]["valid"] and strict_mode:
            issues.append("No company website")
            recommendations.append("Company website helps verify authenticity")
        
        confidence_score = (required_score * 0.7) + (optional_score * 0.3)
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_facebook_data(
        self,
        facebook_data: FacebookData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate Facebook data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "page_url": self._validate_facebook_url(facebook_data.page_url),
            "name": self._validate_non_empty_string(facebook_data.name),
        }
        
        # Optional fields validation
        optional_fields = {
            "posts_exist": {"valid": bool(facebook_data.posts), "value": len(facebook_data.posts or [])},
            "page_info": self._validate_dict_content(facebook_data.page_info),
            "recent_activity": self._validate_recent_posts(facebook_data.posts),
        }
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        confidence_score = (required_score * 0.6) + (optional_score * 0.4)
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_twitter_data(
        self,
        twitter_data: TwitterData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate Twitter data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "handle": self._validate_twitter_handle(twitter_data.handle),
        }
        
        # Optional fields validation
        optional_fields = {
            "profile_info": self._validate_dict_content(twitter_data.profile_info),
            "tweets_exist": {"valid": bool(twitter_data.tweets), "value": len(twitter_data.tweets or [])},
            "followers_count": self._validate_positive_number(twitter_data.followers_count),
            "following_count": self._validate_positive_number(twitter_data.following_count),
            "recent_activity": self._validate_recent_posts(twitter_data.tweets),
        }
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        confidence_score = (required_score * 0.5) + (optional_score * 0.5)
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_social_media_data(
        self,
        social_data: SocialMediaData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate combined social media data."""
        issues = []
        recommendations = []
        
        # Validate individual components
        facebook_valid = False
        twitter_valid = False
        
        if social_data.facebook:
            fb_result = self._validate_facebook_data(social_data.facebook, strict_mode)
            facebook_valid = fb_result.is_valid
        
        if social_data.twitter:
            tw_result = self._validate_twitter_data(social_data.twitter, strict_mode)
            twitter_valid = tw_result.is_valid
        
        # Required: at least one platform
        required_fields = {
            "has_data": {"valid": bool(social_data.facebook or social_data.twitter), "value": "has_social_data"},
        }
        
        # Optional: both platforms
        optional_fields = {
            "facebook_valid": {"valid": facebook_valid, "value": bool(social_data.facebook)},
            "twitter_valid": {"valid": twitter_valid, "value": bool(social_data.twitter)},
            "multiple_platforms": {
                "valid": bool(social_data.facebook and social_data.twitter),
                "value": "multiple_platforms"
            },
        }
        
        if not social_data.facebook and not social_data.twitter:
            issues.append("No social media data available")
            recommendations.append("Provide at least one social media platform data")
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        confidence_score = (required_score * 0.6) + (optional_score * 0.4)
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    def _validate_company_data(
        self,
        company_data: CompanyData,
        strict_mode: bool = False
    ) -> ValidationResult:
        """Validate company data."""
        issues = []
        recommendations = []
        
        # Required fields validation
        required_fields = {
            "name": self._validate_non_empty_string(company_data.name),
            "sources": self._validate_data_sources(company_data.sources),
        }
        
        # Optional fields validation
        optional_fields = {
            "website": self._validate_website_url(company_data.website),
            "financial_data": self._validate_financial_data(company_data.financial),
            "funding_info": self._validate_dict_content(company_data.funding),
            "industry_info": self._validate_dict_content(company_data.industry),
            "employee_data": self._validate_employee_data(company_data.employees),
            "technologies": self._validate_list_content(company_data.technologies),
        }
        
        # Check data richness
        data_sources_count = len(company_data.sources or [])
        if data_sources_count >= 3:
            optional_fields["multi_source"] = {"valid": True, "value": data_sources_count}
        
        # Calculate scores
        required_score = self._calculate_field_score(required_fields)
        optional_score = self._calculate_field_score(optional_fields)
        
        # Check for issues
        if not company_data.sources:
            issues.append("No data sources specified")
            recommendations.append("Specify which sources provided the company data")
        
        if strict_mode and not company_data.website:
            issues.append("No company website")
            recommendations.append("Company website is important for verification")
        
        confidence_score = (required_score * 0.6) + (optional_score * 0.4)
        
        # Bonus for multiple sources
        if data_sources_count >= 2:
            confidence_score += 0.1
        
        return ValidationResult(
            is_valid=required_score >= 0.8,
            confidence_score=min(confidence_score, 1.0),
            required_fields={
                "total": len(required_fields),
                "valid": sum(1 for f in required_fields.values() if f["valid"]),
                "details": required_fields,
            },
            optional_fields={
                "total": len(optional_fields),
                "valid": sum(1 for f in optional_fields.values() if f["valid"]),
                "details": optional_fields,
            },
            issues=issues,
            recommendations=recommendations,
        )
    
    # Helper validation methods
    def _validate_person_name(self, name: Optional[str]) -> Dict[str, Any]:
        """Validate a person's name."""
        if not name or not isinstance(name, str):
            return {"valid": False, "value": name, "issue": "Missing or invalid name"}
        
        name = name.strip()
        if len(name) < 2:
            return {"valid": False, "value": name, "issue": "Name too short"}
        
        # Check for reasonable name pattern
        if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
            return {"valid": False, "value": name, "issue": "Name contains invalid characters"}
        
        # Check for at least first and last name
        name_parts = name.split()
        if len(name_parts) < 2:
            return {"valid": False, "value": name, "issue": "Missing first or last name"}
        
        return {"valid": True, "value": name}
    
    def _validate_linkedin_url(self, url: Optional[str]) -> Dict[str, Any]:
        """Validate LinkedIn profile URL."""
        if not url or not isinstance(url, str):
            return {"valid": False, "value": url, "issue": "Missing LinkedIn URL"}
        
        try:
            parsed = urlparse(url)
            if parsed.netloc not in ['linkedin.com', 'www.linkedin.com']:
                return {"valid": False, "value": url, "issue": "Not a LinkedIn URL"}
            
            if '/in/' not in parsed.path:
                return {"valid": False, "value": url, "issue": "Invalid LinkedIn profile URL format"}
            
            return {"valid": True, "value": url}
        except Exception:
            return {"valid": False, "value": url, "issue": "Invalid URL format"}
    
    def _validate_linkedin_company_url(self, url: Optional[str]) -> Dict[str, Any]:
        """Validate LinkedIn company URL."""
        if not url or not isinstance(url, str):
            return {"valid": False, "value": url, "issue": "Missing LinkedIn company URL"}
        
        try:
            parsed = urlparse(url)
            if parsed.netloc not in ['linkedin.com', 'www.linkedin.com']:
                return {"valid": False, "value": url, "issue": "Not a LinkedIn URL"}
            
            if '/company/' not in parsed.path:
                return {"valid": False, "value": url, "issue": "Invalid LinkedIn company URL format"}
            
            return {"valid": True, "value": url}
        except Exception:
            return {"valid": False, "value": url, "issue": "Invalid URL format"}
    
    def _validate_facebook_url(self, url: Optional[str]) -> Dict[str, Any]:
        """Validate Facebook page URL."""
        if not url or not isinstance(url, str):
            return {"valid": False, "value": url, "issue": "Missing Facebook URL"}
        
        try:
            parsed = urlparse(url)
            if 'facebook.com' not in parsed.netloc:
                return {"valid": False, "value": url, "issue": "Not a Facebook URL"}
            
            return {"valid": True, "value": url}
        except Exception:
            return {"valid": False, "value": url, "issue": "Invalid URL format"}
    
    def _validate_twitter_handle(self, handle: Optional[str]) -> Dict[str, Any]:
        """Validate Twitter handle."""
        if not handle or not isinstance(handle, str):
            return {"valid": False, "value": handle, "issue": "Missing Twitter handle"}
        
        # Remove @ if present
        clean_handle = handle.lstrip('@')
        
        if not re.match(r'^[a-zA-Z0-9_]{1,15}$', clean_handle):
            return {"valid": False, "value": handle, "issue": "Invalid Twitter handle format"}
        
        return {"valid": True, "value": handle}
    
    def _validate_website_url(self, url: Optional[str]) -> Dict[str, Any]:
        """Validate website URL."""
        if not url or not isinstance(url, str):
            return {"valid": False, "value": url, "issue": "Missing website URL"}
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"valid": False, "value": url, "issue": "Incomplete URL"}
            
            if parsed.scheme not in ['http', 'https']:
                return {"valid": False, "value": url, "issue": "Invalid URL scheme"}
            
            return {"valid": True, "value": url}
        except Exception:
            return {"valid": False, "value": url, "issue": "Invalid URL format"}
    
    def _validate_non_empty_string(self, value: Optional[str]) -> Dict[str, Any]:
        """Validate non-empty string."""
        if not value or not isinstance(value, str) or not value.strip():
            return {"valid": False, "value": value, "issue": "Empty or missing string"}
        
        return {"valid": True, "value": value}
    
    def _validate_text_content(self, text: Optional[str], min_length: int = 10) -> Dict[str, Any]:
        """Validate text content with minimum length."""
        if not text or not isinstance(text, str):
            return {"valid": False, "value": text, "issue": "Missing text content"}
        
        text = text.strip()
        if len(text) < min_length:
            return {"valid": False, "value": text, "issue": f"Text too short (min {min_length} chars)"}
        
        return {"valid": True, "value": text}
    
    def _validate_positive_number(self, value: Optional[Union[int, float]]) -> Dict[str, Any]:
        """Validate positive number."""
        if value is None:
            return {"valid": False, "value": value, "issue": "Missing number"}
        
        try:
            num = float(value) if not isinstance(value, (int, float)) else value
            if num <= 0:
                return {"valid": False, "value": value, "issue": "Number must be positive"}
            
            return {"valid": True, "value": value}
        except (ValueError, TypeError):
            return {"valid": False, "value": value, "issue": "Invalid number format"}
    
    def _validate_location(self, location: Optional[str]) -> Dict[str, Any]:
        """Validate location string."""
        if not location or not isinstance(location, str):
            return {"valid": False, "value": location, "issue": "Missing location"}
        
        location = location.strip()
        if len(location) < 2:
            return {"valid": False, "value": location, "issue": "Location too short"}
        
        return {"valid": True, "value": location}
    
    def _validate_image_url(self, url: Optional[str]) -> Dict[str, Any]:
        """Validate image URL."""
        if not url:
            return {"valid": False, "value": url, "issue": "Missing image URL"}
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"valid": False, "value": url, "issue": "Invalid image URL"}
            
            return {"valid": True, "value": url}
        except Exception:
            return {"valid": False, "value": url, "issue": "Invalid URL format"}
    
    def _validate_list_content(self, items: Optional[List[Any]]) -> Dict[str, Any]:
        """Validate list content."""
        if not items or not isinstance(items, list):
            return {"valid": False, "value": items, "issue": "Missing or invalid list"}
        
        if len(items) == 0:
            return {"valid": False, "value": items, "issue": "Empty list"}
        
        return {"valid": True, "value": items}
    
    def _validate_dict_content(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate dictionary content."""
        if not data or not isinstance(data, dict):
            return {"valid": False, "value": data, "issue": "Missing or invalid dictionary"}
        
        if len(data) == 0:
            return {"valid": False, "value": data, "issue": "Empty dictionary"}
        
        return {"valid": True, "value": data}
    
    def _validate_data_sources(self, sources: Optional[List[str]]) -> Dict[str, Any]:
        """Validate data sources list."""
        if not sources or not isinstance(sources, list):
            return {"valid": False, "value": sources, "issue": "Missing data sources"}
        
        valid_sources = {
            "linkedin", "facebook", "twitter", "crunchbase", 
            "duns", "zoominfo", "erasmus"
        }
        
        invalid_sources = [s for s in sources if s not in valid_sources]
        if invalid_sources:
            return {
                "valid": False, 
                "value": sources, 
                "issue": f"Invalid sources: {invalid_sources}"
            }
        
        return {"valid": True, "value": sources}
    
    def _validate_experience_list(self, experience: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate work experience list."""
        if not experience or not isinstance(experience, list):
            return {"valid": False, "value": experience, "issue": "Missing experience data"}
        
        if len(experience) == 0:
            return {"valid": False, "value": experience, "issue": "No experience entries"}
        
        # Validate each experience entry
        valid_count = 0
        for exp in experience:
            if isinstance(exp, dict) and exp.get("title") and exp.get("company"):
                valid_count += 1
        
        if valid_count == 0:
            return {"valid": False, "value": experience, "issue": "No valid experience entries"}
        
        return {"valid": True, "value": experience, "valid_count": valid_count}
    
    def _validate_education_list(self, education: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate education list."""
        if not education or not isinstance(education, list):
            return {"valid": False, "value": education, "issue": "Missing education data"}
        
        if len(education) == 0:
            return {"valid": False, "value": education, "issue": "No education entries"}
        
        # Validate each education entry
        valid_count = 0
        for edu in education:
            if isinstance(edu, dict) and edu.get("school"):
                valid_count += 1
        
        if valid_count == 0:
            return {"valid": False, "value": education, "issue": "No valid education entries"}
        
        return {"valid": True, "value": education, "valid_count": valid_count}
    
    def _validate_skills_list(self, skills: Optional[List[str]]) -> Dict[str, Any]:
        """Validate skills list."""
        if not skills or not isinstance(skills, list):
            return {"valid": False, "value": skills, "issue": "Missing skills data"}
        
        if len(skills) == 0:
            return {"valid": False, "value": skills, "issue": "No skills listed"}
        
        # Filter out empty or invalid skills
        valid_skills = [s for s in skills if isinstance(s, str) and s.strip()]
        
        if len(valid_skills) == 0:
            return {"valid": False, "value": skills, "issue": "No valid skills"}
        
        return {"valid": True, "value": skills, "valid_count": len(valid_skills)}
    
    def _validate_company_size(self, size: Optional[str]) -> Dict[str, Any]:
        """Validate company size string."""
        if not size or not isinstance(size, str):
            return {"valid": False, "value": size, "issue": "Missing company size"}
        
        # Common company size patterns
        size_patterns = [
            r'\d+-\d+',  # e.g., "50-100"
            r'\d+\+',    # e.g., "1000+"
            r'<\d+',     # e.g., "<50"
            r'\d+ employees',  # e.g., "100 employees"
        ]
        
        for pattern in size_patterns:
            if re.search(pattern, size, re.IGNORECASE):
                return {"valid": True, "value": size}
        
        return {"valid": False, "value": size, "issue": "Invalid company size format"}
    
    def _validate_financial_data(self, financial: Optional[CompanyFinancialData]) -> Dict[str, Any]:
        """Validate financial data."""
        if not financial:
            return {"valid": False, "value": financial, "issue": "Missing financial data"}
        
        # Check if at least one financial field is present
        has_data = any([
            financial.revenue,
            financial.valuation,
            financial.funding,
            financial.funding_rounds,
            financial.key_investors,
        ])
        
        if not has_data:
            return {"valid": False, "value": financial, "issue": "No financial information"}
        
        return {"valid": True, "value": financial}
    
    def _validate_employee_data(self, employee: Optional[CompanyEmployeeData]) -> Dict[str, Any]:
        """Validate employee data."""
        if not employee:
            return {"valid": False, "value": employee, "issue": "Missing employee data"}
        
        # Check if at least one employee field is present
        has_data = any([
            employee.employee_count,
            employee.locations,
            employee.executives,
        ])
        
        if not has_data:
            return {"valid": False, "value": employee, "issue": "No employee information"}
        
        return {"valid": True, "value": employee}
    
    def _validate_recent_posts(self, posts: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate recent post activity."""
        if not posts or not isinstance(posts, list):
            return {"valid": False, "value": posts, "issue": "No posts data"}
        
        if len(posts) == 0:
            return {"valid": False, "value": posts, "issue": "No posts found"}
        
        # Check for recent activity (posts in last 6 months)
        recent_threshold = datetime.now().timestamp() - (6 * 30 * 24 * 60 * 60)  # 6 months
        recent_count = 0
        
        for post in posts:
            if isinstance(post, dict):
                created_at = post.get("created_at") or post.get("published_at")
                if created_at:
                    try:
                        # Try to parse various date formats
                        if isinstance(created_at, str):
                            post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
                        else:
                            post_time = float(created_at)
                        
                        if post_time >= recent_threshold:
                            recent_count += 1
                    except:
                        pass  # Skip invalid dates
        
        return {
            "valid": recent_count > 0,
            "value": posts,
            "recent_count": recent_count,
            "total_count": len(posts)
        }
    
    def _validate_post_list(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate list of posts."""
        if not posts:
            return {"valid": False, "value": posts, "issue": "No posts"}
        
        valid_posts = 0
        for post in posts:
            if isinstance(post, dict) and (post.get("text") or post.get("content")):
                valid_posts += 1
        
        if valid_posts == 0:
            return {"valid": False, "value": posts, "issue": "No valid posts with content"}
        
        return {
            "valid": True,
            "value": posts,
            "valid_count": valid_posts,
            "total_count": len(posts)
        }
    
    def _calculate_field_score(self, fields: Dict[str, Dict[str, Any]]) -> float:
        """Calculate score based on field validation results."""
        if not fields:
            return 0.0
        
        valid_count = sum(1 for field in fields.values() if field.get("valid", False))
        total_count = len(fields)
        
        return valid_count / total_count if total_count > 0 else 0.0 