# app.py - Improved version with resume generation and template support
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pathlib
from resume_parser import parse_resume_with_extracta
from templates.resume_templates import get_template_styles
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get current working directory
BASE_DIR = pathlib.Path(__file__).parent.absolute()
FRONTEND_DIR = BASE_DIR.parent / 'Frontend'
UPLOAD_FOLDER = BASE_DIR / 'Uploads'

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

        # Save parsed data to parsed_resume.json (overwrite previous data)
        parsed_resume_path = os.path.join(BASE_DIR, 'parsed_resume.json')
        with open(parsed_resume_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)

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

@app.route('/external-jobs')
def external_jobs():
    import requests
    try:
        query = request.args.get("q", "python")
        print(f"[DEBUG] Fetching jobs for: {query}")
        res = requests.get(
            "https://remotive.io/api/remote-jobs",
            params={"search": query},
            verify=False  # Disable SSL cert verification temporarily
        )
        res.raise_for_status()
        jobs = res.json().get("jobs", [])
        return jsonify(jobs[:10])
    except Exception as e:
        print(f"[ERROR] Failed to fetch jobs: {e}")
        return jsonify({"error": str(e)}), 500



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

        # Generate PDF
        pdf_buffer = generate_pdf_resume(data, template_name)
        pdf_buffer.seek(0)

        # Send the PDF as a downloadable file
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
    """Generate a PDF resume using reportlab with the specified template"""
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

    # Header: Name
    if template_name == 'minimalist' and template['layout'].get('header_bar'):
        story.append(Paragraph(data.get('name', 'Name'), styles['HeaderBar']))
    else:
        story.append(Paragraph(data.get('name', 'Name'), styles['Header']))
    
    # Contact Info
    contact_info = f"{data.get('email', '')} | {data.get('phone', '')}"
    story.append(Paragraph(contact_info, styles['Contact']))
    
    # Header Border (Professional)
    if template['layout'].get('header_border'):
        story.append(Spacer(1, 0.1 * inch))
        story.append(Table(
            [['']],
            colWidths=[doc.width],
            rowHeights=[2],
            style=TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.black)])
        ))
    
    story.append(Spacer(1, template['layout']['section_spacing']))

    # Sidebar Layout for Modern Template
    if template_name == 'modern' and template['layout'].get('sidebar'):
        # Create two-column layout: sidebar (skills) and main content
        main_content = []
        
        # Professional Summary
        main_content.append(Paragraph('Professional Summary', styles['SubHeader']))
        main_content.append(Paragraph(data.get('summary', ''), styles['Normal']))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        # Experience
        main_content.append(Paragraph('Experience', styles['SubHeader']))
        for exp in data.get('experience', []):
            main_content.append(Paragraph(exp.get('jobTitle', ''), styles['NormalBold']))
            main_content.append(Paragraph(f"{exp.get('company', '')} | {exp.get('duration', '')}", styles['NormalItalic']))
            responsibilities = exp.get('responsibilities', '').split('\n')
            resp_list = [ListItem(Paragraph(resp.replace('•', '').strip(), styles['Normal'])) for resp in responsibilities if resp.strip()]
            main_content.append(ListFlowable(resp_list, bulletType='bullet', start='•'))
            main_content.append(Spacer(1, 0.1 * inch))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        # Education
        main_content.append(Paragraph('Education', styles['SubHeader']))
        for edu in data.get('education', []):
            main_content.append(Paragraph(edu.get('degree', ''), styles['NormalBold']))
            main_content.append(Paragraph(f"{edu.get('institution', '')} | {edu.get('duration', '')}", styles['NormalItalic']))
            main_content.append(Paragraph(edu.get('description', ''), styles['Normal']))
            main_content.append(Spacer(1, 0.1 * inch))
        main_content.append(Spacer(1, template['layout']['section_spacing']))

        # Projects
        main_content.append(Paragraph('Projects', styles['SubHeader']))
        for proj in data.get('projects', []):
            main_content.append(Paragraph(proj.get('name', ''), styles['NormalBold']))
            main_content.append(Paragraph(proj.get('description', ''), styles['Normal']))
            main_content.append(Spacer(1, 0.1 * inch))

        # Sidebar: Skills
        sidebar_content = []
        sidebar_content.append(Paragraph('Skills', styles['Sidebar']))
        skills = data.get('skills', [])
        skill_list = [ListItem(Paragraph(skill['name'], styles['Sidebar'])) for skill in skills]
        sidebar_content.append(ListFlowable(skill_list, bulletType='bullet', start='•'))

        # Combine sidebar and main content in a table
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
        # Professional Summary
        story.append(Paragraph('Professional Summary', styles['SubHeader']))
        story.append(Paragraph(data.get('summary', ''), styles['Normal']))
        story.append(Spacer(1, template['layout']['section_spacing']))

        # Skills
        story.append(Paragraph('Skills', styles['SubHeader']))
        skills = data.get('skills', [])
        skill_list = [ListItem(Paragraph(skill['name'], styles['Normal'])) for skill in skills]
        story.append(ListFlowable(skill_list, bulletType='bullet', start='•'))
        story.append(Spacer(1, template['layout']['section_spacing']))

        # Experience
        story.append(Paragraph('Experience', styles['SubHeader']))
        for exp in data.get('experience', []):
            story.append(Paragraph(exp.get('jobTitle', ''), styles['NormalBold']))
            story.append(Paragraph(f"{exp.get('company', '')} | {exp.get('duration', '')}", styles['NormalItalic']))
            responsibilities = exp.get('responsibilities', '').split('\n')
            resp_list = [ListItem(Paragraph(resp.replace('•', '').strip(), styles['Normal'])) for resp in responsibilities if resp.strip()]
            story.append(ListFlowable(resp_list, bulletType='bullet', start='•'))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, template['layout']['section_spacing']))

        # Education
        story.append(Paragraph('Education', styles['SubHeader']))
        for edu in data.get('education', []):
            story.append(Paragraph(edu.get('degree', ''), styles['NormalBold']))
            story.append(Paragraph(f"{edu.get('institution', '')} | {edu.get('duration', '')}", styles['NormalItalic']))
            story.append(Paragraph(edu.get('description', ''), styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, template['layout']['section_spacing']))

        # Projects
        story.append(Paragraph('Projects', styles['SubHeader']))
        for proj in data.get('projects', []):
            story.append(Paragraph(proj.get('name', ''), styles['NormalBold']))
            story.append(Paragraph(proj.get('description', ''), styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)