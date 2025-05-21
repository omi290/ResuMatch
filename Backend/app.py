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
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()

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
        print(f"[DEBUG] Fetching jobs for: {query}")
        
        # Get API key from environment
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            print("[ERROR] RAPIDAPI_KEY not found in environment variables")
            return jsonify({"error": "API key not configured"}), 500
        
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        # Split query into individual skills/keywords
        skills = query.split()
        all_jobs = []
        seen_job_ids = set()
        
        # Load parsed resume skills from JSON file
        parsed_resume_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'parsed_resume.json')
        with open(parsed_resume_path, 'r', encoding='utf-8') as f:
            parsed_resume_data = json.load(f)
        resume_skills = parsed_resume_data.get('skills', [])
        if not resume_skills:
            # Fallback to skills from query if parsed resume skills not found
            resume_skills = skills
        
        # Define a set of stopwords/prepositions to filter out from job skills
        stopwords = set([
            "in", "at", "on", "and", "or", "the", "a", "an", "to", "for", "with", "of", "by", "from",
            "is", "are", "was", "were", "be", "been", "has", "have", "had", "will", "would", "can",
            "could", "should", "may", "might", "must", "do", "does", "did", "but", "if", "else", "then",
            "when", "where", "how", "what", "which", "who", "whom", "this", "that", "these", "those",
            "as", "such", "not", "no", "yes", "all", "any", "some", "each", "every", "other", "more",
            "most", "many", "much", "few", "several", "one", "two", "first", "second", "new", "used"
        ])
        
        for skill in skills:
            params = {
                "query": skill,
                "page": "1",
                "num_pages": "1",
                "date_posted": "month"  # Get jobs from last month
            }
            if location:
                params["query"] = f"{skill} {location}"
            
            print(f"[DEBUG] Making request to: {url} with skill: {skill}")
            res = requests.get(url, headers=headers, params=params, timeout=10)
            
            if res.status_code != 200:
                print(f"[ERROR] API returned status code: {res.status_code} for skill: {skill}")
                print(f"[ERROR] Response: {res.text}")
                continue
            
            data = res.json()
            jobs = data.get("data", [])
            
            for job in jobs:
                job_id = job.get("job_id") or job.get("job_apply_link") or job.get("job_title")  # Use unique identifier
                if job_id and job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    
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
                    
                    # Write job tags to a temporary JSON file for matching
                    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as job_file:
                        job_json = {"tags": job_skills_list}
                        json.dump(job_json, job_file)
                        job_file_path = job_file.name
                    
                    # Write resume skills to a temporary JSON file
                    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as resume_file:
                        resume_json = {"skills": resume_skills}
                        json.dump(resume_json, resume_file)
                        resume_file_path = resume_file.name
                    
                    # Call the C++ skill matcher executable
                    skill_matcher_executable = os.path.join(pathlib.Path(__file__).parent.absolute(), 'skill_matcher')
                    if os.name == 'nt':
                        skill_matcher_executable += '.exe'
                    
                    try:
                        result = subprocess.run([skill_matcher_executable, resume_file_path, job_file_path], capture_output=True, text=True, timeout=5)
                        output = result.stdout.strip()
                        # Parse match percentage from output
                        match_percentage = 0.0
                        if output.startswith("Match Percentage:"):
                            match_percentage = float(output.split(":")[1].replace("%", "").strip())
                    except Exception as e:
                        print(f"[ERROR] Skill matcher execution failed: {e}")
                        match_percentage = 0.0
                    
                    # Clean up temporary files
                    os.unlink(job_file_path)
                    os.unlink(resume_file_path)
                    
                    job['match_percentage'] = match_percentage
                    job['tags'] = job_skills_list
                    all_jobs.append(job)
            
            # Limit total jobs to 50 to avoid large responses
            if len(all_jobs) >= 50:
                break
        
        # Save all jobs to jobs.json for reuse
        jobs_json_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'jobs.json')
        try:
            with open(jobs_json_path, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] Saved {len(all_jobs)} jobs to jobs.json")
        except Exception as e:
            print(f"[ERROR] Failed to save jobs.json: {e}")
        
        # Transform the combined job data to match the frontend expectations
        formatted_jobs = []
        for job in all_jobs[:15]:  # Limit to 15 jobs
            formatted_job = {
                "title": job.get("job_title", ""),
                "company_name": job.get("employer_name", ""),
                "url": job.get("job_apply_link", "") or job.get("job_offer_expiration_datetime_utc", ""),
                "tags": job.get("tags", []),
                "location": job.get("job_city", "") + ", " + job.get("job_state", "") if job.get("job_city") else job.get("job_country", ""),
                "employment_type": job.get("job_employment_type", ""),
                "salary": job.get("job_salary", ""),
                "description": job.get("job_description", "")[:500] + "..." if job.get("job_description") else "",
                "match_percentage": job.get("match_percentage", 0.0)
            }
            formatted_jobs.append(formatted_job)
        
        print(f"[DEBUG] Returning {len(formatted_jobs)} jobs")
        return jsonify(formatted_jobs)
        
    except requests.Timeout:
        print("[ERROR] Request timed out")
        return jsonify({"error": "Request timed out. Please try again."}), 500
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return jsonify({"error": f"Failed to fetch jobs: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Failed to fetch jobs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/jobs')
def get_jobs():
    jobs_json_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'jobs.json')
    try:
        with open(jobs_json_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        # Remove match_percentage for general job listing
        for job in jobs:
            if 'match_percentage' in job:
                del job['match_percentage']
        return jsonify(jobs)
    except Exception as e:
        print(f"[ERROR] Failed to read jobs.json: {e}")

# Add a test endpoint to check if API key is loaded
@app.route('/test-api-key')
def test_api_key():
    api_key = os.getenv("RAPIDAPI_KEY")
    return jsonify({
        "api_key_loaded": bool(api_key),
        "api_key_preview": f"{api_key[:10]}..." if api_key else None
    })

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
