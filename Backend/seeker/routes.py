from flask import Blueprint, jsonify, request
from Backend.auth.auth_handler import require_auth

seeker_bp = Blueprint('seeker', __name__)

@seeker_bp.route('/get-resume-templates', methods=['GET'])
def get_resume_templates():
    templates = [
        {
            'id': 'professional',
            'name': 'Professional',
            'image_url': '/static/images/resume_templates/professional.png'
        },
        {
            'id': 'modern',
            'name': 'Modern',
            'image_url': '/static/images/resume_templates/modern.png'
        },
        {
            'id': 'minimalist',
            'name': 'Minimalist',
            'image_url': '/static/images/resume_templates/minimalist.png'
        }
    ]
    return jsonify(templates)

@seeker_bp.route('/get-user-profile', methods=['GET'])
@require_auth
def get_user_profile():
    user = request.user
    if not user:
        return jsonify({'error': 'User not authenticated'}), 401

    profile_data = {
        'full_name': user.get('full_name', ''),
        'email': user.get('email', ''),
        'phone': user.get('phone', ''),
        'linkedin': user.get('linkedin', ''),
        'portfolio': user.get('portfolio', '')
    }
    return jsonify(profile_data)
