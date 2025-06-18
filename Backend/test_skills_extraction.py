#!/usr/bin/env python3
"""
Test script to verify skills extraction from resumes
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from resume_parser import extract_skills, identify_sections, extract_text_from_file

def test_skills_extraction():
    """Test skills extraction with sample resume text"""
    
    # Sample resume text with various skills
    sample_resume_text = """
    JOHN DOE
    Software Engineer
    john.doe@email.com
    
    SUMMARY
    Experienced software engineer with 5+ years in full-stack development.
    
    TECHNICAL SKILLS
    Programming Languages: Python, Java, JavaScript, C++, SQL
    Frameworks: React, Angular, Django, Spring Boot, Node.js
    Databases: MySQL, PostgreSQL, MongoDB, Redis
    Cloud Platforms: AWS, Azure, Docker, Kubernetes
    Tools: Git, Jenkins, Jira, VS Code
    
    WORK EXPERIENCE
    Senior Software Engineer at Tech Corp (2020-2023)
    - Developed web applications using React and Node.js
    - Implemented REST APIs using Python and Django
    - Worked with AWS services including EC2, S3, and Lambda
    - Used Docker for containerization and Kubernetes for orchestration
    - Experience with machine learning using TensorFlow and scikit-learn
    
    Software Developer at Startup Inc (2018-2020)
    - Built mobile apps using React Native and Flutter
    - Proficient in Java development with Spring framework
    - Knowledge of database design and optimization
    - Familiar with agile methodologies and CI/CD pipelines
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology (2014-2018)
    - Studied algorithms, data structures, and software engineering
    - Completed projects in web development and machine learning
    
    CERTIFICATIONS
    AWS Certified Developer Associate
    Google Cloud Professional Developer
    """
    
    print("Testing Skills Extraction...")
    print("=" * 50)
    
    # Test section identification
    print("1. Testing Section Identification:")
    sections = identify_sections(sample_resume_text)
    for section_name, content in sections.items():
        print(f"   {section_name}: {len(content)} lines")
        if section_name == "skills":
            print(f"   Skills section content: {content[:3]}...")  # Show first 3 lines
    
    # Test skills extraction
    print("\n2. Testing Skills Extraction:")
    skills_section = sections.get("skills", [])
    extracted_skills = extract_skills(sample_resume_text, skills_section)
    
    print(f"   Total skills extracted: {len(extracted_skills)}")
    print(f"   Skills: {extracted_skills}")
    
    # Test with different skills section formats
    print("\n3. Testing Different Skills Section Formats:")
    
    # Format 1: Comma-separated
    skills_text1 = "Python, Java, JavaScript, React, AWS, Docker"
    skills1 = extract_skills(sample_resume_text, [skills_text1])
    print(f"   Comma-separated format: {skills1}")
    
    # Format 2: Bullet points
    skills_text2 = ["• Python", "• Java", "• JavaScript", "• React", "• AWS", "• Docker"]
    skills2 = extract_skills(sample_resume_text, skills_text2)
    print(f"   Bullet points format: {skills2}")
    
    # Format 3: Categories
    skills_text3 = [
        "Programming Languages: Python, Java, JavaScript",
        "Frameworks: React, Angular, Django",
        "Cloud: AWS, Azure, Docker"
    ]
    skills3 = extract_skills(sample_resume_text, skills_text3)
    print(f"   Categories format: {skills3}")
    
    # Test experience-based skill extraction
    print("\n4. Testing Experience-Based Skill Extraction:")
    experience_text = """
    WORK EXPERIENCE
    - Developed applications using Python and Django
    - Worked with React and Node.js for frontend development
    - Experience with AWS services including EC2 and S3
    - Proficient in machine learning using TensorFlow
    - Knowledge of Docker and Kubernetes for deployment
    """
    experience_skills = extract_skills(experience_text, [])
    print(f"   Skills from experience: {experience_skills}")
    
    print("\n" + "=" * 50)
    print("Skills extraction test completed!")

def test_with_real_resume(file_path):
    """Test skills extraction with a real resume file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"\nTesting with real resume: {file_path}")
    print("=" * 50)
    
    try:
        # Extract text from file
        text = extract_text_from_file(file_path)
        if not text:
            print("Failed to extract text from file")
            return
        
        # Identify sections
        sections = identify_sections(text)
        print("Sections found:")
        for section_name, content in sections.items():
            print(f"   {section_name}: {len(content)} lines")
        
        # Extract skills
        skills_section = sections.get("skills", [])
        extracted_skills = extract_skills(text, skills_section)
        
        print(f"\nSkills extracted: {len(extracted_skills)}")
        print(f"Skills: {extracted_skills}")
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    test_skills_extraction()
    
    # Test with a real resume file if provided
    if len(sys.argv) > 1:
        test_with_real_resume(sys.argv[1])
    else:
        print("\nTo test with a real resume file, run:")
        print("python test_skills_extraction.py path/to/resume.pdf") 