from datetime import datetime
from Backend.database import get_db

from Backend.cpp_integration import run_skill_matcher
from datetime import datetime
from Backend.database import get_db

def apply_job(job_id, user_id, resume_id):
    """
    Apply for a job using a specific resume.
    
    Args:
        job_id: The ID of the job to apply for
        user_id: The ID of the user applying
        resume_id: The ID of the resume to use
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        db = get_db()
        
        # Verify job exists and is active
        job = db.jobs.find_one({
            '_id': job_id,
            'status': 'active'
        })
        
        if not job:
            return False, "Job not found or not active"
            
        # Verify resume exists and belongs to user
        resume = db.resumes.find_one({
            '_id': resume_id,
            'user_id': user_id,
            'status': 'active'
        })
        
        if not resume:
            return False, "Resume not found or not active"
            
        # Check if already applied
        existing_application = db.applications.find_one({
            'job_id': job_id,
            'user_id': user_id,
            'status': {'$ne': 'withdrawn'}
        })
        
        if existing_application:
            return False, "You have already applied for this job"
        
        # Calculate match score using C++ skill matcher
        job_requirements = job.get('requirements', [])
        resume_skills = resume.get('parsed_data', {}).get('skills', [])
        match_score = run_skill_matcher(job_requirements, resume_skills)
            
        # Create application
        application = {
            'job_id': job_id,
            'user_id': user_id,
            'resume_id': resume_id,
            'status': 'pending',
            'applied_date': datetime.now(),
            'match_score': round(match_score, 2)
        }
        
        result = db.applications.insert_one(application)
        
        return True, {
            'message': 'Application submitted successfully',
            'application_id': str(result.inserted_id)
        }
        
    except Exception as e:
        return False, f"Error submitting application: {str(e)}"

def get_applications(user_id, status=None):
    """
    Get all applications for a user.
    
    Args:
        user_id: The ID of the user
        status: Optional status filter
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (list/str): List of applications or error message
    """
    try:
        db = get_db()
        query = {'user_id': user_id}
        
        if status:
            query['status'] = status
            
        applications = list(db.applications.find(query))
        
        if not applications:
            return False, "No applications found"
            
        # Enrich application data with job and resume details
        enriched_applications = []
        for app in applications:
            job = db.jobs.find_one({'_id': app['job_id']})
            resume = db.resumes.find_one({'_id': app['resume_id']})
            
            if job and resume:
                enriched_app = {
                    'application_id': str(app['_id']),
                    'job': {
                        'id': str(job['_id']),
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location']
                    },
                    'resume': {
                        'id': str(resume['_id']),
                        'filename': resume['original_filename']
                    },
                    'status': app['status'],
                    'applied_date': app['applied_date'],
                    'match_score': app.get('match_score')
                }
                enriched_applications.append(enriched_app)
                
        return True, enriched_applications
        
    except Exception as e:
        return False, f"Error retrieving applications: {str(e)}"

def withdraw_application(application_id, user_id):
    """
    Withdraw a job application.
    
    Args:
        application_id: The ID of the application to withdraw
        user_id: The ID of the user
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        db = get_db()
        
        # Verify application exists and belongs to user
        application = db.applications.find_one({
            '_id': application_id,
            'user_id': user_id,
            'status': {'$ne': 'withdrawn'}
        })
        
        if not application:
            return False, "Application not found or already withdrawn"
            
        # Update application status
        result = db.applications.update_one(
            {'_id': application_id},
            {'$set': {'status': 'withdrawn'}}
        )
        
        if result.modified_count == 0:
            return False, "Failed to withdraw application"
            
        return True, "Application withdrawn successfully"
        
    except Exception as e:
        return False, f"Error withdrawing application: {str(e)}" 