#include <iostream>
#include <queue>
#include <vector>
#include <string>
#include <unordered_map>
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

class JobMatchQueue {
private:
    priority_queue<JobMatch> matches;
    unordered_map<string, bool> job_exists;  // Track if job is already in queue

public:
    void addMatch(const JobMatch& match) {
        if (job_exists.find(match.job_id) == job_exists.end()) {
            matches.push(match);
            job_exists[match.job_id] = true;
        }
    }

    vector<JobMatch> getTopMatches(int n) {
        vector<JobMatch> result;
        priority_queue<JobMatch> temp = matches;
        
        while (!temp.empty() && result.size() < n) {
            result.push_back(temp.top());
            temp.pop();
        }
        
        return result;
    }

    void clear() {
        while (!matches.empty()) {
            matches.pop();
        }
        job_exists.clear();
    }
};

extern "C" {
    // Function to be called from Python
    const char* processJobMatches(const char* resume_json, const char* jobs_json) {
        try {
            json resume = json::parse(resume_json);
            json jobs = json::parse(jobs_json);
            
            JobMatchQueue queue;
            
            // Get resume skills
            vector<string> resume_skills;
            if (resume.contains("skills") && resume["skills"].is_array()) {
                for (const auto& skill : resume["skills"]) {
                    resume_skills.push_back(skill.get<string>());
                }
            }
            
            // Process each job
            for (const auto& job : jobs) {
                vector<string> job_skills;
                if (job.contains("tags") && job["tags"].is_array()) {
                    for (const auto& skill : job["tags"]) {
                        job_skills.push_back(skill.get<string>());
                    }
                }
                
                // Calculate match score
                double match_score = 0.0;
                if (!resume_skills.empty()) {
                    int match_count = 0;
                    for (const auto& skill : job_skills) {
                        if (find(resume_skills.begin(), resume_skills.end(), skill) != resume_skills.end()) {
                            match_count++;
                        }
                    }
                    match_score = (static_cast<double>(match_count) / resume_skills.size()) * 100.0;
                }
                
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
                
                queue.addMatch(match);
            }
            
            // Get top 10 matches
            vector<JobMatch> top_matches = queue.getTopMatches(10);
            
            // Convert to JSON
            json result = json::array();
            for (const auto& match : top_matches) {
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