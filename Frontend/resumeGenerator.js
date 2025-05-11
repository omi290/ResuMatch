function collectResumeData() {
    // Personal Info
    const name = document.querySelector('#personal-info-section .text-input:nth-child(2)').value;
    const email = document.querySelector('#personal-info-section .text-input:nth-child(4)').value;
    const phone = document.querySelector('#personal-info-section .text-input:nth-child(6)').value;

    // Education
    const educationEntries = document.querySelectorAll('.education-entry');
    const education = Array.from(educationEntries).map(entry => ({
        degree: entry.querySelector('.text-input:nth-child(2)').value,
        institution: entry.querySelector('.text-input:nth-child(4)').value,
        duration: entry.querySelector('.text-input:nth-child(6)').value,
        description: entry.querySelector('.textarea').value
    }));

    // Experience
    const experienceEntries = document.querySelectorAll('#experience-section .field-group');
    const experience = [];
    for (let i = 0; i < experienceEntries.length; i += 4) {
        experience.push({
            jobTitle: experienceEntries[i].querySelector('.text-input').value,
            company: experienceEntries[i + 1].querySelector('.text-input').value,
            duration: experienceEntries[i + 2].querySelector('.text-input').value,
            responsibilities: experienceEntries[i + 3].querySelector('.textarea').value
        });
    }

    // Skills
    const skills = Array.from(document.querySelectorAll('.skill-tag')).map(skill => ({
        name: skill.childNodes[0].textContent.trim(),
        matching: skill.classList.contains('matching-skill-tag')
    }));

    // Professional Summary
    const summary = document.querySelector('#summary-section .textarea').value;

    // Projects
    const projects = [{
        name: document.querySelector('#projects-section .text-input').value,
        description: document.querySelector('#projects-section .textarea').value
    }];

    // Template
    const template = document.querySelector('.template-card.selected')?.getAttribute('data-template') || 'professional';

    return {
        name,
        email,
        phone,
        education,
        experience,
        skills,
        summary,
        projects,
        template
    };
}

// Preview Resume
document.getElementById('previewBtn').addEventListener('click', function() {
    const resumeData = collectResumeData();
    const previewContent = document.querySelector('.resume-preview');
    
    let htmlContent = `
        <h2 style="text-align: center; color: #2c3e50;">${resumeData.name}</h2>
        <p style="text-align: center;">${resumeData.email} | ${resumeData.phone}</p>
        <hr style="margin: 10px 0;">
        
        <h3 style="color: #3498db;">Professional Summary</h3>
        <p>${resumeData.summary}</p>
        
        <h3 style="color: #3498db;">Experience</h3>
    `;
    
    resumeData.experience.forEach(exp => {
        htmlContent += `
            <p><strong>${exp.jobTitle}</strong></p>
            <p><i>${exp.company} | ${exp.duration}</i></p>
            <ul>
                ${exp.responsibilities.split('\n').map(res => `<li>${res.replace('•', '').trim()}</li>`).join('')}
            </ul>
        `;
    });
    
    htmlContent += `
        <h3 style="color: #3498db;">Education</h3>
    `;
    
    resumeData.education.forEach(edu => {
        htmlContent += `
            <p><strong>${edu.degree}</strong></p>
            <p><i>${edu.institution} | ${edu.duration}</i></p>
            <p>${edu.description}</p>
        `;
    });
    
    htmlContent += `
        <h3 style="color: #3498db;">Skills</h3>
        <ul>
            ${resumeData.skills.map(skill => `
                <li style="color: ${skill.matching ? '#0288d1' : 'black'}">${skill.name}</li>
            `).join('')}
        </ul>
        
        <h3 style="color: #3498db;">Projects</h3>
    `;
    
    resumeData.projects.forEach(proj => {
        htmlContent += `
            <p><strong>${proj.name}</strong></p>
            <p>${proj.description}</p>
        `;
    });
    
    previewContent.innerHTML = htmlContent;
    document.getElementById('previewModal').style.display = 'flex';
});