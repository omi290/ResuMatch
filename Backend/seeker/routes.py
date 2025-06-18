from flask import Blueprint, request, jsonify
from .resume_handler import upload_resume, get_resume, update_resume, delete_resume
from .job_applicant import apply_job, get_applications, withdraw_application
from .match_viewer import get_matches, update_match_status
from Backend.auth.auth_handler import require_auth, require_role
from .dashboard import get_overview_recommendations

seeker_bp = Blueprint('seeker', __name__)

# Resume upload
@seeker_bp.route('/resume', methods=['POST'])
@require_auth
@require_role('seeker')
def handle_upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    user_id = request.user['id']
    success, result = upload_resume(file, user_id)
    if success:
        return jsonify(result), 201
    return jsonify({'error': result}), 400

@seeker_bp.route('/overview', methods=['GET'])
@require_auth
@require_role('seeker')
def handle_get_overview():
    user_id = request.user['id']
    success, result = get_overview_recommendations(user_id)
    if success:
        return jsonify(result), 200
    return jsonify({'error': result}), 400

# Get all resumes or a specific resume
@seeker_bp.route('/resume', methods=['GET'])
@require_auth
@require_role('seeker')
def handle_get_resumes():
    user_id = request.user['id']
    resume_id = request.args.get('resume_id')
    success, result = get_resume(user_id, resume_id)
    if success:
        return jsonify(result), 200
    return jsonify({'error': result}), 404

# Update a resume
@seeker_bp.route('/resume/<resume_id>', methods=['PUT'])
@require_auth
@require_role('seeker')
def handle_update_resume(resume_id):
    user_id = request.user['id']
    data = request.get_json()
    success, result = update_resume(resume_id, user_id, data)
    if success:
        return jsonify({'message': result}), 200
    return jsonify({'error': result}), 400

# Delete a resume
@seeker_bp.route('/resume/<resume_id>', methods=['DELETE'])
@require_auth
@require_role('seeker')
def handle_delete_resume(resume_id):
    user_id = request.user['id']
    success, result = delete_resume(resume_id, user_id)
    if success:
        return jsonify({'message': result}), 200
    return jsonify({'error': result}), 400

# Apply for a job
@seeker_bp.route('/apply', methods=['POST'])
@require_auth
@require_role('seeker')
def handle_apply_job():
    user_id = request.user['id']
    data = request.get_json()
    job_id = data.get('job_id')
    resume_id = data.get('resume_id')
    if not job_id or not resume_id:
        return jsonify({'error': 'job_id and resume_id are required'}), 400
    success, result = apply_job(job_id, user_id, resume_id)
    if success:
        return jsonify(result), 201
    return jsonify({'error': result}), 400

# Get all applications
@seeker_bp.route('/applications', methods=['GET'])
@require_auth
@require_role('seeker')
def handle_get_applications():
    user_id = request.user['id']
    status = request.args.get('status')
    success, result = get_applications(user_id, status)
    if success:
        return jsonify(result), 200
    return jsonify({'error': result}), 404

# Withdraw an application
@seeker_bp.route('/application/<application_id>', methods=['DELETE'])
@require_auth
@require_role('seeker')
def handle_withdraw_application(application_id):
    user_id = request.user['id']
    success, result = withdraw_application(application_id, user_id)
    if success:
        return jsonify({'message': result}), 200
    return jsonify({'error': result}), 400

# Get matches
@seeker_bp.route('/matches', methods=['GET'])
@require_auth
@require_role('seeker')
def handle_get_matches():
    user_id = request.user['id']
    status = request.args.get('status')
    success, result = get_matches(user_id, status)
    if success:
        return jsonify(result), 200
    return jsonify({'error': result}), 404

# Update match status
@seeker_bp.route('/match/<match_id>', methods=['PUT'])
@require_auth
@require_role('seeker')
def handle_update_match_status(match_id):
    user_id = request.user['id']
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({'error': 'status is required'}), 400
    success, result = update_match_status(match_id, user_id, status)
    if success:
        return jsonify({'message': result}), 200
    return jsonify({'error': result}), 400 