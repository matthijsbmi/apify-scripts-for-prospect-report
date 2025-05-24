#!/usr/bin/env python3
"""
Test Erasmus+ Organisation Scraper with company/organization names.
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal

from app.core.apify_client import ApifyService


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, Decimal, and other non-serializable objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        return super().default(obj)


async def test_erasmus_company_names():
    """Test Erasmus+ Organisation Scraper with real company/organization names."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper with Company Names")
    print("=" * 70)
    
    apify_service = ApifyService()
    actor_id = "5ms6D6gKCnJhZN61e"  # Erasmus+ Organisation Scraper
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Test with real organization names that are likely in Erasmus+ database
    # Using major European universities and organizations known to participate in Erasmus+
    test_organizations = [
        # Major European Universities
        "University of Amsterdam",
        "KTH Royal Institute of Technology",
        "University of Copenhagen",
        "Technical University of Munich",
        "University of Barcelona",
        "University of Vienna",
        "University of Bologna",
        "Sorbonne University",
        
        # Some companies that might have Erasmus+ partnerships
        "Siemens AG",
        "Philips",
        "SAP SE"
    ]
    
    # Test different organizational name formats
    test_formats = [
        {
            "name": "organizationNames format (primary test)",
            "input": {
                "organizationNames": test_organizations[:3],  # Test with first 3
                "maxResults": 20
            }
        },
        {
            "name": "organizationNames with single university",
            "input": {
                "organizationNames": ["University of Amsterdam"],
                "maxResults": 10
            }
        },
        {
            "name": "organizationNames with tech companies",
            "input": {
                "organizationNames": ["Siemens AG", "Philips", "SAP SE"],
                "maxResults": 15
            }
        },
        {
            "name": "query format alternative",
            "input": {
                "query": "University of Amsterdam",
                "maxResults": 10
            }
        }
    ]
    
    for i, test_format in enumerate(test_formats, 1):
        print(f"\n📋 Test {i}: {test_format['name']}")
        print(f"Organizations: {test_format['input'].get('organizationNames', [test_format['input'].get('query', 'N/A')])}")
        print(f"Max results: {test_format['input'].get('maxResults', 'N/A')}")
        
        try:
            result = await apify_service.run_actor_async(
                actor_id=actor_id,
                input_data=test_format['input'],
                timeout_secs=180  # Longer timeout for organization search
            )
            
            if result.get("success"):
                items = result.get("items", [])
                run_info = result.get("run", {})
                
                print(f"✅ Success! Retrieved {len(items)} organizations")
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units: {run_info.get('computeUnits', 'N/A')}")
                
                if items:
                    print(f"   Data structure keys: {list(items[0].keys()) if items[0] else 'None'}")
                    
                    # Show sample organization data
                    for j, org in enumerate(items[:3], 1):  # Show first 3 orgs
                        print(f"\n   📋 Organization {j}:")
                        if isinstance(org, dict):
                            # Common fields that might be present
                            name = org.get('name', org.get('organizationName', 'N/A'))
                            country = org.get('country', org.get('countryCode', 'N/A'))
                            city = org.get('city', org.get('location', 'N/A'))
                            org_type = org.get('type', org.get('organizationType', 'N/A'))
                            
                            print(f"     Name: {name}")
                            print(f"     Country: {country}")
                            print(f"     City: {city}")
                            print(f"     Type: {org_type}")
                            
                            # Check for project information
                            projects = org.get('projects', [])
                            if isinstance(projects, list):
                                print(f"     Projects: {len(projects)}")
                            elif projects:
                                print(f"     Projects: {projects}")
                            
                            # Check for contact info
                            if 'website' in org:
                                print(f"     Website: {org.get('website', 'N/A')}")
                            
                            # Check for Erasmus code
                            erasmus_code = org.get('erasmusCode', org.get('pic', org.get('organizationId', 'N/A')))
                            print(f"     Erasmus/PIC Code: {erasmus_code}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_companies_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_format['name'],
                            "input": test_format['input'],
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                    
                    # Show organizational stats
                    countries = {}
                    org_types = {}
                    for org in items:
                        if isinstance(org, dict):
                            country = org.get('country', org.get('countryCode', 'Unknown'))
                            org_type = org.get('type', org.get('organizationType', 'Unknown'))
                            
                            countries[country] = countries.get(country, 0) + 1
                            org_types[org_type] = org_types.get(org_type, 0) + 1
                    
                    if countries:
                        print(f"\n   🌍 Countries represented:")
                        for country, count in sorted(countries.items()):
                            print(f"     - {country}: {count}")
                    
                    if org_types:
                        print(f"\n   🏢 Organization types:")
                        for org_type, count in sorted(org_types.items()):
                            print(f"     - {org_type}: {count}")
                
                else:
                    print("   ⚠️  No organizations returned")
                    print("   This could mean:")
                    print("     - Organization names not found in Erasmus+ database")
                    print("     - Names need exact spelling as in database")
                    print("     - Organizations are not Erasmus+ participants")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n✅ Erasmus+ company name testing completed!")
    print("\n📝 Notes:")
    print("   - Erasmus+ database primarily contains EU educational institutions")
    print("   - Organization names must match exactly as registered")
    print("   - Some companies participate through educational partnerships")
    print("   - Try variations of names if no results found")


if __name__ == "__main__":
    asyncio.run(test_erasmus_company_names()) 