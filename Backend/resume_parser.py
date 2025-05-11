# resume_parser.py - Enhanced version with better section detection
import requests
import os
from dotenv import load_dotenv
import json
import logging
import io
import PyPDF2
import docx
import re
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return ""

def extract_text_from_file(file_path):
    """Extract text from file based on extension"""
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(('.docx', '.doc')):
        return extract_text_from_docx(file_path)
    return ""

def identify_sections(text):
    """Identify different sections in the resume"""
    # Define common section headers with regex patterns to match variations
    section_patterns = {
        'contact': r'(?i)(CONTACT|PERSONAL\s+INFORMATION|CONTACT\s+INFORMATION|CONTACT\s+DETAILS)',
        'summary': r'(?i)(SUMMARY|PROFESSIONAL\s+SUMMARY|CAREER\s+OBJECTIVE|CAREER\s+SUMMARY|PROFILE|ABOUT\s+ME|OBJECTIVE)',
        'skills': r'(?i)(SKILLS|TECHNICAL\s+SKILLS|CORE\s+COMPETENCIES|KEY\s+SKILLS|AREAS\s+OF\s+EXPERTISE|COMPETENCIES)',
        'experience': r'(?i)(EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s+EXPERIENCE|WORK\s+HISTORY|CAREER\s+HISTORY)',
        'education': r'(?i)(EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMIC\s+HISTORY|EDUCATIONAL\s+BACKGROUND|QUALIFICATIONS)',
        'certifications': r'(?i)(CERTIFICATIONS|CERTIFICATES|PROFESSIONAL\s+CERTIFICATIONS|ACCREDITATIONS|LICENSES)',
        'projects': r'(?i)(PROJECTS|PROJECT\s+EXPERIENCE|PERSONAL\s+PROJECTS|KEY\s+PROJECTS)',
        'extracurricular': r'(?i)(EXTRACURRICULAR|EXTRACURRICULAR\s+ACTIVITIES|ACTIVITIES|VOLUNTEER|VOLUNTEERING|COMMUNITY\s+SERVICE)',
        'languages': r'(?i)(LANGUAGES|LANGUAGE\s+PROFICIENCY|LANGUAGE\s+SKILLS)',
        'publications': r'(?i)(PUBLICATIONS|PAPERS|RESEARCH\s+PAPERS|ARTICLES)',
        'awards': r'(?i)(AWARDS|HONORS|ACHIEVEMENTS|RECOGNITION)',
        'references': r'(?i)(REFERENCES|REFEREES)'
    }
    
    # Split text into lines and clean
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find sections in the text
    sections = {}
    current_section = 'header'  # Default section for the top of the resume
    sections[current_section] = []
    
    for i, line in enumerate(lines):
        # Check if this line is a section header
        for section_name, pattern in section_patterns.items():
            if re.search(pattern, line) and (len(line) < 50):  # Section headers are typically short
                current_section = section_name
                if current_section not in sections:
                    sections[current_section] = []
                break
        else:
            # If not a section header, add to current section
            sections[current_section].append(line)
    
    return sections

def extract_name_email(text_lines):
    """Extract name and email from the top of the resume"""
    name = ""
    email = ""
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Check the first few lines for name and email
    for line in text_lines[:10]:
        # Extract email
        if not email:
            email_match = re.search(email_pattern, line)
            if email_match:
                email = email_match.group(0)
        
        # Extract name (usually one of the first non-email lines with reasonable length)
        if not name and not re.search(email_pattern, line) and 2 < len(line) < 50:
            # Exclude lines with typical header words
            if not any(word.lower() in line.lower() for word in ["resume", "cv", "curriculum", "vitae", "address", "phone", "tel", "github", "linkedin"]):
                name = line
    
    return name, email

def parse_experience_section(experience_lines):
    """Parse the experience section to extract job entries"""
    if not experience_lines:
        return []
    
    experience_entries = []
    current_entry = {}
    date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s.,-]?(\d{4})\s*(-|–|to|till|until|\s)\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|Present|Current|Now)?[\s.,-]?(\d{0,4})'
    
    for i, line in enumerate(experience_lines):
        # Check if this line contains a date range
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        
        # If we have a date or this is the first line of a new entry
        if date_match or (i > 0 and len(line) < 80 and not line.startswith('•') and not line.startswith('-')):
            # Save the previous entry if it exists
            if current_entry and 'title' in current_entry:
                experience_entries.append(current_entry)
                current_entry = {}
            
            # Start a new entry
            if date_match:
                duration = line
                title_line = experience_lines[i-1] if i > 0 else ""
                company_line = experience_lines[i-2] if i > 1 else ""
                
                # Sometimes the title and company are on the same line as the date
                if len(title_line) > 80 or "•" in title_line or title_line.startswith('-'):
                    title_line = line.split(',')[0] if ',' in line else line
                
                current_entry = {
                    "title": title_line.strip(),
                    "company": company_line.strip(),
                    "duration": duration.strip()
                }
            else:
                # Assume this is a new job title
                current_entry = {
                    "title": line.strip(),
                    "company": "",
                    "duration": ""
                }
        
        # If the current line seems to be a company name (after a job title)
        elif current_entry and 'title' in current_entry and not current_entry.get('company') and len(line) < 80:
            current_entry["company"] = line.strip()
        
        # If the current line seems to be a date range (after a company name)
        elif current_entry and 'company' in current_entry and not current_entry.get('duration') and date_match:
            current_entry["duration"] = line.strip()
    
    # Add the last entry if it exists
    if current_entry and 'title' in current_entry:
        experience_entries.append(current_entry)
    
    # If we couldn't parse any entries but have lines, create a simple entry
    if not experience_entries and experience_lines:
        experience_entries = [{
            "title": experience_lines[0] if len(experience_lines) > 0 else "Professional",
            "company": experience_lines[1] if len(experience_lines) > 1 else "Company",
            "duration": experience_lines[2] if len(experience_lines) > 2 else "2020 - Present"
        }]
    
    return experience_entries

def parse_education_section(education_lines):
    """Parse the education section to extract grouped education entries"""
    if not education_lines:
        return []

    education_entries = []
    current_entry = {}
    degree_keywords = ["grade", "bachelor", "master", "phd", "diploma", "specialization"]
    percentage_keywords = ["percentage", "%"]
    cgpa_keywords = ["cgpa", "gpa"]
    school_keywords = ["school", "university", "college", "institute"]
    year_pattern = r"(19|20)\\d{2}"

    def is_degree(line):
        return any(k in line.lower() for k in degree_keywords)

    def is_percentage(line):
        return any(k in line.lower() for k in percentage_keywords)

    def is_cgpa(line):
        return any(k in line.lower() for k in cgpa_keywords)

    def is_school(line):
        return any(k in line.lower() for k in school_keywords)

    def is_year(line):
        return bool(re.search(year_pattern, line))

    for line in education_lines:
        line = line.strip()
        if not line:
            continue
        # Start a new entry if we see a degree/level
        if is_degree(line):
            if current_entry:
                education_entries.append(current_entry)
                current_entry = {}
            current_entry["degree"] = line
        elif is_school(line):
            current_entry["school"] = line
        elif is_percentage(line):
            current_entry["percentage"] = line
        elif is_cgpa(line):
            current_entry["cgpa"] = line
        elif is_year(line):
            # If the line contains both school and year, split them
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 2:
                    if is_school(parts[0]):
                        current_entry["school"] = parts[0]
                    current_entry["year"] = parts[1]
                else:
                    current_entry["year"] = line
            else:
                current_entry["year"] = line
        else:
            # If the line doesn't match any, try to add as specialization or extra info
            if "specialization" in line.lower():
                current_entry["specialization"] = line
            else:
                # fallback: add as description
                if "description" in current_entry:
                    current_entry["description"] += " " + line
                else:
                    current_entry["description"] = line
    # Add the last entry
    if current_entry:
        education_entries.append(current_entry)
    return education_entries

def extract_skills(text, skills_section):
    """Extract skills from the text"""
    # If we have a skills section, extract skills from there
    skills = []
    
    if skills_section:
        # Look for skill items in bullet points, commas, or separate lines
        skill_text = ' '.join(skills_section)
        # Split by various delimiters
        for delimiter in ['•', '■', '✓', '✔', '→', '-', ',', '|', '\n']:
            if delimiter in skill_text:
                potential_skills = [s.strip() for s in skill_text.split(delimiter) if s.strip()]
                if potential_skills and all(len(s) < 50 for s in potential_skills):
                    skills = potential_skills
                    break
    
    # If we couldn't extract skills from the section, look for common skill keywords
    if not skills:
        skill_keywords = ["Python", "JavaScript", "Java", "C++", "HTML", "CSS", 
                         "React", "Angular", "Vue", "Node.js", "SQL", "NoSQL",
                         "MongoDB", "MySQL", "PostgreSQL", "AWS", "Azure", "GCP",
                         "Docker", "Kubernetes", "Git", "Excel", "Word", "PowerPoint",
                         "Project Management", "Agile", "Scrum", "Communication",
                         "Leadership", "Teamwork", "Problem Solving", "Critical Thinking",
                         "Data Analysis", "Machine Learning", "AI", "Artificial Intelligence"]
        
        # Search for skills in the entire text
        found_skills = []
        for keyword in skill_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                found_skills.append(keyword)
        
        if found_skills:
            skills = found_skills
    
    # If we still don't have skills, add some generic ones
    if not skills:
        skills = random.sample(["Communication", "Teamwork", "Microsoft Office", 
                             "Problem Solving", "Time Management"], 3)
    
    # Clean up skills
    skills = [skill.strip() for skill in skills if 2 < len(skill.strip()) < 50]
    skills = list(dict.fromkeys(skills))  # Remove duplicates while preserving order
    
    return skills

def extract_certifications(certifications_section):
    """Extract certifications from the certifications section"""
    certifications = []
    
    if certifications_section:
        # Simple approach: treat each line as a separate certification
        for line in certifications_section:
            line = line.strip()
            if line and len(line) < 100 and not line.lower().startswith(('certification', 'certifications')):
                certifications.append(line)
    
    return certifications

def basic_resume_parser(file_path):
    """Enhanced basic resume parser as fallback"""
    # Extract text from file
    text = extract_text_from_file(file_path)
    if not text:
        return {"data": {"document": {"name": "", "email": "", "skills": [], "experience": [], "education": []}}}
    
    # Identify different sections in the resume
    sections = identify_sections(text)
    
    # Extract name and email from the header section
    name, email = extract_name_email(sections.get('header', []))
    if not name and 'contact' in sections:
        name, email = extract_name_email(sections['contact'])
    
    # Extract skills
    skills = extract_skills(text, sections.get('skills', []))
    
    # Extract experience
    experience = parse_experience_section(sections.get('experience', []))
    
    # Extract education
    education = parse_education_section(sections.get('education', []))
    
    # Extract certifications (if any) - we'll include these in additional_sections
    certifications = extract_certifications(sections.get('certifications', []))
    
    # Extract extracurricular activities (if any)
    extracurricular = []
    if 'extracurricular' in sections:
        for line in sections['extracurricular']:
            if line and len(line) < 100:
                extracurricular.append(line.strip())
    
    # Create additional sections dictionary
    additional_sections = {}
    if certifications:
        additional_sections["certifications"] = certifications
    if extracurricular:
        additional_sections["extracurricular"] = extracurricular
    
    # Create a structured response
    parsed_data = {
        "data": {
            "document": {
                "name": name,
                "email": email,
                "skills": skills,
                "experience": experience,
                "education": education,
                "additional_sections": additional_sections
            }
        }
    }
    
    return parsed_data

def parse_resume_with_extracta(file_path):
    """
    Parse resume using the Extracta API from RapidAPI with fallback to improved basic parser
    
    Args:
        file_path (str): Path to the resume file
        
    Returns:
        dict: Parsed resume data
    """
    url = "https://resume-parsing-api2.p.rapidapi.com/resume-parser"
    api_key = os.getenv('RAPIDAPI_KEY')
    
    # Check if API key exists
    if not api_key:
        logger.warning("No API key found. Using fallback parser.")
        return basic_resume_parser(file_path)
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "resume-parsing-api2.p.rapidapi.com"
    }
    
    try:
        with open(file_path, "rb") as file:
            files = {"file": file}
            logger.info(f"Sending request to parse resume: {os.path.basename(file_path)}")
            
            # Try with API first
            try:
                response = requests.post(url, files=files, headers=headers, timeout=15)
                
                # Log the response status and headers for debugging
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info("Successfully parsed resume with API")
                        
                        # Save the raw response for debugging
                        debug_file = os.path.join(os.path.dirname(file_path), "parsed_debug.json")
                        with open(debug_file, 'w') as f:
                            json.dump(data, f, indent=2)
                        
                        # Process API response to ensure it matches our expected format
                        # This includes handling certifications and extracurriculars
                        if "data" in data and "document" in data["data"]:
                            doc = data["data"]["document"]
                            
                            # Extract any sections that might be misplaced
                            extracted_text = extract_text_from_file(file_path)
                            sections = identify_sections(extracted_text)
                            
                            # Initialize additional_sections if not present
                            if "additional_sections" not in doc:
                                doc["additional_sections"] = {}
                            
                            # Handle certifications
                            if "certifications" in sections:
                                certifications = extract_certifications(sections["certifications"])
                                if certifications:
                                    doc["additional_sections"]["certifications"] = certifications
                            
                            # Handle extracurricular activities
                            if "extracurricular" in sections:
                                extracurricular = []
                                for line in sections["extracurricular"]:
                                    if line and len(line) < 100:
                                        extracurricular.append(line.strip())
                                if extracurricular:
                                    doc["additional_sections"]["extracurricular"] = extracurricular
                            
                            # Ensure skills is a list
                            if "skills" in doc and not isinstance(doc["skills"], list):
                                doc["skills"] = [doc["skills"]] if doc["skills"] else []
                            
                            # Ensure experience is a list with proper structure
                            if "experience" in doc:
                                if not isinstance(doc["experience"], list):
                                    doc["experience"] = [doc["experience"]] if doc["experience"] else []
                                
                                # Clean up experience entries
                                for i, exp in enumerate(doc["experience"]):
                                    if not isinstance(exp, dict):
                                        doc["experience"][i] = {
                                            "title": str(exp),
                                            "company": "",
                                            "duration": ""
                                        }
                            
                            # Ensure education is a list with proper structure
                            if "education" in doc:
                                if not isinstance(doc["education"], list):
                                    doc["education"] = [doc["education"]] if doc["education"] else []
                                
                                # Clean up education entries
                                for i, edu in enumerate(doc["education"]):
                                    if not isinstance(edu, dict):
                                        doc["education"][i] = {
                                            "degree": str(edu),
                                            "school": "",
                                            "duration": ""
                                        }
                        
                        return data
                    except json.JSONDecodeError:
                        logger.error("Failed to decode JSON response, using fallback parser")
                        logger.error(f"Response content: {response.text[:500]}...")
                else:
                    logger.error(f"API request failed with status code {response.status_code}")
                    logger.error(f"Response content: {response.text[:500]}...")
            except requests.exceptions.RequestException as e:
                logger.error(f"API request error: {str(e)}")
            
            # If we reach here, API parsing failed, use fallback
            logger.warning("Using fallback resume parser")
            return basic_resume_parser(file_path)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return basic_resume_parser(file_path)