function collectResumeData() {
    const personalInfoInputs = document.querySelectorAll('#personal-info-section .text-input');
    const name = personalInfoInputs[0]?.value.trim() || '';
    const email = personalInfoInputs[1]?.value.trim() || '';
    const phone = personalInfoInputs[2]?.value.trim() || '';

    const educationNodes = document.querySelectorAll('.education-entry');
    const education = Array.from(educationNodes).map(entry => {
        const inputs = entry.querySelectorAll('.text-input');
        const textarea = entry.querySelector('.textarea');
        return {
            degree: inputs[0]?.value.trim() || '',
            institution: inputs[1]?.value.trim() || '',
            duration: inputs[2]?.value.trim() || '',
            description: textarea?.value.trim() || ''
        };
    });

    const experienceInputs = document.querySelectorAll('#experience-section .text-input');
    const jobTitle = experienceInputs[0]?.value.trim() || '';
    const company = experienceInputs[1]?.value.trim() || '';
    const jobDuration = experienceInputs[2]?.value.trim() || '';
    const responsibilities = document.querySelector('#experience-section .textarea')?.value.trim() || '';

    const skillTags = document.querySelectorAll('.skills-container .skill-tag');
    const skills = Array.from(skillTags).map(tag => {
        const text = tag.textContent.replace('×', '').trim();
        const isMatching = tag.classList.contains('matching-skill-tag');
        return {
            name: text,
            matching: isMatching
        };
    });

    const summary = document.querySelector('#summary-section .textarea')?.value.trim() || '';

    const projectInputs = document.querySelectorAll('#projects-section .text-input');
    const projectName = projectInputs[0]?.value.trim() || '';
    const projectDescription = document.querySelector('#projects-section .textarea')?.value.trim() || '';

    const selectedTemplateCard = document.querySelector('.template-card.selected');
    const template = selectedTemplateCard ? selectedTemplateCard.getAttribute('data-template') : 'professional';

    return {
        name,
        email,
        phone,
        summary,
        template,
        education,
        experience: [{
            jobTitle,
            company,
            duration: jobDuration,
            responsibilities
        }],
        skills,
        projects: [{
            name: projectName,
            description: projectDescription
        }]
    };
}

document.getElementById('previewBtn')?.addEventListener('click', function() {
    const previewModal = document.getElementById('previewModal');
    if (!previewModal) {
        console.error('Preview modal not found in the DOM');
        return;
    }

    const resumeData = collectResumeData();
    const previewContent = document.querySelector('.resume-preview');
    if (!previewContent) {
        console.error('Resume preview element not found in the DOM');
        return;
    }

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

    htmlContent += `<h3 style="color: #3498db;">Education</h3>`;

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
    previewModal.style.display = 'flex';
});

async function generateResumePDF() {
    console.log("Generate PDF function called");
    const resumeData = collectResumeData();
    console.log("Resume data:", resumeData);

    try {
        showLoadingIndicator();

        const response = await fetch('http://localhost:5000/generate-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resumeData),
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) {
            console.warn(`Server request failed with status: ${response.status}`);
            throw new Error(`Server request failed with status: ${response.status}`);
        }

        const blob = await response.blob();
        downloadPDF(blob, 'resume.pdf');
        hideLoadingIndicator();

    } catch (error) {
        console.warn('Server-side generation failed:', error);
        console.log('Falling back to client-side PDF generation');
        hideLoadingIndicator();

        generateClientSidePDF(resumeData);
    }
}

function showLoadingIndicator() {
    if (document.getElementById('pdf-loading-indicator')) return;

    const indicator = document.createElement('div');
    indicator.id = 'pdf-loading-indicator';
    indicator.style.position = 'fixed';
    indicator.style.top = '50%';
    indicator.style.left = '50%';
    indicator.style.transform = 'translate(-50%, -50%)';
    indicator.style.background = 'rgba(255, 255, 255, 0.9)';
    indicator.style.padding = '20px';
    indicator.style.borderRadius = '5px';
    indicator.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    indicator.style.zIndex = '9999';
    indicator.innerHTML = 'Generating PDF...';

    document.body.appendChild(indicator);
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('pdf-loading-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function generateClientSidePDF(data) {
    try {
        if (typeof window.jspdf === 'undefined') {
            console.error('jsPDF is not loaded. Make sure to include the library in your HTML.');
            alert('PDF generation library is not loaded. Please check your internet connection and refresh the page.');
            return;
        }

        let jsPDF;
        if (window.jspdf && window.jspdf.jsPDF) {
            jsPDF = window.jspdf.jsPDF;
        } else if (window.jsPDF) {

            jsPDF = window.jsPDF;
        } else {
            console.error('Could not find jsPDF constructor');
            alert('PDF generation failed. Please try again later.');
            return;
        }

        const doc = new jsPDF();

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(18);

        const nameWidth = doc.getStringUnitWidth(data.name) * 18 / doc.internal.scaleFactor;
        const pageWidth = doc.internal.pageSize.getWidth();
        doc.text(data.name, (pageWidth - nameWidth) / 2, 20);

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        const contactInfo = `${data.email} | ${data.phone}`;
        const contactWidth = doc.getStringUnitWidth(contactInfo) * 10 / doc.internal.scaleFactor;
        doc.text(contactInfo, (pageWidth - contactWidth) / 2, 28);

        doc.setLineWidth(0.5);
        doc.line(20, 32, pageWidth - 20, 32);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Professional Summary', 20, 40);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);

        const splitSummary = doc.splitTextToSize(data.summary, pageWidth - 40);
        doc.text(splitSummary, 20, 48);

        let yPos = 48 + (splitSummary.length * 5);

        yPos += 10;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Skills', 20, yPos);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        yPos += 8;

        data.skills.forEach(skill => {
            doc.text(`• ${skill.name}`, 25, yPos);
            yPos += 7;
        });

        yPos += 10;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Experience', 20, yPos);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);

        data.experience.forEach(exp => {
            yPos += 8;
            doc.text(`${exp.jobTitle}`, 20, yPos);
            yPos += 5;
            doc.text(`${exp.company} | ${exp.duration}`, 20, yPos);
            yPos += 5;
            const splitResponsibilities = doc.splitTextToSize(exp.responsibilities, pageWidth - 40);
            doc.text(splitResponsibilities, 25, yPos);
            yPos += (splitResponsibilities.length * 5) + 5;
        });

        yPos += 10;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Education', 20, yPos);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);

        data.education.forEach(edu => {
            yPos += 8;
            doc.text(`${edu.degree}`, 20, yPos);
            yPos += 5;
            doc.text(`${edu.institution} | ${edu.duration}`, 20, yPos);
            yPos += 5;
            const splitDescription = doc.splitTextToSize(edu.description, pageWidth - 40);
            doc.text(splitDescription, 25, yPos);
            yPos += (splitDescription.length * 5) + 5;
        });

        yPos += 10;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Projects', 20, yPos);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);

        data.projects.forEach(proj => {
            yPos += 8;
            doc.text(`${proj.name}`, 20, yPos);
            yPos += 5;
            const splitProjDescription = doc.splitTextToSize(proj.description, pageWidth - 40);
            doc.text(splitProjDescription, 25, yPos);
            yPos += (splitProjDescription.length * 5) + 5;
        });

        const pdfBlob = doc.output('blob');
        downloadPDF(pdfBlob, 'resume.pdf');

    } catch (error) {
        console.error('Error generating client-side PDF:', error);
        alert('Failed to generate PDF. Please try again.');
    }
}

function downloadPDF(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}

function ensureJsPdfLoaded() {
    // This function can be used to ensure jsPDF is available before use.
    // In a production app, you might use dynamic imports or a module loader.
}

document.addEventListener('DOMContentLoaded', function() {
    const sectionItems = document.querySelectorAll('.section-item');
    const editorFields = document.querySelectorAll('.section-fields');

    sectionItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all section items
            sectionItems.forEach(s => s.classList.remove('active'));
            // Add active class to the clicked section item
            this.classList.add('active');

            // Hide all editor fields
            editorFields.forEach(field => field.style.display = 'none');

            // Show the corresponding editor field
            const targetSection = this.getAttribute('data-section') + '-section';
            document.getElementById(targetSection).style.display = 'block';
        });
    });

    const resumePreviewIframe = document.getElementById('resumePreview');

    // Function to update the resume preview iframe
    function updatePreviewPane(templateId) {
        let previewHtml = '';
        switch (templateId) {
            case 'professional':
                previewHtml = `
                    <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
                        <h3 style="color: #2c3e50;">Professional Template</h3>
                        <p style="color: #6c757d;">A clean and traditional layout.</p>
                        <div style="width: 100px; height: 120px; border: 1px solid #ccc; margin: 10px auto; background-color: #eee;"></div>
                    </div>`;
                break;
            case 'modern':
                previewHtml = `
                    <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
                        <h3 style="color: #3498db;">Modern Template</h3>
                        <p style="color: #6c757d;">A modern design.</p>
                        <div style="width: 150px; height: 120px; border: 1px solid #ccc; margin: 10px auto; background-color: #eee;"></div>
                    </div>`;
                break;
            case 'minimalist':
                previewHtml = `
                    <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
                        <div style="background-color: #3498db; color: white; padding: 10px 0; margin-bottom: 20px;"><h3>Minimalist</h3></div>
                        <h3 style="color: #2c3e50;">Minimalist Template</h3>
                        <p style="color: #6c757d;">Simple and elegant.</p>
                    </div>`;
                break;
            default:
                previewHtml = '<p style="text-align: center; color: #6c757d;">Select a template and fill in details to see a preview.</p>';
        }
        if (resumePreviewIframe) {
            resumePreviewIframe.srcdoc = previewHtml;
        }
    }

    // Function to fetch and display templates
    async function fetchAndDisplayTemplates() {
        const templatesGrid = document.querySelector('.templates-grid');
        const templateLoadStatus = document.getElementById('templateLoadStatus');
        if (!templatesGrid || !templateLoadStatus) {
            console.error('Templates grid or load status element not found.');
            return;
        }

        try {
            templateLoadStatus.textContent = 'Loading templates...';
            const response = await fetch('/get-resume-templates');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const templates = await response.json();
            console.log('Fetched templates:', templates);

            templatesGrid.innerHTML = ''; // Clear existing content

            templates.forEach(template => {
                const templateCard = document.createElement('div');
                templateCard.classList.add('template-card');
                templateCard.setAttribute('data-template', template.id);
                templateCard.innerHTML = `
                    <div class="template-preview">
                        <img src="${template.image_url}" alt="${template.name} Preview" style="max-width: 100%; max-height: 120px; object-fit: contain; border-radius: 4px;">
                        <p class="mt-2">${template.name} Preview</p>
                    </div>
                    <div class="template-name">${template.name}</div>
                `;
                templatesGrid.appendChild(templateCard);

                templateCard.addEventListener('click', function() {
                    // Remove 'selected' class from all template cards
                    document.querySelectorAll('.template-card').forEach(card => {
                        card.classList.remove('selected');
                    });
                    // Add 'selected' class to the clicked template card
                    this.classList.add('selected');
                    console.log(`Template selected: ${this.getAttribute('data-template')}`);
                    updatePreviewPane(this.getAttribute('data-template')); // Update the preview pane
                });
            });

            templateLoadStatus.textContent = ''; // Clear status on success

            // Select the first template by default if any exist and update preview
            if (templates.length > 0) {
                const firstTemplateCard = document.querySelector('.templates-grid .template-card');
                firstTemplateCard.classList.add('selected');
                updatePreviewPane(firstTemplateCard.getAttribute('data-template'));
            }

        } catch (error) {
            console.error('Error fetching templates:', error);
            templateLoadStatus.textContent = 'Failed to load templates. Please try again later.';
        }
    }

    // Call the function to fetch and display templates when the DOM is loaded
    fetchAndDisplayTemplates();

    // Add event listener for the Generate PDF button
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Generate PDF button clicked');
            generateResumePDF();
        });
    }

    // New code to fetch and pre-fill user profile data
    async function fetchAndPrefillProfile() {
        try {
            const response = await fetch('/get-user-profile');
            if (!response.ok) throw new Error('Failed to fetch user profile');
            const profile = await response.json();

            // Pre-fill form fields
            document.getElementById('fullName').value = profile.full_name || '';
            document.getElementById('email').value = profile.email || '';
            document.getElementById('phone').value = profile.phone || '';
            document.getElementById('linkedin').value = profile.linkedin || '';
            document.getElementById('portfolio').value = profile.portfolio || '';
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }
    }

    // Call pre-fill function on DOMContentLoaded
    fetchAndPrefillProfile();
});
