document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const uploadResumeBtn = document.getElementById('uploadResumeBtn');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const parsingPreview = document.getElementById('parsingPreview');
    const previewContent = document.getElementById('previewContent');
    let uploadedFile = null;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false); // For global prevention
    });

    // Highlight drop area when item is dragged over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    // Handle file input change
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    // Allow clicking the drop area to open file input
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Handle upload button click (form submission)
    document.getElementById('resumeUploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        if (uploadedFile) {
            uploadFile(uploadedFile);
        } else {
            alert('Please select a file to upload.');
        }
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            uploadedFile = files[0];
            const fileType = uploadedFile.name.split('.').pop().toLowerCase();
            if (['pdf', 'docx'].includes(fileType)) {
                fileNameDisplay.textContent = `File Selected: ${uploadedFile.name}`;
                fileNameDisplay.style.display = 'block';
                uploadResumeBtn.disabled = false;
            } else {
                alert('Unsupported file type. Only PDF and DOCX are allowed.');
                resetUploadState();
            }
        } else {
            resetUploadState();
        }
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('resume', file);

        // Update UI for uploading
        uploadResumeBtn.disabled = true;
        uploadResumeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
        fileNameDisplay.textContent = 'Uploading...';

        try {
            const response = await fetch('/upload-resume', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Show parsed data
                displayParsedData(data);
                parsingPreview.style.display = 'block'; // Ensure preview section is visible
                uploadResumeBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Uploaded Successfully!';
                uploadResumeBtn.classList.remove('btn-primary');
                uploadResumeBtn.classList.add('btn-success');
                fileNameDisplay.textContent = `Resume uploaded: ${data.filename}`;
                // Optionally, disable button after success or redirect to dashboard
                // For now, we'll keep it as a success message.
                // setTimeout(() => { window.location.href = '/dashboard'; }, 2000);
            } else {
                if (response.status === 401) {
                    window.location.href = '/login';
                } else {
                    alert('Error uploading resume: ' + (data.error || 'Unknown error'));
                    resetUploadState();
                }
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('An error occurred during upload.');
            resetUploadState();
        }
    }

    function displayParsedData(data) {
        let html = '<div class="parsed-resume-data">';
        
        if (data) {
            const doc = data;
            
            // Personal Information
            html += `
                <div class="section">
                    <h4 class="section-title">Personal Information</h4>
                    <div class="section-content">
                        <p><strong>Name:</strong> ${doc.name || 'N/A'}</p>
                        <p><strong>Email:</strong> ${doc.email || 'N/A'}</p>
                        <p><strong>Phone:</strong> ${doc.phone || 'N/A'}</p>
                        <p><strong>Location:</strong> ${doc.location || 'N/A'}</p>
                    </div>
                </div>
            `;

            // Skills
            if (doc.skills && doc.skills.length > 0) {
                html += `
                    <div class="section">
                        <h4 class="section-title">Skills</h4>
                        <div class="section-content skills-list">
                            ${doc.skills.map(skill => `<span class="badge bg-primary">${skill}</span>`).join('')}
                        </div>
                    </div>
                `;
            }

            // Experience
            if (doc.experience && doc.experience.length > 0) {
                html += `
                    <div class="section">
                        <h4 class="section-title">Experience</h4>
                        <div class="section-content">
                            ${doc.experience.map(exp => `
                                <div class="experience-item">
                                    <h5>${exp.title || 'N/A'}</h5>
                                    <p class="text-muted mb-1">${exp.company || 'N/A'}</p>
                                    <p class="text-muted mb-0">${exp.duration || ''}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Education
            if (doc.education && doc.education.length > 0) {
                html += `
                    <div class="section">
                        <h4 class="section-title">Education</h4>
                        <div class="section-content">
                            ${doc.education.map(edu => `
                                <div class="education-item">
                                    <h5>${edu.degree || 'N/A'}</h5>
                                    <p class="text-muted mb-1">${edu.school || 'N/A'}</p>
                                    <p class="text-muted mb-0">${edu.year || ''}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Additional Sections
            if (doc.certifications && doc.certifications.length > 0) {
                html += `
                    <div class="section">
                        <h4 class="section-title">Certifications</h4>
                        <div class="section-content">
                            <p>${doc.certifications.join(', ')}</p>
                        </div>
                    </div>
                `;
            }
            if (doc.extracurricular && doc.extracurricular.length > 0) {
                html += `
                    <div class="section">
                        <h4 class="section-title">Extracurricular Activities</h4>
                        <div class="section-content">
                            <p>${doc.extracurricular.join(', ')}</p>
                        </div>
                    </div>
                `;
            }
        } else {
            html += '<p class="text-muted text-center">Failed to parse resume or no data available.</p>';
        }

        html += '</div>';
        previewContent.innerHTML = html;
    }

    function resetUploadState() {
        uploadedFile = null;
        fileInput.value = ''; // Clear the file input
        fileNameDisplay.style.display = 'none';
        fileNameDisplay.textContent = '';
        uploadResumeBtn.disabled = true;
        uploadResumeBtn.innerHTML = '<i class="fas fa-upload me-2"></i> Upload Resume';
        uploadResumeBtn.classList.remove('btn-success');
        uploadResumeBtn.classList.add('btn-primary');
        // Hide parsed data preview when resetting
        parsingPreview.style.display = 'none';
        previewContent.innerHTML = ''; // Clear preview content
    }

    // Initialize on page load (e.g., if a resume was already parsed and displayed)
    // This part assumes Flask passes `parsed_resume` to the template,
    // and the template itself renders the initial `parsing-preview` content if available.
    // If the page loads without `parsed_resume` (first visit or no resume),
    // the parsingPreview div will be `display: none;` by default (as per CSS).
    // No explicit JS initialization needed here for initial load if template handles it.
}); 