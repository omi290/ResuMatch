from Backend.database import get_db
from Backend.cpp_integration import run_skill_matcher, run_resume_ranker

def get_overview_recommendations(user_id):
    """
    Get top 10 job recommendations for a user using priority queue via C++ resume_ranker.
    Args:
        user_id (str): User ID
    Returns:
        tuple: (success, result)
            - success (bool)
            - result (list of job dicts) or error message
    """
    try:
        db = get_db()
        
        # Get user's active resume skills
        resume = db.resumes.find_one({'user_id': user_id, 'status': 'active'})
        if not resume:
            return False, "Active resume not found for user"
        
        resume_skills = resume.get('parsed_data', {}).get('skills', [])
        
        # Get all active jobs
        jobs = list(db.jobs.find({'status': 'active'}))
        
        # Prepare list for ranking
        job_list = []
        for job in jobs:
            job_skills = job.get('requirements', [])
            match_score = run_skill_matcher(job_skills, resume_skills)
            if match_score > 0:
                job_list.append({
                    'job_id': str(job['_id']),
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'location': job.get('location'),
                    'requirements': job_skills,
                    'match_score': match_score
                })
        
        # Use C++ resume_ranker to rank jobs by match_score
        ranked_jobs = run_resume_ranker(job_list)
        
        # Return top 10 jobs
        top_jobs = ranked_jobs[:10]
        
        return True, top_jobs
        
    except Exception as e:
        return False, str(e)
