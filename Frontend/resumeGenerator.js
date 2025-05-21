
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
            yPos += 5;
        });
        
        yPos += 5;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Experience', 20, yPos);
        yPos += 8;
        
        data.experience.forEach(exp => {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.text(exp.jobTitle, 20, yPos);
            yPos += 5;
            
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(10);
            doc.text(`${exp.company} | ${exp.duration}`, 20, yPos);
            yPos += 5;
            
            doc.setFont('helvetica', 'normal');
            
            const responsibilities = exp.responsibilities.split('\n');
            responsibilities.forEach(resp => {
                if (resp.trim()) {
                    const cleanedResp = resp.replace('•', '').trim();
                    const splitResp = doc.splitTextToSize(`• ${cleanedResp}`, pageWidth - 45);
                    doc.text(splitResp, 25, yPos);
                    yPos += splitResp.length * 5;
                }
            });
            
            yPos += 5;
        });
        
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Education', 20, yPos);
        yPos += 8;
        
        data.education.forEach(edu => {
            if (yPos > 250) {
                doc.addPage();
                yPos = 20;
            }
            
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.text(edu.degree, 20, yPos);
            yPos += 5;
            
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(10);
            doc.text(`${edu.institution} | ${edu.duration}`, 20, yPos);
            yPos += 5;
            
            doc.setFont('helvetica', 'normal');
            const splitDesc = doc.splitTextToSize(edu.description, pageWidth - 40);
            doc.text(splitDesc, 20, yPos);
            yPos += splitDesc.length * 5 + 5;
        });
        
        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }
        
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.text('Projects', 20, yPos);
        yPos += 8;
        
        data.projects.forEach(proj => {
            if (proj.name) {
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(12);
                doc.text(proj.name, 20, yPos);
                yPos += 5;
                
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(10);
                const splitProjDesc = doc.splitTextToSize(proj.description, pageWidth - 40);
                doc.text(splitProjDesc, 20, yPos);
                yPos += splitProjDesc.length * 5 + 5;
            }
        });
        
        const pdfBlob = doc.output('blob');
        downloadPDF(pdfBlob, 'resume.pdf');
        
    } catch (error) {
        console.error('Error generating PDF client-side:', error);
        alert('Could not generate PDF. Please try again or check if jsPDF is properly loaded.');
    }
}

function downloadPDF(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 100);
}

function ensureJsPdfLoaded() {
    return new Promise((resolve, reject) => {
        if (window.jspdf || window.jsPDF) {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        script.onload = resolve;
        script.onerror = () => reject(new Error('Failed to load jsPDF library'));
        document.head.appendChild(script);
    });
}

document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Content Loaded - Setting up event listeners');
    
    try {
        await ensureJsPdfLoaded();
        console.log('jsPDF loaded successfully');
    } catch (err) {
        console.warn('Could not load jsPDF library:', err);
    }

    const generateBtn = document.getElementById('generateBtn');
    const modalDownloadBtn = document.querySelector('.modal-actions .btn-primary');
 
    if (!generateBtn) {
        console.error('Generate button not found in the DOM');
    } else {
        const newGenerateBtn = generateBtn.cloneNode(true);
        generateBtn.parentNode.replaceChild(newGenerateBtn, generateBtn);
        console.log('Adding click event to Generate button');
        newGenerateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Generate button clicked');
            generateResumePDF();
        });
    }
    
    if (!modalDownloadBtn) {
        console.error('Modal download button not found in the DOM');
    } else {
        const newModalDownloadBtn = modalDownloadBtn.cloneNode(true);
        modalDownloadBtn.parentNode.replaceChild(newModalDownloadBtn, modalDownloadBtn);
        console.log('Adding click event to Modal Download button');
        newModalDownloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Modal Download button clicked');
            generateResumePDF();
        });
    }
    
    const modalCloseBtn = document.querySelector('.modal-actions .btn-secondary');
    if (modalCloseBtn) {
        const newModalCloseBtn = modalCloseBtn.cloneNode(true);
        modalCloseBtn.parentNode.replaceChild(newModalCloseBtn, modalCloseBtn);
        newModalCloseBtn.addEventListener('click', function() {
            const previewModal = document.getElementById('previewModal');
            if (previewModal) {
                previewModal.style.display = 'none';
            }
        });
    }
    
    console.log('Event listeners setup completed');
});