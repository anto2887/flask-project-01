class GroupCreator {
    constructor() {
        this.selectedTeams = new Set();
        this.VALID_PRIVACY_TYPES = ['PRIVATE', 'SEMI_PRIVATE'];
        this.initializeLeagueSelector();
        this.initializeForm();
    }

    initializeLeagueSelector() {
        const leagueInputs = document.querySelectorAll('input[name="league"]');
        leagueInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.loadTeams(e.target.value);
            });
        });
    }

    initializeForm() {
        const form = document.querySelector('form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Add validation for privacy type select
        const privacySelect = form.querySelector('select[name="privacy_type"]');
        privacySelect.addEventListener('change', (e) => {
            this.validatePrivacyType(e.target);
        });
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
        // Validate required fields
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

        if (this.selectedTeams.size === 0) {
            this.showError('Please select at least one team to track');
            return false;
        }

        return true;
    }

    async loadTeams(league) {
        try {
            const teamsContainer = document.getElementById('teamsContainer');
            teamsContainer.innerHTML = '<div class="p-4 text-center">Loading teams...</div>';

            const response = await fetch(`/api/teams/${encodeURIComponent(league)}`);
            if (!response.ok) {
                throw new Error('Failed to fetch teams');
            }

            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.teams)) {
                this.renderTeams(data.teams);
            } else {
                throw new Error(data.message || 'No teams found');
            }
        } catch (error) {
            console.error('Error loading teams:', error);
            this.showError(error.message || 'Failed to load teams');
            document.getElementById('teamsContainer').innerHTML = 
                '<div class="p-4 text-center text-red-600">Error loading teams. Please try again.</div>';
        }
    }

    renderTeams(teams) {
        const container = document.getElementById('teamsContainer');
        container.innerHTML = teams.map(team => `
            <div class="team-option flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50" data-team-id="${team.id}">
                <img src="${team.logo || team.team_logo}" alt="${team.name || team.team_name} logo" class="w-12 h-12 object-contain">
                <span class="ml-2">${team.name || team.team_name}</span>
                <input type="checkbox" 
                       name="tracked_teams" 
                       value="${team.id}"
                       class="hidden">
            </div>
        `).join('');

        container.querySelectorAll('.team-option').forEach(option => {
            option.addEventListener('click', () => this.toggleTeam(option));
        });
    }

    toggleTeam(element) {
        const teamId = element.dataset.teamId;
        const checkbox = element.querySelector('input');

        if (this.selectedTeams.has(teamId)) {
            this.selectedTeams.delete(teamId);
            element.classList.remove('selected', 'bg-blue-50', 'border-blue-500');
            checkbox.checked = false;
        } else {
            this.selectedTeams.add(teamId);
            element.classList.add('selected', 'bg-blue-50', 'border-blue-500');
            checkbox.checked = true;
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        if (!this.validateForm(e.target)) {
            return;
        }

        const submitButton = e.target.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Creating...';

        try {
            const formData = new FormData();
            const form = e.target;
            
            formData.append('name', form.querySelector('#name').value.trim());
            formData.append('league', form.querySelector('input[name="league"]:checked').value);
            formData.append('privacy_type', form.querySelector('select[name="privacy_type"]').value);
            formData.append('description', form.querySelector('#description').value.trim());
            
            this.selectedTeams.forEach(teamId => {
                formData.append('tracked_teams', teamId);
            });

            const response = await fetch('/group/create', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
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
        // Remove any existing error messages
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
    new GroupCreator();
});