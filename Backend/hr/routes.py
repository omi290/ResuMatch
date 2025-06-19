from flask import Blueprint, request, jsonify, render_template
from .job_poster import post_job, get_jobs, update_job, delete_job
from .match_viewer import find_matches, get_matches, update_match_status, find_top_matches_for_job
from Backend.auth.auth_handler import require_auth, require_role

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/post-job', methods=['POST'])
@require_auth
@require_role('hr')
def handle_job_posting():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Get user from request object
        user = request.user
        if not user:
            return jsonify({'error': 'User not found'}), 401

        success, result = post_job(data, user['id'])
        
        if success:
            return jsonify(result), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        print(f"Error posting job: {str(e)}")
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/jobs', methods=['GET'])
@require_auth
@require_role('hr')
def handle_get_jobs():
    try:
        user_id = request.user['id']
        status = request.args.get('status', 'active')
        
        success, result = get_jobs(user_id, status)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>', methods=['PUT'])
@require_auth
@require_role('hr')
def handle_update_job(job_id):
    try:
        data = request.get_json()
        user_id = request.user['id']
        
        success, result = update_job(job_id, data, user_id)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>', methods=['DELETE'])
@require_auth
@require_role('hr')
def handle_delete_job(job_id):
    try:
        user_id = request.user['id']
        
        success, result = delete_job(job_id, user_id)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>/matches', methods=['GET'])
@require_auth
@require_role('hr')
def handle_get_matches(job_id):
    try:
        status = request.args.get('status')
        
        success, result = get_matches(job_id=job_id, status=status)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>/find-matches', methods=['POST'])
@require_auth
@require_role('hr')
def handle_find_matches(job_id):
    try:
        success, result = find_matches(job_id)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/match/<match_id>', methods=['PUT'])
@require_auth
@require_role('hr')
def handle_update_match(match_id):
    try:
        data = request.get_json()
        status = data.get('status')
        user_id = request.user['id']
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
            
        success, result = update_match_status(match_id, status, user_id)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>/top-matches', methods=['GET'])
@require_auth
@require_role('hr')
def handle_top_matches(job_id):
    try:
        success, result = find_top_matches_for_job(job_id)
        if success:
            return jsonify(result), 200
        else:
            return jsonify({'error': result}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hr_bp.route('/job/<job_id>/top-matches-view', methods=['GET'])
@require_auth
@require_role('hr')
def top_matches_view(job_id):
    return render_template('hr_top_matches.html', job_id=job_id) 