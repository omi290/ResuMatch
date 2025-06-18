document.addEventListener('DOMContentLoaded', function() {
    const postJobForm = document.getElementById('postJobForm');
    const skillInput = document.getElementById('skillInput');
    const skillTags = document.getElementById('skillTags');
    let skills = [];

    // Handle skill input
    skillInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const skill = skillInput.value.trim();
            if (skill && !skills.includes(skill)) {
                skills.push(skill);
                updateSkillTags();
                skillInput.value = '';
                showNotification(`Added skill: ${skill}`, 'success');
            } else if (skills.includes(skill)) {
                showNotification('Skill already added!', 'warning');
            }
        }
    });

    // Update skill tags display
    function updateSkillTags() {
        skillTags.innerHTML = skills.map(skill => `
            <span class="skill-tag">
                ${skill}
                <span class="remove-tag" onclick="removeSkill('${skill}')">&times;</span>
            </span>
        `).join('');
        
        // Update the skills count display
        const skillsCount = document.getElementById('skillsCount');
        if (skillsCount) {
            skillsCount.textContent = skills.length;
        }
    }

    // Remove skill
    window.removeSkill = function(skill) {
        skills = skills.filter(s => s !== skill);
        updateSkillTags();
        showNotification(`Removed skill: ${skill}`, 'info');
    };

    // Handle form submission
    postJobForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate required fields
        const title = document.getElementById('title').value.trim();
        const company = document.getElementById('company').value.trim();
        const description = document.getElementById('description').value.trim();
        
        if (!title || !company || !description) {
            showNotification('Please fill in all required fields', 'error');
            return;
        }

        if (skills.length === 0) {
            showNotification('Please add at least one required skill', 'error');
            return;
        }

        const formData = {
            title: title,
            company: company,
            description: description,
            requirements: skills.join(', '),
            location: document.getElementById('location').value,
            job_type: document.getElementById('type').value,
            department: document.getElementById('department').value,
            experience_level: document.getElementById('experience').value,
            salary_range: {
                min: document.getElementById('salary-min').value,
                max: document.getElementById('salary-max').value
            }
        };

        // Show loading state
        const submitBtn = postJobForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Posting Job...';

        try {
            const response = await fetch('/hr/post-job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                showNotification(`Job posted successfully! Skills saved: ${skills.join(', ')}`, 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                showNotification(data.error || 'Failed to post job', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error posting job. Please try again.', 'error');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});

// Notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} notification`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style); 