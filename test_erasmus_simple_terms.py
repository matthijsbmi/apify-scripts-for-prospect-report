#!/usr/bin/env python3
"""
Test Erasmus+ Organisation Scraper with simple, more likely search terms.
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


async def test_erasmus_simple_terms():
    """Test Erasmus+ Organisation Scraper with simple, likely search terms."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper - Simple Terms")
    print("=" * 70)
    
    apify_service = ApifyService()
    actor_id = "5ms6D6gKCnJhZN61e"  # Erasmus+ Organisation Scraper
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Test with simpler terms that are more likely to be found
    test_cases = [
        {
            "name": "Simple university terms",
            "input": {
                "debugMode": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                },
                "searchTerms": [
                    "University",
                    "College"
                ]
            }
        },
        {
            "name": "Country-specific search",
            "input": {
                "debugMode": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                },
                "searchTerms": [
                    "Amsterdam",
                    "Berlin"
                ]
            }
        },
        {
            "name": "Common organization terms",
            "input": {
                "debugMode": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                },
                "searchTerms": [
                    "Foundation",
                    "Institute"
                ]
            }
        },
        {
            "name": "Technical terms",
            "input": {
                "debugMode": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                },
                "searchTerms": [
                    "Technical",
                    "School"
                ]
            }
        },
        {
            "name": "Very broad search",
            "input": {
                "debugMode": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                },
                "searchTerms": [
                    "European"
                ]
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Search terms: {test_case['input']['searchTerms']}")
        
        try:
            result = await apify_service.run_actor_async(
                actor_id=actor_id,
                input_data=test_case['input'],
                timeout_secs=300  # Longer timeout for broader searches
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
                            # Extract key fields
                            name = org.get('name', org.get('legalName', 'N/A'))
                            legal_name = org.get('legalName', 'N/A')
                            business_name = org.get('businessName', 'N/A')
                            country = org.get('country', 'N/A')
                            city = org.get('city', 'N/A')
                            website = org.get('website', 'N/A')
                            org_id = org.get('organisationId', 'N/A')
                            pic = org.get('pic', 'N/A')
                            
                            print(f"     Name: {name}")
                            print(f"     Legal Name: {legal_name}")
                            print(f"     Business Name: {business_name}")
                            print(f"     Country: {country}")
                            print(f"     City: {city}")
                            print(f"     Website: {website}")
                            print(f"     Organization ID: {org_id}")
                            print(f"     PIC: {pic}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_simple_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_case['name'],
                            "input": test_case['input'],
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                    
                    # Stop after first successful test to avoid too much data
                    if len(items) > 0:
                        print(f"\n🎉 SUCCESS! Found organizations with search term: {test_case['input']['searchTerms']}")
                        break
                
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n✅ Erasmus+ simple terms testing completed!")


if __name__ == "__main__":
    asyncio.run(test_erasmus_simple_terms()) 