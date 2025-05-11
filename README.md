# ResuMatch 🚀
**AI-Powered Resume Optimization for Perfect Job Fits**

## 📋 Overview
ResuMatch is an intelligent resume optimization platform that helps job seekers find their perfect job matches. It uses advanced AI algorithms to analyze resumes, match them with job requirements, and generate optimized resumes tailored to specific job postings.

## ✨ Features
- **Smart Resume Parsing**: Extract skills, experience, and education from uploaded resumes
- **Job Matching Algorithm**: Advanced C++ implementation using Trie and Heap data structures
- **Resume Generation**: Create professional resumes from templates
- **Job API Integration**: Fetch real-time job listings from multiple sources
- **Skill Matching**: Highlight matching skills between resumes and job requirements
- **PDF Generation**: Convert resumes to professional PDF format

## 🛠️ Tech Stack
- **Backend**: Python (Flask), C++
- **Frontend**: HTML, CSS, JavaScript
- **Data Processing**: Python NLP libraries
- **PDF Generation**: WeasyPrint
- **Job APIs**: Remotive, JSearch

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- C++ compiler (for job_matcher.cpp)
- pip (Python package manager)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/omi290/ResuMatch.git
cd ResuMatch
```

2. Create and activate a virtual environment:
```bash
python -m venv resume
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Compile the C++ job matcher:
```bash
g++ -o job_matcher job_matcher.cpp
```

### Running the Application
1. Start the Flask server:
```bash
python backend/app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## 📁 Project Structure
```
ResuMatch/
├── backend/              # Backend application code
│   ├── app.py           # Main Flask application
│   ├── resume_parser.py # Resume parsing logic
│   ├── job_matcher.cpp  # C++ job matching algorithm
│   └── ...
├── frontend/            # Frontend HTML/CSS/JS files
│   ├── job-matching-page.html
│   ├── resume-upload-page.html
│   └── resume-generation-page.html
└── requirements.txt     # Python dependencies
```

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support
For support, email support@resumatch.com or open an issue in the repository.

---

## 👨‍💻 Team CodeXplorers – B.Tech CSE, 4th Semester (DAA)
- **Priyanka** – Team Leader (L1) – 230112164  
- **Vaibhav Baloni** –  (L2) – 23011984  
- **Om Prakash Barmola** –  (J2) – 23011901  
- **Yuvika Chalotra** –  (G1) – 230223658  

---

## 🧩 Key Features
- 🔍 Upload resume and extract skills, experience, education
- 🤝 Match job descriptions using **Trie**, **Heap**, **Graph**
- 🧠 Score and rank jobs with DSA
- ⚡ Generate 5 resumes at once using **parallel processing**
- 🧾 Resume rendered using Jinja2 & converted to PDF
- 🌐 Fetch job listings from external APIs (e.g. Remotive)

---

## ⚙️ Tech Stack

| Layer       | Technology |
|-------------|------------|
| Frontend    | HTML, CSS, JS |
| Backend     | Flask (Python) |
| Resume Parsing | pdfplumber / python-docx |
| Matching Logic | C++ (Trie, Heap, Graph, DP) |
| Resume Generator | Jinja2 + WeasyPrint |
| Parallel Execution | Python `concurrent.futures` |
| Data Storage | JSON / SQLite |
| External APIs | Remotive / JSearch (via RapidAPI) |

---


