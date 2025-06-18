#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include "json.hpp"

using json = nlohmann::json;
using namespace std;

struct Job {
    string id;
    string title;
    string company;
    string location;
    vector<string> tags;
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
            jobs.push_back(job);
        }
    }
    return jobs;
}

void build_job_graph(const vector<Job>& jobs) {
    unordered_map<string, vector<string>> skill_to_jobs;
    for (const auto& job : jobs) {
        for (const auto& tag : job.tags) {
            skill_to_jobs[tag].push_back(job.id);
        }
    }

    cout << "Job Graph:" << endl;
    for (const auto& [skill, job_ids] : skill_to_jobs) {
        cout << "Skill: " << skill << " -> Jobs: ";
        for (const auto& job_id : job_ids) {
            cout << job_id << " ";
        }
        cout << endl;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cout << "Usage: job_graph <jobs_json_file>" << endl;
        return 1;
    }

    string jobs_file = argv[1];
    vector<Job> jobs = load_jobs_from_json(jobs_file);
    if (jobs.empty()) {
        cout << "No jobs found in JSON." << endl;
        return 1;
    }

    build_job_graph(jobs);
    return 0;
}
