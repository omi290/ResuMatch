from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
from Backend.database import users, resumes
from bson.objectid import ObjectId

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)

def register_user(email, password, role, company_name=None, name=None):
    """Register a new user"""
    try:
        # Check if user already exists
        if users.find_one({'email': email}):
            return False, 'Email already registered'
        
        # Create new user
        user = {
            'email': email,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.utcnow()
        }

        if name:
            user['name'] = name

        if role == 'hr' and company_name:
            user['company_name'] = company_name
        
        users.insert_one(user)
        return True, 'User registered successfully'
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    """Authenticate a user"""
    try:
        user = users.find_one({'email': email})
        if not user:
            return False, 'User not found'
        
        if not check_password_hash(user['password'], password):
            return False, 'Invalid password'
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'email': user['email'],
            'role': user['role'],
            'name': user.get('name'),
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return True, {
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'role': user['role'],
                'name': user.get('name')
            }
        }
    except Exception as e:
        return False, str(e)

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, 'Token has expired'
    except jwt.InvalidTokenError:
        return False, 'Invalid token'

def get_current_user():
    """Get current user from session"""
    print(f"DEBUG: Checking session for user_id. Session: {session.keys()}")
    if 'user_id' not in session:
        print("DEBUG: user_id not in session.")
        return None
    
    user_id_str = session['user_id']
    print(f"DEBUG: user_id found in session as string: {user_id_str}")
    
    try:
        user_id_obj = ObjectId(user_id_str)
    except Exception as e:
        print(f"DEBUG: Error converting user_id to ObjectId: {e}")
        return None

    user = users.find_one({'_id': user_id_obj})
    if not user:
        print(f"DEBUG: User not found in DB for ObjectId: {user_id_obj}")
        return None
    
    print(f"DEBUG: User found in DB: {user.get('email')}, Role: {user.get('role')}, Name: {user.get('name')}")
    
    # Fetch parsed resume data from the 'resumes' collection
    user_resume = resumes.find_one({'user_id': user_id_str, 'status': 'active'})
    if user_resume:
        user['parsed_resume_data'] = user_resume.get('parsed_data', {})
        user['resume_uploaded'] = True
        user['resume_filename'] = user_resume.get('original_filename')
        user['resume_last_updated'] = user_resume.get('upload_date')
        print(f"DEBUG: Fetched resume data for user {user_id_str}: {user_resume.get('original_filename')}")
    else:
        user['parsed_resume_data'] = {}
        user['resume_uploaded'] = False
        user['resume_filename'] = None
        user['resume_last_updated'] = None
        print(f"DEBUG: No active resume found for user {user_id_str}")

    # Ensure 'name' is always present, default to 'None' if not in DB
    user_name = user.get('name')
    if user_name is None:
        if user.get('role') == 'hr':
            user_name = "HR Professional"
        else:
            user_name = "Job Seeker"

    # Debug print the parsed_resume_data before returning the user object
    print(f"DEBUG: Parsed resume data attached to user object: {user.get('parsed_resume_data')}")

    return {
        'id': str(user['_id']),
        'email': user['email'],
        'role': user['role'],
        'name': user_name,
        'company_name': user.get('company_name', ''),
        'phone': user.get('phone', ''),
        'location': user.get('location', ''),
        'profile_pic_url': user.get('profile_pic_url', None),
        'education': user.get('education', []),
        'skills': user.get('skills', []),
        'experience': user.get('experience', []),
        'resume_uploaded': user.get('resume_uploaded', False),
        'resume_filename': user.get('resume_filename', None),
        'resume_last_updated': user.get('resume_last_updated', None),
        'parsed_resume_data': user.get('parsed_resume_data', {}) if user.get('parsed_resume_data') is not None else {}
    }

def require_auth(f):
    """Decorator to require authentication"""
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            print("DEBUG: Authentication failed in require_auth, user is None")
            return jsonify({'error': 'Authentication required'}), 401
        print(f"DEBUG: User authenticated: {user}")
        # Set the user object in the request
        request.user = user
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                print("DEBUG: Authentication failed in require_role, user is None")
                return jsonify({'error': 'Authentication required'}), 401
            if user['role'] != role:
                print(f"DEBUG: User {user.get('email')} has role {user.get('role')}, but {role} is required")
                return jsonify({'error': 'Insufficient permissions'}), 403
            print(f"DEBUG: User {user.get('email')} has required role {role}")
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated
    return decorator 