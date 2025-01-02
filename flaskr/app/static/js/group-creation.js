class GroupCreator {
    constructor() {
        this.selectedTeams = new Set();
        this.VALID_PRIVACY_TYPES = ['PRIVATE', 'SEMI_PRIVATE'];
        this.initializeLeagueSelector();
        this.initializeForm();
        console.log('GroupCreator initialized');
    }

    initializeLeagueSelector() {
        const leagueInputs = document.querySelectorAll('input[name="league"]');
        console.log('Found league inputs:', leagueInputs.length);
        leagueInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.loadTeams(e.target.value);
            });
        });
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

        if (this.selectedTeams.size === 0) {
            this.showError('Please select at least one team to track');
            return false;
        }

        console.log('Form validation passed');
        return true;
    }

    async loadTeams(league) {
        try {
            const teamsContainer = document.getElementById('teamsContainer');
            teamsContainer.innerHTML = '<div class="p-4 text-center">Loading teams...</div>';

            console.log('Fetching teams for league:', league);
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const response = await fetch(`/group/api/teams/${encodeURIComponent(league)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Response data:', data);

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch teams');
            }

            // Handle both possible formats: array or object with a teams key
            const teams = Array.isArray(data) ? data : data.teams || [];
            if (teams.length === 0) {
                throw new Error('No teams available for this league');
            }

            console.log('Teams array:', teams);
            console.log('Sample team structure:', teams[0]);
            this.renderTeams(teams);
            
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
                        <img src="${teamLogo}" 
                             alt="${teamName} logo" 
                             class="w-12 h-12 object-contain"
                             onerror="this.style.display='none'">
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
                selectedTeams: Array.from(this.selectedTeams)
            });

            this.selectedTeams.forEach(teamId => {
                formData.append('tracked_teams', teamId);
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
