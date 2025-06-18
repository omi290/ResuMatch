import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'resumatch')

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
jobs = db.jobs

# Update jobs missing tags
updated_count = 0
for job in jobs.find({'tags': {'$exists': False}}):
    requirements = job.get('requirements', '')
    # Split by comma or newline, strip whitespace, ignore empty
    tags = [tag.strip() for tag in requirements.replace('\n', ',').split(',') if tag.strip()]
    
    # Update the job with tags
    result = jobs.update_one(
        {'_id': job['_id']},
        {'$set': {'tags': tags}}
    )
    
    if result.modified_count > 0:
        updated_count += 1
        print(f"Updated job '{job.get('title', 'N/A')}' with tags: {tags}")

print(f"\nUpdated {updated_count} jobs with tags generated from requirements.") 