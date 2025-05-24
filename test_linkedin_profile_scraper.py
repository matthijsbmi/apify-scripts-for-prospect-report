#!/usr/bin/env python3
"""
Test script for LinkedIn Profile Scraper.

This script tests the LinkedIn Profile Bulk Scraper with a real profile
and saves the output to JSON.
"""

import asyncio
import json
import os
from datetime import datetime
from decimal import Decimal

from app.actors.linkedin.profile_scraper import LinkedInProfileScraper
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, Decimal, and other non-serializable objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # For complex objects, convert to dict
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            # For iterables, convert to list
            return list(obj)
        
        # Let the base class default method raise the TypeError
        return super().default(obj)


async def test_linkedin_profile_scraper():
    """Test the LinkedIn Profile Scraper with a real profile."""
    
    print("🚀 Testing LinkedIn Profile Bulk Scraper")
    print("=" * 50)
    
    # Initialize services
    print("📊 Initializing services...")
    apify_service = ApifyService()
    cost_manager = CostManager()
    scraper = LinkedInProfileScraper(apify_service, cost_manager)
    
    # Check if Apify service is available
    if not apify_service.is_available():
        print("❌ Apify service not available. Please check your APIFY_API_TOKEN.")
        return
    
    print("✅ Apify service initialized successfully")
    
    # Test input - using a public LinkedIn profile
    test_input = {
        "profileUrls": [
            "https://www.linkedin.com/in/williamhgates/"  # Bill Gates' public profile
        ],
        "includeSkills": True,
        "includeEducation": True,
        "includeExperience": True,
        "includeRecommendations": False,
        "includeCourses": False
    }
    
    print(f"📋 Testing with {len(test_input['profileUrls'])} profile(s)")
    for url in test_input['profileUrls']:
        print(f"   - {url}")
    
    # Validate input
    print("\n🔍 Validating input...")
    try:
        scraper.validate_input(test_input)
        print("✅ Input validation passed")
    except ValueError as e:
        print(f"❌ Input validation failed: {e}")
        return
    
    # Estimate cost
    print("\n💰 Estimating cost...")
    cost_estimate = scraper.estimate_cost(test_input)
    print(f"   Estimated cost: ${cost_estimate['estimated_cost']:.4f}")
    print(f"   Compute units: {cost_estimate['compute_units']:.2f}")
    print(f"   Profiles: {cost_estimate['cost_breakdown']['profiles']}")
    
    # Run the scraper
    print("\n🔄 Running LinkedIn Profile Scraper...")
    print("   This may take a few minutes...")
    
    try:
        result = await scraper.run_actor_async(test_input, timeout=600)
        
        if result.get("success"):
            print("✅ Scraping completed successfully!")
            
            # Display basic results info
            items = result.get("items", [])
            print(f"📊 Retrieved {len(items)} profile(s)")
            
            if "run" in result:
                run_info = result["run"]
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units used: {run_info.get('computeUnits', 'N/A')}")
                
                if run_info.get('computeUnits'):
                    from app.core.config import settings
                    actual_cost = run_info['computeUnits'] * settings.default_compute_unit_cost
                    print(f"   Actual cost: ${actual_cost:.4f}")
            
            # Save to JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"linkedin_profile_scraper_output_{timestamp}.json"
            
            print(f"\n💾 Saving output to {output_file}...")
            
            # Create output data with metadata
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "input": test_input,
                "cost_estimate": cost_estimate,
                "result": result,
                "summary": {
                    "profiles_found": len(items),
                    "success": True,
                    "run_id": result.get("run", {}).get("id"),
                    "compute_units": result.get("run", {}).get("computeUnits"),
                    "status": result.get("run", {}).get("status")
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            
            print(f"✅ Output saved to {output_file}")
            
            # Display sample profile data (first profile only, limited fields)
            if items:
                print("\n📋 Sample profile data (first profile):")
                first_profile = items[0]
                
                if isinstance(first_profile, dict):
                    # Show basic profile info
                    if "profile" in first_profile:
                        profile = first_profile["profile"]
                        print(f"   Name: {profile.get('fullName', 'N/A')}")
                        print(f"   Headline: {profile.get('headline', 'N/A')}")
                        print(f"   Location: {profile.get('location', 'N/A')}")
                        print(f"   Connections: {profile.get('connectionsCount', 'N/A')}")
                    
                    # Show experience count
                    if "experience" in first_profile:
                        exp_count = len(first_profile["experience"])
                        print(f"   Experience entries: {exp_count}")
                    
                    # Show education count
                    if "education" in first_profile:
                        edu_count = len(first_profile["education"])
                        print(f"   Education entries: {edu_count}")
                    
                    # Show skills count
                    if "skills" in first_profile:
                        skills_count = len(first_profile["skills"])
                        print(f"   Skills: {skills_count}")
                        
                        # Show top 3 skills
                        if first_profile["skills"]:
                            print("   Top skills:")
                            for skill in first_profile["skills"][:3]:
                                if isinstance(skill, dict):
                                    name = skill.get('name', 'N/A')
                                    endorsements = skill.get('endorsements', 0)
                                    print(f"     - {name} ({endorsements} endorsements)")
            else:
                print("\n⚠️  No profile data found. This could be because:")
                print("   - The profile URL is not accessible")
                print("   - The actor needs different input parameters")
                print("   - The LinkedIn profile is private or restricted")
                print("   - Rate limiting or anti-bot measures are in place")
            
        else:
            print("❌ Scraping failed!")
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            # Still save the error result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"linkedin_profile_scraper_error_{timestamp}.json"
            
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "input": test_input,
                "cost_estimate": cost_estimate,
                "result": result,
                "summary": {
                    "success": False,
                    "error": error
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            
            print(f"📄 Error details saved to {output_file}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Display cost summary using correct CostManager properties
    print(f"\n💰 Cost Summary:")
    print(f"   Total cost tracked: ${float(cost_manager.total_cost):.4f}")
    
    # Get cost breakdown if possible
    try:
        cost_breakdown = cost_manager.get_cost_breakdown()
        print(f"   Total executions: {len(cost_manager.execution_history)}")
    except Exception:
        print(f"   Execution history: {len(cost_manager.execution_history)} records")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_linkedin_profile_scraper()) 