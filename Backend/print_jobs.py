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
jobs = db.jobs

pp = pprint.PrettyPrinter(indent=2)
print("All jobs in the database (full documents):")
for job in jobs.find():
    pp.pprint(job) 