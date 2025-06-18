# Backend/database.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'resumatch')

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Collections
users = db.users
resumes = db.resumes
jobs = db.jobs
matches = db.matches
applications = db.applications

def get_collection(collection_name):
    """Get a collection by name"""
    return db[collection_name]

def init_db():
    """Initialize database with required indexes"""
    # Users collection indexes
    users.create_index('email', unique=True)
    users.create_index('role')
    
    # Resumes collection indexes
    resumes.create_index('user_id')
    resumes.create_index('skills')
    
    # Jobs collection indexes
    jobs.create_index('company')
    jobs.create_index('skills')
    jobs.create_index('status')
    
    # Matches collection indexes
    matches.create_index([('job_id', 1), ('resume_id', 1)], unique=True)
    matches.create_index('match_score')

def add_missing_user_names_to_db():
    """Adds a 'name' field to existing user documents that lack one, using email or role as fallback.
    This function is idempotent and can be run multiple times safely.
    """
    print("INFO: Checking for users without a 'name' field and adding defaults...")
    
    # Find users who do not have a 'name' field
    # Using a batch update for efficiency if many users need updating
    # Note: For very large collections, consider using aggregation pipeline with $out or $merge for better performance
    
    bulk_operations = []
    for user in users.find({"name": {"$exists": False}}):
        user_id = user.get('_id')
        email = user.get('email')
        role = user.get('role', 'seeker') # Default to 'seeker' if role is missing

        new_name = email.split('@')[0] if email else None
        if not new_name:
            if role == 'hr':
                new_name = "HR Professional"
            else:
                new_name = "Job Seeker"
        
        bulk_operations.append({
            'update_one': {
                'filter': {'_id': user_id},
                'update': {'$set': {'name': new_name}},
                'upsert': False
            }
        })

    if bulk_operations:
        try:
            result = users.bulk_write(bulk_operations)
            print(f"INFO: Successfully added 'name' field to {result.modified_count} user(s).")
        except Exception as e:
            print(f"ERROR: Failed to add missing user names: {e}")
    else:
        print("INFO: No users found without a 'name' field. Database is already up-to-date.")

def ensure_profile_fields():
    """Ensures all user documents have the necessary profile fields with default values.
    This function is idempotent and can be run multiple times safely.
    """
    print("INFO: Checking for users without complete profile fields and adding defaults...")
    
    # Define the default profile structure
    default_profile = {
        'name': '',
        'email': '',
        'phone': '',
        'location': '',
        'profile_pic_url': None,
        'education': [],
        'skills': [],
        'experience': [],
        'company_name': None,  # For HR users
        'resume_uploaded': False,  # For seekers
        'resume_filename': None,  # For seekers
        'resume_last_updated': None,  # For seekers
        'parsed_resume_data': {}  # For seekers
    }
    
    # Find users who are missing any of these fields
    bulk_operations = []
    for user in users.find({}):
        user_id = user.get('_id')
        updates = {}
        
        # Check each field and add if missing
        for field, default_value in default_profile.items():
            if field not in user:
                updates[field] = default_value
        
        if updates:
            bulk_operations.append({
                'update_one': {
                    'filter': {'_id': user_id},
                    'update': {'$set': updates},
                    'upsert': False
                }
            })

    if bulk_operations:
        try:
            result = users.bulk_write(bulk_operations)
            print(f"INFO: Successfully added missing profile fields to {result.modified_count} user(s).")
        except Exception as e:
            print(f"ERROR: Failed to add missing profile fields: {e}")
    else:
        print("INFO: All users have complete profile fields. Database is already up-to-date.")

def migrate_requirements_to_tags():
    """
    For all jobs, if 'tags' is missing but 'requirements' exists,
    split 'requirements' into a list and save as 'tags'.
    """
    jobs_to_update = jobs.find({"tags": {"$exists": False}, "requirements": {"$exists": True}})
    count = 0
    for job in jobs_to_update:
        req = job["requirements"]
        # Split by comma, strip whitespace, and filter out empty strings
        tags = [tag.strip() for tag in req.split(",") if tag.strip()]
        jobs.update_one({"_id": job["_id"]}, {"$set": {"tags": tags}})
        count += 1
    print(f"Updated {count} jobs with tags from requirements.")

# Initialize database on import
init_db()
# You can choose to call these functions here if you want them to run on every app startup
# However, it's generally better to call them explicitly as a migration step or via an admin interface.
# add_missing_user_names_to_db()
# ensure_profile_fields() 
