import os
from werkzeug.utils import secure_filename
from flask import current_app, jsonify
from Backend.database import resumes, get_db
from Backend.resume_parser import parse_resume_with_extracta
import json
from datetime import datetime
from Backend.utils.file_utils import allowed_file, parse_resume
from Backend.templates.resume_templates import get_template_styles

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_resume(file, user_id):
    """
    Upload and process a resume file for a job seeker.
    
    Args:
        file: The uploaded file object
        user_id: The ID of the user uploading the resume
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        if not file or not allowed_file(file.filename):
            return False, "Invalid file type. Please upload a PDF or DOCX file."
            
        # Secure the filename and create upload path
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{user_id}_{timestamp}_{filename}"
        upload_path = os.path.join('uploads', 'resumes', filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        # Save the file
        file.save(upload_path)
        
        # Parse the resume
        parsed_data = parse_resume(upload_path)
        if not parsed_data:
            return False, "Failed to parse resume. Please ensure the file is readable."
            
        # Store resume data in database
        db = get_db()
        resume_doc = {
            'user_id': user_id,
            'filename': filename,
            'original_filename': file.filename,
            'upload_path': upload_path,
            'upload_date': datetime.now(),
            'status': 'active',
            'parsed_data': parsed_data
        }
        
        result = db.resumes.insert_one(resume_doc)
        
        return True, {
            'message': 'Resume uploaded successfully',
            'resume_id': str(result.inserted_id)
        }
        
    except Exception as e:
        return False, f"Error uploading resume: {str(e)}"

def get_resume(user_id, resume_id=None):
    """
    Get resume(s) for a user.
    
    Args:
        user_id: The ID of the user
        resume_id: Optional specific resume ID to retrieve
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (list/dict/str): Resume data or error message
    """
    try:
        db = get_db()
        query = {'user_id': user_id}
        
        if resume_id:
            query['_id'] = resume_id
            
        resumes = list(db.resumes.find(query))
        
        if not resumes:
            return False, "No resumes found"
            
        # Convert ObjectId to string for JSON serialization
        for resume in resumes:
            resume['_id'] = str(resume['_id'])
            
        return True, resumes[0] if resume_id else resumes
        
    except Exception as e:
        return False, f"Error retrieving resume(s): {str(e)}"

def update_resume(resume_id, user_id, data):
    """
    Update resume information.
    
    Args:
        resume_id: The ID of the resume to update
        user_id: The ID of the user
        data: Dictionary containing fields to update
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        db = get_db()
        
        # Verify resume exists and belongs to user
        resume = db.resumes.find_one({
            '_id': resume_id,
            'user_id': user_id
        })
        
        if not resume:
            return False, "Resume not found or unauthorized"
            
        # Update allowed fields
        allowed_fields = ['status', 'parsed_data']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return False, "No valid fields to update"
            
        result = db.resumes.update_one(
            {'_id': resume_id},
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            return False, "No changes made to resume"
            
        return True, "Resume updated successfully"
        
    except Exception as e:
        return False, f"Error updating resume: {str(e)}"

def delete_resume(resume_id, user_id):
    """
    Delete a resume.
    
    Args:
        resume_id: The ID of the resume to delete
        user_id: The ID of the user
        
    Returns:
        tuple: (success, result)
            - success (bool): Whether the operation was successful
            - result (dict/str): Success message or error message
    """
    try:
        db = get_db()
        
        # Verify resume exists and belongs to user
        resume = db.resumes.find_one({
            '_id': resume_id,
            'user_id': user_id
        })
        
        if not resume:
            return False, "Resume not found or unauthorized"
            
        # Delete the file
        if os.path.exists(resume['upload_path']):
            os.remove(resume['upload_path'])
            
        # Delete from database
        result = db.resumes.delete_one({'_id': resume_id})
        
        if result.deleted_count == 0:
            return False, "Failed to delete resume"
            
        return True, "Resume deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting resume: {str(e)}"

def parse_resume(resume_id):
    """Get parsed resume data"""
    try:
        resume = resumes.find_one({'_id': resume_id})
        if not resume:
            return False, "Resume not found"
        
        return True, resume['parsed_data']
        
    except Exception as e:
        return False, str(e)

def generate_resume(resume_id, template_name):
    """Generate resume in specified template"""
    try:
        resume = resumes.find_one({'_id': resume_id})
        if not resume:
            return False, "Resume not found"
        
        # Get template styles
        template = get_template_styles(template_name)
        
        if not template:
            return False, "Template not found"
        
        # Generate PDF using template and resume data
        # This is a placeholder - implement actual PDF generation
        generated_file = f"generated_{resume_id}_{template_name}.pdf"
        
        return True, {
            'filename': generated_file,
            'download_url': f"/download/{generated_file}"
        }
        
    except Exception as e:
        return False, str(e)

def get_user_resumes(user_id):
    """Get all resumes for a user"""
    try:
        user_resumes = list(resumes.find({'user_id': user_id}))
        return True, [{
            'id': str(resume['_id']),
            'filename': resume['original_filename'],
            'upload_date': resume['upload_date'],
            'status': resume['status']
        } for resume in user_resumes]
        
    except Exception as e:
        return False, str(e) 