#!/usr/bin/env python3
"""
Simple debug script to test ErasmusActor raw results without transformation.
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal

from app.actors.company.erasmus_actor import ErasmusActor
from app.actors.base import ActorRunOptions


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
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


async def debug_erasmus_raw():
    """Test ErasmusActor by getting raw results without transformation."""
    
    print("🔍 Debug ErasmusActor - Raw Results (No Transformation)")
    print("=" * 70)
    
    erasmus_actor = ErasmusActor()
    
    # Test with a domain that we know works
    test_domain = "www.uva.nl"
    cleaned_domain = erasmus_actor.clean_domain(test_domain)
    
    print(f"Testing domain: {test_domain}")
    print(f"Cleaned domain: {cleaned_domain}")
    
    # Prepare input exactly like the working script
    input_data = {
        "maxResults": 10,
        "searchTerms": [],
        "debugMode": False,
        "websiteName": cleaned_domain,
        "proxyConfiguration": {
            "useApifyProxy": True
        }
    }
    
    print(f"Input data: {json.dumps(input_data, indent=2)}")
    
    try:
        # Test the raw BaseActor.run_async method directly
        options = ActorRunOptions(
            timeout_secs=300,
            memory_mbytes=512,
        )
        
        print("\n🚀 Running actor with BaseActor.run_async()...")
        result = await erasmus_actor.run_async(
            input_data=input_data,
            options=options,
            max_budget=None,
        )
        
        print(f"✅ Actor run completed!")
        print(f"Run ID: {result.run_id}")
        print(f"Status: {result.status}")
        print(f"Items count: {result.items_count}")
        print(f"Success: {result.success}")
        
        if result.items:
            print(f"\n📋 Raw items found: {len(result.items)}")
            
            # Show first item structure
            first_item = result.items[0]
            print(f"First item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            print(f"First item: {json.dumps(first_item, indent=2, cls=CustomJSONEncoder)}")
            
            # Save raw result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"debug_erasmus_raw_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_domain": test_domain,
                    "cleaned_domain": cleaned_domain,
                    "input_data": input_data,
                    "result": {
                        "run_id": result.run_id,
                        "status": result.status,
                        "items_count": result.items_count,
                        "success": result.success,
                        "items": result.items,
                        "metadata": result.metadata
                    }
                }, f, indent=2, cls=CustomJSONEncoder)
            
            print(f"💾 Saved raw result to {output_file}")
            
        else:
            print("⚠️  No items returned")
            
        # Now test the transformation separately if we have items
        if result.items:
            print(f"\n🔄 Testing transformation on first item...")
            from app.actors.company.transformers import transform_erasmus_data
            
            try:
                first_item = result.items[0]
                company_data = transform_erasmus_data(first_item)
                print(f"✅ Transformation successful!")
                print(f"Company name: {company_data.name}")
                print(f"Company data: {json.dumps(company_data.model_dump(), indent=2, cls=CustomJSONEncoder)}")
                
            except Exception as transform_error:
                print(f"❌ Transformation failed: {transform_error}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Actor run failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_erasmus_raw()) 