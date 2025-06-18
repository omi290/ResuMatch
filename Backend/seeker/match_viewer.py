from Backend.database import get_db

def get_matches(user_id, status=None):
    """
    Get all job matches for a user.
    
    Args:
        user_id: The ID of the user
        status: Optional status filter
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (list/str): List of matches or error message
    """
    try:
        db = get_db()
        query = {'user_id': user_id}
        
        if status:
            query['status'] = status
            
        matches = list(db.matches.find(query))
        
        if not matches:
            return False, "No matches found"
            
        # Enrich match data with job and resume details
        enriched_matches = []
        for match in matches:
            job = db.jobs.find_one({'_id': match['job_id']})
            resume = db.resumes.find_one({'_id': match['resume_id']})
            
            if job and resume:
                enriched_match = {
                    'match_id': str(match['_id']),
                    'job': {
                        'id': str(job['_id']),
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'job_type': job.get('job_type'),
                        'description': job.get('description')
                    },
                    'resume': {
                        'id': str(resume['_id']),
                        'filename': resume['original_filename']
                    },
                    'status': match['status'],
                    'match_score': match.get('match_score'),
                    'match_date': match.get('match_date')
                }
                enriched_matches.append(enriched_match)
                
        return True, enriched_matches
        
    except Exception as e:
        return False, f"Error retrieving matches: {str(e)}"

def update_match_status(match_id, user_id, status):
    """
    Update the status of a match.
    
    Args:
        match_id: The ID of the match to update
        user_id: The ID of the user
        status: The new status
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        db = get_db()
        
        # Verify match exists and belongs to user
        match = db.matches.find_one({
            '_id': match_id,
            'user_id': user_id
        })
        
        if not match:
            return False, "Match not found or unauthorized"
            
        # Validate status
        valid_statuses = ['interested', 'not_interested', 'applied']
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
        # Update match status
        result = db.matches.update_one(
            {'_id': match_id},
            {'$set': {'status': status}}
        )
        
        if result.modified_count == 0:
            return False, "No changes made to match status"
            
        return True, "Match status updated successfully"
        
    except Exception as e:
        return False, f"Error updating match status: {str(e)}" 