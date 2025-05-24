#!/usr/bin/env python3
"""
Test script for the updated ErasmusActor with website domain search capability.
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal

from app.actors.company.erasmus_actor import ErasmusActor


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
        elif hasattr(obj, '__str__'):  # Handle Pydantic Url objects and other string-like objects
            return str(obj)
        return super().default(obj)


async def test_erasmus_actor():
    """Test the updated ErasmusActor implementation with website domain searches."""
    
    print("🔍 Testing ErasmusActor with Website Domain Search")
    print("=" * 70)
    
    # Initialize actor
    erasmus_actor = ErasmusActor()
    
    # Test domains (from our successful tests)
    test_domains = [
        {
            "name": "University of Amsterdam",
            "domain": "www.uva.nl"
        },
        {
            "name": "Technical University of Munich",
            "domain": "www.tum.de"
        },
        {
            "name": "Business Models Inc",
            "domain": "www.businessmodelsinc.com"
        }
    ]
    
    # Test organization names
    test_names = [
        "Erasmus University Rotterdam",
        "Delft University of Technology",
        "Eindhoven University of Technology"
    ]
    
    # Test domain cleaning
    print("\n🧹 Testing domain cleaning:")
    test_urls = [
        "https://www.example.com/en/about",
        "http://example.com/nl/contact",
        "www.example.com/path?query=1",
        "example.com",
        "https://subdomain.example.com/path/to/page"
    ]
    
    for url in test_urls:
        cleaned = erasmus_actor.clean_domain(url)
        print(f"   {url} → {cleaned}")
    
    # Test domain search with scrape_by_domain method
    print("\n🌐 Testing scrape_by_domain method:")
    for i, test_case in enumerate(test_domains, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Domain: {test_case['domain']}")
        
        try:
            result = await erasmus_actor.scrape_by_domain(
                website_domain=test_case['domain'],
                max_results=10
            )
            
            data = result.get("data", [])
            metadata = result.get("metadata", {})
            
            print(f"✅ Success! Retrieved {len(data)} organizations")
            print(f"   Run ID: {metadata.actor_run_id if hasattr(metadata, 'actor_run_id') else 'N/A'}")
            print(f"   Status: {metadata.status if hasattr(metadata, 'status') else 'N/A'}")
            
            if data:
                print(f"   First organization: {data[0].name}")
                if hasattr(data[0], 'location') and data[0].location:
                    print(f"   Country: {data[0].location.get('country', 'N/A')}")
                    print(f"   City: {data[0].location.get('city', 'N/A')}")
                
                # Save successful result
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"erasmus_actor_domain_test_{i}_{timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "test_name": test_case['name'],
                        "domain": test_case['domain'],
                        "data": data,
                        "metadata": metadata
                    }, f, indent=2, cls=CustomJSONEncoder)
                
                print(f"   💾 Saved to {output_file}")
            else:
                print("   ⚠️  No organizations returned")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    # Test organization name search
    print("\n📝 Testing organization name search:")
    for i, org_name in enumerate(test_names, 1):
        print(f"\n📋 Test {i}: {org_name}")
        
        try:
            result = await erasmus_actor.scrape_single_organization(
                organization_name=org_name,
                max_results=10
            )
            
            data = result.get("data")
            metadata = result.get("metadata", {})
            
            if data:
                print(f"✅ Success! Retrieved organization data")
                print(f"   Name: {data.name}")
                if hasattr(data, 'location') and data.location:
                    print(f"   Country: {data.location.get('country', 'N/A')}")
                    print(f"   City: {data.location.get('city', 'N/A')}")
                
                # Save successful result
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"erasmus_actor_name_test_{i}_{timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "organization_name": org_name,
                        "data": data,
                        "metadata": metadata
                    }, f, indent=2, cls=CustomJSONEncoder)
                
                print(f"   💾 Saved to {output_file}")
            else:
                print("   ⚠️  No organization data returned")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n✅ ErasmusActor testing completed!")


if __name__ == "__main__":
    asyncio.run(test_erasmus_actor()) 