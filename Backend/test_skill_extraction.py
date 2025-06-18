#!/usr/bin/env python3
"""
Test script for skill extraction functionality
"""

from resume_parser import extract_skills
import re

def test_skill_extraction():
    """Test the skill extraction with various skill formats"""
    
    # Test cases with different skill formats
    test_cases = [
        {
            "name": "Basic programming languages",
            "text": "I have experience with C, C++, Java programming, DBMS, MySQL database, Python, JavaScript, and React.",
            "skills_section": ["Skills: C, C++, Java, DBMS, MySQL, Python, JavaScript, React"]
        },
        {
            "name": "Skills with abbreviations",
            "text": "Proficient in JS, TS, CPP, SQL, ML, AI, and REST APIs. Experience with DBMS and MySQL.",
            "skills_section": ["Technical Skills: JavaScript, TypeScript, C++, SQL, Machine Learning, AI, REST APIs"]
        },
        {
            "name": "Skills with variations",
            "text": "Worked with Java programming language, C++ programming, MySQL database management, and database management systems.",
            "skills_section": ["Programming: Java, C++, MySQL, DBMS"]
        },
        {
            "name": "Mixed case and formats",
            "text": "Skills include: c programming, C++ development, JAVA, dbms, mySQL, python, javascript, react.js",
            "skills_section": ["Technical Skills: C, C++, Java, DBMS, MySQL, Python, JavaScript, React"]
        },
        {
            "name": "C++ specific test",
            "text": "I know C++ and C programming. Also familiar with C++ programming language.",
            "skills_section": ["Programming Languages: C, C++"]
        }
    ]
    
    print("Testing Enhanced Skill Extraction\n")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        print(f"Skills section: {test_case['skills_section']}")
        
        try:
            # Debug: Check if C++ appears in the text
            cpp_in_text = "C++" in test_case['text'] or "cpp" in test_case['text'].lower()
            print(f"C++ in text: {cpp_in_text}")
            
            # Debug: Check regex patterns
            full_text = test_case['text'].lower()
            cpp_patterns = [
                r'\bc\+\+\b',
                r'\bcpp\b', 
                r'\bc plus plus\b'
            ]
            
            for pattern in cpp_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    print(f"Pattern '{pattern}' found: {matches}")
            
            skills = extract_skills(test_case['text'], test_case['skills_section'])
            print(f"Extracted skills: {skills}")
            
            # Check for specific skills mentioned by user
            target_skills = ['C', 'C++', 'Java', 'DBMS', 'MySQL']
            found_targets = [skill for skill in skills if skill in target_skills]
            print(f"Target skills found: {found_targets}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_skill_extraction() 