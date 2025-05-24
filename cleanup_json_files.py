#!/usr/bin/env python3
"""
Analyze and cleanup JSON test files - keep only the latest for each type.
"""

import os
import re
from datetime import datetime
from collections import defaultdict

def parse_filename(filename):
    """Parse filename to extract type and timestamp."""
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Extract timestamp if present (format: YYYYMMDD_HHMMSS)
    timestamp_match = re.search(r'(\d{8}_\d{6})$', name)
    timestamp = None
    if timestamp_match:
        timestamp_str = timestamp_match.group(1)
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            # Remove timestamp from name to get the type
            name = name.replace('_' + timestamp_str, '')
        except ValueError:
            pass
    
    # Categorize by file type patterns
    if name.startswith('linkedin_company'):
        if 'raw_output' in name:
            return 'linkedin_company_raw', timestamp
        elif 'final_demo' in name:
            return 'linkedin_company_demo', timestamp
        elif 'final_output' in name:
            return 'linkedin_company_final', timestamp
        elif 'real_output' in name:
            return 'linkedin_company_real', timestamp
        elif 'summary' in name:
            return 'linkedin_company_summary', timestamp
        elif name == 'linkedin_company_output':  # No timestamp
            return 'linkedin_company_basic', None
        else:
            return 'linkedin_company_other', timestamp
    elif name.startswith('linkedin_posts'):
        if 'scraper_output' in name:
            return 'linkedin_posts_scraper', timestamp
        elif 'test_' in name:
            return 'linkedin_posts_test', timestamp
        else:
            return 'linkedin_posts_other', timestamp
    elif name.startswith('linkedin_profile'):
        if 'error' in name:
            return 'linkedin_profile_error', timestamp
        elif 'output' in name:
            return 'linkedin_profile_output', timestamp
        else:
            return 'linkedin_profile_other', timestamp
    elif name.startswith('linkedin_raw'):
        return 'linkedin_raw', timestamp
    elif name.startswith('linkedin_test'):
        return 'linkedin_test', timestamp
    elif name.startswith('erasmus_actor_domain'):
        return 'erasmus_actor_domain', timestamp
    elif name.startswith('erasmus_actor_name'):
        return 'erasmus_actor_name', timestamp
    elif name.startswith('erasmus_org_result'):
        return 'erasmus_org_result', timestamp
    elif name.startswith('erasmus_website'):
        return 'erasmus_website', timestamp
    elif name.startswith('debug_erasmus'):
        return 'debug_erasmus', timestamp
    elif name.startswith('twitter_actor'):
        if 'error' in name:
            return 'twitter_actor_error', timestamp
        elif 'summary' in name:
            return 'twitter_actor_summary', timestamp
        elif 'test_' in name:
            return 'twitter_actor_test', timestamp
        else:
            return 'twitter_actor_other', timestamp
    else:
        return 'unknown', timestamp

def main():
    """Main function to analyze and cleanup JSON files."""
    print("🔍 Analyzing JSON test files...")
    
    # Get all JSON files
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    
    # Group files by type
    file_groups = defaultdict(list)
    
    for filename in json_files:
        file_type, timestamp = parse_filename(filename)
        file_size = os.path.getsize(filename)
        
        file_groups[file_type].append({
            'filename': filename,
            'timestamp': timestamp,
            'size': file_size
        })
    
    print(f"📊 Found {len(json_files)} JSON files in {len(file_groups)} categories:")
    print()
    
    files_to_keep = []
    files_to_delete = []
    
    # For each type, find the latest file
    for file_type, files in file_groups.items():
        print(f"📁 {file_type}:")
        
        # Sort by timestamp (newest first), then by size (largest first) for files without timestamp
        files_with_timestamp = [f for f in files if f['timestamp'] is not None]
        files_without_timestamp = [f for f in files if f['timestamp'] is None]
        
        if files_with_timestamp:
            files_with_timestamp.sort(key=lambda x: x['timestamp'], reverse=True)
            latest = files_with_timestamp[0]
            files_to_keep.append(latest['filename'])
            
            print(f"   ✅ KEEP: {latest['filename']} ({latest['size']:,} bytes) - {latest['timestamp']}")
            
            # Mark others for deletion
            for f in files_with_timestamp[1:] + files_without_timestamp:
                files_to_delete.append(f['filename'])
                ts_str = f['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if f['timestamp'] else 'No timestamp'
                print(f"   ❌ DELETE: {f['filename']} ({f['size']:,} bytes) - {ts_str}")
        elif files_without_timestamp:
            # If no files have timestamps, keep the largest one
            files_without_timestamp.sort(key=lambda x: x['size'], reverse=True)
            latest = files_without_timestamp[0]
            files_to_keep.append(latest['filename'])
            
            print(f"   ✅ KEEP: {latest['filename']} ({latest['size']:,} bytes) - Largest file")
            
            # Mark others for deletion
            for f in files_without_timestamp[1:]:
                files_to_delete.append(f['filename'])
                print(f"   ❌ DELETE: {f['filename']} ({f['size']:,} bytes)")
        
        print()
    
    print(f"📋 Summary:")
    print(f"   🟢 Files to KEEP: {len(files_to_keep)}")
    print(f"   🔴 Files to DELETE: {len(files_to_delete)}")
    print()
    
    if files_to_delete:
        print("🗑️  Files to be deleted:")
        for filename in sorted(files_to_delete):
            print(f"   - {filename}")
        
        print()
        response = input("❓ Proceed with deletion? (y/N): ").lower().strip()
        
        if response == 'y':
            deleted_count = 0
            for filename in files_to_delete:
                try:
                    os.remove(filename)
                    print(f"   ✅ Deleted: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Error deleting {filename}: {e}")
            
            print(f"\n🎉 Cleanup complete! Deleted {deleted_count} files.")
            print(f"📁 Kept {len(files_to_keep)} files (latest of each type).")
        else:
            print("❌ Cleanup cancelled.")
    else:
        print("✅ No files need to be deleted.")

if __name__ == "__main__":
    main() 