from datetime import datetime
from Backend.database import jobs, resumes, matches
from bson import ObjectId
from Backend.cpp_integration import run_skill_matcher, run_resume_ranker

def calculate_match_score(job_requirements, resume_skills):
    """Calculate match score between job requirements and resume skills using C++ skill_matcher"""
    try:
        match_score = run_skill_matcher(job_requirements, resume_skills)
        return round(match_score, 2)
    except Exception as e:
        print(f"Error calculating match score with C++: {str(e)}")
        return 0

def find_matches(job_id):
    """Find matching resumes for a job using C++ skill matcher and resume ranker"""
    try:
        job = jobs.find_one({'_id': ObjectId(job_id)})
        if not job:
            return False, "Job not found"
        
        all_resumes = list(resumes.find({'status': 'active'}))
        
        # Prepare list for ranking
        resume_list = []
        for resume in all_resumes:
            skills = resume.get('parsed_data', {}).get('skills', [])
            match_score = calculate_match_score(job['requirements'], skills)
            if match_score > 0:
                resume_list.append({
                    'resume_id': str(resume['_id']),
                    'user_id': resume['user_id'],
                    'skills': skills,
                    'match_score': match_score
                })
        
        # Use C++ resume_ranker to get top ranked resumes
        top_ranked = run_resume_ranker(resume_list)
        
        job_matches = []
        for item in top_ranked[:10]:  # Top 10 matches
            match_data = {
                'job_id': str(job['_id']),
                'resume_id': item['resume_id'],
                'user_id': item['user_id'],
                'match_score': item['match_score'],
                'created_at': datetime.utcnow(),
                'status': 'pending'
            }
            matches.update_one(
                {
                    'job_id': str(job['_id']),
                    'resume_id': item['resume_id']
                },
                {'$set': match_data},
                upsert=True
            )
            job_matches.append(match_data)
        
        return True, job_matches
        
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
