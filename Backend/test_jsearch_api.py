import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get JSearch API key from environment
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

if not JSEARCH_API_KEY:
    print("ERROR: JSEARCH_API_KEY not found in environment variables. Please set it in your .env file.")
    exit()

url = "https://jsearch.p.rapidapi.com/search"
headers = {
    "X-RapidAPI-Key": JSEARCH_API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

params = {
    "query": "python developer",
    "page": "1",
    "num_pages": "1",
    "date_posted": "month"
}

print(f"Attempting to fetch jobs from {url} for query: {params['query']}")
print(f"Using API Key (first 5 chars): {JSEARCH_API_KEY[:5]}...")

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)

    print(f"HTTP Status Code: {response.status_code}")
    print(f"Raw Response Text (first 500 chars):\n{response.text[:500]}...")

    if response.status_code == 200:
        try:
            data = response.json()
            print("\nSuccessfully parsed JSON response!")
            print(f"Number of jobs found: {len(data.get('data', []))}")
            if data.get('data'):
                print("First job title:", data['data'][0].get('job_title'))
            else:
                print("No job data found in the response.")
        except requests.exceptions.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON response: {e}")
            print(f"Full Raw Response Text:\n{response.text}")
    else:
        print(f"ERROR: API returned a non-200 status code. Full Raw Response Text:\n{response.text}")

except requests.exceptions.Timeout:
    print("ERROR: Request timed out. The API took too long to respond.")
except requests.exceptions.RequestException as e:
    print(f"ERROR: An general request error occurred: {e}")
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}")
