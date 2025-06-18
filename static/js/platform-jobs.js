document.addEventListener('DOMContentLoaded', function () {
    const jobListingsContainer = document.getElementById('jobListingsContainer');

    if (jobListingsContainer) {
        jobListingsContainer.addEventListener('click', async function (event) {
            const applyButton = event.target.closest('.apply-job-btn');
            if (applyButton) {
                const jobId = applyButton.dataset.jobId;
                if (jobId) {
                    // Disable the button to prevent multiple clicks
                    applyButton.disabled = true;
                    applyButton.textContent = 'Applying...';

                    try {
                        const response = await fetch('/apply-job', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ job_id: jobId.toString() }),
                        });

                        const result = await response.json();

                        if (response.ok) {
                            alert(result.message || 'Application submitted successfully!');
                            // Optionally, change button text or style on success
                            applyButton.textContent = 'Applied!';
                            applyButton.classList.remove('btn-primary');
                            applyButton.classList.add('btn-success');
                            // Redirect to dashboard's applied jobs section for both new and already-applied
                            if (result.message && result.message.toLowerCase().includes('already applied')) {
                                window.location.href = '/dashboard#applied-jobs';
                            } else {
                                window.location.href = '/dashboard#applied-jobs';
                            }
                        } else {
                            alert(result.error || 'Failed to submit application.');
                            // Re-enable button on error
                            applyButton.disabled = false;
                            applyButton.textContent = 'Apply Now';
                        }
                    } catch (error) {
                        console.error('Error during application submission:', error);
                        alert('An unexpected error occurred. Please try again.');
                        // Re-enable button on fetch error
                        applyButton.disabled = false;
                        applyButton.textContent = 'Apply Now';
                    }
                }
            }
        });
    }

    // Existing filter and search logic (if any) could be added here later or kept separate
    // For now, focus on apply button functionality.
}); 