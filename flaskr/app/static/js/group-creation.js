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

        const formData = new FormData(e.target);
        formData.set('tracked_teams', Array.from(this.selectedTeams));

        try {
            const response = await fetch('/group/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: formData.get('name'),
                    league: formData.get('league'),
                    tracked_teams: Array.from(this.selectedTeams),
                    description: formData.get('description'),
                    privacy_type: formData.get('privacy_type')
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                this.showError(data.message || 'Error creating group');
            }
        } catch (error) {
            console.error('Error creating group:', error);
            this.showError('Error creating group');
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