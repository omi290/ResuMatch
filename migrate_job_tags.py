#!/usr/bin/env python3
"""
Migration script to add tags to existing jobs that don't have them.
This script extracts skills from the 'requirements' field and creates 'tags'.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Backend'))

from Backend.database import jobs, migrate_requirements_to_tags
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'resumatch')

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
jobs = db.jobs

def main():
    print("Starting job tags migration...")
    
    # Count jobs without tags
    jobs_without_tags = jobs.count_documents({"tags": {"$exists": False}})
    print(f"Found {jobs_without_tags} jobs without tags")
    
    # Count jobs with requirements but no tags
    jobs_with_requirements_no_tags = jobs.count_documents({
        "tags": {"$exists": False}, 
        "requirements": {"$exists": True}
    })
    print(f"Found {jobs_with_requirements_no_tags} jobs with requirements but no tags")
    
    if jobs_with_requirements_no_tags > 0:
        print("Running migration...")
        migrate_requirements_to_tags()
        
        # Verify migration
        remaining_jobs_without_tags = jobs.count_documents({"tags": {"$exists": False}})
        print(f"Jobs without tags after migration: {remaining_jobs_without_tags}")
        
        if remaining_jobs_without_tags == 0:
            print("✅ Migration completed successfully!")
        else:
            print("⚠️  Some jobs still don't have tags")
    else:
        print("✅ No jobs need migration - all jobs already have tags or no requirements")
    
    # Show sample of jobs with tags
    print("\nSample of jobs with tags:")
    sample_jobs = list(jobs.find({"tags": {"$exists": True}}).limit(5))
    for job in sample_jobs:
        print(f"  - {job.get('title', 'N/A')}: {job.get('tags', [])}")

    # Update jobs missing hr_id
    result = jobs.update_many(
        {'hr_id': {'$exists': False}},
        [{'$set': {'hr_id': '$posted_by'}}]  # Use aggregation pipeline to copy posted_by to hr_id
    )

    print(f"Updated {result.modified_count} jobs to set hr_id = posted_by where missing.")

if __name__ == "__main__":
    main() 