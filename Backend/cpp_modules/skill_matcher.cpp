#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_set>
#include <algorithm>
#include <queue>
#include "json.hpp"

using json = nlohmann::json;
using namespace std;

struct JobMatch {
    string job_id;
    double match_score;
    string title;
    string company;
    string location;
    string type;
    vector<string> skills;

    JobMatch(string id, double score, string t, string c, string l, string ty, vector<string> s)
        : job_id(id), match_score(score), title(t), company(c), location(l), type(ty), skills(s) {}

    // Custom comparator for priority queue (higher score = higher priority)
    bool operator<(const JobMatch& other) const {
        return match_score < other.match_score;
    }
};

string to_lowercase(const string& str) {
    string result = str;
    transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

vector<string> load_skills_from_json(const string& filepath, const string& key) {
    vector<string> skills;
    ifstream file(filepath);
    if (!file.is_open()) {
        cerr << "Failed to open file: " << filepath << endl;
        return skills;
    }
    json j;
    file >> j;
    file.close();

    if (j.contains(key) && j[key].is_array()) {
        for (const auto& skill : j[key]) {
            if (skill.is_string()) {
                skills.push_back(to_lowercase(skill.get<string>()));
            }
        }
    }
    return skills;
}

double calculate_match_percentage(const vector<string>& resume_skills, const vector<string>& job_skills) {
    if (job_skills.empty()) return 0.0;
    unordered_set<string> resume_set(resume_skills.begin(), resume_skills.end());
    int match_count = 0;
    for (const auto& skill : job_skills) {
        if (resume_set.find(to_lowercase(skill)) != resume_set.end()) {
            match_count++;
        }
    }
    return (static_cast<double>(match_count) / job_skills.size()) * 100.0;
}

extern "C" {
    const char* processJobMatches(const char* resume_json, const char* jobs_json) {
        try {
            json resume = json::parse(resume_json);
            json jobs = json::parse(jobs_json);
            
            priority_queue<JobMatch> matches;
            
            // Get resume skills
            vector<string> resume_skills;
            if (resume.contains("skills") && resume["skills"].is_array()) {
                for (const auto& skill : resume["skills"]) {
                    resume_skills.push_back(to_lowercase(skill.get<string>()));
                }
            }
            
            // Process each job
            for (const auto& job : jobs) {
                vector<string> job_skills;
                if (job.contains("tags") && job["tags"].is_array()) {
                    for (const auto& skill : job["tags"]) {
                        job_skills.push_back(to_lowercase(skill.get<string>()));
                    }
                }
                
                // Calculate match score
                double match_score = calculate_match_percentage(resume_skills, job_skills);
                
                // Create and add job match
                JobMatch match(
                    job["_id"].get<string>(),
                    match_score,
                    job["title"].get<string>(),
                    job["company"].get<string>(),
                    job["location"].get<string>(),
                    job["type"].get<string>(),
                    job_skills
                );
                
                matches.push(match);
            }
            
            // Get top 10 matches
            json result = json::array();
            int count = 0;
            while (!matches.empty() && count < 10) {
                const JobMatch& match = matches.top();
                json match_json = {
                    {"job_id", match.job_id},
                    {"match_score", match.match_score},
                    {"title", match.title},
                    {"company", match.company},
                    {"location", match.location},
                    {"type", match.type},
                    {"skills", match.skills}
                };
                result.push_back(match_json);
                matches.pop();
                count++;
            }
            
            // Convert to string and return
            string result_str = result.dump();
            char* result_cstr = new char[result_str.length() + 1];
            strcpy(result_cstr, result_str.c_str());
            return result_cstr;
            
        } catch (const exception& e) {
            cerr << "Error processing job matches: " << e.what() << endl;
            return nullptr;
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cout << "Usage: skill_matcher <resume_json_file> <job_json_file>" << endl;
        return 1;
    }

    string resume_file = argv[1];
    string job_file = argv[2];

   
    vector<string> resume_skills = load_skills_from_json(resume_file, "skills");
    if (resume_skills.empty()) {
        cout << "No skills found in resume JSON." << endl;
        return 1;
    }

  
    vector<string> job_skills = load_skills_from_json(job_file, "tags");
    if (job_skills.empty()) {
        cout << "No skills found in job JSON." << endl;
        return 1;
    }

 
    double match_percentage = calculate_match_percentage(resume_skills, job_skills);

    cout << "Match Percentage: " << match_percentage << "%" << endl;

    return 0;
}
