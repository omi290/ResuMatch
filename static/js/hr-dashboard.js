document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('.sidebar nav ul li a');
    const dashboardSections = document.querySelectorAll('.section');

    function showSection(sectionId) {
        dashboardSections.forEach(section => {
            section.classList.remove('active');
        });
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }
    }

    function setActiveLink(clickedLink) {
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
        });
        clickedLink.classList.add('active');
    }

    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1); // Remove '#' from href
            showSection(targetId);
            setActiveLink(this);
        });
    });

    // Show the 'Jobs' section by default on page load
    const initialSection = window.location.hash ? window.location.hash.substring(1) : 'jobs';
    showSection(initialSection);
    const activeLink = document.querySelector(`.sidebar nav ul li a[href="#${initialSection}"]`);
    if (activeLink) {
        setActiveLink(activeLink);
    }

    // Fetch and render jobs
    async function fetchJobs() {
        try {
            const response = await fetch('/hr/jobs');
            if (!response.ok) throw new Error('Failed to fetch jobs');
            const jobs = await response.json();
            renderJobs(jobs);
        } catch (error) {
            console.error(error);
        }
    }

    function renderJobs(jobs) {
        const jobsList = document.getElementById('jobsList');
        jobsList.innerHTML = '';
        jobs.forEach(job => {
            const jobCard = document.createElement('div');
            jobCard.className = 'job-card';
            jobCard.innerHTML = `
                <h3>${job.title}</h3>
                <p class="company">${job.company}</p>
                <p class="location">${job.location || ''}</p>
                <p class="type">${job.jobType || ''}</p>
                <div class="actions">
                    <button class="btn btn-primary view-matches-btn" data-job-id="${job._id}">View Matches</button>
                    <button class="btn btn-secondary edit-job-btn" data-job-id="${job._id}">Edit</button>
                </div>
            `;
            jobsList.appendChild(jobCard);
        });

        // Add event listeners for View Matches buttons
        const viewMatchesButtons = document.querySelectorAll('.view-matches-btn');
        viewMatchesButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const jobId = this.dataset.jobId;
                if (!jobId) {
                    alert('Job ID is missing. Cannot fetch matches.');
                    return;
                }
                try {
                    // First, generate matches by calling find-matches endpoint
                    const generateResponse = await fetch(`/hr/job/${jobId}/find-matches`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    if (!generateResponse.ok) throw new Error('Failed to generate matches');
                    // Then fetch and render matches
                    await fetchAndRenderMatches(jobId);
                    showSection('matches');
                    setActiveLink(document.querySelector('.sidebar nav ul li a[href="#matches"]'));
                } catch (error) {
                    alert('Error fetching matches: ' + error.message);
                }
            });
        });

        // Add event listeners for Edit buttons (implement as needed)
    }

    // Fetch and render matches for a job
    async function fetchAndRenderMatches(jobId) {
        try {
            const response = await fetch(`/hr/job/${jobId}/matches`);
            if (!response.ok) throw new Error('Failed to fetch matches');
            const matches = await response.json();
            renderMatches(matches);
        } catch (error) {
            console.error(error);
        }
    }

    function renderMatches(matches) {
        const matchesList = document.getElementById('matchesList');
        matchesList.innerHTML = '';
        if (matches.length === 0) {
            matchesList.innerHTML = '<p>No matches found for this job.</p>';
            return;
        }
        matches.forEach(match => {
            const matchCard = document.createElement('div');
            matchCard.className = 'match-card';
            matchCard.innerHTML = `
                <h4>${match.resume_name || match.seeker_name || 'Candidate'}</h4>
                <p class="match-score">Match: ${match.match_score}%</p>
                <p class="status">Status: ${match.status || ''}</p>
                <p>Email: ${match.seeker_email || ''}</p>
                <p>Phone: ${match.seeker_phone || ''}</p>
                <p>Location: ${match.seeker_location || ''}</p>
                <div class="actions">
                    <button class="btn btn-primary view-candidate-btn" data-resume-id="${match.resume_id}">View</button>
                </div>
            `;
            matchesList.appendChild(matchCard);
        });

        // Add event listeners for View Candidate buttons
        const viewCandidateButtons = document.querySelectorAll('.view-candidate-btn');
        viewCandidateButtons.forEach(button => {
            button.addEventListener('click', function() {
                const resumeId = this.dataset.resumeId;
                if (resumeId) {
                    window.location.href = `/candidate/${resumeId}`;
                }
            });
        });
    }

    // Add event listeners for View Top Matches buttons in posted jobs
    document.addEventListener('click', async function(e) {
        if (e.target && e.target.classList.contains('view-top-matches-btn')) {
            const jobId = e.target.getAttribute('data-job-id');
            if (!jobId) {
                alert('Job ID is missing. Cannot fetch top matches.');
                return;
            }
            try {
                // Fetch top matches for this job
                const response = await fetch(`/hr/job/${jobId}/top-matches`);
                if (!response.ok) throw new Error('Failed to fetch top matches');
                const matches = await response.json();
                renderMatches(matches);
                showSection('matches');
                setActiveLink(document.querySelector('.sidebar nav ul li a[href="#matches"]'));
            } catch (error) {
                alert('Error fetching top matches: ' + error.message);
            }
        }
    });

    // Initial fetch of jobs
    fetchJobs();
});
