import requests
import json

def test_external_jobs():
    """Test the external jobs endpoint"""
    try:
        # Test with default parameters
        print("Testing external jobs endpoint with default parameters...")
        response = requests.get('http://localhost:5000/external-jobs')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Number of jobs returned: {len(data) if isinstance(data, list) else 'Not a list'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print("First job sample:")
                    first_job = data[0]
                    print(f"  Title: {first_job.get('title', 'N/A')}")
                    print(f"  Company: {first_job.get('company_name', 'N/A')}")
                    print(f"  Location: {first_job.get('location', 'N/A')}")
                    print(f"  Job Type: {first_job.get('job_type', 'N/A')}")
                    print(f"  Match Percentage: {first_job.get('match_percentage', 'N/A')}")
                    print(f"  Tags: {first_job.get('tags', [])}")
                elif isinstance(data, dict) and 'error' in data:
                    print(f"Error returned: {data['error']}")
                else:
                    print("No jobs found or unexpected response format")
                    
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON response: {e}")
                print(f"Raw response: {response.text[:500]}...")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the Flask app is running on localhost:5000")
    except Exception as e:
        print(f"Unexpected error: {e}")

def test_external_jobs_with_filters():
    """Test the external jobs endpoint with filters"""
    try:
        print("\nTesting external jobs endpoint with filters...")
        params = {
            'q': 'python developer',
            'location': 'remote'
        }
        
        response = requests.get('http://localhost:5000/external-jobs', params=params)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of jobs returned with filters: {len(data) if isinstance(data, list) else 'Not a list'}")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the Flask app is running on localhost:5000")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_external_jobs()
    test_external_jobs_with_filters() 