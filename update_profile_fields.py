from Backend.database import ensure_profile_fields, users
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'resumatch')

def update_profile_fields():
    """Update all user documents to ensure they have the required profile fields"""
    print("Starting profile fields update...")
    
    # Define the default profile structure
    default_profile = {
        'name': None,
        'email': None,
        'phone': '',
        'location': '',
        'profile_pic_url': None,
        'education': [],
        'skills': [],
        'company_name': None  # For HR users
    }
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    users_collection = db.users
    
    # Update each user document
    for user in users_collection.find({}):
        user_id = user.get('_id')
        updates = {}
        
        # Check each field and add if missing
        for field, default_value in default_profile.items():
            if field not in user:
                updates[field] = default_value
        
        if updates:
            try:
                users_collection.update_one(
                    {'_id': user_id},
                    {'$set': updates}
                )
                print(f"Updated user {user_id}")
            except Exception as e:
                print(f"Error updating user {user_id}: {e}")
    
    print("Profile fields update completed.")

if __name__ == "__main__":
    update_profile_fields() 