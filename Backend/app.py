# app.py - Improved version with resume generation and template support
from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect, url_for, render_template, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pathlib
from Backend.resume_parser import parse_resume_with_extracta, extract_text_from_file
from Backend.templates.resume_templates import get_template_styles
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import json
from dotenv import load_dotenv  # Add this import
from functools import wraps
from Backend.hr.routes import hr_bp
from Backend.auth.routes import auth_bp  # Import the auth blueprint
from Backend.auth.auth_handler import get_current_user # Import get_current_user
from Backend.database import db, resumes, users # Import the db object and resumes/users collections
from datetime import timedelta, datetime
from bson.objectid import ObjectId
from Backend.hr.job_poster import get_jobs as hr_get_jobs # Import get_jobs with an alias
import inspect # Add this import for debugging
import logging # Ensure logging is imported
from Backend.resume_parser import test_parser_configuration
from bson import ObjectId
import requests
import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'templates'))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'static')) # Define static directory
print(f"DEBUG: STATIC_DIR is set to: {STATIC_DIR}") # Debug print to confirm path

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(hr_bp, url_prefix='/hr')
app.register_blueprint(auth_bp, url_prefix='/auth')  # Register the auth blueprint

# Get current working directory
BASE_DIR = pathlib.Path(__file__).parent.absolute()
FRONTEND_DIR = BASE_DIR.parent / 'Frontend'
UPLOAD_FOLDER = BASE_DIR / 'Uploads'
PROFILE_PICS_FOLDER = BASE_DIR.parent / 'static' / 'profile_pics' # New folder for profile pictures

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True) # Create profile pictures directory
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Add session configuration
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production
app.config['SESSION_PERMANENT'] = True  # Make sessions permanent
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31) # Set session lifetime to 31 days

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: login_required (before check): Session keys: {list(session.keys())}, user_id: {session.get('user_id')}") # More detailed debug
        if 'user_id' not in session:
            print(f"DEBUG: login_required: User ID not in session. Redirecting to login for route {request.path}") # More specific debug
            return redirect(url_for('login'))
        print(f"DEBUG: login_required: User ID found in session for route {request.path}. Proceeding.") # More specific debug
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Update home route
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
@app.route('/')
def home():
    return render_template('index.html', current_year=datetime.now().year)

# Add proper route handlers
@app.route('/about')
def about():
    return render_template('about.html', current_year=datetime.now().year)

@app.route('/login')
def login():
    role = request.args.get('role', 'seeker')
    return render_template('login.html', current_year=datetime.now().year)

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('user_role', 'seeker')
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # Ensure _id is present, fallback to session user_id
    user_id = user.get('id') or session.get('user_id')
    if not user_id:
        session.clear()
        return redirect(url_for('login'))

    current_year = datetime.now().year

    if role == 'hr':
        # Redirect HR users to the dedicated HR dashboard
        return redirect(url_for('hr_dashboard_alt'))
    elif role == 'seeker':
        recent_matches = get_seeker_matches(str(user_id))
        
        # Fetch applied jobs for this seeker
        from Backend.database import applications
        seeker_applications = list(applications.find({'seeker_id': str(user_id)}).sort('application_date', -1))
        applied_jobs = []
        for app in seeker_applications:
            applied_jobs.append({
                'id': str(app['_id']),
                'job_id': app.get('job_id'),
                'job_title': app.get('job_title', 'N/A'),
                'company_name': app.get('company_name', 'N/A'),
                'application_date': app['application_date'].strftime('%Y-%m-%d %H:%M') if app.get('application_date') else 'N/A',
                'status': app.get('status', 'Pending'),
                'status_color': {
                    'Pending': 'warning',
                    'Reviewed': 'info',
                    'Accepted': 'success',
                    'Rejected': 'danger',
                    'Applied': 'primary'
                }.get(app.get('status', 'Pending'), 'secondary'),
            })
        
        seeker_stats = {
            'match_score': user.get('match_score', 0),
            'job_matches': len(recent_matches),
            'applications': len(applied_jobs),
            'profile_views': user.get('profile_views', 0)
        }
        profile_completion = user.get('profile_completion', 0)
        
        return render_template('seeker_dashboard.html', 
                             user=user, 
                             stats=seeker_stats, 
                             recent_matches=recent_matches, 
                             profile_completion=profile_completion, 
                             applied_jobs=applied_jobs, 
                             current_year=current_year)
    return render_template('seeker_dashboard.html', user=user, current_year=current_year)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/post-job')
@login_required
@role_required('hr')
def post_job_page():
    return render_template('post_job.html', current_year=datetime.now().year)

@app.route('/view-matches')
@login_required
@role_required('hr')
def view_matches():
    return render_template('view_matches.html', current_year=datetime.now().year)

@app.route('/resume-upload')
@login_required
@role_required('seeker')
def resume_upload():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))

    parsed_resume_data = user.get('parsed_resume_data', None)
    return render_template('resume-upload-page.html', parsed_resume=parsed_resume_data, current_year=datetime.now().year)

@app.route('/job-matching')
@login_required
@role_required('seeker')
def job_matching():
    print("DEBUG: Accessing job-matching route.") # Debug print
    return render_template('job-matching-page.html', current_year=datetime.now().year)

@app.route('/resume-generation')
@login_required
@role_required('seeker')
def resume_generation():
    print("DEBUG: Accessing resume-generation route.") # Debug print
    user = get_current_user()
    is_logged_in = 'user_id' in session
    return render_template('resume-generation-page.html', current_year=datetime.now().year, user=user, is_logged_in=is_logged_in)

@app.route('/signup')
def signup():
    return render_template('signup.html', current_year=datetime.now().year)

@app.route('/hr-dashboard')
@login_required
def hr_dashboard_alt():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))

    if user.get('role') != 'hr':
        flash('You do not have permission to access the HR dashboard.', 'danger')
        return redirect(url_for('dashboard'))

    current_year = datetime.now().year

    from Backend.database import jobs, applications, users

    # Fetch jobs posted by this HR user
    hr_jobs = list(jobs.find({'hr_id': user['id']}))
    job_ids = [str(job['_id']) for job in hr_jobs]

    # For each job, count applications and fetch candidate details
    total_applications = 0
    jobs_with_candidates = []
    for job in hr_jobs:
        job_id_str = str(job['_id'])
        job_applications = list(applications.find({'job_id': job_id_str}))
        applications_count = len(job_applications)
        total_applications += applications_count
        # Fetch candidate details for each application
        candidates = []
        for app in job_applications:
            seeker = users.find_one({'_id': app.get('seeker_id')})
            candidates.append({
                'application_id': str(app['_id']),
                'seeker_name': app.get('seeker_name', 'N/A'),
                'seeker_email': app.get('seeker_email', 'N/A'),
                'seeker_phone': app.get('seeker_phone', 'N/A'),
                'seeker_location': app.get('seeker_location', 'N/A'),
                'job_title': app.get('job_title', 'N/A'),
                'applied_date': app.get('application_date').strftime('%Y-%m-%d %H:%M') if app.get('application_date') else 'N/A',
                'status': app.get('status', 'Pending'),
                'status_color': {
                    'Pending': 'warning',
                    'Reviewed': 'info',
                    'Accepted': 'success',
                    'Rejected': 'danger',
                    'Applied': 'primary'
                }.get(app.get('status', 'Pending'), 'secondary'),
            })
        job['applications_count'] = applications_count
        job['candidates'] = candidates
        jobs_with_candidates.append(job)

    stats = {
        'active_jobs': len(hr_jobs),
        'total_applications': total_applications,
        'job_views': 0, # To be implemented
        'top_matches': 0 # To be implemented
    }

    # Debug print for posted_jobs and candidates
    pp = pprint.PrettyPrinter(indent=2)
    print("\n[DEBUG] posted_jobs/candidates for HR dashboard:")
    for job in jobs_with_candidates:
        print(f"Job: {job.get('title')} (ID: {job.get('_id')})")
        print(f"  Candidates: {len(job.get('candidates', []))}")
        for cand in job.get('candidates', []):
            print(f"    - {cand.get('seeker_name')} (Status: {cand.get('status')})")

    return render_template('hr_dashboard.html', 
                           user=user,
                           stats=stats,
                           posted_jobs=jobs_with_candidates, # Pass jobs with candidates
                           current_year=current_year)

@app.route('/resume-upload-page')
def resume_upload_page():
    return render_template('resume-upload-page.html', current_year=datetime.now().year)

@app.route('/seeker_dashboard')
@login_required
def seeker_dashboard_alt():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    if user.get('role') != 'seeker':
        flash('You do not have permission to access the seeker dashboard.', 'danger')
        return redirect(url_for('dashboard'))

    current_year = datetime.now().year

    from Backend.database import applications, jobs

    # Fetch applications made by this seeker
    seeker_applications = list(applications.find({'seeker_id': user['id']}).sort('application_date', -1))
    
    applied_jobs = []
    for app in seeker_applications:
        # Optionally, fetch job details from the jobs collection if more info is needed
        # For now, use the snapshot data stored in the application itself
        applied_jobs.append({
            'id': str(app['_id']),
            'job_id': app.get('job_id'),
            'job_title': app.get('job_title', 'N/A'),
            'company_name': app.get('company_name', 'N/A'),
            'application_date': app['application_date'].strftime('%Y-%m-%d %H:%M') if app.get('application_date') else 'N/A',
            'status': app.get('status', 'Pending'),
            'status_color': {
                'Pending': 'warning',
                'Reviewed': 'info',
                'Accepted': 'success',
                'Rejected': 'danger'
            }.get(app.get('status', 'Pending'), 'secondary'),
            # You can add more details from the job itself if needed
            # e.g., 'job_location': jobs.find_one({'_id': ObjectId(app['job_id'])}).get('location')
        })

    # Placeholder stats for seeker dashboard
    seeker_stats = {
        'match_score': user.get('match_score', 0),
        'job_matches': user.get('job_matches', 0),
        'applications': len(seeker_applications),
        'profile_views': user.get('profile_views', 0)
    }

    # `recent_matches` is already fetched in dashboard route if applicable for seeker
    # For this specific route, we'll ensure it's passed if available, else empty list
    recent_matches = user.get('recent_matches', [])

    profile_completion = user.get('profile_completion', 0) # Placeholder for actual calculation

    return render_template('seeker_dashboard.html', 
                           user=user, 
                           stats=seeker_stats, 
                           recent_matches=recent_matches,
                           applied_jobs=applied_jobs, # Pass applied jobs data
                           profile_completion=profile_completion, 
                           current_year=current_year)

@app.route('/view_matches')
def view_matches_alt():
    return render_template('view_matches.html', current_year=datetime.now().year)

@app.route('/hr_dashboard')
@login_required
def hr_dashboard_underscore():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))
    return render_template('hr_dashboard.html', user=user, current_year=datetime.now().year)

@app.route('/job-matching-page')
def job_matching_page():
    return render_template('job-matching-page.html', current_year=datetime.now().year)

@app.route('/resume-generation-page')
def resume_generation_page_alt():
    return render_template('resume-generation-page.html', current_year=datetime.now().year)

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))

    current_year = datetime.now().year # Get current year

    if user['role'] == 'hr':
        return render_template('hr_profile.html', user=user, current_year=current_year)
    elif user['role'] == 'seeker':
        return render_template('seeker_profile.html', user=user, current_year=current_year)
    return redirect(url_for('dashboard')) # Fallback to dashboard if role is unknown

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()
    print(f"DEBUG: Data received for profile update: {data}") # Add this debug print
    updated_fields = {}

    # Fields common to both roles
    if 'name' in data and data['name'].strip() != '':
        updated_fields['name'] = data['name'].strip()
    if 'phone' in data:
        updated_fields['phone'] = data['phone'].strip()
    if 'location' in data:
        updated_fields['location'] = data['location'].strip()

    if user['role'] == 'hr':
        if 'company_name' in data and data['company_name'].strip() != '':
            updated_fields['company_name'] = data['company_name'].strip()
        # Add HR-specific fields
        if 'education' in data and isinstance(data['education'], list):
            updated_fields['education'] = data['education']
        if 'skills' in data and isinstance(data['skills'], list):
            updated_fields['skills'] = data['skills']
        if 'experience' in data and isinstance(data['experience'], list):
            updated_fields['experience'] = data['experience']

    # Fields specific to seeker
    elif user['role'] == 'seeker':
        if 'education' in data and isinstance(data['education'], list):
            updated_fields['education'] = data['education']
        if 'skills' in data and isinstance(data['skills'], list):
            updated_fields['skills'] = data['skills']
        if 'experience' in data and isinstance(data['experience'], list):
            updated_fields['experience'] = data['experience']
        if 'resume_path' in data:
            updated_fields['resume_path'] = data['resume_path']
        if 'parsed_resume_data' in data:
            updated_fields['parsed_resume_data'] = data['parsed_resume_data']

    if updated_fields:
        # Ensure we use ObjectId for database query
        from Backend.database import users # Import users collection
        result = users.update_one({'_id': ObjectId(user['id'])}, {'$set': updated_fields})
        if result.modified_count > 0:
            print(f"DEBUG: User {user['email']} profile updated successfully.")
            return jsonify({'message': 'Profile updated successfully'}), 200
        else:
            print(f"DEBUG: User {user['email']} profile update failed or no changes detected.")
            return jsonify({'message': 'No changes detected or profile update failed'}), 200
    else:
        print("DEBUG: No valid fields provided for profile update.")
        return jsonify({'message': 'No valid fields provided for update'}), 400

@app.route('/profile/upload_photo', methods=['POST'])
@login_required
def upload_profile_photo():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401

    if 'profile_photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['profile_photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user['id']}_{file.filename}") # Prepend user ID to filename
        filepath = os.path.join(PROFILE_PICS_FOLDER, filename)
        file.save(filepath)

        # Update user's profile_pic_url in the database
        from Backend.database import users # Import users collection
        users.update_one({'_id': ObjectId(user['id'])}, {'$set': {'profile_pic_url': url_for('static', filename=f'profile_pics/{filename}')}})

        return jsonify({'message': 'Profile photo uploaded successfully', 'profile_pic_url': url_for('static', filename=f'profile_pics/{filename}')}), 200
    else:
        return jsonify({'error': 'File type not allowed or invalid file'}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    try:
        user = get_current_user()
        if not user:
            logger.error("User not authenticated")
            return jsonify({"error": "User not authenticated"}), 401

        if 'resume' not in request.files:
            logger.error("No file uploaded")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['resume']
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({"error": "Invalid file type. Please upload PDF or DOCX"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(file_path)
            logger.info(f"File saved successfully at: {file_path}")
        except Exception as save_error:
            logger.error(f"Error saving file: {str(save_error)}")
            return jsonify({"error": "Failed to save file"}), 500

        # Parse the resume
        try:
            logger.info("Attempting to parse resume...")
            parsed_data = parse_resume_with_extracta(file_path)
            if not parsed_data:
                logger.error("Parsing returned None")
                return jsonify({"error": "Parsing failed - no data returned"}), 500
            logger.info("Resume parsed successfully")
        except Exception as parse_error:
            logger.error(f"Error during parsing: {str(parse_error)}")
            return jsonify({"error": f"Parsing failed: {str(parse_error)}"}), 500

        # Post-process parsed_data to extract skills from education
        doc = parsed_data.get('data', {}).get('document', {})
        doc['skills'] = list(doc.get('skills', []))  # Ensure it's a list
        doc = extract_skills_from_education(doc)
        parsed_data['data']['document'] = doc

        # Save parsed data to parsed_resume.json temporarily
        try:
            parsed_resume_path = os.path.join(BASE_DIR, 'parsed_resume.json')
            with open(parsed_resume_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            logger.info("Parsed data saved to JSON file")
        except Exception as json_error:
            logger.error(f"Error saving to JSON: {str(json_error)}")
            return jsonify({"error": "Failed to save parsed data"}), 500

        # Format the response data
        try:
            formatted_data = format_response_data(parsed_data)
            logger.info("Data formatted successfully")
        except Exception as format_error:
            logger.error(f"Error formatting data: {str(format_error)}")
            return jsonify({"error": "Failed to format parsed data"}), 500

        # Save to database
        try:
            # Delete existing resume file if it exists for the user
            existing_resume = db.users.find_one({'_id': ObjectId(user['id'])})
            if existing_resume and 'resume_filename' in existing_resume:
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_resume['resume_filename'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    logger.info("Old resume file deleted")

            # Check if user already has a resume document
            existing_resume_doc = resumes.find_one({'user_id': user['id']})

            if existing_resume_doc:
                # Update existing resume document
                resumes.update_one(
                    {'_id': existing_resume_doc['_id']},
                    {'$set': {
                        'parsed_data': parsed_data,
                        'original_filename': filename,
                        'file_path': file_path, # Store the full file path
                        'upload_date': datetime.utcnow(),
                        'status': 'active' # Ensure status is set to active when updating
                    }}
                )
                resume_id = existing_resume_doc['_id']
            else:
                # Insert new resume document
                resume_doc = {
                    'user_id': user['id'],
                    'parsed_data': parsed_data,
                    'original_filename': filename,
                    'file_path': file_path, # Store the full file path
                    'upload_date': datetime.utcnow(),
                    'status': 'active'
                }
                insert_result = resumes.insert_one(resume_doc)
                resume_id = insert_result.inserted_id
                logger.info("New resume document created")

            # Update user document
            users.update_one(
                {'_id': ObjectId(user['id'])},
                {'$set': {
                    'current_resume_id': str(resume_id),
                    'resume_filename': filename,
                    'resume_uploaded': True,
                    'resume_last_updated': datetime.utcnow()
                }}
            )
            logger.info("User document updated with resume information")

            # Clear the parsed_resume.json file
            with open(parsed_resume_path, 'w') as f:
                json.dump({}, f)
            logger.info("Parsed resume JSON file cleared")

            return formatted_data

        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            return jsonify({"error": "Failed to save resume data to database"}), 500

    except Exception as e:
        logger.error(f"Unexpected error in upload_resume: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_skills_from_education(parsed_resume):
    # Ensure 'skills' is a list
    skills = set(parsed_resume.get('skills', []))
    education = parsed_resume.get('education', [])
    for edu in education:
        for key in ['degree', 'school']:
            value = edu.get(key, '')
            # Look for common skill patterns
            if ':' in value:
                label, items = value.split(':', 1)
                if any(word in label.lower() for word in ['skill', 'programming', 'language', 'development', 'tool', 'technology', 'version control']):
                    for skill in items.split(','):
                        skill = skill.strip()
                        if skill and skill.lower() not in ['n/a']:
                            skills.add(skill)
            # Also add if the value itself looks like a skill
            elif value and value.lower() not in ['n/a']:
                if any(word in value.lower() for word in ['python', 'c++', 'html', 'css', 'git', 'excel', 'powerpoint']):
                    skills.add(value.strip())
    parsed_resume['skills'] = list(skills)
    return parsed_resume

def format_response_data(parsed_data):
    """Format the response data to match what the frontend expects"""
    
    # Default empty response structure
    formatted_data = {
        "name": "",
        "email": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "extracurricular": []
    }
    
    try:
        # Extract document from the parsed data
        doc = parsed_data.get("data", {}).get("document", {})
        
        # Basic information
        formatted_data["name"] = doc.get("name", "")
        formatted_data["email"] = doc.get("email", "")
        
        # Skills - ensure it's a list of strings
        skills = doc.get("skills", [])
        if isinstance(skills, list):
            formatted_data["skills"] = skills
        else:
            formatted_data["skills"] = [skills] if skills else []
        
        # Experience
        raw_experience = doc.get("experience", [])
        if not isinstance(raw_experience, list):
            raw_experience = [raw_experience] if raw_experience else []
            
        formatted_experience = []
        for exp in raw_experience:
            if isinstance(exp, dict):
                formatted_exp = {
                    "title": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "duration": f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}" if ('start_date' in exp or 'end_date' in exp) else exp.get("duration", "")
                }
                formatted_experience.append(formatted_exp)
        
        formatted_data["experience"] = formatted_experience
        
        # Education
        raw_education = doc.get("education", [])
        if not isinstance(raw_education, list):
            raw_education = [raw_education] if raw_education else []
            
        formatted_education = []
        for edu in raw_education:
            if isinstance(edu, dict):
                formatted_edu = {
                    "degree": edu.get("degree", ""),
                    "school": edu.get("institution", "") or edu.get("school", ""),
                    "duration": f"{edu.get('start_date', '')} - {edu.get('end_date', 'Present')}" if ('start_date' in edu or 'end_date' in edu) else edu.get("duration", "")
                }
                formatted_education.append(formatted_edu)
        
        formatted_data["education"] = formatted_education
        
        # Additional sections
        additional_sections = doc.get("additional_sections", {})
        
        # Certifications
        if "certifications" in additional_sections:
            certifications = additional_sections["certifications"]
            formatted_data["certifications"] = certifications if isinstance(certifications, list) else [certifications]
        
        # Extracurricular activities
        if "extracurricular" in additional_sections:
            extracurricular = additional_sections["extracurricular"]
            formatted_data["extracurricular"] = extracurricular if isinstance(extracurricular, list) else [extracurricular]
        
        logger.info(f"Formatted data being sent to frontend: {json.dumps(formatted_data, indent=2)}")
        return jsonify(formatted_data)
    except Exception as e:
        logger.error(f"Error formatting response data: {str(e)}")
        # Return default empty structure on error to prevent crashing frontend
        return jsonify(formatted_data)

import subprocess
import tempfile
import json
import os

@app.route('/external-jobs')
def external_jobs():
    import requests
    try:
        query = request.args.get("q", "python developer")
        location = request.args.get("location", "")
        print(f"[DEBUG] external_jobs route - Received query: '{query}', location: '{location}'")
        
        # Validate query
        if not query or query.strip() == "":
            query = "python developer"
        
        # Get API key from environment
        api_key = os.getenv("JSEARCH_API_KEY")
        if not api_key:
            print("[ERROR] JSEARCH_API_KEY not found in environment variables")
            # Try to load cached jobs as fallback
            return load_cached_jobs()
        
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        # Split query into individual skills/keywords and clean them
        skills = [skill.strip().lower() for skill in query.split() if skill.strip()]
        if not skills:
            skills = ["python", "developer"]
        print(f"[DEBUG] external_jobs route - Skills derived from query: {skills}")
        
        all_jobs = []
        seen_job_ids = set()
        
        # Load parsed resume skills from JSON file
        parsed_resume_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'parsed_resume.json')
        print(f"[DEBUG] external_jobs route - Loading parsed resume from: {parsed_resume_path}")
        resume_skills = []
        try:
            with open(parsed_resume_path, 'r', encoding='utf-8') as f:
                parsed_resume_data = json.load(f)
            resume_skills = parsed_resume_data.get('skills', [])
            print(f"[DEBUG] external_jobs route - Resume skills loaded: {resume_skills}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARNING] Could not load or decode parsed_resume.json: {e}. Falling back to query skills.")
            resume_skills = skills
            print(f"[DEBUG] external_jobs route - Using fallback skills: {resume_skills}")
        
        # Define a set of stopwords/prepositions to filter out from job skills/tags
        stopwords = set([
            "in", "at", "on", "and", "or", "the", "a", "an", "to", "for", "with", "of", "by", "from",
            "is", "are", "was", "were", "be", "been", "has", "have", "had", "will", "would", "can",
            "could", "should", "may", "might", "must", "do", "does", "did", "but", "if", "else", "then",
            "when", "where", "how", "what", "which", "who", "whom", "this", "that", "these", "those",
            "as", "such", "not", "no", "yes", "all", "any", "some", "each", "every", "other", "more",
            "most", "many", "much", "few", "several", "one", "two", "first", "second", "new", "used"
        ])
        
        api_success = False
        for skill in skills:
            if len(all_jobs) >= 50:  # Limit total jobs
                break
                
            params = {
                "query": skill,
                "page": "1",
                "num_pages": "1",
                "date_posted": "month"  # Get jobs from last month
            }
            if location:
                params["query"] = f"{skill} {location}"
            
            print(f"[DEBUG] Making request to: {url} with skill: {skill}")
            try:
                res = requests.get(url, headers=headers, params=params, timeout=15)  # Increased timeout
                
                if res.status_code != 200:
                    print(f"[ERROR] API returned status code: {res.status_code} for skill: {skill}")
                    print(f"[ERROR] Raw API Response: {res.text[:200]}...")  # Limit response text
                    continue  # Continue with next skill instead of returning error
                
                try:
                    data = res.json()
                    jobs = data.get("data", [])
                    print(f"[DEBUG] API call for skill '{skill}' returned {len(jobs)} jobs.")
                    api_success = True
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to decode JSON for skill {skill}: {e}")
                    continue
                
                for job in jobs:
                    if len(all_jobs) >= 50:  # Limit total jobs
                        break
                        
                    job_id = job.get("job_id") or job.get("job_apply_link") or job.get("job_title")
                    if job_id and job_id not in seen_job_ids:
                        seen_job_ids.add(job_id)
                        print(f"[DEBUG] Adding job ID: {job_id} to all_jobs. Current total: {len(all_jobs) + 1}")
                        
                        # Extract and clean job skills/tags
                        job_tags = job.get("job_highlights", {}).get("Qualifications", [])
                        job_skills_list = []
                        for qual in job_tags:
                            # Split by commas and spaces, filter out stopwords and short words
                            words = [w.strip().lower() for w in qual.replace(',', ' ').split()]
                            filtered_words = [w for w in words if w.isalpha() and len(w) > 2 and w not in stopwords]
                            job_skills_list.extend(filtered_words)
                        
                        # Remove duplicates and limit to 10 skills
                        job_skills_list = list(dict.fromkeys(job_skills_list))[:10]
                        
                        # Simple skill matching without C++ executable
                        match_percentage = 0.0
                        if resume_skills and job_skills_list:
                            # Convert all skills to lowercase for comparison
                            resume_skills_lower = [skill.lower() for skill in resume_skills]
                            job_skills_lower = [skill.lower() for skill in job_skills_list]
                            
                            # Count matches
                            matches = sum(1 for job_skill in job_skills_lower if any(resume_skill in job_skill or job_skill in resume_skill for resume_skill in resume_skills_lower))
                            
                            # Calculate percentage based on job skills (what percentage of job skills match resume skills)
                            if job_skills_lower:
                                match_percentage = (matches / len(job_skills_lower)) * 100
                        
                        print(f"[DEBUG] Skill matcher for job {job_id} returned: {match_percentage}%")
                        
                        job['match_percentage'] = match_percentage
                        job['tags'] = job_skills_list
                        all_jobs.append(job)
                    
            except requests.Timeout:
                print(f"[ERROR] Request timed out for skill: {skill}")
                continue
            except requests.RequestException as e:
                print(f"[ERROR] Request failed for skill {skill}: {e}")
                continue
        
        # If API failed completely, try to load cached jobs
        if not api_success or len(all_jobs) == 0:
            print("[WARNING] API failed or returned no jobs. Loading cached jobs as fallback.")
            return load_cached_jobs()
        
        # Save all jobs to jobs.json for reuse
        jobs_json_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'jobs.json')
        print(f"[DEBUG] Attempting to save {len(all_jobs)} jobs to jobs.json")
        try:
            with open(jobs_json_path, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] Saved {len(all_jobs)} jobs to jobs.json")
        except Exception as e:
            print(f"[ERROR] Failed to save jobs.json: {e}")
        
        # Transform the combined job data to match the frontend expectations
        formatted_jobs = []
        for job in all_jobs[:15]:  # Limit to 15 jobs
            # Clean and validate job data
            title = job.get("job_title", "").strip()
            company = job.get("employer_name", "").strip()
            location = job.get("job_city", "") + ", " + job.get("job_state", "") if job.get("job_city") else job.get("job_country", "")
            
            # Skip jobs with missing essential data
            if not title or not company:
                continue
                
            formatted_job = {
                "title": title,
                "company_name": company,
                "url": job.get("job_apply_link", "") or job.get("job_google_link", ""),
                "tags": job.get("tags", []),
                "location": location,
                "job_type": job.get("job_employment_type", ""),
                "salary": job.get("job_salary", "") or "Not specified",
                "description": job.get("job_description", "")[:500] + "..." if job.get("job_description") else "",
                "match_percentage": job.get("match_percentage", 0.0)
            }
            formatted_jobs.append(formatted_job)
        
        print(f"[DEBUG] Returning {len(formatted_jobs)} formatted jobs to frontend.")
        return jsonify(formatted_jobs)
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch jobs: {e}")
        # Try to load cached jobs as fallback
        return load_cached_jobs()

def load_cached_jobs():
    """Load cached jobs from jobs.json as fallback"""
    try:
        jobs_json_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'jobs.json')
        if os.path.exists(jobs_json_path):
            with open(jobs_json_path, 'r', encoding='utf-8') as f:
                cached_jobs = json.load(f)
            
            # Transform cached jobs to match frontend expectations
            formatted_jobs = []
            for job in cached_jobs[:15]:  # Limit to 15 jobs
                formatted_job = {
                    "title": job.get("job_title", ""),
                    "company_name": job.get("employer_name", ""),
                    "url": job.get("job_apply_link", "") or job.get("job_google_link", ""),
                    "tags": job.get("tags", []),
                    "location": job.get("job_city", "") + ", " + job.get("job_state", "") if job.get("job_city") else job.get("job_country", ""),
                    "job_type": job.get("job_employment_type", ""),
                    "salary": job.get("job_salary", "") or "Not specified",
                    "description": job.get("job_description", "")[:500] + "..." if job.get("job_description") else "",
                    "match_percentage": job.get("match_percentage", 0.0)
                }
                formatted_jobs.append(formatted_job)
            
            print(f"[DEBUG] Loaded {len(formatted_jobs)} cached jobs as fallback.")
            return jsonify(formatted_jobs)
        else:
            return jsonify({"error": "No cached jobs available. Please try again later."}), 500
    except Exception as e:
        print(f"[ERROR] Failed to load cached jobs: {e}")
        return jsonify({"error": "Failed to load jobs. Please try again later."}), 500

def serialize_job(job):
    job = dict(job)
    # Convert _id to string
    if '_id' in job and isinstance(job['_id'], ObjectId):
        job['_id'] = str(job['_id'])
    # Convert datetime fields to string
    for key, value in job.items():
        if isinstance(value, datetime):
            job[key] = value.strftime('%Y-%m-%d')
    # Ensure tags is a list
    if 'tags' in job:
        if isinstance(job['tags'], str):
            job['tags'] = [tag.strip() for tag in job['tags'].split(',') if tag.strip()]
        elif not isinstance(job['tags'], list):
            job['tags'] = list(job['tags'])
    else:
        job['tags'] = []
    # Ensure company name is present
    if 'company' not in job:
        job['company'] = job.get('company_name', 'N/A')
    # Format salary
    salary = job.get('salary_range') or job.get('salary')
    if isinstance(salary, dict):
        min_sal = salary.get('min')
        max_sal = salary.get('max')
        if min_sal and max_sal:
            job['salary'] = f"₹{min_sal} - ₹{max_sal}"
        elif min_sal:
            job['salary'] = f"From ₹{min_sal}"
        elif max_sal:
            job['salary'] = f"Up to ₹{max_sal}"
        else:
            job['salary'] = 'Not specified'
    elif isinstance(salary, (int, float, str)):
        job['salary'] = str(salary)
    else:
        job['salary'] = 'Not specified'
    # Format posted_date
    if 'posted_date' in job and isinstance(job['posted_date'], str):
        job['posted_date'] = job['posted_date'][:10]
    elif 'posted_date' in job and isinstance(job['posted_date'], datetime):
        job['posted_date'] = job['posted_date'].strftime('%Y-%m-%d')
    else:
        job['posted_date'] = ''
    # Job type
    job['job_type'] = job.get('job_type', job.get('type', 'Full-time'))
    return job

@app.route('/jobs')
def get_all_jobs():
    jobs_from_db = db.jobs.find({'status': 'active'})
    jobs = [serialize_job(job) for job in jobs_from_db]
    # Get current user and their skills
    user = get_current_user()
    seeker_skills = []
    if user and user.get('parsed_resume_data'):
        seeker_skills = user['parsed_resume_data'].get('skills', [])
        if not seeker_skills:
            seeker_skills = user['parsed_resume_data'].get('data', {}).get('document', {}).get('skills', [])
    # Add match percent and matched_skills to each job
    for job in jobs:
        job_skills = job.get('tags', [])
        if seeker_skills and job_skills:
            matched_skills = [skill for skill in job_skills if skill.lower() in [s.lower() for s in seeker_skills]]
            match_count = len(matched_skills)
            match_percent = int((match_count / len(seeker_skills)) * 100) if seeker_skills else 0
            job['match_percent'] = match_percent
            job['matched_skills'] = matched_skills
        else:
            job['match_percent'] = 0
            job['matched_skills'] = []
    return jsonify(jobs)

@app.route('/platform-jobs')
def platform_jobs_page():
    # Fetch jobs using the same logic as /jobs
    jobs_from_db = db.jobs.find({'status': 'active'})
    jobs = [serialize_job(job) for job in jobs_from_db]
    user = get_current_user()
    seeker_skills = []
    if user and user.get('parsed_resume_data'):
        seeker_skills = user['parsed_resume_data'].get('skills', [])
        if not seeker_skills:
            seeker_skills = user['parsed_resume_data'].get('data', {}).get('document', {}).get('skills', [])
    for job in jobs:
        job_skills = job.get('tags', [])
        if seeker_skills and job_skills:
            matched_skills = [skill for skill in job_skills if skill.lower() in [s.lower() for s in seeker_skills]]
            match_count = len(matched_skills)
            match_percent = int((match_count / len(seeker_skills)) * 100) if seeker_skills else 0
            job['match_percent'] = match_percent
            job['matched_skills'] = matched_skills
        else:
            job['match_percent'] = 0
            job['matched_skills'] = []
    return render_template('platform-jobs.html', jobs=jobs)

# Add a test endpoint to check if API key is loaded
@app.route('/test-api-key')
def test_api_key():
    """Test endpoint to verify RapidAPI configuration"""
    try:
        api_key = os.getenv("JSEARCH_API_KEY")
        if not api_key:
            return jsonify({
                "status": "error",
                "message": "JSEARCH_API_KEY not found in environment variables",
                "api_key_configured": False
            }), 500
        
        # Test the API with a simple request
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        params = {
            "query": "python",
            "page": "1",
            "num_pages": "1"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "API key is valid and working",
                "api_key_configured": True,
                "api_response_status": response.status_code
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"API returned status code {response.status_code}",
                "api_key_configured": True,
                "api_response_status": response.status_code,
                "api_response": response.text[:200]
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error testing API: {str(e)}",
            "api_key_configured": bool(os.getenv("JSEARCH_API_KEY"))
        }), 500

@app.route('/job-fetching-status')
def job_fetching_status():
    """Check the status of the job fetching system"""
    try:
        status = {
            "api_key_configured": bool(os.getenv("JSEARCH_API_KEY")),
            "cached_jobs_available": False,
            "cached_jobs_count": 0,
            "parsed_resume_available": False,
            "parsed_resume_skills_count": 0
        }
        
        # Check if cached jobs are available
        jobs_json_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'jobs.json')
        if os.path.exists(jobs_json_path):
            try:
                with open(jobs_json_path, 'r', encoding='utf-8') as f:
                    cached_jobs = json.load(f)
                status["cached_jobs_available"] = True
                status["cached_jobs_count"] = len(cached_jobs)
            except Exception as e:
                status["cached_jobs_error"] = str(e)
        
        # Check if parsed resume is available
        parsed_resume_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'parsed_resume.json')
        if os.path.exists(parsed_resume_path):
            try:
                with open(parsed_resume_path, 'r', encoding='utf-8') as f:
                    parsed_resume_data = json.load(f)
                resume_skills = parsed_resume_data.get('skills', [])
                status["parsed_resume_available"] = True
                status["parsed_resume_skills_count"] = len(resume_skills)
            except Exception as e:
                status["parsed_resume_error"] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error checking job fetching status: {str(e)}"
        }), 500

# Generate Resume (POST)
@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        template_name = data.get('template', 'professional').lower()
        if template_name not in ['professional', 'modern', 'minimalist']:
            return jsonify({"error": "Invalid template name"}), 400

        pdf_buffer = generate_pdf_resume(data, template_name)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name='resume.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating resume: {str(e)}")
        return jsonify({"error": str(e)}), 500

def generate_pdf_resume(data, template_name):
    template = get_template_styles(template_name)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=template['page_size'],
        rightMargin=template['margins']['right'],
        leftMargin=template['margins']['left'],
        topMargin=template['margins']['top'],
        bottomMargin=template['margins']['bottom']
    )
    styles = template['styles']
    story = []

    if template_name == 'minimalist' and template['layout'].get('header_bar'):
        story.append(Paragraph(data.get('name', 'Name'), styles['HeaderBar']))
    else:
        story.append(Paragraph(data.get('name', 'Name'), styles['Header']))

    contact_info = f"{data.get('email', '')} | {data.get('phone', '')}"
    story.append(Paragraph(contact_info, styles['Contact']))

    if template['layout'].get('header_border'):
        story.append(Spacer(1, 0.1 * inch))
        story.append(Table(
            [['']],
            colWidths=[doc.width],
            rowHeights=[2],
            style=TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.black)])
        ))

    story.append(Spacer(1, template['layout']['section_spacing']))

    if template_name == 'modern' and template['layout'].get('sidebar'):
        main_content = []
        main_content.append(Paragraph('Professional Summary', styles['SubHeader']))
        main_content.append(Paragraph(data.get('summary', ''), styles['Normal']))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        main_content.append(Paragraph('Experience', styles['SubHeader']))
        for exp in data.get('experience', []):
            main_content.append(Paragraph(exp.get('jobTitle', ''), styles['NormalBold']))
            main_content.append(Paragraph(f"{exp.get('company', '')} | {exp.get('duration', '')}", styles['NormalItalic']))
            responsibilities = exp.get('responsibilities', '').split('\n')
            resp_list = [ListItem(Paragraph(resp.replace('•', '').strip(), styles['Normal'])) for resp in responsibilities if resp.strip()]
            main_content.append(ListFlowable(resp_list, bulletType='bullet', start='•'))
            main_content.append(Spacer(1, 0.1 * inch))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        main_content.append(Paragraph('Education', styles['SubHeader']))
        for edu in data.get('education', []):
            main_content.append(Paragraph(edu.get('degree', ''), styles['NormalBold']))
            main_content.append(Paragraph(f"{edu.get('institution', '')} | {edu.get('duration', '')}", styles['NormalItalic']))
            main_content.append(Paragraph(edu.get('description', ''), styles['Normal']))
            main_content.append(Spacer(1, 0.1 * inch))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        main_content.append(Paragraph('Projects', styles['SubHeader']))
        for proj in data.get('projects', []):
            main_content.append(Paragraph(proj.get('name', ''), styles['NormalBold']))
            main_content.append(Paragraph(proj.get('description', ''), styles['Normal']))
            main_content.append(Spacer(1, 0.1 * inch))

        sidebar_content = []
        sidebar_content.append(Paragraph('Skills', styles['Sidebar']))
        skills = data.get('skills', [])
        skill_list = [ListItem(Paragraph(skill['name'], styles['Sidebar'])) for skill in skills]
        sidebar_content.append(ListFlowable(skill_list, bulletType='bullet', start='•'))

        table_data = [[sidebar_content, main_content]]
        table = Table(
            table_data,
            colWidths=[template['layout']['sidebar_width'], doc.width - template['layout']['sidebar_width']],
            style=TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2c3e50'))
            ])
        )
        story.append(table)
    else:
        story.append(Paragraph('Professional Summary', styles['SubHeader']))
        story.append(Paragraph(data.get('summary', ''), styles['Normal']))
        story.append(Spacer(1, template['layout']['section_spacing']))

        story.append(Paragraph('Skills', styles['SubHeader']))
        skills = data.get('skills', [])
        skill_list = [ListItem(Paragraph(skill['name'], styles['Normal'])) for skill in skills]
        story.append(ListFlowable(skill_list, bulletType='bullet', start='•'))
        story.append(Spacer(1, template['layout']['section_spacing']))

        story.append(Paragraph('Experience', styles['SubHeader']))
        for exp in data.get('experience', []):
            story.append(Paragraph(exp.get('jobTitle', ''), styles['NormalBold']))
            story.append(Paragraph(f"{exp.get('company', '')} | {exp.get('duration', '')}", styles['NormalItalic']))
            responsibilities = exp.get('responsibilities', '').split('\n')
            resp_list = [ListItem(Paragraph(resp.replace('•', '').strip(), styles['Normal'])) for resp in responsibilities if resp.strip()]
            story.append(ListFlowable(resp_list, bulletType='bullet', start='•'))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, template['layout']['section_spacing']))

        story.append(Paragraph('Education', styles['SubHeader']))
        for edu in data.get('education', []):
            story.append(Paragraph(edu.get('degree', ''), styles['NormalBold']))
            story.append(Paragraph(f"{edu.get('institution', '')} | {edu.get('duration', '')}", styles['NormalItalic']))
            story.append(Paragraph(edu.get('description', ''), styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, template['layout']['section_spacing']))

        story.append(Paragraph('Projects', styles['SubHeader']))
        for proj in data.get('projects', []):
            story.append(Paragraph(proj.get('name', ''), styles['NormalBold']))
            story.append(Paragraph(proj.get('description', ''), styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer

@app.route('/delete-resume', methods=['POST'])
@login_required
def delete_resume():
    try:
        user = get_current_user()
        if not user:
            logger.error("Authentication required for resume deletion.")
            return jsonify({"error": "Authentication required"}), 401

        from Backend.database import resumes
        
        # Find the user's active resume
        resume = resumes.find_one({
            'user_id': user['id'],
            'status': 'active'
        })
        
        if not resume:
            logger.warning(f"No active resume found for user {user['id']} to delete.")
            return jsonify({"error": "No active resume found"}), 404
        
        # Get the file path from the database document
        file_path_to_delete = resume.get('file_path')
        
        # Delete the physical file if path exists
        if file_path_to_delete:
            try:
                if os.path.exists(file_path_to_delete):
                    os.remove(file_path_to_delete)
                    logger.info(f"Physical resume file deleted: {file_path_to_delete}")
                else:
                    logger.warning(f"Physical resume file not found at expected path: {file_path_to_delete}")
            except Exception as e:
                logger.error(f"Error deleting physical file {file_path_to_delete}: {str(e)}")
                # Continue to update database status even if physical file deletion fails
        else:
            logger.warning(f"No file_path found in database for resume {resume['_id']} of user {user['id']}.")

        # Update resume status to 'deleted' in database
        resumes.update_one(
            {'_id': resume['_id']},
            {'$set': {'status': 'deleted'}}
        )
        logger.info(f"Resume status updated to 'deleted' for resume ID: {resume['_id']}")
        
        # Clear parsed_resume.json (this is already handled by upload, but kept for explicit cleanup)
        parsed_resume_path = os.path.join(BASE_DIR, 'parsed_resume.json')
        if os.path.exists(parsed_resume_path):
            try:
                os.remove(parsed_resume_path)
                logger.info("Temporary parsed_resume.json cleared during deletion.")
            except Exception as e:
                logger.error(f"Error clearing parsed_resume.json during deletion: {str(e)}")
        
        return jsonify({"message": "Resume deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Unexpected error deleting resume: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get-resume-status', methods=['GET'])
def get_resume_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'has_resume': False, 'error': 'User not logged in'}), 401

    user_resume = db.resumes.find_one({'user_id': user_id})
    if user_resume and user_resume.get('status') != 'deleted':
        return jsonify({
            'has_resume': True,
            'filename': user_resume.get('original_filename', 'N/A'),
            'last_updated': user_resume.get('upload_date', 'N/A').isoformat() if user_resume.get('upload_date') else 'N/A'
        })
    else:
        return jsonify({'has_resume': False})

@app.route('/get-resume-templates')
def get_resume_templates():
    # In a real application, you might want to dynamically get these or cache them.
    # For now, we'll hardcode based on the available templates in resume_templates.py
    templates = [
        {'id': 'professional', 'name': 'Professional', 'description': 'A clean and traditional resume template.'},
        {'id': 'modern', 'name': 'Modern', 'description': 'A modern template with a sidebar.'},
        {'id': 'minimalist', 'name': 'Minimalist', 'description': 'A simple and elegant design.'},
    ]
    return jsonify(templates)

@app.route('/apply-job', methods=['POST'])
@login_required
def apply_for_job():
    try:
        user = get_current_user()
        if not user or user.get('role') != 'seeker':
            logger.warning(f"Unauthorized application attempt by user {user.get('email')} with role {user.get('role') if user else 'None'}.")
            return jsonify({"error": "Unauthorized"}), 403

        job_id = str(request.json.get('job_id'))
        if not job_id:
            logger.warning("Job ID not provided in application request.")
            return jsonify({"error": "Job ID is required"}), 400

        from Backend.database import jobs, resumes, applications

        job = jobs.find_one({'_id': ObjectId(job_id)})
        if not job:
            logger.warning(f"Job not found for ID: {job_id}.")
            return jsonify({"error": "Job not found"}), 404

        seeker_id = str(user['id'])

        # Check if seeker has already applied for this job
        existing_application = applications.find_one({
            'seeker_id': seeker_id,
            'job_id': job_id
        })

        if existing_application:
            logger.info(f"Seeker {seeker_id} already applied for job {job_id}.")
            return jsonify({"message": "Already applied for this job"}), 200

        seeker_resume = resumes.find_one({'user_id': seeker_id, 'status': 'active'})
        if not seeker_resume:
            logger.warning(f"No active resume found for seeker {seeker_id} during job application for job {job_id}.")
            return jsonify({"error": "No active resume found. Please upload your resume first."}), 400

        resume_snapshot = seeker_resume.get('parsed_data', {})
        application_data = {
            'seeker_id': seeker_id,
            'job_id': job_id,
            'job_title': job.get('title'),
            'company_name': job.get('company'),
            'application_date': datetime.utcnow(),
            'status': 'Applied',
            'resume_snapshot': resume_snapshot,
            'seeker_name': user.get('name', 'Job Seeker'),
            'seeker_email': user.get('email'),
            'seeker_phone': user.get('phone'),
            'seeker_location': user.get('location')
        }

        applications.insert_one(application_data)
        jobs.update_one({'_id': ObjectId(job_id)}, {'$inc': {'applications_count': 1}})
        logger.info(f"Seeker {seeker_id} successfully applied for job {job_id}. Application saved.")
        return jsonify({"message": "Application submitted successfully"}), 200

    except Exception as e:
        logger.error(f"Error applying for job: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to submit application"}), 500

@app.route('/view-candidate/<string:application_id>')
@login_required
def view_candidate_details(application_id):
    user = get_current_user()
    if not user or user.get('role') != 'hr':
        flash('You do not have permission to view candidate details.', 'danger')
        return redirect(url_for('dashboard'))

    from Backend.database import applications, jobs

    try:
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            flash('Application not found.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))
        
        # Ensure the HR user has permission to view this application (i.e., they posted the job)
        job = jobs.find_one({'_id': ObjectId(application.get('job_id'))})
        if not job or job.get('hr_id') != user['id']:
            flash('You do not have permission to view this application.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))

        # Prepare data for template
        candidate_data = {
            'application_id': str(application['_id']),
            'seeker_name': application.get('seeker_name', 'N/A'),
            'seeker_email': application.get('seeker_email', 'N/A'),
            'seeker_phone': application.get('seeker_phone', 'N/A'),
            'seeker_location': application.get('seeker_location', 'N/A'),
            'job_title': application.get('job_title', 'N/A'),
            'company_name': application.get('company_name', 'N/A'),
            'application_date': application['application_date'].strftime('%Y-%m-%d %H:%M UTC') if application.get('application_date') else 'N/A',
            'status': application.get('status', 'Pending'),
            'match_score': application.get('match_score', 'N/A'),
            'resume_data': application.get('resume_snapshot', {}).get('data', {}).get('document', {}) # Extract the nested document
        }

        return render_template('candidate_details.html', candidate=candidate_data, current_year=datetime.now().year)

    except Exception as e:
        logger.error(f"Error viewing candidate details for application ID {application_id}: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('hr_dashboard_alt'))

def match_jobs_with_resume(resume_data, jobs):
    """Match jobs with resume using C++ skill matcher implementation"""
    try:
        # Convert resume data and jobs to JSON strings
        resume_json = json.dumps(resume_data)
        jobs_json = json.dumps(jobs)
        
        # Call C++ function through ctypes
        import ctypes
        from ctypes import cdll
        
        # Load the shared library
        lib = cdll.LoadLibrary('./cpp_modules/skill_matcher.so')
        
        # Set up function signature
        lib.processJobMatches.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        lib.processJobMatches.restype = ctypes.c_char_p
        
        # Call the function
        result = lib.processJobMatches(
            resume_json.encode('utf-8'),
            jobs_json.encode('utf-8')
        )
        
        if result:
            # Convert result back to Python object
            matches = json.loads(result.decode('utf-8'))
            return matches
        return []
    except Exception as e:
        logger.error(f"Error in job matching: {str(e)}")
        return []

def get_seeker_matches(user_id):
    """Get stored matches for a seeker from matches collection"""
    try:
        # Get matches from matches collection
        stored_matches = list(db.matches.find(
            {'resume_id': str(user_id)},
            {'_id': 0}  # Exclude _id field
        ).sort('match_score', -1).limit(10))
        
        if stored_matches:
            return stored_matches
            
        # If no stored matches, calculate new ones
        return update_seeker_matches(user_id)
    except Exception as e:
        logger.error(f"Error getting seeker matches: {str(e)}")
        return []

def update_seeker_matches(user_id):
    """Update job matches for a seeker and store in matches collection"""
    try:
        # Get user's resume data
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user or 'parsed_resume_data' not in user:
            return []
        # Get all active jobs
        active_jobs = list(db.jobs.find({'status': 'active'}))
        # Debug output for troubleshooting
        resume_skills = user['parsed_resume_data'].get('skills', [])
        print(f"[DEBUG] Resume skills for user {user_id}: {resume_skills}")
        for job in active_jobs:
            print(f"[DEBUG] Job '{job.get('title')}' tags: {job.get('tags')}")
        # Print the actual JSON sent to the matcher
        print("[DEBUG] Resume JSON sent to matcher:")
        print(json.dumps(user['parsed_resume_data'], indent=2))
        print("[DEBUG] Jobs JSON sent to matcher:")
        print(json.dumps(active_jobs, indent=2, default=str))
        # Convert ObjectId to string for all jobs
        active_jobs = [serialize_job(job) for job in active_jobs]
        # Match jobs with resume
        matches = match_jobs_with_resume(user['parsed_resume_data'], active_jobs)
        print(f"[DEBUG] Matches returned: {matches}")
        # Store matches in matches collection
        for match in matches:
            db.matches.update_one(
                {
                    'job_id': match['job_id'],
                    'resume_id': str(user['_id'])
                },
                {
                    '$set': {
                        'match_score': match['match_score'],
                        'title': match['title'],
                        'company': match['company'],
                        'location': match['location'],
                        'type': match['type'],
                        'skills': match['skills'],
                        'last_updated': datetime.now()
                    }
                },
                upsert=True
            )
        # Update user's recent matches
        users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'recent_matches': matches,
                    'match_score': matches[0]['match_score'] if matches else 0
                }
            }
        )
        return matches
    except Exception as e:
        logger.error(f"Error updating seeker matches: {str(e)}")
        return []

@app.route('/hr/post-job', methods=['POST'])
@login_required
@role_required('hr')
def post_job_api():
    try:
        job_data = request.json
        job_data['status'] = 'active'
        job_data['posted_by'] = session['user_id']
        job_data['posted_date'] = datetime.now()
        job_data['hr_id'] = session['user_id']  # Ensure hr_id is set for HR jobs

        # Extract skills from requirements and create tags
        if 'requirements' in job_data:
            req = job_data['requirements']
            tags = [tag.strip() for tag in req.split(',') if tag.strip()]
            job_data['tags'] = tags
            print(f"[DEBUG] Extracted tags from requirements: {tags}")
        elif 'tags' not in job_data:
            job_data['tags'] = []
            print("[DEBUG] No requirements provided, creating empty tags list")

        if not isinstance(job_data.get('tags'), list):
            job_data['tags'] = []

        result = db.jobs.insert_one(job_data)
        print(f"[DEBUG] Job posted successfully with ID: {result.inserted_id}")
        print(f"[DEBUG] Job tags: {job_data.get('tags')}")

        all_seekers = users.find({'role': 'seeker'})
        for seeker in all_seekers:
            update_seeker_matches(str(seeker['_id']))

        return jsonify({'success': True, 'job_id': str(result.inserted_id)})
    except Exception as e:
        logger.error(f"Error posting job: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update-application-status', methods=['POST'])
@login_required
def update_application_status():
    """Update application status (Accept/Decline) by HR"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'hr':
            flash('You do not have permission to update application status.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))

        application_id = request.form.get('application_id')
        new_status = request.form.get('status')
        
        if not application_id or not new_status:
            flash('Missing required parameters.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))

        from Backend.database import applications, jobs

        # Find the application
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            flash('Application not found.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))

        # Verify the HR user posted the job this application is for
        job = jobs.find_one({'_id': ObjectId(application.get('job_id'))})
        if not job or job.get('hr_id') != user['id']:
            flash('You do not have permission to update this application.', 'danger')
            return redirect(url_for('hr_dashboard_alt'))

        # Update the application status
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': new_status}}
        )

        if result.modified_count > 0:
            status_text = 'accepted' if new_status == 'Accepted' else 'rejected'
            flash(f'Application {status_text} successfully.', 'success')
        else:
            flash('No changes were made to the application.', 'info')

        return redirect(url_for('hr_dashboard_alt'))

    except Exception as e:
        logger.error(f"Error updating application status: {str(e)}", exc_info=True)
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('hr_dashboard_alt'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
