#!/usr/bin/env python3
"""
Test Erasmus+ Organisation Scraper to understand the correct input format.
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


async def test_erasmus_formats():
    """Test different Erasmus+ Organisation Scraper input formats."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper Formats")
    print("=" * 60)
    
    apify_service = ApifyService()
    actor_id = "5ms6D6gKCnJhZN61e"  # Erasmus+ Organisation Scraper
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Test different input formats
    # Note: These are hypothetical organization IDs for testing
    test_formats = [
        {
            "name": "organizationIds format (expected)",
            "input": {
                "organizationIds": [
                    "999990094",  # Sample organization ID
                    "999999999"   # Another sample ID
                ],
                "maxResults": 10
            }
        },
        {
            "name": "organizationNames format",
            "input": {
                "organizationNames": [
                    "University of Amsterdam",
                    "KTH Royal Institute of Technology"
                ],
                "maxResults": 10
            }
        },
        {
            "name": "combined format",
            "input": {
                "organizationIds": [
                    "999990094"
                ],
                "organizationNames": [
                    "University of Amsterdam"
                ],
                "maxResults": 10
            }
        },
        {
            "name": "query format (alternative)",
            "input": {
                "query": "University of Amsterdam",
                "maxResults": 10
            }
        }
    ]
    
    for i, test_format in enumerate(test_formats, 1):
        print(f"\n📋 Test {i}: {test_format['name']}")
        print(f"Input: {json.dumps(test_format['input'], indent=2)}")
        
        try:
            result = await apify_service.run_actor_async(
                actor_id=actor_id,
                input_data=test_format['input'],
                timeout_secs=120  # Shorter timeout for testing
            )
            
            if result.get("success"):
                items = result.get("items", [])
                run_info = result.get("run", {})
                
                print(f"✅ Success! Retrieved {len(items)} organizations")
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units: {run_info.get('computeUnits', 'N/A')}")
                
                if items:
                    print(f"   First org keys: {list(items[0].keys()) if items[0] else 'None'}")
                    
                    # Show sample organization data
                    first_org = items[0]
                    if isinstance(first_org, dict):
                        if "name" in first_org:
                            print(f"   Sample org name: {first_org.get('name', 'N/A')}")
                        if "country" in first_org:
                            print(f"   Country: {first_org.get('country', 'N/A')}")
                        if "projects" in first_org:
                            project_count = len(first_org.get('projects', []))
                            print(f"   Projects: {project_count}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_format['name'],
                            "input": test_format['input'],
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    print("\n✅ Erasmus+ format testing completed!")


if __name__ == "__main__":
    asyncio.run(test_erasmus_formats()) 