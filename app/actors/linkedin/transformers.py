"""
Data transformers for LinkedIn actors.

Contains functions for transforming raw actor responses into standardized formats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.data import (
    LinkedInProfile, LinkedInPost, LinkedInCompany, LinkedInCompanyLocation,
    LinkedInEmployee, LinkedInCompanyUpdate, LinkedInSimilarCompany
)


def transform_profile_data(raw_profile: Dict[str, Any]) -> LinkedInProfile:
    """
    Transform raw LinkedIn profile data to standardized format.
    
    Args:
        raw_profile: Raw profile data from actor response.
        
    Returns:
        Standardized LinkedIn profile.
    """
    # Extract basic profile information
    profile_url = raw_profile.get("profileUrl", "")
    full_name = raw_profile.get("fullName", "Unknown")
    headline = raw_profile.get("headline", "")
    
    # Extract location information
    location = raw_profile.get("locationName", "")
    country = raw_profile.get("locationCountry", "")
    
    # Extract industry information
    industry = raw_profile.get("industryName", "")
    
    # Extract company information
    current_company_name = None
    current_company_url = None
    current_title = None
    
    # Try to extract current position
    experiences = raw_profile.get("experience", [])
    if experiences:
        # Find current position (no end date)
        current_positions = [
            exp for exp in experiences
            if not exp.get("timePeriod", {}).get("endDate")
        ]
        
        if current_positions:
            current_position = current_positions[0]
            current_company_name = current_position.get("companyName")
            current_company_url = current_position.get("companyUrl")
            current_title = current_position.get("title")
    
    # Process skills
    skills = []
    for skill in raw_profile.get("skills", []):
        if isinstance(skill, str):
            skills.append(skill)
        elif isinstance(skill, dict):
            skills.append(skill.get("name", ""))
    
    # Create standardized profile
    return LinkedInProfile(
        profile_url=profile_url,
        full_name=full_name,
        headline=headline,
        location=location,
        country=country,
        industry=industry,
        current_company=current_company_name,
        current_company_url=current_company_url,
        current_title=current_title,
        summary=raw_profile.get("summary", ""),
        skills=skills,
        education=_transform_education(raw_profile.get("education", [])),
        experience=_transform_experience(raw_profile.get("experience", [])),
        profile_image_url=raw_profile.get("profileImageUrl", ""),
        background_image_url=raw_profile.get("backgroundImageUrl", ""),
        languages=raw_profile.get("languages", []),
        raw_data=raw_profile,  # Store the raw data for future reference
        extracted_at=datetime.now(),
    )


def _transform_education(edu_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform education entries to standardized format.
    
    Args:
        edu_list: List of education entries from raw profile.
        
    Returns:
        List of standardized education entries.
    """
    result = []
    
    for edu in edu_list:
        # Parse dates
        start_date = None
        end_date = None
        
        time_period = edu.get("timePeriod", {})
        if time_period:
            start_date_obj = time_period.get("startDate", {})
            if start_date_obj:
                start_year = start_date_obj.get("year")
                if start_year:
                    start_date = str(start_year)
            
            end_date_obj = time_period.get("endDate", {})
            if end_date_obj:
                end_year = end_date_obj.get("year")
                if end_year:
                    end_date = str(end_year)
        
        # Create standardized education entry
        result.append({
            "school": edu.get("schoolName", ""),
            "degree": edu.get("degree", ""),
            "field_of_study": edu.get("fieldOfStudy", ""),
            "start_date": start_date,
            "end_date": end_date,
            "description": edu.get("description", ""),
        })
    
    return result


def _transform_experience(exp_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform experience entries to standardized format.
    
    Args:
        exp_list: List of experience entries from raw profile.
        
    Returns:
        List of standardized experience entries.
    """
    result = []
    
    for exp in exp_list:
        # Parse dates
        start_date = None
        end_date = None
        
        time_period = exp.get("timePeriod", {})
        if time_period:
            start_date_obj = time_period.get("startDate", {})
            if start_date_obj:
                start_year = start_date_obj.get("year")
                start_month = start_date_obj.get("month")
                if start_year:
                    start_date = f"{start_year}"
                    if start_month:
                        start_date = f"{start_month}/{start_year}"
            
            end_date_obj = time_period.get("endDate", {})
            if end_date_obj:
                end_year = end_date_obj.get("year")
                end_month = end_date_obj.get("month")
                if end_year:
                    end_date = f"{end_year}"
                    if end_month:
                        end_date = f"{end_month}/{end_year}"
            
            if not end_date_obj:
                end_date = "Present"
        
        # Create standardized experience entry
        result.append({
            "company": exp.get("companyName", ""),
            "company_url": exp.get("companyUrl", ""),
            "title": exp.get("title", ""),
            "location": exp.get("locationName", ""),
            "start_date": start_date,
            "end_date": end_date,
            "description": exp.get("description", ""),
            "duration": exp.get("durationInDays"),  # Duration in days if available
        })
    
    return result


def transform_posts_data(raw_posts: List[Dict[str, Any]]) -> List[LinkedInPost]:
    """
    Transform raw LinkedIn posts data to standardized format.
    
    Args:
        raw_posts: Raw posts data from actor response.
        
    Returns:
        List of standardized LinkedIn posts.
    """
    result = []
    
    for post in raw_posts:
        # Parse published date
        published_at = None
        if post.get("published"):
            try:
                published_at = datetime.fromisoformat(post.get("published").replace("Z", "+00:00"))
            except (ValueError, TypeError):
                # If date parsing fails, use current time
                published_at = datetime.now()
        else:
            published_at = datetime.now()
        
        # Create standardized post
        result.append(LinkedInPost(
            post_url=post.get("postUrl", ""),
            author_name=post.get("author", {}).get("name", ""),
            author_url=post.get("author", {}).get("profileUrl", ""),
            content=post.get("text", ""),
            published_at=published_at,
            likes_count=post.get("statistics", {}).get("likes", 0),
            comments_count=post.get("statistics", {}).get("comments", 0),
            shares_count=post.get("statistics", {}).get("shares", 0),
            media=post.get("media", []),
            raw_data=post,  # Store the raw data for future reference
            extracted_at=datetime.now(),
        ))
    
    return result


def transform_company_data(raw_company: Dict[str, Any]) -> LinkedInCompany:
    """
    Transform raw LinkedIn company data to standardized format.
    
    Args:
        raw_company: Raw company data from actor response.
        
    Returns:
        Standardized LinkedIn company.
    """
    # Transform locations
    locations = []
    for loc in raw_company.get("locations", []):
        locations.append(LinkedInCompanyLocation(
            is_hq=loc.get("is_hq"),
            office_address_line_1=loc.get("office_address_line_1"),
            office_address_line_2=loc.get("office_address_line_2"),
            office_location_link=loc.get("office_location_link")
        ))
    
    # Transform employees
    employees = []
    for emp in raw_company.get("employees", []):
        employees.append(LinkedInEmployee(
            employee_photo=emp.get("employee_photo"),
            employee_name=emp.get("employee_name"),
            employee_position=emp.get("employee_position"),
            employee_profile_url=emp.get("employee_profile_url")
        ))
    
    # Transform updates
    updates = []
    for update in raw_company.get("updates", []):
        updates.append(LinkedInCompanyUpdate(
            text=update.get("text"),
            article_posted_date=update.get("articlePostedDate"),
            total_likes=update.get("totalLikes")
        ))
    
    # Transform similar companies
    similar_companies = []
    for similar in raw_company.get("similar_companies", []):
        similar_companies.append(LinkedInSimilarCompany(
            link=similar.get("link"),
            name=similar.get("name"),
            summary=similar.get("summary"),
            location=similar.get("location")
        ))
    
    # Create standardized company
    return LinkedInCompany(
        company_url=raw_company.get("company_url"),
        company_name=raw_company.get("company_name"),
        universal_name_id=raw_company.get("universal_name_id"),
        background_cover_image_url=raw_company.get("background_cover_image_url"),
        linkedin_internal_id=raw_company.get("linkedin_internal_id"),
        industry=raw_company.get("industry"),
        location=raw_company.get("location"),
        follower_count=raw_company.get("follower_count"),
        tagline=raw_company.get("tagline"),
        company_size_on_linkedin=raw_company.get("company_size_on_linkedin"),
        about=raw_company.get("about"),
        website=raw_company.get("website"),
        industries=raw_company.get("industries"),
        company_size=raw_company.get("company_size"),
        headquarters=raw_company.get("headquarters"),
        type=raw_company.get("type"),
        founded=raw_company.get("founded"),
        specialties=raw_company.get("specialties"),
        locations=locations,
        employees=employees,
        updates=updates,
        similar_companies=similar_companies,
        affiliated_companies=raw_company.get("affiliated_companies", []),
        extracted_at=datetime.now(),
    )


 