from flask import Blueprint, request, jsonify, session
from .auth_handler import register_user, login_user
from Backend.database import users

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'seeker')  # Default to seeker if not specified
        company_name = data.get('company_name') if role == 'hr' else None
        name = data.get('name')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if role not in ['seeker', 'hr']:
            return jsonify({'error': 'Invalid role'}), 400

        if role == 'hr' and not company_name:
            return jsonify({'error': 'Company name is required for HR professionals'}), 400

        success, message = register_user(email, password, role, company_name, name)
        
        if success:
            return jsonify({'message': message}), 201
        else:
            return jsonify({'error': message}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        success, result = login_user(email, password)
        
        if success:
            # Store user info in session
            session['user_id'] = result['user']['id']
            session['user_role'] = result['user']['role']

            # Redirect based on role
            if result['user']['role'] == 'hr':
                return jsonify({
                    'message': 'Login successful',
                    'token': result['token'],
                    'user': result['user'],
                    'redirect': '/hr-dashboard'
                }), 200
            else:
                return jsonify({
                    'message': 'Login successful',
                    'token': result['token'],
                    'user': result['user'],
                    'redirect': '/dashboard'
                }), 200
        else:
            return jsonify({'error': result}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    try:
        if 'user_id' in session:
            user = users.find_one({'_id': session['user_id']})
            if user:
                return jsonify({
                    'is_authenticated': True,
                    'user': {
                        'id': str(user['_id']),
                        'email': user['email'],
                        'role': user['role']
                    }
                }), 200
        return jsonify({'is_authenticated': False}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
