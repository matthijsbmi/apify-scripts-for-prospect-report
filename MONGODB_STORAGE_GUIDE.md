# MongoDB Storage Guide for Apify Actor Scripts

This document demonstrates how all actor outputs from this script collection can be stored in MongoDB with separate JSON documents per actor while maintaining execution run relationships.

## Overview

This project provides **script components for integration** into larger systems. The MongoDB storage structure outlined here is **conceptual and ready for implementation** depending on your backend architecture. Each integration will need to configure the specific storage implementation based on their database setup and requirements.

## Recommended Collection Structure

### Core Collections

1. **`actor_runs`** - Execution metadata linking related actor outputs
2. **`linkedin_profiles`** - LinkedIn profile data
3. **`linkedin_posts`** - LinkedIn posts data  
4. **`linkedin_companies`** - LinkedIn company data
5. **`facebook_posts`** - Facebook posts data
6. **`twitter_posts`** - Twitter/X posts data
7. **`erasmus_organizations`** - Erasmus+ organization data
8. **`zoominfo_companies`** - ZoomInfo company data
9. **`duns_companies`** - Dun & Bradstreet company data

## Document Examples

### Actor Run Metadata (Collection: `actor_runs`)

```json
{
  "_id": "run_2024_01_15_001",
  "session_id": "prospect_analysis_session_123",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:45:00Z",
  "status": "completed",
  "total_actors_executed": 4,
  "actors_executed": [
    {
      "actor_type": "linkedin_profiles",
      "count": 5,
      "collection": "linkedin_profiles",
      "cost_usd": 0.02
    },
    {
      "actor_type": "duns_companies", 
      "count": 3,
      "collection": "duns_companies",
      "cost_usd": 0.15
    }
  ],
  "total_cost_usd": 0.17,
  "request_metadata": {
    "user_id": "user_456",
    "project_id": "project_789"
  }
}
```

### LinkedIn Profile Data (Collection: `linkedin_profiles`)

```json
{
  "_id": "linkedin_profile_001",
  "run_id": "run_2024_01_15_001",
  "actor_type": "linkedin_profiles",
  "scraped_at": "2024-01-15T10:32:00Z",
  "profile_data": {
    "url": "https://www.linkedin.com/in/johndoe",
    "name": "John Doe",
    "headline": "Software Engineer at Tech Corp",
    "location": "San Francisco, CA",
    "connections": 500,
    "about": "Experienced software engineer...",
    "experience": [...],
    "education": [...],
    "skills": [...],
    "recommendations": [...]
  },
  "metadata": {
    "extraction_timestamp": "2024-01-15T10:32:00Z",
    "actor_run_id": "apify_run_xyz789",
    "cost_computation_units": 0.004
  }
}
```

### D&B Company Data (Collection: `duns_companies`)

```json
{
  "_id": "duns_company_001", 
  "run_id": "run_2024_01_15_001",
  "actor_type": "duns_companies",
  "scraped_at": "2024-01-15T10:35:00Z",
  "company_data": {
    "url": "https://www.dnb.com/business-directory/company-profiles.apple_inc.12345.html",
    "name": "Apple Inc.",
    "description": "Technology company...",
    "website": "https://www.apple.com",
    "numberOfEmployees": 147000,
    "telephone": "+1-408-996-1010",
    "addressCountry": "United States",
    "addressLocality": "Cupertino",
    "addressRegion": "CA",
    "postalCode": "95014",
    "streetAddress": "One Apple Park Way",
    "type": "Public Company",
    "role": "Headquarters",
    "industry": "Computer Manufacturing",
    "revenue": "$365.8 billion",
    "fiscalYearEnd": "September",
    "yearStart": 1976,
    "incorporated": "January 3, 1977"
  },
  "search_metadata": {
    "search_term": "Apple Inc",
    "filters_applied": {
      "revenue_min": 1000000,
      "country_in": "United States"
    }
  }
}
```

### Facebook Posts Data (Collection: `facebook_posts`)

```json
{
  "_id": "facebook_post_001",
  "run_id": "run_2024_01_15_001", 
  "actor_type": "facebook_posts",
  "scraped_at": "2024-01-15T10:40:00Z",
  "post_data": {
    "facebookUrl": "https://www.facebook.com/nytimes",
    "pageId": "5281959998",
    "postId": "10150628743919999",
    "pageName": "The New York Times",
    "url": "https://www.facebook.com/nytimes/posts/10150628743919999",
    "time": "January 14, 2024 at 2:30 PM",
    "timestamp": 1705250400,
    "likes": 1250,
    "comments": 89,
    "shares": 42,
    "text": "Breaking news update...",
    "link": "https://www.nytimes.com/article-link",
    "thumb": "https://external.xx.fbcdn.net/safe_image.php?...",
    "media": []
  },
  "page_metadata": {
    "page_url": "https://www.facebook.com/nytimes",
    "results_limit": 50
  }
}
```

## Implementation Guidelines

### Integration Approach

**This is a script collection, not a standalone application.** The MongoDB storage structure should be implemented by the parent system that integrates these scripts:

1. **Integration Layer**: Parent system calls actor scripts and handles data storage
2. **Raw Data Preservation**: Store complete raw JSON outputs from each actor
3. **Run Tracking**: Link all related actor outputs using session/run IDs
4. **Cost Tracking**: Monitor and aggregate costs across all actor executions

### Storage Configuration Options

Different backend systems may choose different approaches:

#### Option 1: Separate Collections (Recommended)
- Each actor type gets its own collection
- Clear separation and easy querying
- Optimal for analytics and reporting

#### Option 2: Single Collection with Type Field
- All actor data in one collection with `actor_type` field
- Simpler schema management
- Good for smaller volumes

#### Option 3: Hybrid Approach
- Core collections for high-volume actors (LinkedIn, D&B)
- Combined collection for lower-volume actors
- Balance between organization and simplicity

### Schema Considerations

**Flexible Schema Design:**
- Raw data stored in nested `*_data` objects
- Consistent metadata structure across collections
- Run tracking with `run_id` field in all documents
- Timestamps for data freshness tracking

**Indexing Strategy:**
```javascript
// Recommended indexes for performance
db.actor_runs.createIndex({ "created_at": -1 })
db.actor_runs.createIndex({ "session_id": 1 })

db.linkedin_profiles.createIndex({ "run_id": 1 })
db.linkedin_profiles.createIndex({ "profile_data.url": 1 })

db.duns_companies.createIndex({ "run_id": 1 })
db.duns_companies.createIndex({ "company_data.name": 1 })

// Add similar indexes for other collections
```

### Data Retention & Cleanup

```javascript
// Example cleanup strategy
// Remove runs older than 90 days
const cutoffDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);

// Find old runs
const oldRuns = db.actor_runs.find({ 
  "created_at": { $lt: cutoffDate } 
}, { "_id": 1 });

// Clean up related data
oldRuns.forEach(run => {
  db.linkedin_profiles.deleteMany({ "run_id": run._id });
  db.duns_companies.deleteMany({ "run_id": run._id });
  // ... clean other collections
});

// Remove old runs
db.actor_runs.deleteMany({ "created_at": { $lt: cutoffDate } });
```

## Integration Code Examples

### Node.js Integration Example

```javascript
const { MongoClient } = require('mongodb');

class ActorDataStorage {
  constructor(mongoUrl, dbName) {
    this.client = new MongoClient(mongoUrl);
    this.db = this.client.db(dbName);
  }

  async storeActorRun(sessionId, actorExecutions) {
    const runId = `run_${new Date().toISOString().replace(/[:.]/g, '_')}`;
    
    // Store run metadata
    await this.db.collection('actor_runs').insertOne({
      _id: runId,
      session_id: sessionId,
      created_at: new Date(),
      status: 'in_progress',
      actors_executed: actorExecutions.map(exec => ({
        actor_type: exec.type,
        count: exec.data.length,
        collection: this.getCollectionName(exec.type)
      }))
    });

    // Store actor data
    for (const execution of actorExecutions) {
      await this.storeActorData(runId, execution);
    }

    // Mark run as completed
    await this.db.collection('actor_runs').updateOne(
      { _id: runId },
      { 
        $set: { 
          status: 'completed',
          completed_at: new Date()
        }
      }
    );

    return runId;
  }

  async storeActorData(runId, execution) {
    const collection = this.getCollectionName(execution.type);
    const documents = execution.data.map(item => ({
      run_id: runId,
      actor_type: execution.type,
      scraped_at: new Date(),
      [`${execution.type}_data`]: item,
      metadata: execution.metadata || {}
    }));

    await this.db.collection(collection).insertMany(documents);
  }

  getCollectionName(actorType) {
    const collectionMap = {
      'linkedin_profiles': 'linkedin_profiles',
      'linkedin_posts': 'linkedin_posts', 
      'linkedin_companies': 'linkedin_companies',
      'facebook_posts': 'facebook_posts',
      'twitter_posts': 'twitter_posts',
      'erasmus_organizations': 'erasmus_organizations',
      'zoominfo_companies': 'zoominfo_companies',
      'duns_companies': 'duns_companies'
    };
    return collectionMap[actorType] || 'unknown_actor_data';
  }
}
```

### Python Integration Example

```python
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Any

class ActorDataStorage:
    def __init__(self, mongo_url: str, db_name: str):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
    
    async def store_actor_run(self, session_id: str, actor_executions: List[Dict[str, Any]]) -> str:
        run_id = f"run_{datetime.now().isoformat().replace(':', '_').replace('.', '_')}"
        
        # Store run metadata
        await self.db.actor_runs.insert_one({
            "_id": run_id,
            "session_id": session_id,
            "created_at": datetime.now(),
            "status": "in_progress",
            "actors_executed": [
                {
                    "actor_type": exec["type"],
                    "count": len(exec["data"]),
                    "collection": self.get_collection_name(exec["type"])
                }
                for exec in actor_executions
            ]
        })
        
        # Store actor data
        for execution in actor_executions:
            await self.store_actor_data(run_id, execution)
        
        # Mark run as completed
        await self.db.actor_runs.update_one(
            {"_id": run_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now()
                }
            }
        )
        
        return run_id
    
    def get_collection_name(self, actor_type: str) -> str:
        collection_map = {
            "linkedin_profiles": "linkedin_profiles",
            "linkedin_posts": "linkedin_posts",
            "linkedin_companies": "linkedin_companies",
            "facebook_posts": "facebook_posts", 
            "twitter_posts": "twitter_posts",
            "erasmus_organizations": "erasmus_organizations",
            "zoominfo_companies": "zoominfo_companies",
            "duns_companies": "duns_companies"
        }
        return collection_map.get(actor_type, "unknown_actor_data")
```

## Summary

This MongoDB storage structure is **ready for implementation** and provides:

✅ **Separation**: Each actor's data in separate collections  
✅ **Linking**: Run-based relationship tracking  
✅ **Raw Data**: Complete preservation of actor outputs  
✅ **Metadata**: Execution tracking and cost monitoring  
✅ **Flexibility**: Adaptable to different backend architectures  

**Next Steps for Integration:**
1. Implement storage layer in your backend system
2. Configure MongoDB collections and indexes
3. Add data retention and cleanup policies
4. Test with sample actor outputs from this script collection
5. Monitor performance and adjust schema as needed

The exact implementation details will depend on your specific backend architecture, but this guide provides the foundation for storing all actor outputs efficiently in MongoDB. 