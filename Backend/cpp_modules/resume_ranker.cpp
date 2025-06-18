#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include "json.hpp"

using json = nlohmann::json;
using namespace std;

struct Resume {
    string id;
    string name;
    vector<string> skills;
    double score;
};

vector<Resume> load_resumes_from_json(const string& filepath) {
    vector<Resume> resumes;
    ifstream file(filepath);
    if (!file.is_open()) {
        cerr << "Failed to open file: " << filepath << endl;
        return resumes;
    }
    json j;
    file >> j;
    file.close();

    if (j.is_array()) {
        for (const auto& resume_json : j) {
            Resume resume;
            resume.id = resume_json["id"].get<string>();
            resume.name = resume_json["name"].get<string>();
            for (const auto& skill : resume_json["skills"]) {
                resume.skills.push_back(skill.get<string>());
            }
            resume.score = 0.0;
            resumes.push_back(resume);
        }
    }
    return resumes;
}

void rank_resumes(vector<Resume>& resumes, const vector<string>& required_skills) {
    for (auto& resume : resumes) {
        int match_count = 0;
        for (const auto& skill : required_skills) {
            if (find(resume.skills.begin(), resume.skills.end(), skill) != resume.skills.end()) {
                match_count++;
            }
        }
        resume.score = (static_cast<double>(match_count) / required_skills.size()) * 100.0;
    }
    sort(resumes.begin(), resumes.end(), [](const Resume& a, const Resume& b) { return a.score > b.score; });
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cout << "Usage: resume_ranker <resumes_json_file> <required_skills_json_file>" << endl;
        return 1;
    }

    string resumes_file = argv[1];
    string required_skills_file = argv[2];

    vector<Resume> resumes = load_resumes_from_json(resumes_file);
    if (resumes.empty()) {
        cout << "No resumes found in JSON." << endl;
        return 1;
    }

    ifstream skills_file(required_skills_file);
    if (!skills_file.is_open()) {
        cout << "Failed to open required skills file." << endl;
        return 1;
    }
    json skills_json;
    skills_file >> skills_json;
    skills_file.close();

    vector<string> required_skills;
    if (skills_json.contains("skills") && skills_json["skills"].is_array()) {
        for (const auto& skill : skills_json["skills"]) {
            required_skills.push_back(skill.get<string>());
        }
    }

    rank_resumes(resumes, required_skills);

    cout << "Ranked Resumes:" << endl;
    for (const auto& resume : resumes) {
        cout << "Resume: " << resume.name << " (Score: " << resume.score << "%)" << endl;
    }

    return 0;
}
