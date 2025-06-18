import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pprint

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'resumatch')

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
applications = db.applications

pp = pprint.PrettyPrinter(indent=2)
print("All applications in the database (full documents):")
for app in applications.find():
    pp.pprint(app) 