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

    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1); // Remove '#' from href
            showSection(targetId);
            setActiveLink(this);
        });
    });

    // Show the 'Overview' section by default on page load
    const initialSection = window.location.hash ? window.location.hash.substring(1) : 'overview';
    showSection(initialSection);
    const activeLink = document.querySelector(`.sidebar-nav a[href="#${initialSection}"]`);
    if (activeLink) {
        setActiveLink(activeLink);
    }

    // Handle View Candidate button clicks
    const viewCandidateButtons = document.querySelectorAll('.view-candidate-btn');
    viewCandidateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const applicationId = this.dataset.applicationId;
            if (applicationId) {
                window.location.href = `/view-candidate/${applicationId}`;
            }
        });
    });
}); 