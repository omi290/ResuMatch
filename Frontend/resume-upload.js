// Enhanced JavaScript for the resume upload functionality
document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const parsingPreview = document.getElementById('parsingPreview');
    const confirmBtn = document.getElementById('confirmBtn');
    const loadingIndicator = createLoadingIndicator();
    
    let selectedFile = null;
    
    // Add loading indicator to the page
    document.querySelector('.upload-container').appendChild(loadingIndicator);
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    // Handle selected files
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    }, false);
    
    // Setup help button
    const helpBtn = document.querySelector('.header-actions .btn:last-child');
    if (helpBtn) {
        helpBtn.addEventListener('click', function() {
            alert('Help Center: For assistance with job matching, resume generation, or resume uploads, please contact support@resumatch.com');
        });
    }
    
    // Setup confirm button
    if (confirmBtn) {
        confirmBtn.addEventListener('click', uploadResume);
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.style.borderColor = '#3498db';
        dropArea.style.backgroundColor = '#f0f8ff';
    }
    
    function unhighlight() {
        dropArea.style.borderColor = '#ccc';
        dropArea.style.backgroundColor = '#f9f9f9';
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        selectedFile = files.length ? files[0] : null;
        if (selectedFile) {
            console.log('File selected:', selectedFile.name, selectedFile.type, selectedFile.size);
            
            // Update the drop area to show the selected file
            dropArea.innerHTML = `
                <div class="drop-icon">📄</div>
                <h3 class="drop-text">${selectedFile.name}</h3>
                <p class="file-types">${formatBytes(selectedFile.size)} - Click to change</p>
            `;
            
            // Hide parsing preview until file is uploaded and parsed
            parsingPreview.style.display = 'none';
        }
    }
    
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    function createLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-indicator';
        loadingDiv.style.display = 'none';
        loadingDiv.innerHTML = `
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            ">
                <div style="
                    text-align: center;
                ">
                    <div style="
                        border: 5px solid #f3f3f3;
                        border-top: 5px solid #3498db;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        margin: 0 auto 15px auto;
                        animation: spin 2s linear infinite;
                    "></div>
                    <p>Processing your resume...</p>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        return loadingDiv;
    }
    
    function showLoading() {
        loadingIndicator.style.display = 'block';
    }
    
    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }
    
    async function uploadResume() {
        if (!selectedFile) {
            alert('Please select a file first!');
            return;
        }
        
        try {
            showLoading();
            console.log('Uploading file...');
            
            const formData = new FormData();
            formData.append('resume', selectedFile);
            
            // Determine server URL based on current environment
            // For local development, use localhost, for production use relative URL
            const serverUrl = window.location.hostname === 'localhost' || 
                             window.location.hostname === '127.0.0.1' 
                ? 'http://localhost:5000/upload-resume'
                : '/upload-resume';
            
            const response = await fetch(serverUrl, {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Upload failed (${response.status}): ${errorText}`);
            }
            
            const responseText = await response.text();
            console.log('Response received');
            
            // Try to parse the response as JSON
            let data;
            try {
                data = JSON.parse(responseText);
                console.log('Parsed data:', data);
            } catch (e) {
                console.error('Failed to parse response as JSON:', e);
                throw new Error('Server returned invalid JSON data');
            }
            
            // Check for error in the parsed data
            if (data.error) {
                throw new Error(`Server error: ${data.error}`);
            }
            
            // Display the parsed data
            displayParsedData(data);
            
            // Store the parsed data in localStorage for use in job matching
            localStorage.setItem('parsedResume', JSON.stringify(data));
            
            // Show success message
            alert('Resume uploaded and parsed successfully!');
            
            // Show the parsing preview section
            parsingPreview.style.display = 'block';
            
            // Optional: redirect to job matching page after successful upload
            // window.location.href = 'job-matching-page.html';
            
        } catch (error) {
            console.error('Upload error:', error);
            alert('Error: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayParsedData(data) {
        // Display skills
        const skillsList = document.getElementById('skillsList');
        if (data.skills && data.skills.length > 0) {
            skillsList.innerHTML = data.skills.map(skill => 
                `<span class="skill-tag">${skill}</span>`
            ).join('');
        } else {
            skillsList.innerHTML = '<p>No skills found</p>';
        }

        // Display experience
        const experienceList = document.getElementById('experienceList');
        if (data.experience && data.experience.length > 0) {
            experienceList.innerHTML = data.experience.map(exp => `
                <div class="experience-item">
                    <div class="experience-title">${exp.title || 'Position'}</div>
                    <div class="experience-company">${exp.company || 'Company'}</div>
                    <div class="experience-duration">${exp.duration || 'Duration'}</div>
                    ${exp.description ? `<div class="experience-description">${exp.description}</div>` : ''}
                </div>
            `).join('');
        } else {
            experienceList.innerHTML = '<p>No experience found</p>';
        }

        // Display education
        const educationList = document.getElementById('educationList');
        if (data.education && data.education.length > 0) {
            educationList.innerHTML = data.education.map(edu => `
                <div class="education-item">
                    <div class="education-title">${edu.degree || 'Degree'}</div>
                    <div class="education-school">${edu.school || 'School'}</div>
                    <div class="education-duration">${edu.duration || 'Duration'}</div>
                    ${edu.gpa ? `<div class="education-gpa">GPA: ${edu.gpa}</div>` : ''}
                </div>
            `).join('');
        } else {
            educationList.innerHTML = '<p>No education found</p>';
        }
        
        // Display certifications if available
        if (document.getElementById('certificationsList') && data.certifications && data.certifications.length > 0) {
            const certificationsList = document.getElementById('certificationsList');
            certificationsList.innerHTML = data.certifications.map(cert => `
                <div class="certification-item">
                    <div class="certification-name">${cert.name || 'Certification'}</div>
                    <div class="certification-issuer">${cert.issuer || ''}</div>
                    <div class="certification-date">${cert.date || ''}</div>
                </div>
            `).join('');
            document.getElementById('certificationsSection').style.display = 'block';
        } else if (document.getElementById('certificationsSection')) {
            document.getElementById('certificationsSection').style.display = 'none';
        }
        
        // Show the parsing preview section
        parsingPreview.style.display = 'block';
    }
});