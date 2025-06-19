from datetime import datetime
from Backend.database import jobs, resumes, matches, applications, users
from bson import ObjectId
from Backend.cpp_integration import run_skill_matcher, run_resume_ranker

def calculate_match_score(job_requirements, resume_skills):
    """Calculate match score between job requirements and resume skills using C++ skill_matcher"""
    try:
        # Parse job requirements into a list of skills
        if isinstance(job_requirements, str):
            job_skills_norm = [s.strip().lower() for s in job_requirements.split(',') if s.strip()]
        elif isinstance(job_requirements, list):
            job_skills_norm = [s.strip().lower() for s in job_requirements if isinstance(s, str) and s.strip()]
        else:
            job_skills_norm = []
        resume_skills_norm = [skill.strip().lower() for skill in resume_skills if isinstance(skill, str)]
        print(f"Calculating match score. Job skills: {job_skills_norm}, Resume skills: {resume_skills_norm}")
        match_score = run_skill_matcher(job_skills_norm, resume_skills_norm)
        print(f"Match score calculated: {match_score}")
        return round(match_score, 2)
    except Exception as e:
        print(f"Error calculating match score with C++: {str(e)}")
        return 0

def find_matches(job_id):
    """Find matching applicants for a job using C++ skill matcher and priority queue"""
    try:
        job = jobs.find_one({'_id': ObjectId(job_id)})
        if not job:
            return False, "Job not found"
        # Fetch all applications for this job
        job_applications = list(applications.find({'job_id': str(job_id)}))
        if not job_applications:
            return True, []
        # Prepare list for ranking
        applicant_list = []
        for app in job_applications:
            seeker_id = app.get('seeker_id')
            resume = resumes.find_one({'user_id': seeker_id, 'status': 'active'})
            if not resume:
                continue
            skills = resume.get('parsed_data', {}).get('skills', [])
            match_score = calculate_match_score(job.get('requirements', []), skills)
            user = users.find_one({'_id': ObjectId(seeker_id)})
            applicant_list.append({
                'application_id': str(app['_id']),
                'resume_id': str(resume['_id']),
                'user_id': seeker_id,
                'skills': skills,
                'match_score': match_score,
                'seeker_name': user.get('name', 'N/A') if user else 'N/A',
                'seeker_email': user.get('email', 'N/A') if user else 'N/A',
                'seeker_phone': user.get('phone', 'N/A') if user else 'N/A',
                'seeker_location': user.get('location', 'N/A') if user else 'N/A',
                'applied_date': app.get('application_date', ''),
                'status': app.get('status', 'Pending')
            })
        # Sort by match_score descending, take top 10 or all if less
        sorted_applicants = sorted(applicant_list, key=lambda x: x['match_score'], reverse=True)[:10]
        return True, sorted_applicants
    except Exception as e:
        return False, str(e)

def get_matches(job_id=None, user_id=None, status=None):
    """Get matches, optionally filtered by job_id, user_id, or status"""
    try:
        query = {}
        if job_id:
            query['job_id'] = job_id
        if user_id:
            query['user_id'] = user_id
        if status:
            query['status'] = status
            
        match_list = list(matches.find(query).sort('match_score', -1))
        
        enriched_matches = []
        for match in match_list:
            job = jobs.find_one({'_id': ObjectId(match['job_id'])})
            resume = resumes.find_one({'_id': ObjectId(match['resume_id'])})
            
            if job and resume:
                enriched_match = {
                    'id': str(match['_id']),
                    'job_id': match['job_id'],
                    'resume_id': match['resume_id'],
                    'match_score': match['match_score'],
                    'status': match['status'],
                    'created_at': match['created_at'],
                    'job_title': job['title'],
                    'company': job['company'],
                    'resume_name': resume['original_filename']
                }
                enriched_matches.append(enriched_match)
        
        return True, enriched_matches
        
    except Exception as e:
        return False, str(e)

def update_match_status(match_id, status, user_id):
    """Update the status of a match"""
    try:
        match = matches.find_one({'_id': ObjectId(match_id)})
        if not match:
            return False, "Match not found"
            
        job = jobs.find_one({'_id': ObjectId(match['job_id'])})
        if not job or job['posted_by'] != user_id:
            return False, "Unauthorized"
            
        result = matches.update_one(
            {'_id': ObjectId(match_id)},
            {'$set': {'status': status}}
        )
        
        if result.modified_count == 0:
            return False, "No changes made"
            
        return True, "Match status updated successfully"
        
    except Exception as e:
        return False, str(e)

def find_top_matches_for_job(job_id):
    """Find top matching seekers for a job using C++ skill matcher and priority queue (for HR View button)."""
    try:
        job = jobs.find_one({'_id': ObjectId(job_id)})
        if not job:
            return False, "Job not found"
        # Parse job requirements into a list of skills
        if isinstance(job.get('requirements', []), str):
            job_skills = [s.strip().lower() for s in job['requirements'].split(',') if s.strip()]
        elif isinstance(job.get('requirements', []), list):
            job_skills = [s.strip().lower() for s in job['requirements'] if isinstance(s, str) and s.strip()]
        else:
            job_skills = []
        seeker_users = list(users.find({'role': 'seeker'}))
        if not seeker_users:
            return True, []
        seeker_list = []
        for user in seeker_users:
            user_id = user.get('_id')
            resume = resumes.find_one({'user_id': str(user_id), 'status': 'active'})
            print(f"User: {user.get('email')}, Resume: {resume}")
            if not resume:
                continue
            # Extract skills from the correct nested path
            skills = (
                resume.get('parsed_data', {})
                      .get('data', {})
                      .get('document', {})
                      .get('skills', [])
            )
            if not skills:
                # fallback to old path if needed
                skills = resume.get('parsed_data', {}).get('skills', [])
            print(f"Parsed skills for user {user.get('email')}: {skills}")
            match_score = calculate_match_score(job_skills, skills)
            seeker_list.append({
                'user_id': str(user_id),
                'resume_id': str(resume['_id']),
                'skills': skills,
                'match_score': match_score,
                'seeker_name': user.get('name', 'N/A'),
                'seeker_email': user.get('email', 'N/A'),
                'seeker_phone': user.get('phone', 'N/A'),
                'seeker_location': user.get('location', 'N/A'),
                'status': 'Not Applied'  # Default status for non-applicants
            })
        sorted_seekers = sorted(seeker_list, key=lambda x: x['match_score'], reverse=True)[:10]
        return True, sorted_seekers
    except Exception as e:
        return False, str(e)
