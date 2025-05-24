#!/usr/bin/env python3
"""
Test LinkedIn Posts Bulk Scraper to understand the correct input format.
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


async def test_linkedin_posts_formats():
    """Test different LinkedIn posts input formats."""
    
    print("🔍 Testing LinkedIn Posts Bulk Scraper Formats")
    print("=" * 60)
    
    apify_service = ApifyService()
    actor_id = "A3cAPGpwBEG8RJwse"  # LinkedIn Posts Bulk Scraper
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Test different input formats based on learnings from profile scraper
    test_formats = [
        {
            "name": "profileUrls format",
            "input": {
                "profileUrls": [
                    "https://www.linkedin.com/in/williamhgates/"
                ],
                "maxPostsPerProfile": 5
            }
        },
        {
            "name": "urls format (learned from profile scraper)",
            "input": {
                "urls": [
                    "https://www.linkedin.com/in/williamhgates/"
                ],
                "maxPostsPerProfile": 5
            }
        },
        {
            "name": "startUrls format",
            "input": {
                "startUrls": [
                    {"url": "https://www.linkedin.com/in/williamhgates/"}
                ],
                "maxPostsPerProfile": 5
            }
        },
        {
            "name": "posts format",
            "input": {
                "posts": [
                    "https://www.linkedin.com/in/williamhgates/"
                ],
                "maxPostsPerProfile": 5
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
                
                print(f"✅ Success! Retrieved {len(items)} posts")
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units: {run_info.get('computeUnits', 'N/A')}")
                
                if items:
                    print(f"   First post keys: {list(items[0].keys()) if items[0] else 'None'}")
                    
                    # Show sample post data
                    first_post = items[0]
                    if isinstance(first_post, dict):
                        if "text" in first_post:
                            text_preview = first_post["text"][:100] + "..." if len(first_post.get("text", "")) > 100 else first_post.get("text", "")
                            print(f"   Sample text: {text_preview}")
                        if "author" in first_post:
                            print(f"   Author: {first_post.get('author', {}).get('name', 'N/A')}")
                        if "publishedAt" in first_post:
                            print(f"   Published: {first_post.get('publishedAt', 'N/A')}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"linkedin_posts_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_format['name'],
                            "input": test_format['input'],
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                else:
                    print("   ⚠️  No posts returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    print("\n✅ LinkedIn Posts format testing completed!")


if __name__ == "__main__":
    asyncio.run(test_linkedin_posts_formats()) 