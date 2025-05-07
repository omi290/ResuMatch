# app.py - Improved version with additional section handling
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pathlib
from resume_parser import parse_resume_with_extracta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get current working directory
BASE_DIR = pathlib.Path(__file__).parent.absolute()
FRONTEND_DIR = BASE_DIR.parent / 'Frontend'
UPLOAD_FOLDER = BASE_DIR / 'uploads'

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Serve static frontend HTML files
@app.route('/')
def home():
    return send_from_directory(str(FRONTEND_DIR), 'resume-upload-page.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(FRONTEND_DIR), filename)

# Upload & Parse Resume (POST)
@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            return jsonify({"error": "Invalid file type. Please upload PDF or DOCX"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        parsed_data = parse_resume_with_extracta(file_path)
        if not parsed_data:
            return jsonify({"error": "Parsing failed"}), 500

        # Format the response data to match what the frontend expects
        return format_response_data(parsed_data)

    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
        
        return jsonify(formatted_data)
    except Exception as e:
        print(f"Error formatting response data: {str(e)}")
        return jsonify(formatted_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)