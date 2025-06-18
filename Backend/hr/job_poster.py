from datetime import datetime
from Backend.database import jobs, matches
from bson import ObjectId

def post_job(job_data, user_id):
    """Create a new job posting"""
    try:
        # Validate required fields
        required_fields = ['title', 'company', 'description', 'requirements', 'location', 'department', 'experience_level']
        for field in required_fields:
            if field not in job_data:
                return False, f"Missing required field: {field}"

        # Extract tags from requirements
        requirements = job_data.get('requirements', '')
        # Split by comma or newline, strip whitespace, ignore empty
        tags = [tag.strip() for tag in requirements.replace('\n', ',').split(',') if tag.strip()]

        # Create job document
        job = {
            'title': job_data['title'],
            'company': job_data['company'],
            'description': job_data['description'],
            'requirements': job_data['requirements'],
            'location': job_data['location'],
            'salary_range': job_data.get('salary_range'),
            'job_type': job_data.get('job_type', 'Full-time'),
            'department': job_data['department'],
            'experience_level': job_data['experience_level'],
            'posted_by': user_id,
            'hr_id': user_id,
            'posted_date': datetime.utcnow(),
            'status': 'active',
            'applications': [],
            'tags': tags
        }

        # Insert into database
        result = jobs.insert_one(job)
        
        return True, {
            'job_id': str(result.inserted_id),
            'message': 'Job posted successfully'
        }

    except Exception as e:
        return False, str(e)

def get_jobs(user_id=None, status='active'):
    """Get all jobs, optionally filtered by user_id and status"""
    try:
        query = {'status': status}
        if user_id:
            query['posted_by'] = user_id

        job_list = list(jobs.find(query).sort('posted_date', -1))
        
        # Debug logging
        print("DEBUG: Found jobs:", len(job_list))
        for job in job_list:
            print(f"DEBUG: Job {job['title']} requirements:", job.get('requirements'))
            print(f"DEBUG: Job {job['title']} requirements type:", type(job.get('requirements')))
        
        formatted_jobs = []
        for job in job_list:
            # Handle requirements
            requirements = job.get('requirements', '')
            if isinstance(requirements, str):
                skills = [skill.strip() for skill in requirements.split(',') if skill.strip()]
            elif isinstance(requirements, list):
                skills = requirements
            else:
                skills = []
            
            formatted_job = {
                'id': str(job['_id']),
                'title': job['title'],
                'company_name': job['company'],
                'location': job['location'],
                'type': job['job_type'],
                'salary': job.get('salary_range', 'Not specified'),
                'experience_level': job.get('experience_level', 'Not specified'),
                'required_skills': skills,
                'description': job.get('description', ''),
                'posted_date': job['posted_date'],
                'status': job['status'],
                'applications_count': len(job['applications'])
            }
            formatted_jobs.append(formatted_job)
            
            # Debug logging for formatted job
            print(f"DEBUG: Formatted job {formatted_job['title']} required_skills:", formatted_job['required_skills'])
        
        return True, formatted_jobs

    except Exception as e:
        print(f"DEBUG: Error in get_jobs: {str(e)}")
        return False, str(e)

def update_job(job_id, update_data, user_id):
    """Update an existing job posting"""
    try:
        # Verify job exists and belongs to user
        job = jobs.find_one({
            '_id': ObjectId(job_id),
            'posted_by': user_id
        })
        
        if not job:
            return False, "Job not found or unauthorized"

        # Update allowed fields
        allowed_fields = [
            'title', 'description', 'requirements', 'location',
            'salary_range', 'job_type', 'status'
        ]
        
        update_dict = {
            k: v for k, v in update_data.items()
            if k in allowed_fields
        }
        
        if not update_dict:
            return False, "No valid fields to update"

        # Update job
        result = jobs.update_one(
            {'_id': ObjectId(job_id)},
            {'$set': update_dict}
        )
        
        if result.modified_count == 0:
            return False, "No changes made"
            
        return True, "Job updated successfully"

    except Exception as e:
        return False, str(e)

def delete_job(job_id, user_id):
    """Delete a job posting"""
    try:
        # Verify job exists and belongs to user
        job = jobs.find_one({
            '_id': ObjectId(job_id),
            'posted_by': user_id
        })
        
        if not job:
            return False, "Job not found or unauthorized"

        # Delete job
        result = jobs.delete_one({'_id': ObjectId(job_id)})
        
        if result.deleted_count == 0:
            return False, "Failed to delete job"
            
        # Delete associated matches
        matches.delete_many({'job_id': job_id})
            
        return True, "Job deleted successfully"

    except Exception as e:
        return False, str(e) 