#!/usr/bin/env python3
"""
Debug script to identify the exact error in Erasmus actor.
"""

import asyncio
import json
import traceback
from datetime import datetime
from decimal import Decimal

from app.actors.company.erasmus_actor import ErasmusActor


async def debug_erasmus_error():
    """Debug the exact error location in Erasmus actor."""
    
    print("🔍 Debugging Erasmus Actor Error")
    print("=" * 50)
    
    # Initialize actor
    erasmus_actor = ErasmusActor()
    
    print("Testing with University of Amsterdam domain: www.uva.nl")
    
    try:
        result = await erasmus_actor.scrape_by_domain(
            website_domain="www.uva.nl",
            max_results=10
        )
        
        print("✅ Success! No error occurred")
        print(f"Data: {len(result.get('data', []))} organizations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Full traceback:")
        traceback.print_exc()
        
        # Let's also try to catch the error at different levels
        print("\n🔍 Trying to isolate the error...")
        
        try:
            # Test just the base actor run without transformation
            from app.actors.base import ActorRunOptions
            
            input_data = {
                "maxResults": 10,
                "searchTerms": [],
                "debugMode": False,
                "websiteName": "www.uva.nl",
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            options = ActorRunOptions(
                timeout_secs=300,
                memory_mbytes=512,
            )
            
            print("Testing base actor run...")
            base_result = await erasmus_actor.run_async(
                input_data=input_data,
                options=options,
                max_budget=None,
            )
            
            print(f"Base actor run succeeded with {len(base_result.items)} items")
            
            # Now test transformation
            print("Testing data transformation...")
            from app.actors.company.transformers import transform_erasmus_data
            
            for i, item in enumerate(base_result.items):
                print(f"Transforming item {i+1}...")
                print(f"Item data: {json.dumps(item, indent=2, default=str)}")
                
                try:
                    company_data = transform_erasmus_data(item)
                    print(f"✅ Item {i+1} transformed successfully")
                except Exception as transform_error:
                    print(f"❌ Item {i+1} transformation failed: {transform_error}")
                    traceback.print_exc()
                    break
                    
        except Exception as base_error:
            print(f"❌ Base actor error: {base_error}")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_erasmus_error()) 