import subprocess
import json
import os
import tempfile

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
        # Write resume_skills and job_skills to temporary JSON files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as resume_file, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as job_file:
            json.dump({"skills": resume_skills}, resume_file)
            resume_file.flush()
            json.dump({"tags": job_skills}, job_file)
            job_file.flush()
            resume_file_path = resume_file.name
            job_file_path = job_file.name
        exe_path = os.path.join(os.path.dirname(__file__), "cpp_modules", "skill_matcher.exe")
        # Call the executable with file paths as arguments
        result = subprocess.run([exe_path, resume_file_path, job_file_path], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        # Clean up temp files
        os.remove(resume_file_path)
        os.remove(job_file_path)
        # Parse output for match percentage
        for line in output.splitlines():
            if "Match Percentage:" in line:
                percent_str = line.split(":")[-1].replace("%", "").strip()
                return float(percent_str)
        # If not found, return 0
        return 0.0
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
