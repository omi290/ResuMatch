import subprocess
import json
import os

def run_skill_matcher(job_skills, resume_skills):
    """
    Run the skill_matcher.exe C++ executable to calculate match percentage.
    Args:
        job_skills (list of str): Skills required by the job
        resume_skills (list of str): Skills from the resume
    Returns:
        float: match percentage (0-100)
    """
    try:
        # Prepare input JSON string
        input_data = json.dumps({
            "job_skills": job_skills,
            "resume_skills": resume_skills
        })
        # Path to skill_matcher executable
        exe_path = os.path.join(os.path.dirname(__file__), "cpp_modules", "skill_matcher.exe")
        # Run subprocess with input data
        result = subprocess.run([exe_path], input=input_data.encode(), capture_output=True, check=True)
        # Parse output as float match percentage
        output = result.stdout.decode().strip()
        match_percentage = float(output)
        return match_percentage
    except Exception as e:
        print(f"Error running skill_matcher: {e}")
        return 0.0

def run_resume_ranker(resume_list):
    """
    Run the resume_ranker.exe C++ executable to rank resumes using priority queue.
    Args:
        resume_list (list of dict): Each dict contains resume_id and skills
    Returns:
        list of dict: Top ranked resumes with match scores
    """
    try:
        input_data = json.dumps(resume_list)
        exe_path = os.path.join(os.path.dirname(__file__), "cpp_modules", "resume_ranker.exe")
        result = subprocess.run([exe_path], input=input_data.encode(), capture_output=True, check=True)
        output = result.stdout.decode().strip()
        ranked_resumes = json.loads(output)
        return ranked_resumes
    except Exception as e:
        print(f"Error running resume_ranker: {e}")
        return []
