#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_set>
#include <algorithm>
#include "json.hpp"


using json = nlohmann::json;
using namespace std;


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
    if (resume_skills.empty()) return 0.0;
    unordered_set<string> resume_set(resume_skills.begin(), resume_skills.end());
    int match_count = 0;
    for (const auto& skill : job_skills) {
        if (resume_set.find(to_lowercase(skill)) != resume_set.end()) {
            match_count++;
        }
    }
    return (static_cast<double>(match_count) / resume_skills.size()) * 100.0;
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
