document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    const dashboardSections = document.querySelectorAll('.dashboard-section');

    function showSection(sectionId) {
        dashboardSections.forEach(section => {
            section.style.display = 'none';
        });
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
    }

    function setActiveLink(clickedLink) {
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
        });
        clickedLink.classList.add('active');
    }

    // Handle sidebar navigation clicks
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Only prevent default and handle internally for hash links
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1); // Remove '#'
                showSection(targetId);
                setActiveLink(this);
                // Update URL hash without reloading page for better user experience
                history.pushState(null, '', `#${targetId}`);
            } else if (this.getAttribute('href') === '/profile') {
                // Allow direct navigation for /profile and /settings
                window.location.href = this.getAttribute('href');
            } else if (this.getAttribute('href') === '/settings') {
                window.location.href = this.getAttribute('href');
            }
        });
    });

    // Show the initial section based on URL hash or default to 'overview'
    const initialSectionId = window.location.hash ? window.location.hash.substring(1) : 'overview';
    showSection(initialSectionId);
    const initialActiveLink = document.querySelector(`.sidebar-nav a[href="#${initialSectionId}"]`);
    if (initialActiveLink) {
        setActiveLink(initialActiveLink);
    }

    // Placeholder functions for job actions
    window.applyJob = function(jobId) {
        alert('Applying for job: ' + jobId);
        // Implement actual job application logic here
    };

    window.saveJob = function(jobId) {
        alert('Saving job: ' + jobId);
        // Implement actual job saving logic here
    };

    window.viewParsedResume = function() {
        alert('Viewing parsed resume - implement actual view logic.');
    };

    window.refreshDashboard = function() {
        window.location.reload();
    };

    // Global notification function (defined once within DOMContentLoaded)
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});

// Removed redundant global functions that were moved into DOMContentLoaded or are no longer needed.
// For example, loadDashboard(), setupEventListeners(), handleResumeUpload().

// These utility functions might still be useful globally
function getToken() {
    return localStorage.getItem('token');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function handleJobSearch(event) {
    // Implementation for job search if needed
    console.log('Job search triggered:', event.target.value);
}

async function handleStatusFilter(event) {
    // Implementation for status filter if needed
    console.log('Status filter triggered:', event.target.value);
}

// Resume Management Functions
async function updateResume(resumeId) {
    // Redirect to resume update page or open modal
    window.location.href = `/resume/update/${resumeId}`;
}

async function viewAnalysis(resumeId) {
    try {
        const response = await fetch(`/api/seeker/resume/${resumeId}/analysis`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            // Display analysis in a modal or redirect to analysis page
            console.log(data);
        } else {
            showNotification(data.error || 'Failed to load analysis', 'error');
        }
    } catch (error) {
        showNotification('Error loading analysis', 'error');
        console.error('Error:', error);
    }
} 