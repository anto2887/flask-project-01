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
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderTeams(data.teams);
            } else {
                this.showError('Error loading teams');
            }
        } catch (error) {
            this.showError('Failed to load teams');
        }
    }

    renderTeams(teams) {
        const container = document.getElementById('teamsContainer');
        container.innerHTML = teams.map(team => `
            <div class="team-option" data-team-id="${team.id}">
                <img src="${team.logo}" alt="${team.name} logo">
                <span>${team.name}</span>
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
            element.classList.remove('selected');
            checkbox.checked = false;
        } else {
            this.selectedTeams.add(teamId);
            element.classList.add('selected');
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
                body: formData
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Error creating group');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-100 text-red-700 p-4 rounded shadow-lg';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    new GroupCreator();
});