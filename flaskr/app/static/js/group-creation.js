class GroupCreator {
    constructor() {
        this.VALID_PRIVACY_TYPES = ['PRIVATE', 'SEMI_PRIVATE'];
        this.initializeForm();
        console.log('GroupCreator initialized');
    }

    initializeForm() {
        const form = document.querySelector('#createGroupForm');
        console.log('Found form:', form);

        if (!form) {
            console.error('Create group form not found!');
            return;
        }

        form.addEventListener('submit', (e) => {
            console.log('Form submission triggered');
            this.handleSubmit(e);
        });

        const privacySelect = form.querySelector('select[name="privacy_type"]');
        if (privacySelect) {
            privacySelect.addEventListener('change', (e) => {
                this.validatePrivacyType(e.target);
            });
        }
    }

    validatePrivacyType(select) {
        const value = select.value;
        if (!this.VALID_PRIVACY_TYPES.includes(value)) {
            select.setCustomValidity('Please select a valid privacy type');
            this.showError('Invalid privacy type selected');
            return false;
        }
        select.setCustomValidity('');
        return true;
    }

    validateForm(form) {
        console.log('Validating form...');
        
        const name = form.querySelector('#name').value.trim();
        if (!name) {
            this.showError('Group name is required');
            return false;
        }

        const league = form.querySelector('input[name="league"]:checked');
        if (!league) {
            this.showError('Please select a league');
            return false;
        }

        const privacyType = form.querySelector('select[name="privacy_type"]');
        if (!this.validatePrivacyType(privacyType)) {
            return false;
        }

        // Check for selected teams from React component
        const trackedTeams = form.querySelectorAll('input[name="tracked_teams"]');
        if (trackedTeams.length === 0) {
            this.showError('Please select at least one team to track');
            return false;
        }

        console.log('Form validation passed');
        return true;
    }

    async handleSubmit(e) {
        e.preventDefault();
        console.log('HandleSubmit called');

        if (!this.validateForm(e.target)) {
            console.log('Form validation failed');
            return;
        }

        const submitButton = e.target.querySelector('button[type="submit"]');
        console.log('Submit button:', submitButton);

        submitButton.disabled = true;
        submitButton.textContent = 'Creating...';

        try {
            const formData = new FormData(e.target);
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

            console.log('Form data:', {
                name: formData.get('name'),
                league: formData.get('league'),
                privacyType: formData.get('privacy_type'),
                description: formData.get('description'),
                trackedTeams: Array.from(formData.getAll('tracked_teams'))
            });

            console.log('Sending form data to server...');
            const response = await fetch('/group/create', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            console.log('Server response:', data);
            
            if (response.ok && data.status === 'success') {
                console.log('Redirecting to:', data.redirect_url);
                window.location.href = data.redirect_url;
            } else {
                throw new Error(data.message || 'Failed to create group');
            }
        } catch (error) {
            console.error('Error creating group:', error);
            this.showError(error.message || 'Failed to create group. Please try again.');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Create Group';
        }
    }

    showError(message) {
        const existingErrors = document.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message fixed bottom-4 right-4 bg-red-100 text-red-700 p-4 rounded shadow-lg z-50';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing GroupCreator');
    
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.error('CSRF token meta tag not found');
    } else {
        console.log('CSRF token meta tag found');
    }
    
    const groupCreator = new GroupCreator();
});