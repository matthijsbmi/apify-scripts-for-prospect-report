#!/usr/bin/env python3
"""
Test script for Erasmus+ Organisation Scraper.

This script tests the Erasmus+ Organisation Scraper with real domains
and saves the output to JSON.
"""

import asyncio
import json
import os
from datetime import datetime
from decimal import Decimal

from app.actors.erasmus.organisation_scraper import ErasmusOrganisationScraper
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
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        return super().default(obj)


async def test_erasmus_scraper():
    """Test the Erasmus+ Organisation Scraper implementation."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper Implementation")
    print("=" * 70)
    
    # Initialize services
    apify_service = ApifyService()
    cost_manager = CostManager()
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Initialize scraper
    erasmus_scraper = ErasmusOrganisationScraper(apify_service, cost_manager)
    
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
    
    # Test search terms
    test_search_terms = [
        ["Erasmus University Rotterdam"],
        ["Delft University of Technology"],
        ["Eindhoven University of Technology"]
    ]
    
    # Test domain search
    print("\n🌐 Testing search_by_domain method:")
    for i, test_case in enumerate(test_domains, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Domain: {test_case['domain']}")
        
        try:
            result = await erasmus_scraper.search_by_domain(test_case['domain'])
            
            if result.get("success"):
                organizations = result.get("organizations", [])
                metadata = result.get("metadata", {})
                
                print(f"✅ Success! Retrieved {len(organizations)} organizations")
                print(f"   Run ID: {metadata.get('run_id', 'N/A')}")
                print(f"   Status: {metadata.get('status', 'N/A')}")
                print(f"   Compute units: {metadata.get('compute_units', 'N/A')}")
                
                if organizations:
                    print(f"   First organization: {organizations[0]['name']} ({organizations[0]['legal_name']})")
                    print(f"   Country: {organizations[0]['location'].get('country', 'N/A')}")
                    print(f"   City: {organizations[0]['location'].get('city', 'N/A')}")
                    print(f"   Organization ID: {organizations[0]['identifiers'].get('organisation_id', 'N/A')}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_domain_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_case['name'],
                            "domain": test_case['domain'],
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    # Test search by terms
    print("\n🔍 Testing search_by_terms method:")
    for i, terms in enumerate(test_search_terms, 1):
        print(f"\n📋 Test {i}: Search terms: {terms}")
        
        try:
            result = await erasmus_scraper.search_by_terms(terms)
            
            if result.get("success"):
                organizations = result.get("organizations", [])
                metadata = result.get("metadata", {})
                
                print(f"✅ Success! Retrieved {len(organizations)} organizations")
                print(f"   Run ID: {metadata.get('run_id', 'N/A')}")
                print(f"   Status: {metadata.get('status', 'N/A')}")
                print(f"   Compute units: {metadata.get('compute_units', 'N/A')}")
                
                if organizations:
                    print(f"   First organization: {organizations[0]['name']} ({organizations[0]['legal_name']})")
                    print(f"   Country: {organizations[0]['location'].get('country', 'N/A')}")
                    print(f"   City: {organizations[0]['location'].get('city', 'N/A')}")
                    print(f"   Organization ID: {organizations[0]['identifiers'].get('organisation_id', 'N/A')}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_terms_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "search_terms": terms,
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
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
        cleaned = erasmus_scraper.clean_domain(url)
        print(f"   {url} → {cleaned}")
    
    print("\n✅ Erasmus+ Organisation Scraper testing completed!")


if __name__ == "__main__":
    # Create the erasmus directory if it doesn't exist
    os.makedirs("app/actors/erasmus", exist_ok=True)
    
    # Create an empty __init__.py file in the erasmus directory if it doesn't exist
    init_file = "app/actors/erasmus/__init__.py"
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Erasmus+ actors package\n")
    
    # Run the test
    asyncio.run(test_erasmus_scraper()) 