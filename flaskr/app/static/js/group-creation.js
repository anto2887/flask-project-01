class GroupCreator {
    constructor() {
        this.selectedTeams = new Set();
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
    }

    async loadTeams(league) {
        try {
            const response = await fetch(`/api/teams/${league}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const teams = await response.json();
            
            if (Array.isArray(teams) && teams.length > 0) {
                this.renderTeams(teams);
            } else {
                throw new Error('No teams found');
            }
        } catch (error) {
            console.error('Error loading teams:', error);
            this.showError('Failed to load teams');
        }
    }

    renderTeams(teams) {
        const container = document.getElementById('teamsContainer');
        container.innerHTML = teams.map(team => `
            <div class="team-option flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50" data-team-id="${team.id}">
                <img src="${team.logo}" alt="${team.name} logo" class="w-12 h-12 object-contain">
                <span class="ml-2">${team.name}</span>
                <input type="checkbox" 
                       name="tracked_teams" 
                       value="${team.id}"
                       class="hidden">
            </div>
        `).join('');

        // Add click handlers
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

        if (this.selectedTeams.size === 0) {
            this.showError('Please select at least one team to track');
            return;
        }

        const submitButton = e.target.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Creating...';

        try {
            const formData = new FormData();
            const form = e.target;
            
            // Append all form fields
            formData.append('name', form.querySelector('#name').value);
            formData.append('league', form.querySelector('input[name="league"]:checked').value);
            formData.append('privacy_type', form.querySelector('select[name="privacy_type"]').value);
            formData.append('description', form.querySelector('#description').value || '');
            
            // Append each selected team ID
            this.selectedTeams.forEach(teamId => {
                formData.append('tracked_teams', teamId);
            });

            console.log('Submitting form with data:', {
                name: form.querySelector('#name').value,
                league: form.querySelector('input[name="league"]:checked').value,
                privacy_type: form.querySelector('select[name="privacy_type"]').value,
                description: form.querySelector('#description').value,
                tracked_teams: Array.from(this.selectedTeams)
            });

            const response = await fetch('/group/create', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            console.log('Server response:', data);
            
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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-100 text-red-700 p-4 rounded shadow-lg z-50';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    new GroupCreator();
});