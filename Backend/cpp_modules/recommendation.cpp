#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include "json.hpp"

using json = nlohmann::json;
using namespace std;

struct Job {
    string id;
    string title;
    string company;
    string location;
    vector<string> tags;
    double score;
};

vector<Job> load_jobs_from_json(const string& filepath) {
    vector<Job> jobs;
    ifstream file(filepath);
    if (!file.is_open()) {
        cerr << "Failed to open file: " << filepath << endl;
        return jobs;
    }
    json j;
    file >> j;
    file.close();

    if (j.is_array()) {
        for (const auto& job_json : j) {
            Job job;
            job.id = job_json["id"].get<string>();
            job.title = job_json["title"].get<string>();
            job.company = job_json["company"].get<string>();
            job.location = job_json["location"].get<string>();
            for (const auto& tag : job_json["tags"]) {
                job.tags.push_back(tag.get<string>());
            }
            job.score = 0.0;
            jobs.push_back(job);
        }
    }
    return jobs;
}

void recommend_jobs(vector<Job>& jobs, const vector<string>& user_skills) {
    for (auto& job : jobs) {
        int match_count = 0;
        for (const auto& skill : user_skills) {
            if (find(job.tags.begin(), job.tags.end(), skill) != job.tags.end()) {
                match_count++;
            }
        }
        job.score = (static_cast<double>(match_count) / job.tags.size()) * 100.0;
    }
    sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) { return a.score > b.score; });
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cout << "Usage: recommendation <jobs_json_file> <user_skills_json_file>" << endl;
        return 1;
    }

    string jobs_file = argv[1];
    string user_skills_file = argv[2];

    vector<Job> jobs = load_jobs_from_json(jobs_file);
    if (jobs.empty()) {
        cout << "No jobs found in JSON." << endl;
        return 1;
    }

    ifstream skills_file(user_skills_file);
    if (!skills_file.is_open()) {
        cout << "Failed to open user skills file." << endl;
        return 1;
    }
    json skills_json;
    skills_file >> skills_json;
    skills_file.close();

    vector<string> user_skills;
    if (skills_json.contains("skills") && skills_json["skills"].is_array()) {
        for (const auto& skill : skills_json["skills"]) {
            user_skills.push_back(skill.get<string>());
        }
    }

    recommend_jobs(jobs, user_skills);

    cout << "Recommended Jobs:" << endl;
    for (const auto& job : jobs) {
        cout << "Job: " << job.title << " at " << job.company << " in " << job.location << " (Score: " << job.score << "%)" << endl;
    }

    return 0;
}
