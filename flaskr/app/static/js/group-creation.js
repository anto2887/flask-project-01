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

            console.log('Fetching teams for league:', league);
            const response = await fetch(`/api/teams/${encodeURIComponent(league)}`);
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Response data:', data);

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch teams');
            }

            if (data.status === 'success' && Array.isArray(data.teams)) {
                console.log('Teams array:', data.teams);
                if (data.teams.length === 0) {
                    throw new Error('No teams available for this league');
                }
                // Log a sample team to verify structure
                if (data.teams.length > 0) {
                    console.log('Sample team structure:', data.teams[0]);
                }
                this.renderTeams(data.teams);
            } else {
                console.error('Invalid data structure:', data);
                throw new Error('Invalid response format from server');
            }
        } catch (error) {
            console.error('Error loading teams:', error);
            this.showError(error.message || 'Failed to load teams');
            document.getElementById('teamsContainer').innerHTML = 
                '<div class="p-4 text-center text-red-600">Error loading teams. Please try again.</div>';
        }
    }

    renderTeams(teams) {
        try {
            console.log('Starting team rendering, number of teams:', teams.length);
            const container = document.getElementById('teamsContainer');
            
            const teamElements = teams.map(team => {
                // Log individual team data for debugging
                console.log('Processing team:', team);
                
                const teamId = team.id;
                const teamName = team.name || team.team_name;
                const teamLogo = team.logo || team.team_logo;
                
                if (!teamId || !teamName) {
                    console.error('Invalid team data:', team);
                    return ''; // Skip invalid teams
                }

                return `
                    <div class="team-option flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50" data-team-id="${teamId}">
                        <img src="${teamLogo || '/static/pictures/default-team.png'}" 
                             alt="${teamName} logo" 
                             class="w-12 h-12 object-contain"
                             onerror="this.src='/static/pictures/default-team.png'">
                        <span class="ml-2">${teamName}</span>
                        <input type="checkbox" 
                               name="tracked_teams" 
                               value="${teamId}"
                               class="hidden">
                    </div>
                `;
            }).filter(Boolean).join('');

            container.innerHTML = teamElements || '<div class="p-4 text-center">No teams available</div>';

            container.querySelectorAll('.team-option').forEach(option => {
                option.addEventListener('click', () => this.toggleTeam(option));
            });
            
            console.log('Team rendering complete');
        } catch (error) {
            console.error('Error in renderTeams:', error);
            throw error;
        }
    }

    toggleTeam(element) {
        try {
            const teamId = element.dataset.teamId;
            if (!teamId) {
                console.error('No team ID found on element:', element);
                return;
            }

            const checkbox = element.querySelector('input');
            if (!checkbox) {
                console.error('No checkbox found in team element:', element);
                return;
            }

            if (this.selectedTeams.has(teamId)) {
                this.selectedTeams.delete(teamId);
                element.classList.remove('selected', 'bg-blue-50', 'border-blue-500');
                checkbox.checked = false;
            } else {
                this.selectedTeams.add(teamId);
                element.classList.add('selected', 'bg-blue-50', 'border-blue-500');
                checkbox.checked = true;
            }

            console.log('Selected teams:', Array.from(this.selectedTeams));
        } catch (error) {
            console.error('Error in toggleTeam:', error);
            this.showError('Error selecting team');
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